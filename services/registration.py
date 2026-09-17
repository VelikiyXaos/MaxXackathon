from db.crud import city as city_crud
from . import session_scope


async def get_regions_by_city_name(city_name: str) -> dict:
    """Возвращает словарь с количеством регионов и их названиями для указанного города."""
    async with session_scope() as session:
        names = await city_crud.get_subject_names_by_city_name(session, city_name)
        return {"count": len(names), "names": names}
