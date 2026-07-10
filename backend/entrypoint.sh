#!/bin/sh
set -e

echo "[entrypoint] applying database migrations (alembic upgrade head)..."
alembic upgrade head

echo "[entrypoint] starting API..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
