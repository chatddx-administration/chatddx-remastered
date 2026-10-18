import { describe, expect, it } from "vitest";
import { fieldOf, replaced, said, shortly, stepped, valued, viewed } from "./review";

const STEPS = { previous: "/review/1", next: "/review/3" };

function pressed(key: string, more: Record<string, unknown> = {}) {
  return { key, altKey: false, ctrlKey: false, metaKey: false, target: null, ...more };
}

describe("stepped", () => {
  it("goes to the next case on j and the one before on k", () => {
    expect(stepped(pressed("j"), STEPS)).toBe("/review/3");
    expect(stepped(pressed("k"), STEPS)).toBe("/review/1");
    expect(stepped(pressed("j"), { previous: null, next: null })).toBeNull();
  });

  it("leaves keys alone while something is typed or held", () => {
    expect(stepped(pressed("j", { target: { tagName: "TEXTAREA" } }), STEPS)).toBeNull();
    expect(stepped(pressed("j", { target: { tagName: "DIV", isContentEditable: true } }), STEPS)).toBeNull();
    expect(stepped(pressed("j", { ctrlKey: true }), STEPS)).toBeNull();
    expect(stepped(pressed("x"), STEPS)).toBeNull();
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

describe("fieldOf", () => {
  it("names the top-level field a selector starts in", () => {
    expect(fieldOf("/diagnosis")).toBe("diagnosis");
    expect(fieldOf("/dont_miss/pattern")).toBe("dont_miss");
    expect(fieldOf("/a~1b")).toBe("a/b");
    expect(fieldOf("$.notes[?@.author == 'carol'].comment")).toBe("notes");
    expect(fieldOf("$['dont miss']")).toBe("dont miss");
  });

  it("names none for the whole expectation or a field it can't tell", () => {
    expect(fieldOf("")).toBeNull();
    expect(fieldOf("$[*]")).toBeNull();
    expect(fieldOf("$..pattern")).toBeNull();
  });
});

describe("shortly", () => {
  it("says what was picked in a line, cut short", () => {
    expect(shortly([{ pattern: "sepsis | septic & shock" }])).toBe("pattern: sepsis | septic & shock");
    expect(shortly(["Chock,\n troligen  septisk.", "Uteslut UVI."])).toBe("Chock, troligen septisk. · Uteslut UVI.");
    expect(shortly(["a".repeat(100)], 10)).toBe(`${"a".repeat(9)}…`);
    expect(shortly([false])).toBe("false");
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
