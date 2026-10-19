import { describe, expect, it } from "vitest";
import { blank, jsonOf, moved, numberOf, rowsOf, settingsOf, shown, stopsOf, valueOf } from "./chunks";

describe("a settings table", () => {
  it("keeps a value's type through its text", () => {
    const settings = { min_tokens: 8, logprobs: true, stop: "END", count: "5", nested: { a: [1] } };
    expect(rowsOf(settings)).toEqual([
      { key: "min_tokens", value: "8" },
      { key: "logprobs", value: "true" },
      { key: "stop", value: "END" },
      { key: "count", value: '"5"' },
      { key: "nested", value: '{"a":[1]}' },
    ]);
    expect(settingsOf(rowsOf(settings))).toEqual(settings);
  });

  it("reads JSON where it is JSON, else a text, and leaves out a row without a key", () => {
    expect(valueOf("0.5")).toBe(0.5);
    expect(valueOf("a word")).toBe("a word");
    expect(shown("null")).toBe('"null"');
    expect(settingsOf([{ key: " top ", value: "1" }, { key: "", value: "2" }])).toEqual({ top: 1 });
  });
});

describe("a field as typed", () => {
  it("is a number, nothing, or the text for the check to refuse", () => {
    expect(numberOf(" 0.7 ")).toBe(0.7);
    expect(numberOf("")).toBeNull();
    expect(numberOf("warm")).toBe("warm");
  });

  it("is JSON, nothing, or why it isn't JSON", () => {
    expect(jsonOf('{"type": "object"}')).toEqual({ value: { type: "object" } });
    expect(jsonOf("  ")).toEqual({ value: null });
    expect("problem" in jsonOf("{")).toBe(true);
  });

  it("is a stop sequence a line", () => {
    expect(stopsOf("END\n\n###")).toEqual(["END", "###"]);
    expect(stopsOf("")).toEqual([]);
  });
});

describe("a new chunk", () => {
  it("starts as the least each kind holds", () => {
    expect(blank("chunk.prompt")).toEqual({ kind: "chunk.prompt", purpose: "generation", segments: [{ slot: "vignette" }] });
    expect(blank("chunk.reasoning")).toEqual({ kind: "chunk.reasoning", level: "default" });
    expect(blank("chunk.output")).toEqual({ kind: "chunk.output", contract: { kind: "text" } });
  });
});

describe("a list's order", () => {
  it("moves one up or down, and not past either end", () => {
    expect(moved(["a", "b", "c"], 1, -1)).toEqual(["b", "a", "c"]);
    expect(moved(["a", "b", "c"], 1, 1)).toEqual(["a", "c", "b"]);
    expect(moved(["a", "b"], 0, -1)).toEqual(["a", "b"]);
  });
});
