"""Подключение к ЭСУО: коннекторы, реестр и фабрика.

Публичный API:
    * `AbstractEgasConnector` — базовый класс коннектора к ЭСУО;
    * `get_egas_connector(student_id)` — коннектор для студента;
    * `register_connector` / `get_connector_class` — реестр;
    * `EgasError` / `EgasAuthError` — ошибки, не зависящие от ЭСУО.
"""

from connection.ABS_egas_connector import AbstractEgasConnector, GradesCount
from connection.errors import (
    EgasAuthError,
    EgasError,
    EgasStudentNotFoundError,
)
from connection.factory import get_egas_connector
from connection.registry import (
    get_connector_class,
    load_connectors,
    register_connector,
    registered_connectors,
)

__all__ = [
    "AbstractEgasConnector",
    "EgasAuthError",
    "EgasError",
    "EgasStudentNotFoundError",
    "GradesCount",
    "get_connector_class",
    "get_egas_connector",
    "load_connectors",
    "register_connector",
    "registered_connectors",
]
