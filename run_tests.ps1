$ErrorActionPreference = "Stop"
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest -q
