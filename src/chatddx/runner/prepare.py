from dataclasses import dataclass

from pydantic import JsonValue

from chatddx.factors.base import Finding, Fingerprint, Resolver, resolve
from chatddx.factors.cases import Case, Prepared, prepare_case
from chatddx.factors.engine import LocalEngine, RemoteEngine, served_model_name
from chatddx.factors.request import AppendixLayout, Skeleton, render
from chatddx.factors.trial import Trial
from chatddx.inventory import Inventory
from chatddx.ledger import ItemKey
from chatddx.store import fetch_vignette
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
        engine = get(self.trial.engine)
        assert isinstance(engine, LocalEngine | RemoteEngine)
        self.engine: LocalEngine | RemoteEngine = engine

    def case(self, case: str, layout: AppendixLayout) -> Prepared:
        found = resolve(self._get, case, Case)
        raw = fetch_vignette(self._conn, self._inventory, found.vignette)
        return prepare_case(found, raw, self._get, layout, self.trial.cleanup)

    def item(self, key: ItemKey) -> PreparedItem:
        prepared = self.case(key.case, self.skeleton.appendix_layout)
        seed = self.trial.seeds[key.replicate]
        body = render(
            self.skeleton,
            model=served_model_name(self.engine, self._get),
            seed=seed,
            fills=prepared.fills,
        )
        return PreparedItem(key, seed, prepared.fingerprint, body, prepared.findings)
