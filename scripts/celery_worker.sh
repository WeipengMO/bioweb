#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate
celery -A backend.app.tasks.celery_app.celery_app worker --loglevel=info

