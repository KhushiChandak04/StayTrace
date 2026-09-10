from pathlib import Path

import cv2
import numpy as np

from staytrace.cv.diff import compare_images
from staytrace.cv.align import align_images


def test_identical_images_have_low_change():
    img = np.full((240, 320, 3), 120, dtype=np.uint8)
    result = compare_images(img, img.copy())
    assert result.score < 0.01
    assert result.changed_area_ratio == 0.0


def test_changed_region_is_detected():
    before = np.full((240, 320, 3), 120, dtype=np.uint8)
    after = before.copy()
    cv2.rectangle(after, (100, 80), (180, 150), (230, 230, 230), -1)
    result = compare_images(before, after)
    assert result.changed_area_ratio > 0.05
    assert result.changed_area_ratio > 0.0


def test_alignment_returns_same_shape():
    before = np.zeros((200, 300, 3), dtype=np.uint8)
    after = np.zeros((100, 150, 3), dtype=np.uint8)
    result = align_images(before, after)
    assert result.aligned.shape == before.shape
