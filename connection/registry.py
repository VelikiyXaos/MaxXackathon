from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from typing import Iterator

import connection.connectors
from connection.ABS_egas_connector import AbstractEgasConnector

logger = logging.getLogger(__name__)

CONNECTORS_PACKAGE = connection.connectors.__name__

_CONNECTORS: dict[str, type[AbstractEgasConnector]] = {}
_loaded = False


def register_connector(
    connector_cls: type[AbstractEgasConnector],
) -> type[AbstractEgasConnector]:
    """Регистрирует коннектор вручную"""
    if not issubclass(connector_cls, AbstractEgasConnector):
        raise TypeError(
            f"{connector_cls.__name__} не наследует AbstractEgasConnector"
        )
    if inspect.isabstract(connector_cls):
        raise TypeError(
            f"{connector_cls.__name__} абстрактный: реализуйте "
            f"_authenticate() и _fetch_grades()"
        )

    keys = [connector_cls.__name__]
    code = getattr(connector_cls, "code", "")
    if code:
        keys.append(code.upper())

    for key in keys:
        current = _CONNECTORS.get(key)
        if current is not None and current is not connector_cls:
            raise ValueError(
                f"Имя '{key}' уже занято коннектором {current.__module__}."
                f"{current.__name__}"
            )
        _CONNECTORS[key] = connector_cls

    return connector_cls


def _iter_connector_classes() -> Iterator[type[AbstractEgasConnector]]:
    """Отдаёт неабстрактные классы из пакета connection/connectors"""
    seen: set[type] = set()
    stack: list[type] = [AbstractEgasConnector]

    while stack:
        base = stack.pop()
        for subclass in base.__subclasses__():
            if subclass in seen:
                continue
            seen.add(subclass)
            stack.append(subclass)

            if inspect.isabstract(subclass):
                continue
            if not subclass.__module__.startswith(CONNECTORS_PACKAGE + "."):
                continue
            yield subclass


def load_connectors(
    *, force: bool = False
) -> dict[str, type[AbstractEgasConnector]]:
    """Импортирует модули из connection/connectors и наполняет реестр"""
    global _loaded
    if _loaded and not force:
        return dict(_CONNECTORS)

    for module_info in pkgutil.iter_modules(connection.connectors.__path__):
        if module_info.name.startswith("_"):
            continue
        module_name = f"{CONNECTORS_PACKAGE}.{module_info.name}"
        try:
            importlib.import_module(module_name)
        except Exception:
            logger.exception("Не удалось импортировать модуль %s", module_name)

    for connector_cls in _iter_connector_classes():
        try:
            register_connector(connector_cls)
        except (TypeError, ValueError) as exc:
            logger.warning("Коннектор %s не зарегистрирован: %s", connector_cls, exc)

    _loaded = True
    logger.debug("Зарегистрировано коннекторов ЭСУО: %s", sorted(_CONNECTORS))
    return dict(_CONNECTORS)


def get_connector_class(name: str) -> type[AbstractEgasConnector]:
    """Возвращает класс коннектора по имени из EGAS.API_file"""
    load_connectors()

    connector_cls = _CONNECTORS.get(name)
    if connector_cls is None:
        raise ValueError(
            f"Коннектор ЭСУО '{name}' не найден. "
            f"Доступные: {sorted(_CONNECTORS)}. "
            f"Добавьте файл с классом в connection/connectors/ "
            f"и впишите имя класса в EGAS.API_file."
        )
    return connector_cls


def registered_connectors() -> dict[str, type[AbstractEgasConnector]]:
    """Отдаёт текущее содержимое реестра"""
    return load_connectors()
