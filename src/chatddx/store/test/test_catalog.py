from functools import partial
from typing import Any
from uuid import uuid4

import pytest
from psycopg import errors, sql
from pydantic import JsonValue, ValidationError

from chatddx.catalog import (
    LANGUAGE_KINDS,
    THREAD_KINDS,
    About,
    Entry,
    EntryField,
    Subject,
    Survey,
    families,
    read,
    threads,
    titles,
)
from chatddx.catalog.language import language_of
from chatddx.catalog.titles import short
from chatddx.factors import request
from chatddx.factors.base import Code, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Appendix, Case, Vignette
from chatddx.factors.facts import Intent, ModelFacts, ReasoningFacts, Writes
from chatddx.factors.kinds import BY_KIND
from chatddx.factors.lint import lint
from chatddx.factors.request import (
    RECIPE_PARTS,
    Compilation,
    Insert,
    NativeOutput,
    Output,
    Prompt,
    Reasoning,
    Recipe,
    Sampling,
    Slot,
    Translations,
    texts,
)
from chatddx.factors.scoring import Expectation, Judge, Scoring
from chatddx.factors.test.sample import NOW, RIG, fp, generation_recipe, world
from chatddx.identity import Person
from chatddx.ledger import RunStarted, ScoreStarted
from chatddx.store import Catalog, People, Rows, Store
from chatddx.store.store import Connection


def stored_world(
    conn: Connection,
) -> tuple[Catalog, Store, Registry, dict[str, str], Person]:
    reg = Registry()
    ids = world(reg)
    store = Store(conn)
    _ = store.add(reg, [ids["trial"], ids["scoring"], ids["canaries"]])
    return Catalog(conn), store, reg, ids, People(conn).add("alice", "Alice")


def compiled(store: Store, reg: Registry, *instructions: str) -> Compilation:
    return compiled_recipe(store, reg, generation_recipe(reg, *instructions))


def compiled_recipe(
    store: Store, reg: Registry, recipe: Recipe, into: str | None = None
) -> Compilation:
    skeleton, compilation = request.compiled(recipe, reg.get, RIG, into=into)
    _ = reg.add(skeleton)
    _ = store.add(reg, [reg.add(compilation)])
    return compilation


def instructions(c: Compilation) -> str:
    assert c.recipe.instructions is not None
    return c.recipe.instructions


def test_a_digest_is_kept_in_a_new_thread_a_new_edit_or_as_it_is(
    conn: Connection,
) -> None:
    catalog, store, reg, _, alice = stored_world(conn)
    rows = Rows(conn)
    v1 = instructions(compiled(store, reg))
    v2 = instructions(compiled(store, reg, "You are a cardiologist."))
    first, kept = catalog.keep(v1, alice.id, None, name="physician")
    assert kept == "created"
    assert read.about(rows, Subject(thread=first.thread)).name == "physician"
    assert catalog.keep(v1, alice.id, first.thread) == (first, "unchanged")
    second, kept = catalog.keep(v2, alice.id, first.thread)
    assert (kept, threads.history(rows, first.thread)) == ("edited", [first, second])
    fork, kept = catalog.keep(v2, alice.id, None, forked_from=second.id)
    assert kept == "created"
    assert threads.thread(rows, fork.thread).forked_from == second.id


