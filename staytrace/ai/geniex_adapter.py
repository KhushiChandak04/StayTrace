from __future__ import annotations

import json
import os
from pathlib import Path

from .base import VisionReasoner


class GenieXUnavailable(RuntimeError):
    pass


class GenieXReasoner(VisionReasoner):
    name = "qualcomm-geniex"

    def __init__(self, model_id: str, device_map: str = "qairt") -> None:
        try:
            from geniex import AutoModelForCausalLM
        except Exception as exc:  # pragma: no cover - platform dependent
            raise GenieXUnavailable(
                "GenieX Python package is not installed in this environment."
            ) from exc

        self.model_id = model_id
        self.device_map = device_map
        self._model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map=device_map,
        )
        self.available = True

    @staticmethod
    def _extract_text(output) -> str:
        if hasattr(output, "text"):
            return str(output.text)
        return str(output)

    def describe(self, image_path: Path, prompt: str) -> str:
        image_path = image_path.resolve()
        if not image_path.exists():
            raise FileNotFoundError(image_path)

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": str(image_path)},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        template = self._model.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        output = self._model.generate(
            template,
            images=[str(image_path)],
            max_new_tokens=384,
        )
        return self._extract_text(output)

    def describe_json(self, image_path: Path, prompt: str) -> dict:
        raw = self.describe(image_path, prompt)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                return json.loads(raw[start : end + 1])
        raise ValueError("GenieX model did not return valid JSON.")

    def close(self) -> None:
        model = getattr(self, "_model", None)
        if model is not None and hasattr(model, "close"):
            model.close()


def build_reasoner(model_id: str, device_map: str, backend: str):
    if backend in {"demo", "none"}:
        from .heuristic import HeuristicReasoner

        return HeuristicReasoner()

    try:
        return GenieXReasoner(model_id=model_id, device_map=device_map)
    except Exception:
        if backend == "geniex":
            raise
        from .heuristic import HeuristicReasoner

        return HeuristicReasoner()
