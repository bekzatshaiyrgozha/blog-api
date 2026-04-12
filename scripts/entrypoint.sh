#!/bin/bash
set -euo pipefail

echo "Waiting for Redis..."
REDIS_URL=${BLOG_REDIS_URL:-redis://redis:6379/0}
REDIS_HOST=$(echo $REDIS_URL | sed 's/redis:\/\/\([^:]*\).*/\1/')
REDIS_PORT=${REDIS_PORT:-6379}

for i in {1..30}; do
    if nc -z $REDIS_HOST $REDIS_PORT 2>/dev/null; then
        echo "Redis is ready"
        break
    fi
    echo "Redis not ready, waiting... ($i/30)"
    sleep 1
done

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Compiling messages..."
django-admin compilemessages || true

if [ "${BLOG_SEED_DB:-false}" = "true" ]; then
    echo "Seeding database..."
    python manage.py seed || true
fi

echo "Starting application..."
exec "$@"