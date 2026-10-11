from collections.abc import Iterable

from chatddx.catalog import MovedOn

__all__ = ["Ambiguous", "Conflict", "MovedOn", "NotFound", "OverQuota"]


# Nothing the person sees goes by that name or id. `per_model` holds the threads made
# per model under the name, when no model was given to pick one by.
class NotFound(LookupError):
    def __init__(self, message: str, per_model: Iterable[str] = ()) -> None:
        super().__init__(message)
        self.per_model: tuple[str, ...] = tuple(per_model)


# More than one thing the person sees goes by that name or id.
class Ambiguous(LookupError):
    pass


# The write would undo what the person has, unless they say so.
class Conflict(ValueError):
    pass


# The person has written as much of something as a day takes.
class OverQuota(ValueError):
    pass
