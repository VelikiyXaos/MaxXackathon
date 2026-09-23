# models

from .admin import Admin
from .application import Application
from .associations import EI_with_EGAS, student_bonus
from .bonus import Bonus
from .city import City
from .educational_institution import EducationalInstitution
from .egas import EGAS
from .partner import Partner
from .student import Student
from .subject import Subject

__all__ = [
    "Subject",
    "City",
    "EGAS",
    "EducationalInstitution",
    "Student",
    "Partner",
    "Bonus",
    "Admin",
    "Application",
    "EI_with_EGAS",
    "student_bonus",
]