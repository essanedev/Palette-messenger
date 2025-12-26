#!/usr/bin/env sh

set -e

cd /palette-messenger

mkdir -p ./logs
chmod -R 0777 ./logs || true
chown -R palette-user:palette-user ./logs 2>/dev/null || true

python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py compress_files

exec python -m daphne -b 0.0.0.0 -p 8000 Palette.asgi:application