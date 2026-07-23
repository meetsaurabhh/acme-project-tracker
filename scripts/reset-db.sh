#!/usr/bin/env bash
# Wipe the database and reload the demo portfolio.
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose exec -T backend python -m app.seeds.seed_data
echo "Demo data reloaded."
