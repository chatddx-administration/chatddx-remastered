import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { EVENTS, type Event } from "./events";
import { begun, failed, fold, tally } from "./progress";

function folded(events: [Event, unknown][]) {
  const progress = begun();
  for (const [name, data] of events) fold(progress, name, data);
  return progress;
}

const STARTED = {
  run: "r",
  trial: "t",
  skeleton: "s",
  endpoint: "qwen@fake",
  cases: ["a", "b"],
  seeds: [7],
  greedy: false,
};

describe("the events", () => {
  it("are the API's", () => {
    const document = JSON.parse(readFileSync(new URL("../../../openapi.json", import.meta.url), "utf8"));
    const said: string = document.paths["/api/runs/{run}/events"].get.responses["200"].description;
    const listed = said.split("The events are ")[1]?.split(", each with")[0] ?? "";
    expect([...listed.matchAll(/`([a-z.]+)`/g)].map((m) => m[1])).toEqual([...EVENTS]);
  });
});

describe("a run's progress", () => {
  it("holds an item per case, as it is sent and as it ends", () => {
    const progress = folded([
      ["run.started", STARTED],
      ["item.started", { case: "a", replicate: 0, seed: 7 }],
      ["item.delta", { case: "a", replicate: 0, kind: "reasoning", text: "Hm", tokens: 1 }],
      ["item.delta", { case: "a", replicate: 0, kind: "reasoning", text: "m.", tokens: 2 }],
      ["item.delta", { case: "a", replicate: 0, kind: "content", text: "Colic", tokens: 3 }],
    ]);
    const [a, b] = progress.items;
    if (!a || !b) throw new Error("an item per case");
    expect([a.phase, a.kind, a.tokens, a.text.reasoning, a.text.content]).toEqual([
      "sending",
      "content",
      3,
      "Hmm.",
      "Colic",
    ]);
    expect(b.phase).toBe("waiting");
    expect(tally(progress)).toEqual({ ended: 0, of: 2, outcomes: [] });

    fold(progress, "item.ended", {
      case: "a",
      replicate: 0,
      outcome: "valid",
      prompt_tokens: 10,
      completion_tokens: 3,
      why: null,
    });
    fold(progress, "item.ended", {
      case: "b",
      replicate: 0,
      outcome: "stopped",
      prompt_tokens: 10,
      completion_tokens: 0,
      why: "halted",
    });
    expect([a.phase, a.kind, a.outcome, a.received, a.text.content]).toEqual(["ended", null, "valid", 3, "Colic"]);
    expect(tally(progress)).toEqual({
      ended: 2,
      of: 2,
      outcomes: [
        ["valid", 1],
        ["stopped", 1],
      ],
    });
  });

  it("holds an item per case and seed, each case's together", () => {
    const progress = folded([["run.started", { ...STARTED, seeds: [7, 9] }]]);
    expect(progress.items.map((i) => [i.case, i.replicate, i.phase])).toEqual([
      ["a", 0, "waiting"],
      ["a", 1, "waiting"],
      ["b", 0, "waiting"],
      ["b", 1, "waiting"],
    ]);
  });

  it("follows the scoring scorer by scorer, with its judges", () => {
    const progress = folded([
      ["run.finished", { findings: [] }],
      [
        "run.scoring",
        {
          scorers: [
            { scorer: "x", name: "plan" },
            { scorer: "y", name: "notes" },
          ],
        },
      ],
      ["score.started", { scorer: "x", name: "plan", score: "s1", labels: ["a", "b"] }],
      ["score.item", { score: "s1", case: "a", replicate: 0, view: 0, value: 1, detail: null }],
      ["score.item", { score: "s1", case: "a", replicate: 0, view: 1, value: 0, detail: null }],
      ["score.started", { scorer: "y", name: "notes", score: "s2", labels: ["graded"] }],
      ["judge.asked", { case: "a", replicate: 0, scorer: "y", view: 0, judge: "j", seed_index: 0 }],
      ["judge.answered", { case: "a", replicate: 0, view: 0, judge: "j", seed_index: 0, verdict: null, call: null }],
      ["score.noted", { level: "warning", code: "c", message: "m", subject: null, wording: null, params: {} }],
      ["run.scored", { scores: [] }],
      ["done", { halted: false }],
    ]);
    expect(progress.scorings.map((s) => [s.name, s.views, s.scored, s.asked, s.answered])).toEqual([
      ["plan", 2, 2, 0, 0],
      ["notes", 1, 0, 1, 1],
    ]);
    expect([progress.noted.length, progress.scores, progress.done]).toEqual([1, [], { halted: false }]);
    expect(progress.items).toEqual([]);
  });

  it("keeps what went wrong", () => {
    expect(folded([["error", { detail: "the engine went away" }]]).errors).toEqual(["the engine went away"]);
  });
});

describe("a run that went wrong", () => {
  it("says what failed, else that it didn't finish, as a run told from the ledger has no errors", () => {
    expect(
      failed(
        folded([
          ["run.started", STARTED],
          ["run.finished", { findings: [] }],
          ["done", { halted: null }],
        ]),
      ),
    ).toBe(null);
    expect(
      failed(
        folded([
          ["run.started", STARTED],
          ["done", { halted: null }],
        ]),
      ),
    ).toBe("the run didn't finish");
    const errored = folded([
      ["run.started", STARTED],
      ["error", { detail: "run r failed: boom" }],
      ["done", { halted: false }],
    ]);
    expect(failed(errored)).toBe("run r failed: boom");
  });
});
