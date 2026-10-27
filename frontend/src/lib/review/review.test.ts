import { describe, expect, it } from "vitest";
import { begun } from "$lib/runs/progress";
import { added, doing, replaced, said, valued, viewed } from "./review";

describe("added", () => {
  it("adds what is typed, comma by comma, once and sorted", () => {
    expect(added(["copd", "swedish"], " akm, copd ,dutch,akm")).toEqual(["akm", "copd", "dutch", "swedish"]);
  });

  it("keeps the tags as they are when nothing new is typed", () => {
    const tags = ["copd"];
    expect(added(tags, " , copd")).toBe(tags);
  });
});

describe("viewed", () => {
  const items = [
    { case: "c", replicate: 0, view: 0, value: 0.5, detail: { answer: "2. Septic shock" }, judge_calls: [] },
    { case: "c", replicate: 0, view: 1, value: 1, detail: { seeds: [1] }, judge_calls: [{}, {}] },
    { case: "c", replicate: 1, view: 0, value: 0, detail: { reason: "not listed" }, judge_calls: [] },
  ];

  it("gives each view of a replicate its value, what it said and its judges' calls", () => {
    expect(viewed(items, 0, ["differential", "comment", "graded"], ["", "", ""])).toEqual([
      { label: "differential", value: "0.50", said: [["answer", "2. Septic shock"]], calls: 0 },
      { label: "comment", value: "1.00", said: [["seeds", "[1]"]], calls: 2 },
      { label: "graded", value: "—", said: [], calls: 0 },
    ]);
  });
});

describe("valued", () => {
  it("shows a score to two places and an offset as where it is", () => {
    expect(valued(0.5, "")).toBe("0.50");
    expect(valued(44, "@")).toBe("@44");
    expect(valued(null, "@")).toBe("—");
  });
});

describe("said", () => {
  it("reads a detail as pairs, and anything else as one", () => {
    expect(said({ reason: "no answer" })).toEqual([["reason", "no answer"]]);
    expect(said("plain")).toEqual([["", "plain"]]);
    expect(said(null)).toEqual([]);
  });
});

describe("replaced", () => {
  it("follows the case shown to the one that replaced it", () => {
    const back = "/review/3?case=old&tag=swedish";
    expect(replaced(back, "old", { old: "new" })).toBe("/review/3?case=new&tag=swedish");
    expect(replaced("/review/3", "old", { old: "new" })).toBe("/review/3?case=new");
    expect(replaced(back, "old", { other: "new" })).toBe(back);
  });
});

describe("doing", () => {
  const item = { case: "c", replicate: 0, tools: 0, outcome: null, why: null, sent: 0, received: 0 };
  const text = { reasoning: "", content: "", tool_call: "" };

  it("says how far a run under way has come, in a line", () => {
    const progress = begun();
    expect(doing(progress)).toBe("queued");
    progress.items.push({ ...item, phase: "sending", kind: "content", tokens: 12, text });
    expect(doing(progress)).toBe("0 of 1 ended, writing: 12 tokens");
    progress.items[0] = { ...item, phase: "ended", kind: "content", tokens: 30, text };
    expect(doing(progress)).toBe("1 of 1 ended");
  });

  it("says its scoring, and when it is done", () => {
    const progress = begun();
    progress.scorings.push({ scorer: "s", name: "judged", score: "x", views: 3, scored: 2, asked: 4, answered: 3 });
    expect(doing(progress)).toBe("scoring: 2 scored, judges answered 3 of 4");
    progress.done = { halted: false } as never;
    expect(doing(progress)).toBe("done");
  });
});
