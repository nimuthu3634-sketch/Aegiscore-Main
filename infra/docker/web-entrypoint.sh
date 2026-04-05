#!/bin/sh
set -eu

cd /srv/apps/web

echo "Syncing web dependencies into the mounted node_modules volume..."
npm install --no-fund --no-audit

exec "$@"
