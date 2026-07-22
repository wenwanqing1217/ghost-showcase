#!/bin/bash
set -e
cd "$(dirname "$0")/.."
pip install -e ".[dev]"
playwright install chromium
uvicorn mindflow_map.main:app --reload --port 2002 --host 0.0.0.0
