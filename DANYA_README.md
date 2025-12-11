
SECRET_KEY=z(98@e6)n@o(1)2e(ts-a2w^r48q-qvp=vrc-w&b4y7h$o+wb!
DJANGO_ENVIRONMENT=development

DB_NAME=palette_messenger
DB_USER=postgres
DB_PASSWORD=admin1
DB_HOST=localhost
DB_PORT=5432

дальше короче запускаешь по через дафни

`python -m daphne -b 127.0.0.1 -p 8000 Palette.asgi:application`

------------------------------
Надеюсь как сетапить докер ты знаешь а дальше всё расписано.

Для того чтобы собрать проект в дев режиме используй
docker compose -f ./docker-compose-dev.yml up -d --build palette
 
Чтобы разобрать 
docker compose down -f ./docker-compose-dev.yml --volumes --rmi all

Чтобы разобрать статику и не коммитить на гит
python manage.py collectstatic --noinput --clear --no-post-process

# .env Для прода:

DATABASE_URL=postgresql://postgres:475PzuSvqa6u@palette-database-gssyhi:5432/palette_messenger
BETTER_AUTH_SECRET=9lbG9HJsF6r3ZbD9ibevQZcT0Pa96R86
SECRET_KEY=z(98@e6)n@o(1)2e(ts-a2w^r48q-qvp=vrc-w&b4y7h$o+wb!
DJANGO_ENVIRONMENT=development

CORS_ALLOWED_ORIGINS=https://messengerpalette.ru,https://217.60.1.117:8001
CSRF_TRUSTED_ORIGINS=https://messengerpalette.ru,https://217.60.1.117:8001
ALLOWED_HOSTS=localhost,127.0.0.1,217.60.1.117,0.0.0.0

# Database settings
DATABASE_ENGINE=postgresql_psycopg2
DATABASE_NAME=palette_messenger
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=475PzuSvqa6u
DATABASE_HOST=palette-database-gssyhi
DATABASE_PORT=5432

# Postgrtes container settings
POSTGRES_DB=palette_messenger
POSTGRES_USER=postgres
POSTGRES_PASSWORD=475PzuSvqa6u


# .env Для дебага:


DATABASE_URL=postgresql://postgres:475PzuSvqa6u@palette-database-gssyhi:5432/palette_messenger
BETTER_AUTH_SECRET=9lbG9HJsF6r3ZbD9ibevQZcT0Pa96R86
SECRET_KEY=z(98@e6)n@o(1)2e(ts-a2w^r48q-qvp=vrc-w&b4y7h$o+wb!
DJANGO_ENVIRONMENT=development

CORS_ALLOWED_ORIGINS=https://messengerpalette.ru,https://217.60.1.117:8001,http://localhost:8000,http://127.0.0.1:8000
CSRF_TRUSTED_ORIGINS=https://messengerpalette.ru,https://217.60.1.117:8001,http://localhost:8000,http://127.0.0.1:8000
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database settings
DATABASE_ENGINE=postgresql_psycopg2
DATABASE_NAME=palette_messenger
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=475PzuSvqa6u
DATABASE_HOST=db
DATABASE_PORT=5432

# Postgrtes container settings
POSTGRES_DB=palette_messenger
POSTGRES_USER=postgres
POSTGRES_PASSWORD=475PzuSvqa6u