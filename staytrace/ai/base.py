from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class VisionReasoner(ABC):
    name = "abstract"
    available = False

    @abstractmethod
    def describe(self, image_path: Path, prompt: str) -> str:
        raise NotImplementedError

    def close(self) -> None:
        return None
