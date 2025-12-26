#!/usr/bin/env sh

set -e

ENVIRONMENT=${DJANGO_ENVIRONMENT:-development}

if [ "$ENVIRONMENT" = "production" ]; then
    PORT=${PORT:-8001}
else
    PORT=${PORT:-8000}
fi

mkdir -p ./logs ./static ./staticfiles ./media

if [ "$ENVIRONMENT" = "production" ]; then
    chmod -R 0777 ./logs ./static ./staticfiles ./media || true
    chown -R palette-user:palette-user ./logs ./static ./staticfiles ./media 2>/dev/null || true

    python manage.py collectstatic --noinput
    python manage.py migrate --noinput
else
    python manage.py migrate --noinput || echo "Warning: migrate failed"
fi

exec python -m daphne -b 0.0.0.0 -p "$PORT" Palette.asgi:application
#!/usr/bin/env sh

set -e

ENVIRONMENT=${DJANGO_ENVIRONMENT:-development}

if [ "$ENVIRONMENT" = "production" ]; then
	PORT=${PORT:-8001}
else
	PORT=${PORT:-8000}
fi

mkdir -p ./logs ./static ./staticfiles ./media

if [ "$ENVIRONMENT" = "production" ]; then
	chmod -R 0777 ./logs ./static ./staticfiles ./media || true
	chown -R palette-user:palette-user ./logs ./static ./staticfiles ./media 2>/dev/null || true

	python manage.py collectstatic --noinput
	python manage.py migrate --noinput
else
	python manage.py migrate --noinput || echo "Warning: migrate failed"
fi

exec python -m daphne -b 0.0.0.0 -p "$PORT" Palette.asgi:application