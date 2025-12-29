#!/usr/bin/env bash
set -euo pipefail

echo "==> Running backend tests"
pushd backend >/dev/null
if [ -d "venv" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi
pytest
popd >/dev/null

echo "==> Running frontend tests"
pushd frontend >/dev/null
npm test -- --run
popd >/dev/null

echo "==> All tests completed"
