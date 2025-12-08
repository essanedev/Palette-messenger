#!/usr/bin/env sh

set -e

# Ensure necessary directories exist and are writable. When
# `./static` and `./staticfiles` are bind-mounted from the host they
# may be owned by a different user; run permissive chmod/chown so
# `collectstatic` can write into them. Running as root in the
# container allows these operations.
mkdir -p ./logs ./static ./staticfiles ./media
# Make world-writable as a fallback so an unprivileged user can write.
chmod -R 0777 ./logs ./static ./staticfiles ./media || true
# Attempt to chown to the application user if present (no-op if fails).
chown -R palette-user:palette-user ./logs ./static ./staticfiles ./media 2>/dev/null || true

python manage.py collectstatic --noinput
python manage.py migrate --noinput

python -m gunicorn -b 0.0.0.0:8000 Palette.wsgi:application --workers 3 --timeout 120