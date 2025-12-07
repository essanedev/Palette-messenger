йоу, Даня, создаешь окружение, тянешь пакеты. Не забуь создать .env и туда прокинуть креды к бд. мой енв выглядит так:

SECRET_KEY=z(98@e6)n@o(1)2e(ts-a2w^r48q-qvp=vrc-w&b4y7h$o+wb!
DJANGO_ENVIRONMENT=development

DB_NAME=palette_messenger
DB_USER=postgres
DB_PASSWORD=admin1
DB_HOST=localhost
DB_PORT=5432

собственно тут поменяй только db (использую постгри, sqlite - рудимент)) данные, ключик можешь оставить. окружения два про запас: девеломпент и прод

Есть что-то лишнее, что-то про запас аххаха - можешь почистить, думаю, что нужно в таком минимальном виде загрузить на сервак, чтобы тестеры могли потестировать. Блин с пушами задолбался, чот пока не могу придумаь как их порешать. Джава скриптом это надо делать, а это путь фронта. Голосовые, кружки и файлы в целом на потом оставил. Остальное в минимальном режиме воркает

дальше короче запускаешь по через дафни


`python -m daphne -b 127.0.0.1 -p 8000 Palette.asgi:application`

Для дебаг запуска использовать комманду сверху /\
Для деплоя docker compose

.env теперь выглядит вот так:

SECRET_KEY=z(98@e6)n@o(1)2e(ts-a2w^r48q-qvp=vrc-w&b4y7h$o+wb!
DJANGO_ENVIRONMENT=development

CSRF_TRUSTED_ORIGINS = ['https://messengerpalette.ru/']
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '31.57.26.182', '0.0.0.0']

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