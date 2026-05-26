#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/service-api/service-python"
WEB_DIR="$ROOT_DIR/client-web"

case "${1:-unit}" in
  unit)
    cd "$API_DIR"
    python -m pytest
    ;;
  api)
    cd "$API_DIR"
    python -m pytest tests/test_sentiment.py tests/test_history.py
    ;;
  web)
    cd "$WEB_DIR"
    npm install
    npm run lint
    npm run build
    ;;
  performance)
    cd "$API_DIR"
    python -m pytest -m slow
    ;;
  all)
    "$0" unit
    "$0" web
    ;;
  *)
    echo "Uso: ./scripts/test.sh [unit|api|web|performance|all]"
    exit 1
    ;;
esac
