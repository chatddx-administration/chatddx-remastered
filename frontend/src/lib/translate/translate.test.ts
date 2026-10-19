import { describe, expect, it } from "vitest";
import {
  type Body,
  type Configuration,
  closest,
  edges,
  entriesOf,
  type Held,
  marked,
  missingOf,
  places,
  savedTo,
  translationsOf,
  unlike,
  visible,
} from "./translate";

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

describe("closest", () => {
  const unused = {
    "List the plausible diagnoses, one per line, most likely first.": "Lista de tänkbara diagnoserna, en per rad.",
    "Something else entirely.": "Något helt annat.",
  };

  it("offers the unused entry of a text much like it, with what differs word by word", () => {
    const offer = closest("List the likely diagnoses, one per line, most likely first.", unused);
    expect(offer?.translation).toBe("Lista de tänkbara diagnoserna, en per rad.");
    expect(offer?.words.filter((w) => w.removed).map((w) => w.value)).toEqual(["plausible"]);
    expect(offer?.words.filter((w) => w.added).map((w) => w.value)).toEqual(["likely"]);
  });

  it("offers none when no unused text is near", () => {
    expect(closest("Give your assessment.", unused)).toBeNull();
    expect(closest("Anything.", {})).toBeNull();
  });
});

const HELD: Held = {
  title: "sample",
  thread: 3,
  head: 30,
  mine: false,
  owner: "archive",
  digest: "sha256:held",
  body: { kind: "chunk.translations", into: { de: { A: "A-de" }, sv: { A: "A-sv", Gone: "Borta" } } },
};
const CONFIGURATION: Configuration = {
  thread: 7,
  head: 70,
  latest: true,
  mine: true,
  owner: "alice",
  name: "lines-guided",
  translations: "sha256:held",
};

describe("what is saved", () => {
  it("keeps what was typed, the unused entries kept, and the other languages", () => {
    const entries = entriesOf({ A: "Á", B: "" }, { Gone: "Borta", A: "old" });
    expect(entries).toEqual({ Gone: "Borta", A: "Á" });
    expect(translationsOf(HELD, "sv", entries)).toEqual({
      kind: "chunk.translations",
      into: { de: { A: "A-de" }, sv: entries },
    });
    expect(translationsOf(HELD, "fi", { A: "A-fi" })?.into).toHaveProperty("fi");
    expect(translationsOf(HELD, "de", {})?.into).not.toHaveProperty("de");
    expect(translationsOf(null, "sv", {})).toBeNull();
  });

  it("says where the translations and the configuration go", () => {
    const both = { translations: false, configuration: false };
    expect(savedTo(HELD, CONFIGURATION, both)).toBe(
      "Saves a fork of archive's sample as your own, and a new version of your lines-guided, holding them.",
    );
    expect(savedTo({ ...HELD, mine: true, owner: "alice" }, CONFIGURATION, { ...both, configuration: true })).toBe(
      "Saves a new version of your sample.",
    );
    expect(savedTo(null, { ...CONFIGURATION, mine: false, owner: "bob" }, both)).toBe(
      "Saves new translations of your own, lines-guided, and a fork of bob's lines-guided as your own, holding them.",
    );
    expect(savedTo(HELD, { ...CONFIGURATION, latest: false }, { translations: true, configuration: false })).toBe(
      "Saves a fork of alice's lines-guided as your own.",
    );
    expect(savedTo(HELD, CONFIGURATION, { translations: true, configuration: true })).toBe(
      "Nothing to save: it holds these already.",
    );
  });
});
