#!/usr/bin/env bash
#
# One command to get the ACME Project Tracker running on the workshop VDI.
#
#   chmod +x scripts/setup-vdi.sh
#   ./scripts/setup-vdi.sh
#
# Assumes the workshop's setup-environment.sh has already run, so Python,
# Node and PostgreSQL are present.

set -euo pipefail
cd "$(dirname "$0")/.."

DB_NAME="acme_pm"
DB_USER="acme"
DB_PASS="acme"

echo "==> 1/5 Checking prerequisites"
for tool in python3 node npm psql; do
  if ! command -v "$tool" > /dev/null 2>&1; then
    echo "    MISSING: $tool"
    echo "    Ask the workshop organisers, or run ./bin/setup-environment.sh -d"
    exit 1
  fi
  echo "    found $tool"
done

echo "==> 2/5 Making sure PostgreSQL is running"
if ! pg_isready -q 2>/dev/null; then
  echo "    starting the service"
  sudo systemctl start postgresql || sudo service postgresql start
  sleep 3
fi

echo "==> 3/5 Creating the database and user (skipped if they exist)"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" \
  | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" \
  | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

echo "==> 4/5 Setting up the backend"
cd backend

# Write the .env file the application reads at startup.
if [ ! -f .env ]; then
  cat > .env << ENVEOF
DATABASE_URL=postgresql+psycopg2://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}
JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || echo "workshop-dev-secret-change-me")
CORS_ORIGINS=http://localhost:3030
ENVEOF
  echo "    created backend/.env"
else
  echo "    backend/.env already exists, leaving it alone"
fi

python3 -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt
./.venv/bin/python -m app.seeds.seed_data
cd ..

echo "==> 5/5 Setting up the frontend"
cd frontend
npm install --silent
cd ..

cat << 'MSG'

Setup complete.

Start the application with two terminals:

  Terminal 1:
    cd backend
    source .venv/bin/activate
    uvicorn app.main:app --reload

  Terminal 2:
    cd frontend
    npm run dev

Then open http://localhost:3030 and sign in:

  admin@acme.com   / Admin@123
  manager@acme.com / Manager@123
  viewer@acme.com  / Viewer@123

MSG
