from __future__ import annotations


class EgasError(RuntimeError):
    pass


class EgasAuthError(EgasError):
    pass


class EgasStudentNotFoundError(EgasError):
    pass
