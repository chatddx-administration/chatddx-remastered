import os
from collections.abc import Iterable

from chatddx.factors.base import Resolver, resolve
from chatddx.factors.cases import Case
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial
from chatddx.inventory import Inventory, confirm


class Refused(Exception):
    pass


def check(
    inventory: Inventory,
    get: Resolver,
    endpoint: str,
    trial: Trial,
    timeout: float = 10.0,
) -> str | None:
    tools = bool(resolve(get, trial.skeleton, Skeleton).tools)
    return admit(
        inventory, get, endpoint, trial.engine, trial.cases, tools, "trial", timeout
    )


def admit(
    inventory: Inventory,
    get: Resolver,
    endpoint: str,
    engine: str,
    cases: Iterable[str],
    tools: bool,
    whose: str,
    timeout: float = 10.0,
) -> str | None:
    try:
        spec = inventory.endpoint(endpoint)
        sources = sorted({resolve(get, c, Case).vignette.source for c in cases})
        sensitive = [s for s in sources if inventory.source(s).sensitive]
    except LookupError as e:
        raise Refused(str(e)) from None
    if spec.engine != engine:
        raise Refused(
            f"endpoint {endpoint!r} serves engine {spec.engine}, the {whose}'s is "
            + engine
        )
    if uncleared := sorted(set(sensitive) - inventory.cleared_for(endpoint)):
        raise Refused(
            f"endpoint {endpoint!r} isn't cleared for source {', '.join(uncleared)}, "
            + "which is sensitive"
        )
    if tools and sensitive:
        raise Refused(
            f"the skeleton's tools would get content from source {', '.join(sensitive)}, "
            + "which is sensitive, and tools can't be cleared yet"
        )
    key = secret(inventory, endpoint)
    try:
        confirm(inventory, get, endpoint, timeout, key)
    except (LookupError, OSError) as e:
        raise Refused(f"endpoint {endpoint!r} can't be confirmed: {e}") from None
    return key


def secret(inventory: Inventory, endpoint: str) -> str | None:
    credential = inventory.endpoint(endpoint).credential
    if credential is None:
        return None
    value = os.environ.get(credential)
    if not value:
        raise Refused(
            f"endpoint {endpoint!r} needs the secret in ${credential}, which isn't set"
        )
    return value
