#!/usr/bin/env bash
# Start the API from the repository root. Redis is optional; local fallback is automatic.
set -euo pipefail
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
