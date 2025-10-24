#!/usr/bin/env bash
# Non-interactive start script for the Gym Backend.
# Does not rely on a virtualenv; expects system Python in container.

set -euo pipefail

# Install dependencies if not already installed.
# This is idempotent in the preview container.
if command -v pip3 >/dev/null 2>&1; then
  pip3 install --no-input --disable-pip-version-check -r requirements.txt
else
  echo "pip3 not found. Python environment may be misconfigured." >&2
  exit 1
fi

# Start uvicorn on port 3001
exec uvicorn src.api.main:app --host 0.0.0.0 --port 3001
