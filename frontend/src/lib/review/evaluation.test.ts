import { describe, expect, it } from "vitest";
import { cells, type Configured, keyed, replicates, type Scored, shown, valued, worded } from "./evaluation";

const configured: Configured = {
  configuration: 7,
  name: "lines",
  runs: [
    { run: "a", seeds: [11, 12, 13], greedy: false },
    { run: "b", seeds: [13], greedy: false },
  ],
};

describe("replicates", () => {
  it("numbers a configuration's items across its runs, the fourth under the third's seed", () => {
    expect(replicates(configured).map((r) => [r.key, r.n, r.seed])).toEqual([
      ["a:0", 1, 11],
      ["a:1", 2, 12],
      ["a:2", 3, 13],
      ["b:0", 4, 13],
    ]);
    const greedy = { ...configured, runs: configured.runs.map((r) => ({ ...r, greedy: true })) };
    expect(replicates(greedy).every((r) => r.seed === null)).toBe(true);
  });
});

describe("cells", () => {
  const scorers = {
    s: [
      { label: "differential", field: "diagnosis", unit: "" },
      { label: "dont-miss", field: "dont_miss", unit: "" },
    ],
  };
  it("averages each view reading a field over the configuration's items", () => {
    const scored: Scored = {
      [keyed("a", 0)]: { "s#0": 1, "s#1": null },
      [keyed("a", 1)]: { "s#0": 0 },
      [keyed("b", 0)]: { "s#0": 0.5 },
      [keyed("other", 0)]: { "s#0": 0 },
    };
    expect(cells(configured, "diagnosis", scored, scorers)).toEqual([
      { scorer: "s", view: 0, label: "differential", mean: 0.5, unit: "" },
    ]);
    expect(cells(configured, "dont_miss", scored, scorers)).toEqual([
      { scorer: "s", view: 1, label: "dont-miss", mean: null, unit: "" },
    ]);
    expect(cells(configured, "notes", scored, scorers)).toEqual([]);
    expect(cells(configured, "diagnosis", { "a:0": { "unknown#0": 1 } }, scorers)).toEqual([]);
  });
});

describe("what an item gave", () => {
  it("is valid, salvaged or broken, but for stopped", () => {
    expect(
      ["valid", "completed", "salvaged", "invalid", "errored", "unread", "stopped"].map((o) => worded(o as never)),
    ).toEqual(["valid", "valid", "salvaged", "broken", "broken", "broken", "stopped"]);
  });

  it("shows text as it is and structure as JSON", () => {
    expect(shown("Sepsis")).toEqual({ text: "Sepsis" });
    expect(shown({ a: [1] })).toEqual({ code: '{\n  "a": [\n    1\n  ]\n}' });
    expect([valued(null, ""), valued(0.5, ""), valued(2.7, "@")]).toEqual(["—", "0.50", "@2"]);
  });
});
