from dataclasses import dataclass

from pydantic import JsonValue

from chatddx.factors.base import (
    Finding,
    Fingerprint,
    Resolver,
    StructuralError,
    resolve,
)
from chatddx.factors.cases import Case, Prepared, prepare_case
from chatddx.factors.engine import served_model_name
from chatddx.factors.request import AppendixLayout, Skeleton
from chatddx.factors.trial import Trial
from chatddx.inventory import Inventory
from chatddx.ledger import ItemKey, Run, fingerprint_request
from chatddx.store import Store, fetch_vignette
from chatddx.store.store import Connection


@dataclass(frozen=True)
class PreparedItem:
    key: ItemKey
    seed: int
    vignette: Fingerprint
    body: dict[str, JsonValue]
    findings: tuple[Finding, ...]


class Items:
    def __init__(
        self, conn: Connection, inventory: Inventory, get: Resolver, trial: str
    ) -> None:
        self._conn: Connection = conn
        self._inventory: Inventory = inventory
        self._get: Resolver = get
        self.trial: Trial = resolve(get, trial, Trial)
        self.skeleton: Skeleton = resolve(get, self.trial.skeleton, Skeleton)

    def case(self, case: str, layout: AppendixLayout) -> Prepared:
        found = resolve(self._get, case, Case)
        raw = fetch_vignette(self._conn, self._inventory, found.vignette)
        return prepare_case(found, raw, self._get, layout, self.trial.cleanup)

    def item(self, key: ItemKey) -> PreparedItem:
        prepared = self.case(key.case, self.skeleton.appendix_layout)
        seed = self.trial.seeds[key.replicate]
        body = self.skeleton.render(
            model=served_model_name(self.trial.engine, self._get),
            seed=seed,
            fills=prepared.fills,
        )
        return PreparedItem(key, seed, prepared.fingerprint, body, prepared.findings)


def rendered_again(
    conn: Connection, inventory: Inventory, run: Run
) -> dict[ItemKey, str | None]:
    registry = Store(conn).load([run.started.trial])
    items = Items(conn, inventory, registry.get, run.started.trial)
    found: dict[ItemKey, str | None] = {}
    for item in run.items:
        try:
            prepared = items.item(item.key)
        except (LookupError, StructuralError) as e:
            found[item.key] = str(e)
            continue
        if prepared.vignette != item.vignette:
            found[item.key] = "the vignette at the source isn't the one sent"
        elif fingerprint_request(prepared.body) != item.call.request:
            found[item.key] = "the request renders otherwise now"
        else:
            found[item.key] = None
    return found
