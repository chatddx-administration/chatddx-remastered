from chatddx.catalog import MovedOn
from chatddx.factors import Worded

__all__ = ["Ambiguous", "Conflict", "MovedOn", "NotFound", "OverQuota"]


class NotFound(Worded, LookupError):
    pass


class Ambiguous(Worded, LookupError):
    pass


class Conflict(Worded, ValueError):
    pass


class OverQuota(Worded, ValueError):
    pass
