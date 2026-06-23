#!/usr/bin/env bash
# Start Celery worker — run from backend/
set -euo pipefail
cd "$(dirname "$0")/.."
exec celery -A app.worker.celery_app:celery_app worker \
  --loglevel=info \
  --queues=intel \
  --concurrency=1 \
  --hostname=zdr-worker@%h
