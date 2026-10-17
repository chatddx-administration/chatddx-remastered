from chatddx.catalog import MovedOn

__all__ = ["Ambiguous", "Conflict", "MovedOn", "NotFound", "OverQuota"]


class NotFound(LookupError):
    pass


class Ambiguous(LookupError):
    pass


class Conflict(ValueError):
    pass


class OverQuota(ValueError):
    pass
