#!/bin/sh
set -eu

cd /srv/apps/web

echo "Checking web dependencies..."
if npm ls react-router-dom >/dev/null 2>&1; then
  echo "Dependencies already available."
else
  echo "react-router-dom missing; syncing dependencies into mounted node_modules..."
  if [ -f package-lock.json ]; then
    npm ci --no-fund --no-audit
  else
    npm install --no-fund --no-audit
  fi
fi

exec "$@"
