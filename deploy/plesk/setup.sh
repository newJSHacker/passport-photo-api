#!/usr/bin/env bash
# Run on the Plesk server inside:
# /var/www/vhosts/digitalpassportphotos.us/api.digitalpassportphotos.us
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$APP_DIR"

echo "==> Passport Photo API setup in $APP_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required"
  exit 1
fi

if [ ! -f .env ]; then
  cat > .env <<'EOF'
DEBUG=false
CORS_ORIGINS=https://digitalpassportphotos.us,https://www.digitalpassportphotos.us
STORAGE_PATH=storage
BACKGROUND_REMOVER=modnet
DATABASE_URL=postgresql+asyncpg://passport_api:CHANGE_ME@127.0.0.1:5432/passport_photo
EOF
  echo "Created .env — edit DATABASE_URL before going live."
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p storage app/data
python scripts/download_modnet.py || echo "WARN: MODNet download failed; background removal may not work."

alembic upgrade head || echo "WARN: migrations failed — check DATABASE_URL."

cat > start-api.sh <<'EOF'
#!/usr/bin/env bash
cd "$(dirname "$0")"
source .venv/bin/activate
set -a
source .env
set +a
exec uvicorn app.main:app --host 127.0.0.1 --port 8001
EOF
chmod +x start-api.sh

if ! pgrep -f "uvicorn app.main:app" >/dev/null 2>&1; then
  nohup ./start-api.sh > api.log 2>&1 &
  sleep 2
fi

if curl -fsS http://127.0.0.1:8001/health >/dev/null; then
  echo "API is running: http://127.0.0.1:8001/health"
else
  echo "API did not respond on port 8001 — check api.log"
  tail -20 api.log || true
  exit 1
fi
