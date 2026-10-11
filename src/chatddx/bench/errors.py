from collections.abc import Iterable

from chatddx.catalog import MovedOn

__all__ = ["Ambiguous", "Conflict", "MovedOn", "NotFound", "OverQuota"]


class NotFound(LookupError):
    def __init__(self, message: str, per_model: Iterable[str] = ()) -> None:
        super().__init__(message)
        self.per_model: tuple[str, ...] = tuple(per_model)


class Ambiguous(LookupError):
    pass


class Conflict(ValueError):
    pass


class OverQuota(ValueError):
    pass
