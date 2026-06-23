#!/usr/bin/env bash
# Start Redis on localhost (no Docker). Run once before Celery worker/beat.
set -euo pipefail

if redis-cli -h 127.0.0.1 ping >/dev/null 2>&1; then
  echo "Redis already running on 127.0.0.1:6379"
  exit 0
fi

if command -v redis-server >/dev/null 2>&1; then
  echo "Starting redis-server on localhost..."
  redis-server --daemonize yes --bind 127.0.0.1 --port 6379
  sleep 1
  redis-cli ping
  exit 0
fi

echo "Redis not installed. Install on Ubuntu/WSL:"
echo "  sudo apt update && sudo apt install -y redis-server"
echo "  sudo service redis-server start"
exit 1
