from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image


ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def safe_filename(name: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    return cleaned.strip("._") or "image.jpg"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_image(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return image.size


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
