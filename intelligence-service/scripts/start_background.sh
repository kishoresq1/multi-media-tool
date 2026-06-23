#!/usr/bin/env bash
# Start all background services on localhost (no Docker):
#   1. Redis (if not running)
#   2. Celery worker
#   3. Celery beat (20 min schedule)
#
# Usage (from backend/):
#   ./scripts/start_background.sh
#
# Run FastAPI separately:
#   uvicorn app.main:app --reload --port 8009

set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Zero Day Radar — localhost background setup ==="

./scripts/start_redis_local.sh

if [ ! -d ".venv" ]; then
  echo "Create venv first: python -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo ""
echo "Starting Celery worker (queue=intel)..."
.venv/bin/celery -A app.worker.celery_app:celery_app worker \
  --loglevel=info \
  --queues=intel \
  --concurrency=1 \
  --hostname=zdr-worker@%h &

WORKER_PID=$!
echo "Worker PID: $WORKER_PID"

echo "Starting Celery beat (every ${ZDR_CELERY_BEAT_INTERVAL_MINUTES:-20} min)..."
.venv/bin/celery -A app.worker.celery_app:celery_app beat \
  --loglevel=info &

BEAT_PID=$!
echo "Beat PID: $BEAT_PID"

echo ""
echo "Background jobs running on localhost."
echo "  Redis:  127.0.0.1:6379"
echo "  Worker: PID $WORKER_PID"
echo "  Beat:   PID $BEAT_PID"
echo ""
echo "Trigger manually:"
echo "  curl -X POST http://localhost:8009/api/v1/jobs/run/all"
echo ""
echo "Check status:"
echo "  curl http://localhost:8009/api/v1/health/worker"
echo ""
echo "Press Ctrl+C to stop worker and beat."

trap 'kill $WORKER_PID $BEAT_PID 2>/dev/null; echo Stopped.' INT TERM
wait
