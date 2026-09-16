from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EducationalInstitution


async def create(
    session: AsyncSession,
    *,
    name: str,
    city_id: int,
) -> EducationalInstitution:
    """Создаёт новое образовательное учреждение и возвращает его."""
    institution = EducationalInstitution(name=name, city_id=city_id)
    session.add(institution)
    await session.commit()
    await session.refresh(institution)
    return institution


async def get(
    session: AsyncSession, institution_id: int
) -> EducationalInstitution | None:
    """Возвращает образовательное учреждение по id или None."""
    return await session.get(EducationalInstitution, institution_id)


async def get_all(session: AsyncSession) -> list[EducationalInstitution]:
    """Возвращает список всех образовательных учреждений."""
    result = await session.execute(select(EducationalInstitution))
    return list(result.scalars())


async def get_by_city(
    session: AsyncSession, city_id: int
) -> list[EducationalInstitution]:
    """Возвращает учреждения, находящиеся в указанном городе."""
    result = await session.execute(
        select(EducationalInstitution).where(
            EducationalInstitution.city_id == city_id
        )
    )
    return list(result.scalars())


async def update(
    session: AsyncSession,
    institution_id: int,
    **fields: object,
) -> EducationalInstitution | None:
    """Обновляет указанные поля учреждения и возвращает его или None."""
    institution = await session.get(EducationalInstitution, institution_id)
    if institution is None:
        return None
    for field, value in fields.items():
        setattr(institution, field, value)
    await session.commit()
    await session.refresh(institution)
    return institution


async def delete(session: AsyncSession, institution_id: int) -> bool:
    """Удаляет учреждение по id. Возвращает True, если запись удалена."""
    institution = await session.get(EducationalInstitution, institution_id)
    if institution is None:
        return False
    await session.delete(institution)
    await session.commit()
    return True