from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="staytrace")
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run", help="Start the Streamlit app")
    run.add_argument("--port", type=int, default=8501)
    demo = sub.add_parser("demo", help="Generate built-in demo images")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.command == "demo":
        subprocess.run([sys.executable, str(root / "scripts" / "generate_demo.py")], check=True)
    elif args.command == "run":
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(root / "app.py"), "--server.port", str(args.port)], check=True)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
