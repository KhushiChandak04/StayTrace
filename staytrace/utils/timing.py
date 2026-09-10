from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator


@contextmanager
def stopwatch() -> Iterator[callable]:
    start = perf_counter()
    box = {}

    def elapsed_ms() -> float:
        value = (perf_counter() - start) * 1000
        box["ms"] = value
        return value

    try:
        yield elapsed_ms
    finally:
        elapsed_ms()
