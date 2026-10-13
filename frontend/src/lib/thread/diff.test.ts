import { describe, expect, it } from "vitest";
import { changes, same } from "./diff";

describe("what a version changed", () => {
  it("is nothing when it holds the same", () => {
    expect(changes({ a: [1, { b: "x" }] }, { a: [1, { b: "x" }] })).toEqual([]);
    expect(same({ a: 1, b: 2 }, { b: 2, a: 1 })).toBe(true);
  });

  it("is a text's words", () => {
    const [change] = changes({ text: "Be careful." }, { text: "Be very careful." });
    expect(change).toMatchObject({ path: "/text", was: "changed" });
    if (change?.was !== "changed" || !change.words) throw new Error("a text changed");
    expect(change.words.filter((w) => w.added).map((w) => w.value.trim())).toEqual(["very"]);
    expect(change.words.filter((w) => w.removed)).toEqual([]);
  });

  it("is each field added, removed or changed, as deep as they go", () => {
    const before = { kind: "x", data: { warning: { pattern: "a" }, notes: [1] }, gone: true };
    const after = { kind: "x", data: { warning: false, notes: [1], disposition: { text: "home" } } };
    expect(changes(before, after).map((c) => [c.path, c.was])).toEqual([
      ["/data/warning", "changed"],
      ["/data/disposition", "added"],
      ["/gone", "removed"],
    ]);
  });

  it("is a whole list when it grows or shrinks, and each item when it doesn't", () => {
    expect(changes({ a: [1, 2] }, { a: [1, 3] }).map((c) => c.path)).toEqual(["/a/1"]);
    expect(changes({ a: [1] }, { a: [1, 2] }).map((c) => c.path)).toEqual(["/a"]);
  });
});
