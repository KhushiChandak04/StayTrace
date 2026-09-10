from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from skimage.metrics import structural_similarity


@dataclass
class DifferenceResult:
    score: float
    mask: np.ndarray
    heatmap: np.ndarray
    changed_area_ratio: float
    bbox: tuple[int, int, int, int] | None


def _largest_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(contour)
    return int(x), int(y), int(w), int(h)


def compare_images(before: np.ndarray, after: np.ndarray) -> DifferenceResult:
    if before.shape[:2] != after.shape[:2]:
        after = cv2.resize(after, (before.shape[1], before.shape[0]), interpolation=cv2.INTER_AREA)

    gray_before = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    gray_after = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
    ssim_score, similarity = structural_similarity(gray_before, gray_after, full=True)
    diff = (1.0 - similarity).clip(0, 1)
    threshold = (diff > max(0.16, np.percentile(diff, 85))).astype(np.uint8) * 255
    kernel = np.ones((5, 5), np.uint8)
    threshold = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel)
    threshold = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel)
    changed_ratio = float(np.mean(threshold > 0))
    change_score = float(1.0 - ssim_score)
    heatmap = cv2.applyColorMap((diff * 255).astype(np.uint8), cv2.COLORMAP_JET)
    return DifferenceResult(
        score=change_score,
        mask=threshold,
        heatmap=heatmap,
        changed_area_ratio=changed_ratio,
        bbox=_largest_bbox(threshold),
    )