def test_threads_follow_edits(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    v1 = instructions(compiled(store, reg))
    v2 = instructions(compiled(store, reg, "You are a cardiologist."))
    first = catalog.create(v1, alice.id)
    second = catalog.edit(first.thread, v2, alice.id)
    assert threads.history(rows, first.thread) == [first, second]
    assert threads.head(rows, first.thread) == second
    assert threads.thread(rows, first.thread).kind == "chunk.instructions"
    reverted = catalog.edit(first.thread, v1, alice.id)
    assert threads.head(rows, first.thread).digest == v1
    assert rows.edits_holding([v1]) == [first, reverted]
    assert [e for e, _ in threads.heads(rows, "chunk.instructions")] == [reverted]

    with pytest.raises(LookupError):
        _ = catalog.create("sha256:" + "9" * 64, alice.id)
    with pytest.raises(ValueError, match="case"):
        _ = catalog.create(ids["case"], alice.id)
    for kind in ("engine", "canaries"):
        assert threads.history(rows, catalog.create(ids[kind], alice.id).thread)
    with pytest.raises(LookupError):
        _ = catalog.edit(999, v1, alice.id)
    with pytest.raises(LookupError):
        _ = threads.history(rows, 999)
    with pytest.raises(errors.ForeignKeyViolation), conn.transaction():
        _ = catalog.edit(first.thread, ids["trial"], alice.id)


def test_skeleton_threads_carry_their_recipe(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    v1 = compiled(store, reg)
    v2 = compiled(store, reg, "You are a cardiologist.")
    edit = catalog.create(v1.skeleton, alice.id, compilation=v1.digest)
    assert edit.compilation == v1.digest
    with pytest.raises(errors.ForeignKeyViolation), conn.transaction():
        _ = catalog.edit(edit.thread, v2.skeleton, alice.id, compilation=v1.digest)
    with pytest.raises(errors.CheckViolation), conn.transaction():
        _ = catalog.create(instructions(v1), alice.id, compilation=v1.digest)
    with pytest.raises(errors.ForeignKeyViolation), conn.transaction():
        _ = catalog.edit(edit.thread, v1.skeleton, alice.id, compilation=ids["trial"])

    judge = resolve(reg.get, ids["judge"], Judge)
    hand_written = catalog.create(judge.skeleton, alice.id)
    assert hand_written.compilation is None
    shown = f"judge configuration {short(judge.skeleton)}"
    assert titles.title(rows, hand_written.thread) == shown


def test_a_skeleton_thread_keeps_each_recipe_of_its_request(conn: Connection) -> None:
    catalog, store, reg, _, alice = stored_world(conn)
    rows = Rows(conn)
    base = generation_recipe(reg)
    plan = compiled_recipe(store, reg, base)
    split = reg.add(
        Prompt(
            segments=(
                "Case:",
                "\n",
                Slot(slot="vignette"),
                Slot(slot="appendices"),
                "\n\nDifferential?",
            )
        )
    )
    resplit = compiled_recipe(store, reg, base.model_copy(update={"prompt": split}))
    assert resplit.skeleton == plan.skeleton
    newer = Code(distribution="chatddx", version="0.0.1", revision="def456")
    _, recompiled = request.compiled(base, reg.get, newer)
    _ = store.add(reg, [reg.add(recompiled)])
    assert recompiled.digest != plan.digest

    first = catalog.create(plan.skeleton, alice.id, compilation=plan.digest)
    for same in (None, plan.digest, recompiled.digest):
        kept = catalog.keep(plan.skeleton, alice.id, first.thread, compilation=same)
        assert kept == (first, "unchanged")
    second, kept = catalog.keep(
        plan.skeleton, alice.id, first.thread, compilation=resplit.digest
    )
    assert (kept, second.compilation) == ("edited", resplit.digest)
    assert threads.recipe(rows, threads.head(rows, first.thread)) == resplit.recipe

    hand_written = catalog.create(plan.skeleton, alice.id)
    _, kept = catalog.keep(
        plan.skeleton, alice.id, hand_written.thread, compilation=plan.digest
    )
    assert kept == "edited"


def test_forks(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    bob = People(conn).add("bob", "Bob")
    v1 = instructions(compiled(store, reg))
    v2 = instructions(compiled(store, reg, "You are a cardiologist."))
    origin = catalog.create(v1, alice.id)
    fork = catalog.create(v2, bob.id, forked_from=origin.id)
    assert threads.thread(rows, fork.thread).forked_from == origin.id
    assert [e for e, _ in threads.heads(rows, "chunk.instructions")] == [origin, fork]
    with pytest.raises(errors.ForeignKeyViolation), conn.transaction():
        _ = catalog.create(ids["trial"], alice.id, forked_from=origin.id)


@pytest.mark.slow
def test_a_fork_s_changes_are_reapplied_on_request(conn: Connection) -> None:
    catalog, store, reg, _, alice = stored_world(conn)
    rows = Rows(conn)
    base = generation_recipe(reg)
    shown = reg.add(
        Output(
            contract=NativeOutput(),
            json_schema={"type": "object"},
            guidance=("Answer with JSON matching:\n\n", Insert(insert="schema")),
        )
    )
    plan = compiled_recipe(store, reg, base)
    plan_shown = compiled_recipe(store, reg, base.model_copy(update={"output": shown}))
    origin = catalog.create(plan.skeleton, alice.id, compilation=plan.digest)
    fork = catalog.create(
        plan_shown.skeleton,
        alice.id,
        compilation=plan_shown.digest,
        forked_from=origin.id,
    )
    assert threads.recipe(rows, threads.head(rows, origin.thread)) == base
    assert threads.divergence(rows, origin.thread) is None
    diverged = threads.divergence(rows, fork.thread)
    assert diverged is not None
    assert (diverged.base, diverged.origin_head) == (origin, origin)
    assert not diverged.moved
    assert diverged.varies == {"/recipe/output": (base.output, shown)}
    assert threads.proposal(rows, fork.thread) is None

    greedy = reg.add(Sampling(temperature=0))
    _ = store.add(reg, [greedy])
    moved_recipe = base.model_copy(update={"sampling": greedy})
    moved = compiled_recipe(store, reg, moved_recipe)
    head = catalog.edit(
        origin.thread, moved.skeleton, alice.id, compilation=moved.digest
    )
    diverged = threads.divergence(rows, fork.thread)
    assert diverged is not None
    assert (diverged.base, diverged.origin_head) == (origin, head)
    assert diverged.moved
    proposal = threads.proposal(rows, fork.thread)
    assert proposal == moved_recipe.model_copy(update={"output": shown})

    assert isinstance(proposal, Recipe)
    accepted = compiled_recipe(store, reg, proposal)
    with pytest.raises(ValueError, match="origin"):
        _ = catalog.edit(fork.thread, accepted.skeleton, alice.id, based_on=fork.id)
    reapplied = catalog.edit(
        fork.thread,
        accepted.skeleton,
        alice.id,
        compilation=accepted.digest,
        based_on=head.id,
    )
    assert reapplied.based_on == head.id
    diverged = threads.divergence(rows, fork.thread)
    assert diverged is not None
    assert (diverged.base, diverged.moved) == (head, False)
    assert diverged.varies == {"/recipe/output": (base.output, shown)}
    assert threads.proposal(rows, fork.thread) is None

    with pytest.raises(errors.RaiseException, match="origin"), conn.transaction():
        _ = conn.execute(
            """
            INSERT INTO catalog.edit (thread, kind, digest, by, based_on)
            VALUES (%s, 'skeleton', %s, %s, %s)
            """,
            (fork.thread, accepted.skeleton, alice.id, fork.id),
        )


def test_a_chunk_fork_diverges_by_its_fields(conn: Connection) -> None:
    catalog, store, reg, _, alice = stored_world(conn)
    rows = Rows(conn)
    recommended, longer, cooler = (
        reg.add(Sampling(temperature=0.6, top_p=0.95)),
        reg.add(Sampling(temperature=0.6, top_p=0.95, max_output_tokens=4096)),
        reg.add(Sampling(temperature=0.7, top_p=0.95)),
    )
    _ = store.add(reg, [recommended, longer, cooler])
    origin = catalog.create(recommended, alice.id)
    fork = catalog.create(longer, alice.id, forked_from=origin.id)
    diverged = threads.divergence(rows, fork.thread)
    assert diverged is not None
    assert diverged.varies == {"/max_output_tokens": (None, 4096)}
    _ = catalog.edit(origin.thread, cooler, alice.id)
    assert threads.proposal(rows, fork.thread) == Sampling(
        temperature=0.7, top_p=0.95, max_output_tokens=4096
    )


@pytest.mark.slow
def test_threads_behind_are_proposed_not_moved(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    v1 = compiled(store, reg)
    v2 = compiled(store, reg, "You are a cardiologist.")
    chunk = catalog.create(instructions(v1), alice.id)
    skeleton = catalog.create(v1.skeleton, alice.id, compilation=v1.digest)
    trial = catalog.create(ids["trial"], alice.id)
    _ = catalog.create(instructions(v2), alice.id, forked_from=chunk.id)
    assert threads.behind(rows, skeleton.thread) == []
    assert threads.behind(rows, trial.thread) == []

    _ = catalog.edit(chunk.thread, instructions(v2), alice.id)
    [behind] = threads.behind(rows, skeleton.thread)
    assert behind.head is not None
    assert (behind.path, behind.digest, behind.head.digest) == (
        "/recipe/instructions",
        instructions(v1),
        instructions(v2),
    )
    assert threads.behind(rows, trial.thread) == []

    moved = catalog.edit(skeleton.thread, v2.skeleton, alice.id, compilation=v2.digest)
    assert threads.behind(rows, skeleton.thread) == []
    [behind] = threads.behind(rows, trial.thread)
    assert (behind.path, behind.head) == ("/skeleton", moved)
    assert threads.head(rows, trial.thread) == trial

    catalog.note(
        Subject(thread=skeleton.thread), Entry(field=EntryField.DELETED), alice.id
    )
    assert threads.behind(rows, trial.thread) == []


def test_a_configuration_is_behind_facts_corrected_where_it_reaches(
    conn: Connection,
) -> None:
    catalog, store, reg, _, alice = stored_world(conn)
    rows = Rows(conn)

    def facts(default: Intent, **more: JsonValue) -> str:
        reasoning = ReasoningFacts(
            default=default,
            on=Writes(chat_template_kwargs={"enable_thinking": True}),
            off=Writes(chat_template_kwargs={"enable_thinking": False}),
        )
        return reg.add(
            ModelFacts.model_validate(
                {"model": "google/gemma-3-12b-it", "reasoning": reasoning, **more}
            )
        )

    old, longer, cooler = facts("on"), facts("on", context_length=8192), facts("off")
    _ = store.add(reg, [old, longer, cooler])
    held = catalog.create(old, alice.id)
    asked = reg.add(Reasoning(level="default"))
    base = generation_recipe(reg).model_copy(update={"reasoning": asked})
    skeleton, made = request.compiled(
        base, reg.get, RIG, resolve(reg.get, old, ModelFacts)
    )
    _ = reg.add(skeleton)
    _ = store.add(reg, [reg.add(made)])
    configuration = catalog.create(skeleton.digest, alice.id, compilation=made.digest)
    assert threads.behind(rows, configuration.thread) == []

    _ = catalog.edit(held.thread, longer, alice.id)
    assert threads.behind(rows, configuration.thread) == []
    moved = catalog.edit(held.thread, cooler, alice.id)
    [behind] = threads.behind(rows, configuration.thread)
    assert (behind.path, behind.digest, behind.head) == ("/facts", old, moved)


def test_entries(conn: Connection) -> None:
    catalog, store, _, ids, alice = stored_world(conn)
    rows = Rows(conn)
    bob = People(conn).add("bob", "Bob")
    trial = catalog.create(ids["trial"], alice.id)
    subject = Subject(thread=trial.thread)
    assert read.about(rows, subject) == About(owner=alice.id)
    handed = catalog.create(ids["engine"], alice.id, owner=bob.id)
    assert read.about(rows, Subject(thread=handed.thread)) == About(owner=bob.id)
    for entry in (
        Entry(field=EntryField.NAME, value="baseline"),
        Entry(field=EntryField.NAME, value="gemma baseline"),
        Entry(field=EntryField.DESCRIPTION, value="first try"),
        Entry(field=EntryField.TAG, value="gemma"),
        Entry(field=EntryField.TAG, value="draft"),
        Entry(field=EntryField.TAG, value="draft", present=False),
        Entry(field=EntryField.OWNER, person=bob.id),
        Entry(field=EntryField.COLLABORATOR, person=bob.id),
        Entry(field=EntryField.DELETED),
    ):
        catalog.note(subject, entry, alice.id)
    assert read.about(rows, subject) == About(
        name="gemma baseline",
        description="first try",
        tags=frozenset({"gemma"}),
        owner=bob.id,
        collaborators=frozenset({bob.id}),
        deleted=True,
    )
    assert [(e, a.deleted) for e, a in threads.heads(rows, "trial")] == [(trial, True)]
    catalog.note(subject, Entry(field=EntryField.DELETED, present=False), bob.id)
    assert [(e, a.deleted) for e, a in threads.heads(rows, "trial")] == [(trial, False)]

    run, score = uuid4(), uuid4()
    store.append(RunStarted(run=run, at=NOW, rig=RIG, trial=ids["trial"]))
    store.append(
        ScoreStarted(
            score=score,
            run=run,
            at=NOW,
            rig=RIG,
            scorer_version=1,
            scoring=ids["scoring"],
        )
    )
    catalog.note(Subject(run=run), Entry(field=EntryField.OWNER, person=bob.id), bob.id)
    catalog.note(
        Subject(score=score), Entry(field=EntryField.TAG, value="pilot"), bob.id
    )
    assert read.about(rows, Subject(run=run)) == About(owner=bob.id)
    assert read.about(rows, Subject(score=score)) == About(tags=frozenset({"pilot"}))
    with pytest.raises(errors.ForeignKeyViolation), conn.transaction():
        catalog.note(
            Subject(run=uuid4()), Entry(field=EntryField.TAG, value="x"), bob.id
        )


def test_a_run_says_what_it_varied(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    plan = compiled(store, reg)
    configuration = catalog.create(plan.skeleton, alice.id, compilation=plan.digest)
    chunk = catalog.create(instructions(plan), alice.id)
    other = instructions(compiled(store, reg, "You are a cardiologist."))
    run = uuid4()
    store.append(RunStarted(run=run, at=NOW, rig=RIG, trial=ids["trial"]))
    subject = Subject(run=run)
    for entry in (
        Entry.varied(configuration.id),
        Entry.replaced("instructions", other),
        Entry.replaced("reasoning", None),
        Entry.replaced("model", ids["model"]),
    ):
        catalog.note(subject, entry, alice.id)
    assert read.about(rows, subject) == About(
        varied=configuration.id,
        replaced={"instructions": other, "reasoning": None, "model": ids["model"]},
    )
    later = uuid4()
    store.append(RunStarted(run=later, at=NOW, rig=RIG, trial=ids["trial"]))
    catalog.note(Subject(run=later), Entry.started_with(run), alice.id)
    assert read.about(rows, Subject(run=later)).started_with == run

    for refused, said in (
        ((Subject(thread=configuration.thread), Entry.varied(configuration.id)), "run"),
        ((subject, Entry.varied(chunk.id)), "no configuration's"),
        ((subject, Entry.replaced("prompt", other)), "isn't a chunk of prompt"),
        ((subject, Entry.replaced("model", other)), "isn't a model"),
    ):
        with pytest.raises(ValueError, match=said):
            catalog.note(*refused, alice.id)
    for value in ("0", "edit 1", "reasoning", "few-shot=", f"output={other[7:]}"):
        with pytest.raises(ValidationError):
            _ = Entry(field=EntryField.REPLACED, value=value)
    with pytest.raises(ValidationError):
        _ = Entry(field=EntryField.VARIED, value="first")
    with pytest.raises(ValidationError):
        _ = Entry(field=EntryField.WITH, value="the first run")

    def written(field: str, value: str, at: Subject = subject) -> None:
        _ = conn.execute(
            """
            INSERT INTO catalog.entry (thread, run, run_stage, field, value, by)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                at.thread,
                at.run,
                None if at.run is None else "started",
                field,
                value,
                alice.id,
            ),
        )

    for field, value, at in (
        ("varied", str(configuration.id), Subject(thread=configuration.thread)),
        ("varied", "first", subject),
        ("replaced", "reasoning", subject),
        ("replaced", f"few-shot={other}", subject),
        ("with", str(run), Subject(thread=configuration.thread)),
        ("with", "the first run", subject),
    ):
        with pytest.raises(errors.CheckViolation), conn.transaction():
            written(field, value, at)
    for field, value in (
        ("varied", str(chunk.id)),
        ("replaced", f"prompt={other}"),
        ("replaced", f"model={other}"),
        ("with", str(uuid4())),
    ):
        with pytest.raises(errors.RaiseException), conn.transaction():
            written(field, value)


def test_names_are_optional_and_removable(conn: Connection) -> None:
    catalog, _, _, ids, alice = stored_world(conn)
    rows = Rows(conn)
    named = catalog.create(ids["trial"], alice.id, name="baseline")
    subject = Subject(thread=named.thread)
    assert read.about(rows, subject).name == "baseline"
    unnamed = catalog.create(ids["engine"], alice.id)
    assert read.about(rows, Subject(thread=unnamed.thread)).name is None
    with pytest.raises(ValidationError):
        _ = catalog.create(ids["trial"], alice.id, name="")
    catalog.note(subject, Entry(field=EntryField.NAME, present=False), alice.id)
    assert read.about(rows, subject).name is None
    catalog.note(subject, Entry(field=EntryField.NAME, value="again"), alice.id)
    assert read.about(rows, subject).name == "again"
    for field, value, present in (
        ("name", "x", False),
        ("name", None, True),
        ("tag", None, True),
        ("language", None, True),
    ):
        with pytest.raises(errors.CheckViolation), conn.transaction():
            _ = conn.execute(
                """
                INSERT INTO catalog.entry (thread, field, value, present, by)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (named.thread, field, value, present, alice.id),
            )


@pytest.mark.slow
def test_titles_fall_back_to_what_a_thread_holds(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    base = generation_recipe(reg)
    plan = compiled_recipe(store, reg, base)
    origin = catalog.create(plan.skeleton, alice.id, compilation=plan.digest)
    unnamed = titles.title(rows, origin.thread)
    assert unnamed.startswith('"You are an emergency physician." · ')
    assert titles.title_of(rows, plan.skeleton) == unnamed

    def name(thread: int, value: str) -> None:
        catalog.note(
            Subject(thread=thread), Entry(field=EntryField.NAME, value=value), alice.id
        )

    for part, value in (
        (base.instructions, "ddx"),
        (base.prompt, "case"),
        (base.output, "management-plan"),
        (base.sampling, "recommended"),
        (base.reasoning, "off"),
        (base.model, "gemma"),
    ):
        assert part is not None
        name(catalog.create(part, alice.id).thread, value)
    assert titles.title(rows, origin.thread) == (
        "ddx · case · management-plan · recommended · off · gemma"
    )
    name(origin.thread, "plan")
    assert titles.title(rows, origin.thread) == "plan"

    shown = reg.add(Output(contract=NativeOutput(), json_schema={"title": "Plan"}))
    plan_shown = compiled_recipe(store, reg, base.model_copy(update={"output": shown}))
    fork = catalog.create(
        plan_shown.skeleton,
        alice.id,
        compilation=plan_shown.digest,
        forked_from=origin.id,
    )
    assert titles.title(rows, fork.thread) == "plan, output: native output: Plan"
    name(catalog.create(shown, alice.id).thread, "management-plan-shown")
    assert titles.title(rows, fork.thread) == "plan, output: management-plan-shown"
    same = catalog.create(plan.skeleton, alice.id, forked_from=origin.id)
    assert titles.title(rows, same.thread) == "a fork of plan"

    greedy = reg.add(Sampling(temperature=0))
    moved = compiled_recipe(store, reg, base.model_copy(update={"sampling": greedy}))
    _ = catalog.edit(origin.thread, moved.skeleton, alice.id, compilation=moved.digest)
    assert titles.title_of(rows, moved.skeleton) == "plan"
    assert titles.title_of(rows, plan.skeleton) == "a fork of plan"
    catalog.note(Subject(thread=same.thread), Entry(field=EntryField.DELETED), alice.id)
    assert titles.title_of(rows, plan.skeleton) == "plan (earlier)"

    trial = titles.title_of(rows, ids["trial"])
    assert trial.endswith(" on gemma on vllm 0.24.0 (RTX 5090), 1 case, 2 seeds")
    troponin = '"Troponin 80 ng/L."'
    assert titles.title_of(rows, ids["case"]) == f"registry/c1 with {troponin}"
    family = catalog.adopt(ids["case"], alice.id)
    catalog.note(
        Subject(family=family),
        Entry(field=EntryField.NAME, value="chest pain"),
        alice.id,
    )
    assert titles.title_of(rows, ids["case"]) == f"chest pain with {troponin}"
    bare = reg.add(Case(vignette=resolve(reg.get, ids["case"], Case).vignette))
    _ = store.add(reg, [bare])
    assert titles.title_of(rows, bare) == "chest pain"
    scoring = resolve(reg.get, ids["scoring"], Scoring)
    expectation = catalog.create(scoring.expectations[0], alice.id)
    assert (
        titles.title(rows, expectation.thread)
        == f"expectation for chest pain with {troponin}"
    )

    cool = reg.add(Sampling(temperature=0.5))
    _ = store.add(reg, [cool])
    cooled = catalog.create(cool, alice.id, name="cool")
    _ = catalog.edit(cooled.thread, greedy, alice.id)
    assert titles.title_of(rows, cool) == "cool (earlier)"
    assert titles.title_of(rows, greedy) == "cool"


def test_families(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    family = catalog.adopt(ids["case"], alice.id)
    assert catalog.adopt(ids["case"], alice.id) == family
    assert families.family_of(rows, ids["case"]) == family
    assert read.about(rows, Subject(family=family)).owner == alice.id
    case = resolve(reg.get, ids["case"], Case)
    [binding] = rows.bindings([family])
    assert binding.vignette == case.vignette

    bare = reg.add(Case(vignette=case.vignette))
    _ = store.add(reg, [bare])
    assert catalog.adopt(bare, alice.id) == family
    catalog.note(
        Subject(family=family),
        Entry(field=EntryField.NAME, value="chest pain"),
        alice.id,
    )
    assert read.about(rows, Subject(family=family)).name == "chest pain"

    vignette = case.vignette
    changed = reg.add(
        Case(
            vignette=vignette.model_copy(
                update={"fingerprint": fp("edited at the source")}
            )
        )
    )
    renamed = reg.add(Case(vignette=vignette.model_copy(update={"id": "c1-renamed"})))
    other = reg.add(
        Case(vignette=Vignette(source=vignette.source, id="c2", fingerprint=fp("x")))
    )
    _ = store.add(reg, [changed, renamed, other])
    with pytest.raises(ValueError, match="new content"):
        _ = catalog.adopt(changed, alice.id)
    with pytest.raises(ValueError, match="a new name"):
        _ = catalog.adopt(renamed, alice.id)
    assert families.family_of(rows, changed) is None
    bob = People(conn).add("bob", "Bob")
    handed = catalog.adopt(other, alice.id, owner=bob.id)
    assert handed != family
    assert read.about(rows, Subject(family=handed)).owner == bob.id

    with pytest.raises(LookupError):
        _ = catalog.adopt(ids["trial"], alice.id)
    with pytest.raises(LookupError):
        _ = catalog.repair(999, alice.id, id="c9")

    sharing = [b.vignette for b in rows.bindings_sharing(vignette)]
    assert sharing == [vignette]
    look = vignette.model_copy(update={"id": "c2", "fingerprint": vignette.fingerprint})
    assert [b.vignette.id for b in rows.bindings_sharing(look)] == ["c1", "c2"]
    assert rows.bindings_sharing(look.model_copy(update={"source": "other"})) == []

    assert [b.family for b in rows.bindings([handed, family, 999])] == [family, handed]
    elsewhere = resolve(reg.get, other, Case).vignette
    assert rows.bound_to([elsewhere, vignette, vignette], "case") == sorted(
        [(ids["case"], vignette), (bare, vignette), (other, elsewhere)]
    )
    assert rows.bound_to([vignette], "appendix") == [(case.appendices[0], vignette)]
    assert rows.bound_to([look], "case") == []
    ghost = "sha256:" + "0" * 64
    assert rows.components([other, ghost, bare]) == sorted(
        [(bare, reg.get(bare)), (other, reg.get(other))]
    )


@pytest.mark.slow
def test_behind_looks_through_cases(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    case = resolve(reg.get, ids["case"], Case)
    [appendix] = case.appendices
    edited = reg.add(Appendix(vignette=case.vignette, text="Troponin 120 ng/L."))
    _ = store.add(reg, [edited])
    trial = catalog.create(ids["trial"], alice.id)
    expectation = resolve(reg.get, ids["scoring"], Scoring).expectations[0]
    expected = catalog.create(expectation, alice.id)
    thread = catalog.create(appendix, alice.id)
    assert threads.behind(rows, trial.thread) == []

    head = catalog.edit(thread.thread, edited, alice.id)
    assert [(b.path, b.digest, b.head) for b in threads.behind(rows, trial.thread)] == [
        ("/cases/0/appendices/0", appendix, head)
    ]
    assert [(b.path, b.head) for b in threads.behind(rows, expected.thread)] == [
        ("/case/appendices/0", head)
    ]


def test_renamed_vignettes_are_repaired(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    case = resolve(reg.get, ids["case"], Case)
    [appendix] = case.appendices
    source, fingerprint = case.vignette.source, case.vignette.fingerprint
    family = catalog.adopt(ids["case"], alice.id)
    name = Entry(field=EntryField.NAME, value="chest pain")
    catalog.note(Subject(family=family), name, alice.id)
    trial = catalog.create(ids["trial"], alice.id)
    expectation = resolve(reg.get, ids["scoring"], Scoring).expectations[0]
    expected = catalog.create(expectation, alice.id)
    appended = catalog.create(appendix, alice.id)

    assert families.survey(rows, source, {"c1": fingerprint}) == Survey(
        unchanged=(family,)
    )
    survey = families.survey(rows, source, {"c1-renamed": fingerprint, "c9": fp("new")})
    assert (survey.renamed, survey.new) == (((family, "c1", "c1-renamed"),), ("c9",))
    assert families.survey(rows, source, {}).gone == (family,)

    repair = catalog.repair(family, alice.id, id="c1-renamed")
    renamed = case.vignette.model_copy(update={"id": "c1-renamed"})
    [*_, binding] = rows.bindings([family])
    assert binding.vignette == repair.vignette == renamed
    rebound = resolve(store.get, repair.cases[ids["case"]], Case)
    assert rebound.vignette == renamed
    assert rebound.appendices == (repair.appendices[appendix],)
    new_appendix = resolve(store.get, repair.appendices[appendix], Appendix)
    assert (new_appendix.vignette, new_appendix.text) == (renamed, "Troponin 80 ng/L.")
    assert threads.head(rows, appended.thread).digest == repair.appendices[appendix]
    rekeyed = resolve(
        store.get, threads.head(rows, expected.thread).digest, Expectation
    )
    assert rekeyed.case == repair.cases[ids["case"]]
    assert {t for t, _ in repair.moves} == {appended.thread, expected.thread}
    assert families.family_of(rows, repair.cases[ids["case"]]) == families.family_of(
        rows, ids["case"]
    )
    assert read.about(rows, Subject(family=family)).name == "chest pain"
    assert families.survey(rows, source, {"c1-renamed": fingerprint}).unchanged == (
        family,
    )
    assert [
        (b.path, b.digest, b.binding, b.replacement)
        for b in threads.behind(rows, trial.thread)
    ] == [
        ("/cases/0", ids["case"], binding, repair.cases[ids["case"]]),
        ("/cases/0/appendices/0", appendix, None, None),
    ]
    assert threads.behind(rows, expected.thread) == []

    troponin = '"Troponin 80 ng/L."'
    assert titles.title_of(rows, ids["case"]) == f"chest pain (earlier) with {troponin}"
    assert (
        titles.title_of(rows, repair.cases[ids["case"]])
        == f"chest pain with {troponin}"
    )
    catalog.note(
        Subject(family=family), Entry(field=EntryField.NAME, present=False), alice.id
    )
    assert titles.title_of(rows, ids["case"]) == (
        f"registry/c1-renamed (earlier) with {troponin}"
    )


def test_changed_vignettes_are_repaired(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    case = resolve(reg.get, ids["case"], Case)
    source = case.vignette.source
    family = catalog.adopt(ids["case"], alice.id)
    expectation = resolve(reg.get, ids["scoring"], Scoring).expectations[0]
    expected = catalog.create(expectation, alice.id)
    edited = fp("edited at the source")
    survey = families.survey(rows, source, {"c1": edited})
    assert survey == Survey(changed=((family, "c1", edited),))

    with pytest.raises(ValueError, match="one of the id or the fingerprint"):
        _ = catalog.repair(family, alice.id)
    with pytest.raises(ValueError, match="one of the id or the fingerprint"):
        _ = catalog.repair(family, alice.id, id="c2", fingerprint=edited)
    with pytest.raises(ValueError, match="one of the id or the fingerprint"):
        _ = catalog.repair(family, alice.id, id="c1")
    other = reg.add(
        Case(vignette=Vignette(source=source, id="c2", fingerprint=fp("x")))
    )
    _ = store.add(reg, [other])
    neighbour = catalog.adopt(other, alice.id)
    with pytest.raises(ValueError, match=f"family {neighbour} already has the id 'c2'"):
        _ = catalog.repair(family, alice.id, id="c2")
    with pytest.raises(
        ValueError, match=f"family {neighbour} already has that content"
    ):
        _ = catalog.repair(family, alice.id, fingerprint=fp("x"))
    repair = catalog.repair(family, alice.id, fingerprint=edited)
    rebound = resolve(store.get, repair.cases[ids["case"]], Case)
    assert rebound.vignette == case.vignette.model_copy(update={"fingerprint": edited})
    assert threads.head(rows, expected.thread).digest == expectation
    assert repair.moves == []
    [stale] = [
        b for b in threads.behind(rows, expected.thread) if b.binding is not None
    ]
    assert (stale.path, stale.digest, stale.binding, stale.replacement) == (
        "/case",
        ids["case"],
        rows.bindings([family])[-1],
        repair.cases[ids["case"]],
    )

    for moved_to, id, fingerprint in (
        (source, "elsewhere", '{"hex": "' + "0" * 64 + '"}'),
        ("elsewhere", "c1", '{"hex": "' + edited.hex + '"}'),
    ):
        with (
            pytest.raises(errors.RaiseException, match="keep the source, and the id"),
            conn.transaction(),
        ):
            _ = conn.execute(
                """
                INSERT INTO catalog.binding (family, source, source_id, fingerprint, by)
                VALUES (%s, %s, %s, %s::jsonb, %s)
                """,
                (family, moved_to, id, fingerprint, alice.id),
            )

    second = catalog.repair(family, alice.id, id="c1-renamed")
    [stale] = [
        b for b in threads.behind(rows, expected.thread) if b.binding is not None
    ]
    assert stale.replacement == second.cases[repair.cases[ids["case"]]]


@pytest.mark.parametrize(
    "entry",
    [
        {"field": "name"},
        {"field": "name", "value": ""},
        {"field": "name", "value": "x", "present": False},
        {"field": "name", "value": None, "present": True},
        {"field": "owner", "value": "alice"},
        {"field": "owner", "person": 1, "present": False},
        {"field": "collaborator"},
        {"field": "tag", "value": "x", "person": 1},
        {"field": "deleted", "value": "yes"},
        {"field": "colour", "value": "red"},
        {"field": "language", "value": "Swedish"},
        {"field": "language", "value": "sv_SE"},
        {"field": "language", "value": ""},
        {"field": "language", "value": "sv", "present": False},
    ],
)
def test_entry_shapes(entry: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        _ = Entry.model_validate(entry)


def test_cases_have_a_language(conn: Connection) -> None:
    catalog, _, _, ids, alice = stored_world(conn)
    rows = Rows(conn)
    family = Subject(family=catalog.adopt(ids["case"], alice.id))
    assert read.about(rows, family).language is None
    for language in ("en", "sv", "pt-BR"):
        catalog.note(family, Entry(field=EntryField.LANGUAGE, value=language), alice.id)
    assert read.about(rows, family).language == "pt-BR"
    with pytest.raises(errors.CheckViolation), conn.transaction():
        _ = conn.execute(
            """
            INSERT INTO catalog.entry (family, field, value, by)
            VALUES (%s, 'language', 'Swedish', %s)
            """,
            (family.family, alice.id),
        )


@pytest.mark.slow
def test_languages_are_kept_on_digests(conn: Connection) -> None:
    catalog, store, reg, ids, alice = stored_world(conn)
    rows = Rows(conn)
    base = generation_recipe(reg)
    plan = compiled_recipe(store, reg, base)

    def in_language(digest: str, language: str) -> None:
        catalog.language(digest, language, alice.id)

    assert set(texts(base, reg.get)) == {"instructions", "prompt", "output"}
    assert language_of(rows, plan.skeleton) is None
    assert base.instructions is not None
    in_language(base.instructions, "en")
    in_language(base.prompt, "en")
    assert language_of(rows, plan.skeleton) is None
    in_language(base.output, "en")
    assert language_of(rows, plan.skeleton) == "en"
    assert language_of(rows, ids["trial"]) == "en"
    origin = catalog.create(base.output, alice.id)
    _ = catalog.create(base.output, alice.id, forked_from=origin.id)
    assert language_of(rows, base.output) == "en"
    in_language(base.output, "sv")
    assert language_of(rows, plan.skeleton) is None
    in_language(base.output, "en")
    assert language_of(rows, plan.skeleton) == "en"

    needed = [t for part in texts(base, reg.get).values() for t in part]
    swedish = reg.add(Translations(into={"sv": {t: f"[sv] {t}" for t in needed}}))
    translated = compiled_recipe(
        store, reg, base.model_copy(update={"translations": swedish}), "sv"
    )
    assert language_of(rows, translated.skeleton) == "sv"
    assert titles.title_of(rows, translated.skeleton).endswith(
        f" · translations into sv, {len(needed)} texts · "
        + titles.title_of(rows, base.model)
    )
    with pytest.raises(ValueError, match="translations components have no language"):
        in_language(swedish, "sv")

    vignette, appendices = Slot(slot="vignette"), Slot(slot="appendices")
    split = reg.add(
        Prompt(segments=("Case:", "\n", vignette, appendices, "\n\nDifferential?"))
    )
    resplit = compiled_recipe(store, reg, base.model_copy(update={"prompt": split}))
    assert resplit.skeleton == plan.skeleton
    assert language_of(rows, plan.skeleton) == "en"
    unchanged = reg.add(Translations(into={"sv": {t: t for t in needed}}))
    retold = compiled_recipe(
        store, reg, base.model_copy(update={"translations": unchanged}), "sv"
    )
    assert retold.skeleton == plan.skeleton
    assert language_of(rows, plan.skeleton) is None

    hand_written = resolve(reg.get, ids["judge"], Judge).skeleton
    assert language_of(rows, hand_written) is None
    in_language(hand_written, "en")
    assert language_of(rows, hand_written) == "en"
    assert language_of(rows, ids["judge"]) == "en"

    scoring = resolve(reg.get, ids["scoring"], Scoring)
    assert language_of(rows, ids["case"]) is None
    family = catalog.adopt(ids["case"], alice.id)
    catalog.note(
        Subject(family=family), Entry(field=EntryField.LANGUAGE, value="sv"), alice.id
    )
    assert language_of(rows, ids["case"]) == "sv"
    assert language_of(rows, scoring.expectations[0]) == "sv"
    findings = lint(reg, [ids["trial"]], languages=partial(language_of, rows))
    assert [(f.code, f.message) for f in findings] == [
        ("language.unknown", "the request's language is unknown")
    ]

    with pytest.raises(ValueError, match="not a language tag"):
        catalog.language(base.output, "Swedish", alice.id)
    with pytest.raises(ValueError, match="trial components have no language"):
        catalog.language(ids["trial"], "en", alice.id)
    with pytest.raises(ValueError, match="comes from its recipe"):
        catalog.language(plan.skeleton, "en", alice.id)
    with pytest.raises(LookupError):
        catalog.language("sha256:" + "9" * 64, "en", alice.id)
    thread = Subject(thread=origin.thread)
    with pytest.raises(ValueError, match="kept on its digest"):
        catalog.note(thread, Entry(field=EntryField.LANGUAGE, value="en"), alice.id)
    with pytest.raises(errors.CheckViolation), conn.transaction():
        _ = conn.execute(
            """
            INSERT INTO catalog.entry (thread, field, value, by)
            VALUES (%s, 'language', 'en', %s)
            """,
            (origin.thread, alice.id),
        )
    with pytest.raises(errors.CheckViolation), conn.transaction():
        _ = conn.execute(
            """
            INSERT INTO catalog.language (digest, kind, value, by)
            VALUES (%s, 'chunk.output', 'Swedish', %s)
            """,
            (base.output, alice.id),
        )
    with pytest.raises(errors.CheckViolation), conn.transaction():
        _ = conn.execute(
            """
            INSERT INTO catalog.language (digest, kind, value, by)
            VALUES (%s, 'trial', 'en', %s)
            """,
            (ids["trial"], alice.id),
        )
    with pytest.raises(errors.CheckViolation), conn.transaction():
        _ = conn.execute(
            """
            INSERT INTO catalog.language (digest, kind, value, by)
            VALUES (%s, 'chunk.translations', 'sv', %s)
            """,
            (swedish, alice.id),
        )
    with (
        pytest.raises(errors.RaiseException, match="comes from its recipe"),
        conn.transaction(),
    ):
        _ = conn.execute(
            """
            INSERT INTO catalog.language (digest, kind, value, by)
            VALUES (%s, 'skeleton', 'en', %s)
            """,
            (plan.skeleton, alice.id),
        )


def test_subject_is_one_thing() -> None:
    with pytest.raises(ValidationError):
        _ = Subject()
    with pytest.raises(ValidationError):
        _ = Subject(thread=1, run=uuid4())
    with pytest.raises(ValidationError):
        _ = Subject(thread=1, family=1)


def test_database_guards_the_catalog(conn: Connection, admin: Connection) -> None:
    catalog, _, reg, ids, alice = stored_world(conn)
    trial = catalog.create(ids["trial"], alice.id)
    family = catalog.adopt(ids["case"], alice.id)
    catalog.language(resolve(reg.get, ids["judge"], Judge).skeleton, "en", alice.id)
    catalog.note(
        Subject(thread=trial.thread),
        Entry(field=EntryField.NAME, value="x"),
        alice.id,
    )
    conn.commit()
    for table in ("thread", "edit", "entry", "label", "family", "binding", "language"):
        with pytest.raises(errors.InsufficientPrivilege), conn.transaction():
            _ = conn.execute(
                sql.SQL("DELETE FROM catalog.{}").format(sql.Identifier(table))
            )
    for table in ("edit", "binding", "language"):
        with pytest.raises(errors.RaiseException, match="insert-only"):
            _ = admin.execute(
                sql.SQL("UPDATE catalog.{} SET by = by").format(sql.Identifier(table))
            )
        admin.rollback()
    with pytest.raises(errors.CheckViolation), conn.transaction():
        _ = conn.execute(
            """
            INSERT INTO catalog.entry (thread, family, field, value, by)
            VALUES (%s, %s, 'name', 'x', %s)
            """,
            (trial.thread, family, alice.id),
        )
    for statement in (
        "INSERT INTO catalog.thread (kind, by) VALUES ('case', %s)",
        "INSERT INTO catalog.entry (field, value, by) VALUES ('name', 'x', %s)",
    ):
        with pytest.raises(errors.CheckViolation), conn.transaction():
            _ = conn.execute(statement, (alice.id,))
    for field, value in (("owner", "alice"), ("colour", "red"), ("name", "")):
        with pytest.raises(errors.CheckViolation), conn.transaction():
            _ = conn.execute(
                """
                INSERT INTO catalog.entry (thread, field, value, by)
                VALUES (%s, %s, %s, %s)
                """,
                (trial.thread, field, value, alice.id),
            )
    with pytest.raises(errors.ForeignKeyViolation), conn.transaction():
        _ = conn.execute(
            """
            INSERT INTO catalog.edit (thread, kind, digest, by)
            VALUES (%s, 'trial', %s, %s)
            """,
            (trial.thread, ids["case"], alice.id),
        )


def test_kinds_and_fields_match_the_database(admin: Connection) -> None:
    checks = [
        str(d)
        for (d,) in admin.execute(
            """
            SELECT pg_get_constraintdef(oid) FROM pg_constraint
            WHERE conrelid IN (
                'catalog.thread'::regclass,
                'catalog.entry'::regclass,
                'catalog.language'::regclass
            )
                AND contype = 'c' AND pg_get_constraintdef(oid) LIKE '%%ANY (ARRAY%%'
            """
        )
    ]
    for names in (THREAD_KINDS, {f.value for f in EntryField}, LANGUAGE_KINDS):
        [_] = [
            c
            for c in checks
            if all(f"'{n}'" in c for n in names) and c.count("'") == 2 * len(names)
        ]
    assert THREAD_KINDS == BY_KIND.keys() - {"case", "compilation"}
    [shape] = admin.execute(
        """
        SELECT pg_get_constraintdef(oid) FROM pg_constraint
        WHERE conrelid = 'catalog.entry'::regclass AND conname = 'entry_shape_check'
        """
    ).fetchall()
    assert f"'^({'|'.join(RECIPE_PARTS)})=" in str(shape[0])


def test_reader_reads_the_catalog(conn: Connection) -> None:
    privileges = conn.execute(
        """
        SELECT
            bool_and(has_table_privilege('chatddx_reader', c.oid, 'SELECT')),
            bool_or(has_table_privilege('chatddx_reader', c.oid, 'INSERT')),
            bool_and(has_table_privilege('chatddx_writer', c.oid, 'INSERT')),
            bool_or(has_table_privilege('chatddx_writer', c.oid, 'UPDATE'))
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'catalog' AND c.relkind = 'r'
        """
    ).fetchone()
    assert privileges == (True, False, True, False)
