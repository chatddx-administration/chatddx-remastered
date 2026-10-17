import os
from collections.abc import Iterable

from chatddx.factors.base import Resolver, StructuralError, resolve
from chatddx.factors.cases import Case
from chatddx.factors.engine import served_model_name
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial
from chatddx.inventory import Inventory

from . import wire


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
    bar(inventory, get, endpoint, engine, cases, tools, whose)
    key = secret(inventory, endpoint)
    url = str(inventory.endpoint(endpoint).url)
    try:
        expected = served_model_name(engine, get)
        listed = wire.served(url, secret=key, timeout=timeout)
    except (StructuralError, OSError) as e:
        raise Refused(f"endpoint {endpoint!r} can't be confirmed: {e}") from None
    if expected not in listed:
        raise Refused(
            f"endpoint {endpoint!r} can't be confirmed: it serves "
            + f"{', '.join(listed) or 'nothing'} at {url}, not {expected}"
        )
    return key


# What refuses an endpoint for as long as the World is as it is; admit adds what may pass later.
def bar(
    inventory: Inventory,
    get: Resolver,
    endpoint: str,
    engine: str,
    cases: Iterable[str],
    tools: bool,
    whose: str,
) -> None:
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
    if uncleared := sorted(set(sensitive) - set(inventory.cleared.get(endpoint, ()))):
        raise Refused(
            f"endpoint {endpoint!r} isn't cleared for source {', '.join(uncleared)}, "
            + "which is sensitive"
        )
    if tools and sensitive:
        raise Refused(
            f"the configuration's tools would get content from source {', '.join(sensitive)}, "
            + "which is sensitive, and tools can't be cleared yet"
        )


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
