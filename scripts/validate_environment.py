from __future__ import annotations

import importlib.util
import platform
import sys


def main() -> None:
    checks = {
        "python>=3.10": sys.version_info >= (3, 10),
        "streamlit": importlib.util.find_spec("streamlit") is not None,
        "opencv": importlib.util.find_spec("cv2") is not None,
        "numpy": importlib.util.find_spec("numpy") is not None,
        "Pillow": importlib.util.find_spec("PIL") is not None,
        "skimage": importlib.util.find_spec("skimage") is not None,
        "reportlab": importlib.util.find_spec("reportlab") is not None,
        "geniex": importlib.util.find_spec("geniex") is not None,
    }
    print("StayTrace environment")
    print(f"Python: {sys.version.split()[0]}")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    for name, ok in checks.items():
        print(f"{'OK' if ok else 'MISSING':9} {name}")
    if not checks["geniex"]:
        print("NOTE: GenieX is optional for local development and required only for the Qualcomm-backed deployment path.")


if __name__ == "__main__":
    main()
