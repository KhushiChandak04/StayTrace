from staytrace.core.service import _pair_media


def row(identifier: str, name: str):
    return {"id": identifier, "original_name": name}


def test_pair_media_prefers_matching_filenames():
    before = [row("b1", "01_desk.jpg"), row("b2", "02_bed.jpg")]
    after = [row("a2", "02_bed.jpg"), row("a1", "01_desk.jpg")]
    pairs = _pair_media(before, after)
    assert [(a["original_name"], b["original_name"], method) for a, b, method in pairs] == [
        ("01_desk.jpg", "01_desk.jpg", "filename"),
        ("02_bed.jpg", "02_bed.jpg", "filename"),
    ]


def test_pair_media_falls_back_to_capture_order():
    before = [row("b1", "left.jpg"), row("b2", "right.jpg")]
    after = [row("a1", "out_a.jpg"), row("a2", "out_b.jpg")]
    pairs = _pair_media(before, after)
    assert len(pairs) == 2
    assert all(method == "capture-order-fallback" for _, _, method in pairs)


def test_fallback_findings_normalizes_bbox_to_dict():
    from staytrace.core.service import _fallback_findings

    change = {
        "difference": {
            "score": 0.2,
            "changed_area_ratio": 0.05,
            "bbox": (10, 20, 30, 40),
        }
    }
    findings = _fallback_findings(change, "before.jpg", "after.jpg")
    assert findings[0].region == {"x": 10, "y": 20, "width": 30, "height": 40}
