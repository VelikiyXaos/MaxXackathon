# services

async def get_applications() -> list[dict]:
    # TODO: реализовать получение списка заявок партнёров
    # (db.crud.application.get_all).
    return []


async def accept_application(application_id: int) -> None:
    # TODO: реализовать принятие заявки (db.crud.application.update).
    return None


async def reject_application(application_id: int) -> None:
    # TODO: реализовать отклонение заявки (db.crud.application.delete).
    return None


async def add_admin(max_id: int) -> bool:
    # TODO: реализовать добавление администратора
    # (db.crud.admin.create).
    return True