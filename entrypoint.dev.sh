#!/usr/bin/env sh

set -e

ENVIRONMENT=${DJANGO_ENVIRONMENT:-development}

if [ "$ENVIRONMENT" = "production" ]; then
	PORT=${PORT:-8001}
else
	PORT=${PORT:-8000}
fi

mkdir -p ./logs
python manage.py collectstatic --noinput
python manage.py migrate --noinput

python -m daphne -b 0.0.0.0 -p "$PORT" Palette.asgi:application