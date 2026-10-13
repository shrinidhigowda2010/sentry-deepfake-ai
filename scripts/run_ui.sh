#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
exec streamlit run app.py --server.port "${PORT:-8501}" --browser.gatherUsageStats false
