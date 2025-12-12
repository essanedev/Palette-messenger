#!/usr/bin/env sh

set -e

mkdir -p ./logs ./static ./staticfiles ./media
chmod -R 0777 ./logs ./static ./staticfiles ./media || true
chown -R palette-user:palette-user ./logs ./static ./staticfiles ./media 2>/dev/null || true

#python manage.py collectstatic --noinput
#python manage.py migrate --noinput

#exec python -m daphne -b 0.0.0.0 -p 8000 Palette.asgi:application

# run collect/migrate as palette-user (su -s syntax runs the command as that user)
su -s /bin/sh -c "python manage.py collectstatic --noinput" palette-user
su -s /bin/sh -c "python manage.py migrate --noinput" palette-user

# run daphne as palette-user
exec su -s /bin/sh -c "python -m daphne -b 0.0.0.0 -p 8000 Palette.asgi:application" palette-user