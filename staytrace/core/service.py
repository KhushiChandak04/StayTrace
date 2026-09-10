from __future__ import annotations

import re
import uuid
from pathlib import Path

from PIL import Image

from staytrace.ai.prompts import INSPECTION_PROMPT
from staytrace.core.models import (
    ChangeFinding,
    ClaimAnalysis,
    ConditionStatus,
    EvidenceLevel,
    Observation,
)
from staytrace.cv.pipeline import analyze_pair
from staytrace.db.store import Store
from staytrace.utils.io import sha256_file, safe_filename, validate_image
from staytrace.utils.timing import stopwatch


def _heuristic_items(image_path: Path) -> list[dict]:
    """A deterministic offline baseline for the demo environment.

    It intentionally avoids pretending that a classical CV model has semantic understanding.
    It labels common room objects only when obvious text or demo metadata is present, otherwise
    the UI can still operate on visual change scores.
    """
    name = image_path.stem.lower()
    items = []
    demo_tokens = {
        "desk": "study desk",
        "chair": "chair",
        "bed": "bed",
        "cupboard": "cupboard",
        "window": "window",
        "wall": "wall",
        "fan": "ceiling fan",
        "switch": "switchboard",
    }
    for token, label in demo_tokens.items():
        if token in name:
            items.append({
                "label": label,
                "description": f"Demo-tagged {label} reference.",
                "condition": "uncertain",
                "confidence": 0.65,
            })
    if not items:
        items.append({
            "label": "room scene",
            "description": "Room image ingested for visual comparison.",
            "condition": "uncertain",
            "confidence": 0.50,
        })
    return items


def save_upload(uploaded_file, destination_dir: Path) -> tuple[Path, str, int, int]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    name = safe_filename(uploaded_file.name)
    path = destination_dir / f"{uuid.uuid4().hex[:10]}_{name}"
    path.write_bytes(uploaded_file.getbuffer())
    width, height = validate_image(path)
    return path, sha256_file(path), width, height


def describe_images(store: Store, reasoner, inspection_id: str, media_rows: list) -> list[Observation]:
    observations: list[Observation] = []
    for media in media_rows:
        path = Path(media["path"])
        try:
            if getattr(reasoner, "name", "") == "deterministic-demo":
                result = {"items": _heuristic_items(path)}
            else:
                result = reasoner.describe_json(path, INSPECTION_PROMPT)
                if not isinstance(result, dict) or "items" not in result:
                    result = {"items": []}
        except Exception:
            result = {"items": _heuristic_items(path)}

        for item in result.get("items", []):
            obs = Observation(
                inspection_id=inspection_id,
                image_id=media["id"],
                label=str(item.get("label", "unknown")),
                description=str(item.get("description", "")),
                condition=str(item.get("condition", "uncertain")),
                confidence=max(0.0, min(1.0, float(item.get("confidence", 0.5)))),
                source=getattr(reasoner, "name", "unknown"),
            )
            store.add_observation(obs)
            observations.append(obs)
    return observations


def classify_pair(change: dict, before_obs: list[dict], after_obs: list[dict]) -> list[ChangeFinding]:
    score = float(change["difference"]["score"])
    area = float(change["difference"]["changed_area_ratio"])
    bbox = change["difference"].get("bbox")
    common_labels = {str(o["label"]).lower() for o in before_obs} & {str(o["label"]).lower() for o in after_obs}

    if score < 0.07 and area < 0.04:
        return [ChangeFinding(
            object_label="room scene",
            status=ConditionStatus.UNCHANGED,
            confidence=0.93,
            explanation="The aligned images show low structural difference across the scene.",
            region=bbox,
            review_required=False,
        )]

    confidence = min(0.95, max(0.45, 0.55 + score * 1.2 + area * 2.0))
    label = sorted(common_labels)[0] if common_labels else "visual region"
    if area > 0.18:
        status = ConditionStatus.UNCERTAIN
        explanation = "A large visual difference was detected; object-level attribution is uncertain."
        review = True
    elif score > 0.18 or area > 0.08:
        status = ConditionStatus.NEW
        explanation = "A localized visual difference is consistent with a newly changed region; human review is recommended before relying on it."
        review = True
    else:
        status = ConditionStatus.UNCERTAIN
        explanation = "A modest visual difference was detected, but the available evidence is insufficient for a reliable semantic conclusion."
        review = True

    return [ChangeFinding(
        object_label=label,
        status=status,
        confidence=round(confidence, 3),
        explanation=explanation,
        region=bbox,
        review_required=review,
    )]


def analyze_inspections(store: Store, project_id: str, before_id: str, after_id: str) -> tuple[list[ChangeFinding], dict]:
    before_media = store.get_media(before_id)
    after_media = store.get_media(after_id)
    findings: list[ChangeFinding] = []
    pair_reports = []
    for before, after in zip(before_media, after_media):
        result = analyze_pair(Path(before["path"]), Path(after["path"]))
        before_obs = store.get_observations(before_id)
        after_obs = store.get_observations(after_id)
        pair_findings = classify_pair(result, before_obs, after_obs)
        for finding in pair_findings:
            finding.move_in_image = before["path"]
            finding.move_out_image = after["path"]
            fid = store.add_finding(project_id, finding)
            finding.evidence_ids = [fid]
        findings.extend(pair_findings)
        pair_reports.append({
            "before": before["path"],
            "after": after["path"],
            "alignment": result["alignment"],
            "difference": result["difference"],
            "regions": result["regions"],
        })
    return findings, {"pairs": pair_reports}


def analyze_claim(store: Store, project_id: str, claim: str, findings: list[dict]) -> ClaimAnalysis:
    text = claim.lower().strip()
    if not findings:
        result = ClaimAnalysis(
            claim=claim,
            outcome="No stored findings available",
            confidence=EvidenceLevel.INCONCLUSIVE,
            rationale="The evidence store contains no comparison findings for this project.",
        )
    elif any(key in text for key in ("damaged", "damage", "broke", "broken", "crack", "scratch", "stain")):
        new = [f for f in findings if f.get("status") == ConditionStatus.NEW.value]
        pre = [f for f in findings if f.get("status") == ConditionStatus.PRE_EXISTING.value]
        if new and not pre:
            result = ClaimAnalysis(
                claim=claim,
                outcome="Evidence is consistent with a newly detected change",
                confidence=EvidenceLevel.MEDIUM,
                rationale="The stored comparison contains at least one finding classified as new. This is not a causation or liability finding.",
                evidence=[f.get("explanation", "") for f in new],
            )
        elif pre:
            result = ClaimAnalysis(
                claim=claim,
                outcome="Evidence contains a pre-existing condition",
                confidence=EvidenceLevel.MEDIUM,
                rationale="At least one relevant issue was recorded as pre-existing. Check the linked images before drawing a conclusion.",
                evidence=[f.get("explanation", "") for f in pre],
            )
        else:
            result = ClaimAnalysis(
                claim=claim,
                outcome="Inconclusive",
                confidence=EvidenceLevel.LOW,
                rationale="The current evidence does not support a reliable classification of the claim.",
            )
    else:
        result = ClaimAnalysis(
            claim=claim,
            outcome="Inconclusive",
            confidence=EvidenceLevel.LOW,
            rationale="The prototype supports condition/change claims; this claim does not map cleanly to stored visual findings.",
        )
    store.add_claim(project_id, result)
    return result
