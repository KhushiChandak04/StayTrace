from __future__ import annotations

import io
import os
import platform
import sys
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from staytrace.ai import build_reasoner
from staytrace.core.config import Settings
from staytrace.core.models import ConditionStatus
from staytrace.core.service import analyze_claim, analyze_inspections, describe_images, save_upload
from staytrace.db import Store
from staytrace.report import build_report


st.set_page_config(page_title="StayTrace", page_icon="ST", layout="wide")


@st.cache_resource(show_spinner=False)
def get_settings() -> Settings:
    settings = Settings.from_env()
    settings.ensure_dirs()
    return settings


@st.cache_resource(show_spinner=False)
def get_store(db_path: str) -> Store:
    return Store(Path(db_path))


@st.cache_resource(show_spinner=False)
def get_reasoner(backend: str, model_id: str, device_map: str):
    return build_reasoner(model_id, device_map, backend)


def image_from_path(path: str):
    return Image.open(path)


def init_state() -> None:
    if "project_id" not in st.session_state:
        st.session_state.project_id = None
    if "last_comparison" not in st.session_state:
        st.session_state.last_comparison = None


def header() -> None:
    st.markdown(
        """
        <style>
        .hero {padding: 8px 0 16px 0;}
        .hero h1 {font-size: 42px; margin-bottom: 4px;}
        .hero p {font-size: 17px; color: #5b6470;}
        .metric-card {padding: 12px 16px; border: 1px solid #e5e7eb; border-radius: 12px; background: #fafafa;}
        </style>
        <div class='hero'>
          <h1>StayTrace</h1>
          <p>Visual evidence intelligence for shared living spaces.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar(settings: Settings, store: Store) -> None:
    st.sidebar.header("Workspace")
    projects = store.list_projects()
    names = [f"{r['name']} — {r['id'][:6]}" for r in projects]
    choice = st.sidebar.selectbox("Project", ["Create new project"] + names)
    if choice == "Create new project":
        name = st.sidebar.text_input("Project name", value="Room 407 Evidence Record")
        if st.sidebar.button("Create project", use_container_width=True):
            st.session_state.project_id = store.create_project(name.strip() or "Untitled room")
            st.rerun()
    else:
        idx = names.index(choice)
        st.session_state.project_id = projects[idx]["id"]

    backend_options = ["auto", "demo", "geniex"]
    backend = st.sidebar.selectbox("AI backend", backend_options, index=backend_options.index(settings.backend) if settings.backend in backend_options else 0)
    if backend != settings.backend:
        st.sidebar.caption(f"Environment default: {settings.backend}")
    if backend == "geniex":
        st.sidebar.caption("Requires Qualcomm GenieX on a supported Snapdragon Windows ARM64 environment.")
    st.sidebar.divider()
    st.sidebar.caption(f"Python {platform.python_version()} • {platform.system()} {platform.machine()}")
    st.sidebar.caption(f"Data: {settings.data_dir.resolve()}")


def project_required() -> bool:
    if not st.session_state.project_id:
        st.info("Create or select a project in the sidebar to begin.")
        return False
    return True


def save_uploaded_files(files, inspection_id: str, store: Store, settings: Settings) -> list[dict]:
    saved = []
    for file in files:
        try:
            path, sha, width, height = save_upload(file, settings.data_dir / "media")
            media_id = store.add_media(inspection_id, str(path), file.name, sha, width, height)
            saved.append({"id": media_id, "path": str(path), "name": file.name, "width": width, "height": height})
        except Exception as exc:
            st.error(f"Could not ingest {file.name}: {exc}")
    return saved


def page_inspect(settings: Settings, store: Store, reasoner) -> None:
    st.subheader("1. Capture inspection")
    room = st.text_input("Room / property", value="Room 407")
    kind = st.radio("Inspection", ["move-in", "move-out"], horizontal=True)
    notes = st.text_area("Inspection notes", placeholder="Optional notes that should appear in the evidence record.")
    demo_cols = st.columns([1, 2])
    use_demo = demo_cols[0].button("Load built-in demo", use_container_width=True)
    if use_demo:
        demo_name = "move_in_room.jpg" if kind == "move-in" else "move_out_room.jpg"
        demo_path = settings.data_dir.parent / "data" / "demo" / demo_name
        if not demo_path.exists():
            fallback = Path("data/demo") / demo_name
            demo_path = fallback
        if demo_path.exists():
            st.session_state.demo_path = str(demo_path.resolve())
            st.success(f"Loaded {demo_name}")
        else:
            st.error("Demo asset not found. Run: python scripts/generate_demo.py")
    files = st.file_uploader("Upload inspection photos", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
    camera = st.camera_input("Or capture one photo")
    sources = list(files or [])
    if camera is not None:
        sources.append(camera)
    demo_path = Path(st.session_state.get("demo_path", "")) if st.session_state.get("demo_path") else None
    can_create = bool(sources) or bool(demo_path and demo_path.exists())

    if st.button("Create inspection record", type="primary", disabled=not can_create, use_container_width=True):
        iid = store.create_inspection(st.session_state.project_id, room, kind, notes)
        saved = save_uploaded_files(sources, iid, store, settings)
        if demo_path and demo_path.exists() and not sources:
            with demo_path.open("rb") as handle:
                from types import SimpleNamespace
                wrapper = SimpleNamespace(name=demo_path.name, getbuffer=lambda: handle.read())
                handle.seek(0)
                path = settings.data_dir / "media" / f"demo_{demo_path.name}"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(demo_path.read_bytes())
                from staytrace.utils.io import sha256_file, validate_image
                width, height = validate_image(path)
                mid = store.add_media(iid, str(path), demo_path.name, sha256_file(path), width, height)
                saved = [{"id": mid, "path": str(path), "name": demo_path.name}]
            st.session_state.demo_path = None
        if saved:
            with st.spinner("Analyzing visible evidence..."):
                observations = describe_images(store, reasoner, iid, store.get_media(iid))
            st.success(f"Stored {len(saved)} image(s) and {len(observations)} observation(s).")
            st.session_state.last_inspection_id = iid

    st.divider()
    inspections = store.get_inspections(st.session_state.project_id)
    if not inspections:
        st.caption("No inspections yet.")
        return
    for inspection in inspections:
        with st.expander(f"{inspection['type'].upper()} • {inspection['room_name']} • {inspection['captured_at']}"):
            media = store.get_media(inspection["id"])
            cols = st.columns(min(4, max(1, len(media))))
            for i, m in enumerate(media):
                cols[i % len(cols)].image(m["path"], caption=m["original_name"], use_container_width=True)
            obs = store.get_observations(inspection["id"])
            if obs:
                st.dataframe(
                    [{"label": o["label"], "condition": o["condition"], "confidence": f"{o['confidence']*100:.0f}%", "source": o["source"]} for o in obs],
                    use_container_width=True,
                    hide_index=True,
                )


def page_compare(settings: Settings, store: Store, reasoner) -> None:
    st.subheader("2. Compare move-in vs move-out")
    move_ins = store.get_inspections(st.session_state.project_id, "move-in")
    move_outs = store.get_inspections(st.session_state.project_id, "move-out")
    if not move_ins or not move_outs:
        st.warning("Create at least one move-in and one move-out inspection first.")
        return
    before = st.selectbox("Move-in record", move_ins, format_func=lambda x: f"{x['room_name']} • {x['captured_at']}")
    after = st.selectbox("Move-out record", move_outs, format_func=lambda x: f"{x['room_name']} • {x['captured_at']}")
    before_media = store.get_media(before["id"])
    after_media = store.get_media(after["id"])
    if not before_media or not after_media:
        st.warning("Both inspections need photos.")
        return
    st.caption(f"The engine currently compares paired photos in capture order: {min(len(before_media), len(after_media))} pair(s).")
    if st.button("Run evidence comparison", type="primary", use_container_width=True):
        with st.spinner("Aligning images and computing semantic change candidates..."):
            findings, report = analyze_inspections(store, st.session_state.project_id, before["id"], after["id"])
        st.session_state.last_comparison = {"findings": [f.model_dump() for f in findings], "report": report}
        st.success(f"Generated {len(findings)} comparison finding(s).")

    result = st.session_state.last_comparison
    if not result:
        return
    findings = result["findings"]
    counts = {status.value: sum(f["status"] == status.value for f in findings) for status in ConditionStatus}
    cols = st.columns(5)
    for i, (label, count) in enumerate([("Unchanged", counts["unchanged"]), ("New", counts["new"]), ("Pre-existing", counts["pre-existing"]), ("Missing", counts["missing"]), ("Review", sum(f["review_required"] for f in findings))]):
        cols[i].metric(label, count)

    for i, pair in enumerate(result["report"]["pairs"], 1):
        st.markdown(f"### Evidence pair {i}")
        c1, c2, c3 = st.columns(3)
        c1.image(pair["before"], caption="Move-in", use_container_width=True)
        c2.image(pair["after"], caption="Move-out", use_container_width=True)
        # Heatmap is kept in memory by the analysis function; recompute for display without exposing internal image buffers.
        from staytrace.cv.pipeline import analyze_pair
        cv = analyze_pair(Path(pair["before"]), Path(pair["after"]))
        c3.image(cv["heatmap"][:, :, ::-1], caption="Difference heatmap", use_container_width=True)
        st.json({"alignment": pair["alignment"], "difference": pair["difference"], "candidate_regions": pair["regions"]})

    st.dataframe(
        [{
            "object": f["object_label"],
            "status": f["status"],
            "confidence": f"{f['confidence']*100:.0f}%",
            "review": "Yes" if f["review_required"] else "No",
            "explanation": f["explanation"],
        } for f in findings],
        use_container_width=True,
        hide_index=True,
    )


def page_claims(store: Store) -> None:
    st.subheader("3. Ask the evidence")
    findings = store.get_findings(st.session_state.project_id)
    if not findings:
        st.info("Run a comparison first.")
        return
    claim = st.text_area("Claim to check", value="The desk was damaged during the stay.")
    if st.button("Analyze claim", use_container_width=True):
        result = analyze_claim(store, st.session_state.project_id, claim, findings)
        st.session_state.last_claim = result.model_dump()
    if "last_claim" in st.session_state:
        r = st.session_state.last_claim
        st.markdown(f"### {r['outcome']}")
        st.write(f"**Confidence:** {r['confidence']}")
        st.write(r["rationale"])
        if r["evidence"]:
            st.write("Evidence notes:")
            for e in r["evidence"]:
                st.write(f"- {e}")
        st.caption(r["caveat"])


def page_report(settings: Settings, store: Store) -> None:
    st.subheader("4. Export")
    findings = store.get_findings(st.session_state.project_id)
    claims = store.get_claims(st.session_state.project_id)
    projects = [p for p in store.list_projects() if p["id"] == st.session_state.project_id]
    if not projects:
        return
    project = projects[0]
    inspections = store.get_inspections(st.session_state.project_id)
    room = inspections[0]["room_name"] if inspections else "Unknown"
    if st.button("Generate PDF report", type="primary", use_container_width=True):
        out = settings.data_dir / "reports" / f"staytrace_{project['id'][:8]}.pdf"
        build_report(out, project["name"], room, findings, claims)
        st.session_state.report_path = str(out)
        st.success("Report generated locally.")
    if st.session_state.get("report_path"):
        path = Path(st.session_state.report_path)
        st.download_button("Download report", path.read_bytes(), file_name=path.name, mime="application/pdf")

    payload = {
        "project": dict(project),
        "inspections": [dict(i) for i in inspections],
        "findings": findings,
        "claims": claims,
    }
    import json
    st.download_button("Download evidence JSON", json.dumps(payload, indent=2), file_name="staytrace_evidence.json", mime="application/json")


def page_diagnostics(settings: Settings, store: Store, reasoner) -> None:
    st.subheader("5. Runtime diagnostics")
    st.write("The diagnostics screen is deliberately factual: it reports what this process can observe, not what a benchmark is expected to show.")
    rows = [
        ("Python", platform.python_version()),
        ("OS", platform.platform()),
        ("Architecture", platform.machine()),
        ("CPU", platform.processor() or "unknown"),
        ("AI backend", getattr(reasoner, "name", "unknown")),
        ("GenieX model", settings.geniex_model),
        ("GenieX device map", settings.geniex_device_map),
        ("Data directory", str(settings.data_dir.resolve())),
    ]
    st.table({"Property": [r[0] for r in rows], "Value": [r[1] for r in rows]})
    st.info("On a Snapdragon validation machine, run the real GenieX backend and record the actual output/latency here. This app does not fabricate Snapdragon benchmark figures.")


def run_app() -> None:
    init_state()
    settings = get_settings()
    settings.ensure_dirs()
    store = get_store(str((settings.data_dir / "db" / "staytrace.sqlite3").resolve()))
    header()
    sidebar(settings, store)
    if not project_required():
        return

    backend = st.sidebar.session_state.get("backend_override", settings.backend)
    # Read the currently selected sidebar value without adding global mutable state.
    selected_backend = st.sidebar.selectbox("Runtime", ["auto", "demo", "geniex"], index=["auto", "demo", "geniex"].index(settings.backend) if settings.backend in ["auto", "demo", "geniex"] else 0, key="runtime_select")
    reasoner = get_reasoner(selected_backend, settings.geniex_model, settings.geniex_device_map)

    tabs = st.tabs(["Inspect", "Compare", "Claims", "Export", "Diagnostics"])
    with tabs[0]:
        page_inspect(settings, store, reasoner)
    with tabs[1]:
        page_compare(settings, store, reasoner)
    with tabs[2]:
        page_claims(store)
    with tabs[3]:
        page_report(settings, store)
    with tabs[4]:
        page_diagnostics(settings, store, reasoner)
