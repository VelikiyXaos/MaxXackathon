# Запуск базы данных через Docker

БД PostgreSQL запускается в контейнере посредством `docker compose`.

## Требования

- Docker Desktop (или любой docker daemon с `docker compose`)
- Python 3.10+ для применения миграций

## Конфигурация

Параметры подключения задаются в `.env` (файл создаётся из `.env.template`):

```
POSTGRES_USER=hackathon
POSTGRES_PASSWORD=hackathon
POSTGRES_DB=hackathon
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://hackathon:hackathon@localhost:5432/hackathon
```

Значения по умолчанию проставлены в `docker-compose.yml` — `.env` можно не создавать,
если устраивают дефолты.

## Запуск

```bash
docker compose up -d db
```

Контейнер `hackathon_db` поднимает PostgreSQL на порту 5432. Данные хранятся
в docker volume `pgdata` и переживают перезапуски контейнера.

## Инициализация схемы

Схема создаётся **миграциями Alembic**, а не init-скриптом контейнера:

```bash
python -m alembic upgrade head
```

Подробнее — в [migrations.md](migrations.md).

## Полезные команды

```bash
# Статус контейнера
docker compose ps

# Посмотреть SQL-консоль внутри контейнера
docker exec -it hackathon_db psql -U hackathon -d hackathon

# Логи
docker compose logs -f db

# Остановить (данные сохраняются в volume)
docker compose down

# Полный сброс: удалить контейнер И данные БД
docker compose down -v
```

После полного сброса (`down -v`) схема исчезает — примените миграции заново:

```bash
docker compose up -d db
python -m alembic upgrade head
```