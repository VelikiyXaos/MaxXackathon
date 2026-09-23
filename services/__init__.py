# services

from contextlib import asynccontextmanager

from db.database import SessionFactory


@asynccontextmanager
async def session_scope():
    """Открывает и закрывает сессию базы данных."""
    async with SessionFactory() as session:
        yield session