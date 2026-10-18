import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { chosen, choices, same } from "./selectors";

const TARGETS = JSON.parse(readFileSync(new URL("../../../../worlds/sample/_data/schemas/targets.json", import.meta.url), "utf8"));
const PLAN = JSON.parse(
  readFileSync(new URL("../../../../worlds/sample/_data/schemas/management_plan_v1.json", import.meta.url), "utf8"),
);
const DATA = {
  diagnosis: { pattern: "sepsis" },
  notes: [
    { author: "carol", language: "sv", comment: "Chock." },
    { author: "dave", language: "sv", comment: "UVI." },
  ],
};

describe("choices", () => {
  const found = choices(TARGETS, DATA, "the whole expectation");
  const by = Object.fromEntries(found.map((c) => [c.label, c.selector]));

  it("offers the whole, each field and what a target holds", () => {
    expect(found[0]).toEqual({ label: "the whole expectation", selector: "" });
    expect(by["diagnosis"]).toBe("/diagnosis");
    expect(by["dont miss"]).toBe("/dont_miss");
    expect(by["warning › pattern"]).toBe("/warning/pattern");
  });

  it("offers each item of a list, and the items of an author written", () => {
    expect(by["each of notes › comment"]).toBe("$.notes[*].comment");
    expect(by["notes where author is carol › comment"]).toBe("$.notes[?@.author == 'carol'].comment");
    expect(by["notes where author is dave › answer"]).toBe("$.notes[?@.author == 'dave'].answer");
    expect(by["notes where language is sv › author"]).toBe("$.notes[?@.language == 'sv'].author");
    expect(found.some((c) => c.label.includes("where author is carol › author"))).toBe(false);
  });

  it("offers an answer's fields, and only the whole answer without a schema", () => {
    const plan = Object.fromEntries(choices(PLAN, null, "the whole answer").map((c) => [c.label, c.selector]));
    expect(plan["each of diagnoses › diagnosis"]).toBe("$.diagnoses[*].diagnosis");
    expect(plan["management › disposition"]).toBe("/management/disposition");
    expect(choices(null, null, "the whole answer")).toEqual([{ label: "the whole answer", selector: "" }]);
  });
});

describe("chosen", () => {
  const found = choices(TARGETS, DATA, "the whole expectation");

  it("finds a selector's choice, written as a pointer or a dotted path", () => {
    expect(chosen("/diagnosis", found)?.label).toBe("diagnosis");
    expect(chosen("$.diagnosis", found)?.label).toBe("diagnosis");
    expect(chosen("", found)?.label).toBe("the whole expectation");
    expect(chosen("$.notes[?@.author == 'carol'].comment", found)?.label).toBe("notes where author is carol › comment");
    expect(chosen("$..pattern", found)).toBeUndefined();
  });

  it("reads a dotted path as the pointer to the same place", () => {
    expect(same("$.management.disposition")).toBe("/management/disposition");
    expect(same("$.notes[*]")).toBe("$.notes[*]");
  });
});
