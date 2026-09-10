from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class AlignmentResult:
    aligned: np.ndarray
    score: float
    method: str


def _resize_to_reference(image: np.ndarray, reference: np.ndarray) -> np.ndarray:
    h, w = reference.shape[:2]
    return cv2.resize(image, (w, h), interpolation=cv2.INTER_AREA)


def align_images(reference: np.ndarray, candidate: np.ndarray) -> AlignmentResult:
    candidate = _resize_to_reference(candidate, reference)
    gray_ref = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    gray_candidate = cv2.cvtColor(candidate, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(nfeatures=1500)
    kp1, des1 = orb.detectAndCompute(gray_ref, None)
    kp2, des2 = orb.detectAndCompute(gray_candidate, None)
    if des1 is None or des2 is None or len(kp1) < 8 or len(kp2) < 8:
        return AlignmentResult(candidate, 0.0, "resize-only")

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = matcher.knnMatch(des2, des1, k=2)
    good = [m for m, n in matches if m.distance < 0.72 * n.distance]
    if len(good) < 8:
        return AlignmentResult(candidate, len(good) / 20.0, "orb-no-homography")

    src = np.float32([kp2[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kp1[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    matrix, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    if matrix is None:
        return AlignmentResult(candidate, min(1.0, len(good) / 40.0), "orb-no-homography")

    aligned = cv2.warpPerspective(candidate, matrix, (reference.shape[1], reference.shape[0]))
    inlier_ratio = float(mask.mean()) if mask is not None else 0.0
    return AlignmentResult(aligned, inlier_ratio, "orb-homography")
