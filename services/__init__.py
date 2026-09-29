from contextlib import asynccontextmanager

from db.database import SessionFactory


@asynccontextmanager
async def session_scope():
    """Открывает сессию базы данных и закрывает её на выходе"""
    async with SessionFactory() as session:
        yield session
