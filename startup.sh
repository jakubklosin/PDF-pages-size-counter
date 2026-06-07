#!/usr/bin/env bash
set -e

python -m uvicorn pdf_analyzer.web_app:app --host 0.0.0.0 --port "${PORT:-8000}"
