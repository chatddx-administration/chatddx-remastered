from dataclasses import dataclass

from pydantic import JsonValue

from chatddx.factors.base import Finding
from chatddx.ledger import CanaryCall, ItemKey, JudgeCall, RunItem, ScoreItem, ToolRun

from .send import Delta


@dataclass(frozen=True)
class ItemStarted:
    key: ItemKey
    seed: int


@dataclass(frozen=True)
class Streamed:
    key: ItemKey
    delta: Delta


@dataclass(frozen=True)
class ToolRan:
    key: ItemKey
    run: ToolRun


@dataclass(frozen=True)
class ItemEnded:
    item: RunItem


@dataclass(frozen=True)
class CanaryEnded:
    call: CanaryCall


@dataclass(frozen=True)
class Noted:
    finding: Finding


@dataclass(frozen=True)
class ItemScored:
    item: ScoreItem


@dataclass(frozen=True)
class JudgeAsked:
    key: ItemKey
    scorer: str
    view: int
    judge: str
    seed_index: int


@dataclass(frozen=True)
class JudgeAnswered:
    key: ItemKey
    view: int
    call: JudgeCall
    verdict: JsonValue | None


type RunEvent = ItemStarted | Streamed | ToolRan | ItemEnded | CanaryEnded | Noted
type ScoreEvent = ItemScored | JudgeAsked | Streamed | JudgeAnswered | Noted
