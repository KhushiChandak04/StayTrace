from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Region:
    id: str
    bbox: tuple[int, int, int, int]
    area_ratio: float


def candidate_regions(mask: np.ndarray, max_regions: int = 8) -> list[Region]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = mask.shape[:2]
    image_area = max(1, h * w)
    boxes = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < image_area * 0.002:
            continue
        x, y, rw, rh = cv2.boundingRect(contour)
        boxes.append(Region(f"region-{len(boxes)+1}", (x, y, rw, rh), area / image_area))
    boxes.sort(key=lambda r: r.area_ratio, reverse=True)
    return boxes[:max_regions]
