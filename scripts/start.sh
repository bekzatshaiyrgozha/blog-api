#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "Reading .env (if present) and verifying required variables..."
if [ -f settings/.env.example ]; then
  REQUIRED_VARS=$(awk -F= '/^[^#]/ {print $1}' settings/.env.example)
else
  echo "Missing settings/.env.example" >&2
  exit 1
fi

MISSING=0
for VAR in $REQUIRED_VARS; do
  if [ -z "${!VAR:-}" ]; then
    echo "Missing environment variable: $VAR" >&2
    MISSING=1
  fi
done
if [ "$MISSING" -eq 1 ]; then
  echo "One or more environment variables are missing. Aborting." >&2
  exit 2
fi

echo "Creating virtualenv (venv) if missing..."
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements/base.txt

echo "Running migrations..."
python3 manage.py migrate

echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Compiling translations (if any)..."
if command -v django-admin >/dev/null 2>&1; then
  django-admin compilemessages || true
fi

echo "Creating superuser if not exists..."
python3 manage.py shell -c "from django.contrib.auth import get_user_model;U=get_user_model();
print('superuser exists' if U.objects.filter(email='admin@example.com').exists() else U.objects.create_superuser('admin@example.com','adminpass','Admin','User'))"

echo "Seeding database..."
python3 manage.py seed_data || true

echo "Starting development server..."
python3 manage.py runserver 0.0.0.0:8000
