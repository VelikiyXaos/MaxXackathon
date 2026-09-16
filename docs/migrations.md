# Миграции (Alembic)

Миграции управляются [Alembic](https://alembic.sqlalchemy.org/) — поверх SQLAlchemy,
в асинхронном режиме (`asyncpg`).

## Связь с моделями

`alembic/env.py` импортирует модели из `db/models/` и использует
`target_metadata = Base.metadata` для автогенерации. URL для подключения берётся
из `db/database.py` (читает `DATABASE_URL` из `.env`).

Любые изменения схемы делаются **только через модели**, затем миграция
генерируется автоматически.

## Команды

```bash
# Создать новую миграцию (сравнивает модели с БД)
python -m alembic revision --autogenerate -m "описание изменения"

# Применить все неподанные миграции
python -m alembic upgrade head

# Откатить на одну миграцию назад
python -m alembic downgrade -1

# Показать текущее состояние БД
python -m alembic current

# Показать историю миграций
python -m alembic history
```

## Полный цикл изменения схемы

1. Правьте модели в `db/models/` (например, добавьте колонку):
   ```python
   class Student(Base):
       ...
       new_field: Mapped[str | None] = mapped_column(String(100))
   ```
2. Сгенерируйте миграцию:
   ```bash
   python -m alembic revision --autogenerate -m "add new_field to student"
   ```
3. Проверьте сгенерированный файл в `alembic/versions/` — autogenerate может
   ошибаться, при необходимости дополните `upgrade()`/`downgrade()` вручную.
4. Примените:
   ```bash
   python -m alembic upgrade head
   ```

## Развёртывание с нуля

Схема создаётся миграциями:

```bash
docker compose up -d db
python -m alembic upgrade head
```

## Работа с базой, созданной до внедрения Alembic

Если БД уже содержит схему (например, созданную вручную) и в ней нет таблицы
`alembic_version`, пометьте текущую ревизию как применённую **без выполнения**:

```bash
python -m alembic stamp head
```

После этого `alembic current` покажет `(head)`, а следующие миграции будут
накатываться поверх существующей схемы.

## Файлы

- `alembic.ini` — конфигурация Alembic
- `alembic/env.py` — окружение (модели, URL подключения, async engine)
- `alembic/versions/` — файлы миграций (по одному на изменение)