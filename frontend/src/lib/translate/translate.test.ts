import { describe, expect, it } from "vitest";
import { type Body, edges, marked, missingOf, places, unlike, visible } from "./translate";

const BODIES: Body[] = [
  { part: "appendix_layout", body: { before: "\n\nAppendices:\n", between: "\n\n", after: "" } },
  {
    part: "instructions",
    body: {
      kind: "chunk.instructions",
      role: "developer",
      text: ["Read the case.", { insert: "output_guidance", before: "\n\nThen:\n", after: "" }],
    },
  },
  {
    part: "few_shot",
    body: {
      kind: "chunk.few_shot",
      messages: [
        { role: "user", content: "Chest pain." },
        { role: "assistant", content: "ACS" },
        { role: "user", content: "Fever." },
      ],
    },
  },
  {
    part: "output",
    body: {
      kind: "chunk.output",
      contract: { kind: "tool", name: "plan", description: "The plan." },
      guidance: "Answer.",
      json_schema: {
        title: "Plan",
        properties: {
          urgency: { type: "string", enum: ["The plan."], description: "How urgent." },
          diagnoses: { type: "array", items: { properties: { name: { description: "How urgent." } } } },
        },
      },
    },
  },
  { part: "toolset", body: { kind: "chunk.toolset", guidance: "Look it up.", tools: ["sha256:…"] } },
  {
    part: "toolset",
    body: {
      kind: "tool",
      name: "lookup",
      description: "Look it up.",
      parameters: { properties: { query: { description: "What to look up." } } },
    },
  },
];

describe("places", () => {
  it("says where in its chunk a text sits", () => {
    expect(places("Read the case.", "instructions", BODIES)).toEqual([""]);
    expect(places("\n\nThen:\n", "instructions", BODIES)).toEqual(["before ‹output guidance›"]);
    expect(places("Fever.", "few_shot", BODIES)).toEqual(["user 2"]);
    expect(places("ACS", "few_shot", BODIES)).toEqual(["assistant 1"]);
    expect(places("\n\nAppendices:\n", "appendix_layout", BODIES)).toEqual(["before the appendices"]);
  });

  it("names a schema's text by the properties it sits under, and leaves its data out", () => {
    expect(places("Plan", "output", BODIES)).toEqual(["schema · title"]);
    expect(places("How urgent.", "output", BODIES)).toEqual([
      "schema › urgency · description",
      "schema › diagnoses › name · description",
    ]);
    expect(places("The plan.", "output", BODIES)).toEqual(["the answer tool's description"]);
    expect(places("Answer.", "output", BODIES)).toEqual(["guidance"]);
  });

  it("finds a toolset's texts in its tools too", () => {
    expect(places("Look it up.", "toolset", BODIES)).toEqual(["guidance", "lookup's description"]);
    expect(places("What to look up.", "toolset", BODIES)).toEqual([
      "lookup's parameters, schema › query · description",
    ]);
    expect(places("Look it up.", "output", BODIES)).toEqual([]);
  });
});

describe("whitespace", () => {
  it("is shown at a text's edges and at each line's end", () => {
    expect(visible("\n\nAppendices:\n")).toBe("⏎\n⏎\nAppendices:⏎\n");
    expect(visible("  Case: a b ")).toBe("··Case: a b·");
    expect(edges("\n\nLabs:\n")).toEqual(["\n\n", "\n"]);
    expect(edges("  ")).toEqual(["  ", ""]);
  });

  it("differs when a translation's edges aren't its source's", () => {
    expect(unlike("\n\nAppendices:\n", "\n\nBilagor:\n")).toBe(false);
    expect(unlike("\n\nAppendices:\n", "Bilagor:")).toBe(true);
    expect(unlike("Case: ", "Fall:")).toBe(true);
  });
});

describe("marked", () => {
  it("marks each untranslated text where it is sent, the longest first", () => {
    expect(marked("Fall: List them. List", ["List", "List them."])).toEqual([
      { text: "Fall: ", missing: false },
      { text: "List them.", missing: true },
      { text: " ", missing: false },
      { text: "List", missing: true },
    ]);
    expect(marked("Allt översatt.", ["List"])).toEqual([{ text: "Allt översatt.", missing: false }]);
    expect(marked("", ["List"])).toEqual([]);
  });

  it("takes the texts without a translation, once each", () => {
    const texts = [
      { part: "output", text: "A", translation: null },
      { part: "few_shot", text: "A", translation: null },
      { part: "output", text: "B", translation: "Bé" },
    ];
    expect(missingOf(texts)).toEqual(["A"]);
  });
});
