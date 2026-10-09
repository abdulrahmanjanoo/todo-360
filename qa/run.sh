#!/usr/bin/env bash
# One command to self-test To-Do 360.
#   qa/run.sh          -> install Playwright (first run) + python unit tests + browser tests on a fake vault
#   qa/run.sh app      -> only the specs whose file name matches
set -e
cd "$(dirname "$0")"

if [ ! -d node_modules/@playwright ]; then
  echo "Installing @playwright/test (uses the system Chrome, no browser download)…"
  npm install --no-audit --no-fund
fi

# 1. Python unit tests (exporter, money lens, decisions, server guards)
(cd .. && python3 -m unittest discover -s tests -q) || { echo "PYTHON UNIT TESTS FAILED"; exit 1; }

# 2. Browser tests against a server on a throwaway vault
PORT=${TODO360_QA_PORT:-8361}
python3 fake_server.py "$PORT" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null' EXIT
for i in $(seq 1 30); do curl -sf "http://127.0.0.1:$PORT/api/snapshot" >/dev/null && break; sleep 0.2; done
TODO360_URL="http://127.0.0.1:$PORT" npx playwright test "$@"
