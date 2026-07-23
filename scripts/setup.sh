#!/usr/bin/env bash
# One command to bring the whole stack up and load demo data.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Building and starting containers"
docker compose up -d --build

echo "==> Waiting for the API to answer"
for i in {1..40}; do
  if curl -sf http://localhost:8000/health > /dev/null; then break; fi
  sleep 2
done

echo "==> Loading demo data"
docker compose exec -T backend python -m app.seeds.seed_data

cat <<'MSG'

Everything is running.

  App        http://localhost:3030
  API docs   http://localhost:8000/docs

Sign in with:
  admin@acme.com   / Admin@123
  manager@acme.com / Manager@123
  viewer@acme.com  / Viewer@123

Stop it all with:  docker compose down
MSG
