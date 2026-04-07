#!/bin/sh
set -eu

DB_CONNECT_MAX_ATTEMPTS="${DB_CONNECT_MAX_ATTEMPTS:-25}"
DB_CONNECT_BACKOFF_SECONDS="${DB_CONNECT_BACKOFF_SECONDS:-2}"

echo "Waiting for database connectivity..."
attempt=1
while [ "$attempt" -le "$DB_CONNECT_MAX_ATTEMPTS" ]; do
  if python -c "from sqlalchemy import create_engine, text; from app.core.config import get_settings; engine = create_engine(get_settings().database_url, pool_pre_ping=True); conn = engine.connect(); conn.execute(text('SELECT 1')); conn.close()"; then
    echo "Database connection succeeded."
    break
  fi
  echo "Database not ready (attempt ${attempt}/${DB_CONNECT_MAX_ATTEMPTS}); retrying in ${DB_CONNECT_BACKOFF_SECONDS}s..."
  attempt=$((attempt + 1))
  sleep "$DB_CONNECT_BACKOFF_SECONDS"
done

if [ "$attempt" -gt "$DB_CONNECT_MAX_ATTEMPTS" ]; then
  echo "Database did not become reachable before timeout."
  exit 1
fi

echo "Applying database migrations..."
alembic upgrade head

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
