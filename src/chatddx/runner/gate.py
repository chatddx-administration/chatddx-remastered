import os

from chatddx.factors.base import Resolver, StructuralError, resolve
from chatddx.factors.cases import Case
from chatddx.factors.engine import served_model_name
from chatddx.factors.request import Skeleton, Slot
from chatddx.factors.scoring import Judge
from chatddx.factors.trial import Trial
from chatddx.inventory import Inventory

from .wire import served


class Refused(Exception):
    pass


def admit(
    inventory: Inventory,
    get: Resolver,
    endpoint: str,
    trial: Trial,
    judge: Judge | None = None,
    timeout: float = 10.0,
) -> str | None:
    bar(inventory, get, endpoint, trial, judge)
    engine = trial.engine if judge is None else judge.engine
    key = _secret(inventory, endpoint)
    url = str(inventory.endpoint(endpoint).url)
    try:
        expected = served_model_name(engine, get)
        listed = served(url, secret=key, timeout=timeout)
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
    trial: Trial,
    judge: Judge | None = None,
) -> None:
    if judge is None:
        engine, whose = trial.engine, "trial"
        tools = bool(resolve(get, trial.skeleton, Skeleton).tools)
    else:
        engine, whose, tools = judge.engine, "judge", False
        skeleton = resolve(get, judge.skeleton, Skeleton)
        if read := sorted(_slots(skeleton) & {"vignette", "appendices"}):
            raise Refused(
                f"judge {judge.digest} reads the {' and '.join(read)}, which no judge "
                + "is given"
            )
    try:
        spec = inventory.endpoint(endpoint)
        sources = sorted({resolve(get, c, Case).vignette.source for c in trial.cases})
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


def _slots(skeleton: Skeleton) -> set[str]:
    return {s.slot for m in skeleton.messages for s in m.content if isinstance(s, Slot)}


def _secret(inventory: Inventory, endpoint: str) -> str | None:
    credential = inventory.endpoint(endpoint).credential
    if credential is None:
        return None
    value = os.environ.get(credential)
    if not value:
        raise Refused(
            f"endpoint {endpoint!r} needs the secret in ${credential}, which isn't set"
        )
    return value
