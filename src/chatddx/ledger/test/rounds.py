from dataclasses import dataclass
from uuid import uuid4

from pydantic import JsonValue

from chatddx.factors.base import Finding, Fingerprint, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case
from chatddx.factors.engine import LocalEngine
from chatddx.factors.request import Output, Tool, ToolOutput, Toolset, compile_request
from chatddx.factors.test.sample import NOW, RIG, fp, generation_recipe, world
from chatddx.factors.trial import Trial
from chatddx.ledger import (
    Call,
    ItemKey,
    Run,
    RunItem,
    RunStarted,
    ToolCode,
    ToolRun,
    Turn,
    check_run,
)
from chatddx.test.helpers import one_attempt


def ran(
    *ids: str, name: str = "web_search", error: str | None = None
) -> tuple[ToolRun, ...]:
    return tuple(
        ToolRun(
            id=i, name=name, started_at=NOW, finished_at=NOW, result="r", error=error
        )
        for i in ids
    )


@dataclass(frozen=True)
class Rounds:
    reg: Registry
    ids: dict[str, str]
    web: str
    answer: str
    trial: str
    started: RunStarted
    vignette: Fingerprint
    served: str

    def call(self, *names: str, model: str | None = None) -> Call:
        calls: list[JsonValue] = [
            {
                "id": f"c{i}",
                "type": "function",
                "function": {"name": n, "arguments": "{}"},
            }
            for i, n in enumerate(names)
        ]
        message: dict[str, JsonValue] = {"role": "assistant", "tool_calls": calls}
        return Call(
            request=fp("body"),
            started_at=NOW,
            finished_at=NOW,
            attempts=one_attempt(NOW),
            status=200,
            response={
                "model": model or self.served,
                "choices": [{"message": message}],
                "prompt_token_ids": [1],
            },
        )

    def item(self, first: Call, *turns: Turn) -> RunItem:
        return RunItem(
            run=self.started.run,
            key=ItemKey(case=self.ids["case"], replicate=0),
            vignette=self.vignette,
            call=first,
            turns=turns,
        )

    def findings(self, first: Call, *turns: Turn) -> list[Finding]:
        run = Run(started=self.started, items=(self.item(first, *turns),))
        return check_run(run, self.reg)

    def check(self, first: Call, *turns: Turn) -> list[str]:
        return [f.code for f in self.findings(first, *turns)]


def rounds(reg: Registry) -> Rounds:
    ids = world(reg)
    engine = resolve(reg.get, ids["engine"], LocalEngine)
    web = reg.add(
        Tool(
            name="web_search",
            description="Search the web.",
            parameters={"type": "object"},
            entry_point="chatddx_tools.web:search",
            version=1,
        )
    )
    answer = reg.add(
        Output(
            contract=ToolOutput(name="answer", description="Answer."),
            json_schema={"type": "object"},
        )
    )
    recipe = generation_recipe(reg).model_copy(
        update={
            "output": answer,
            "toolset": reg.add(Toolset(tools=(web,), max_rounds=2)),
        }
    )
    skeleton = reg.add(compile_request(recipe, reg.get))
    trial = reg.add(
        Trial(skeleton=skeleton, engine=ids["engine"], cases=(ids["case"],), seeds=(1,))
    )
    started = RunStarted(
        run=uuid4(),
        at=NOW,
        rig=RIG,
        trial=trial,
        tool_code=(ToolCode(tool=web, version=1),),
    )
    return Rounds(
        reg=reg,
        ids=ids,
        web=web,
        answer=answer,
        trial=trial,
        started=started,
        vignette=resolve(reg.get, ids["case"], Case).vignette.fingerprint,
        served=engine.digest,
    )
