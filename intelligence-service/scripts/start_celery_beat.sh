#!/usr/bin/env bash
# Start Celery Beat scheduler (every 20 min) — run from backend/
set -euo pipefail
cd "$(dirname "$0")/.."
exec celery -A app.worker.celery_app:celery_app beat \
  --loglevel=info \
  --scheduler celery.beat:PersistentScheduler
