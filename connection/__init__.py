"""Подключение к ЭСУО: абстрактный провайдер оценок и его реализации."""

from connection.ABS_grade_provider import AbstractGradeProvider, GradesCount
from connection.egas_client import NetSchoolClient
from connection.factory import get_grade_provider
from connection.grade_provider_NetSchoolAPI import EgasGradeProvider

__all__ = [
    "AbstractGradeProvider",
    "EgasGradeProvider",
    "GradesCount",
    "NetSchoolClient",
    "get_grade_provider",
]
