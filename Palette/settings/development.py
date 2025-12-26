from .base import *
import os
import sys

DEBUG = True

CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
 
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'palette_messenger'),
        'USER': os.environ.get('DATABASE_USERNAME', 'postgres'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
        'OPTIONS': {
            'options': '-c client_encoding=UTF8'
        },
    }
}

DATABASES['default']['OPTIONS'] = {
    'options': '-c client_encoding=UTF8'
}

CORS_ALLOW_ALL_ORIGINS = True

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use lightweight SQLite in-memory database when running tests locally
# This allows `python manage.py test` on the host machine to run without
# requiring the Docker Postgres service.
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }