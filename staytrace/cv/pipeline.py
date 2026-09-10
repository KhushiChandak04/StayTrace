from __future__ import annotations

from pathlib import Path

import cv2

from .align import align_images
from .diff import compare_images
from .regions import candidate_regions


def analyze_pair(before_path: Path, after_path: Path) -> dict:
    before = cv2.imread(str(before_path))
    after = cv2.imread(str(after_path))
    if before is None or after is None:
        raise ValueError("One or both images could not be read.")
    alignment = align_images(before, after)
    difference = compare_images(before, alignment.aligned)
    regions = candidate_regions(difference.mask)
    return {
        "alignment": {
            "method": alignment.method,
            "confidence": round(alignment.score, 4),
        },
        "difference": {
            "score": round(difference.score, 4),
            "changed_area_ratio": round(difference.changed_area_ratio, 4),
            "bbox": difference.bbox,
        },
        "regions": [
            {"id": r.id, "bbox": r.bbox, "area_ratio": round(r.area_ratio, 4)}
            for r in regions
        ],
        "heatmap": difference.heatmap,
    }
