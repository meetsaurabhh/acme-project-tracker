#!/usr/bin/env bash
# Wipe the database and reload the demo portfolio.
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose exec -T backend python -m app.seed
echo "Demo data reloaded."
