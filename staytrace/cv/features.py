from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class ImageFeatures:
    width: int
    height: int
    mean_brightness: float
    edge_density: float
    blur_score: float
    phash: str


def _phash(image: np.ndarray) -> str:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    dct = cv2.dct(gray)
    low = dct[:8, :8]
    med = np.median(low[1:])
    bits = (low > med).flatten()
    return "".join("1" if bit else "0" for bit in bits)


def extract_features(path: Path) -> ImageFeatures:
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    return ImageFeatures(
        width=int(image.shape[1]),
        height=int(image.shape[0]),
        mean_brightness=float(np.mean(gray)),
        edge_density=float(np.mean(edges > 0)),
        blur_score=float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        phash=_phash(image),
    )


def hamming_distance(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))
