from __future__ import annotations

from pathlib import Path

from PIL import Image

from .base import VisionReasoner


class HeuristicReasoner(VisionReasoner):
    name = "deterministic-demo"
    available = True

    def describe(self, image_path: Path, prompt: str) -> str:
        with Image.open(image_path) as image:
            w, h = image.size
        return (
            f"Demo visual analysis for {image_path.name}: image size {w}x{h}. "
            "For competition deployment, replace this descriptive fallback with "
            "the validated Qualcomm GenieX multimodal model."
        )
