import { describe, expect, it } from "vitest";
import { kept, measuredAt, segments, type Text } from "./measure.svelte";

function text(found: boolean | null, alternatives: number[] = []): Text {
  return { texts: [], marks: [], found, value: null, unit: "", reason: null, count: 1, alternatives, seen: [] };
}

describe("a text measured", () => {
  it("is marked where the pattern found it, overlaps merged", () => {
    expect(
      segments("Discharge home", [
        { start: 10, end: 14 },
        { start: 0, end: 9 },
      ]),
    ).toEqual([
      { text: "Discharge", marked: true },
      { text: " ", marked: false },
      { text: "home", marked: true },
    ]);
    expect(
      segments("Home", [
        { start: 0, end: 4 },
        { start: 2, end: 3 },
      ]),
    ).toEqual([{ text: "Home", marked: true }]);
    expect(segments("Reassess.", [])).toEqual([{ text: "Reassess.", marked: false }]);
  });

  it("is kept as it was scored and by the alternative picked", () => {
    const shown = new Set(["missed", "found"] as const);
    expect(kept(text(true, [1]), shown, null)).toBe(true);
    expect(kept(text(true, [1]), shown, 0)).toBe(false);
    expect(kept(text(null), shown, null)).toBe(false);
    expect(kept(text(false), shown, null)).toBe(true);
  });
});

describe("what is measured", () => {
  it("is kept in the address, the rest of it as it is", () => {
    expect(measuredAt("/review/12?case=c&tag=t#x", "warning")).toBe("/review/12?case=c&tag=t&measure=warning#x");
    expect(measuredAt("/review/12?measure=warning&case=c", null)).toBe("/review/12?case=c");
  });
});
