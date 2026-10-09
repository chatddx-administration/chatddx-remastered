from collections.abc import Iterable


# Nothing the person sees goes by that name or id. `per_model` holds the threads made
# per model under the name, when no model was given to pick one by.
class NotFound(LookupError):
    def __init__(self, message: str, per_model: Iterable[str] = ()) -> None:
        super().__init__(message)
        self.per_model: tuple[str, ...] = tuple(per_model)


# More than one thing the person sees goes by that name or id.
class Ambiguous(LookupError):
    pass
