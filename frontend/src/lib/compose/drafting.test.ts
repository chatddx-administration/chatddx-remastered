import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { type Chunks, CHUNKS, cleaned, counted, kept, offered, paired, restaled, settled } from "./drafting";

describe("translations as they are drafted", () => {
  it("leave out what has no translation, and a language with none", () => {
    expect(cleaned({ sv: { Read: "Läs", Answer: " " }, de: { Read: "" } })).toEqual({ sv: { Read: "Läs" } });
  });

  it("keep a language added before it has any, as the server answers without it", () => {
    expect(kept({ sv: {}, de: {} }, { sv: { Read: "Läs" } })).toEqual({ de: {}, sv: { Read: "Läs" } });
  });

  it("count each text once, wherever it is held", () => {
    expect(counted({ prompt: ["Read", "Answer"], output: ["Read"] }, { Read: "Läs" })).toEqual([1, 2]);
  });
});

describe("translations carried over", () => {
  it("are to be looked over once carried to a text that changed, and no more once that text is gone", () => {
    const before = { sv: { Read: "Läs", Answer: "Svara" } };
    const after = { sv: { "Read it": "Läs", Answer: "Svara" } };
    expect(restaled({}, before, after)).toEqual({ sv: ["Read it"] });
    expect(restaled({ sv: ["Read it"] }, after, { sv: { Answer: "Svara" } })).toEqual({});
  });

  it("are looked over one at a time", () => {
    expect(settled({ sv: ["Read", "Answer"], de: ["Read"] }, "sv", "Read")).toEqual({ sv: ["Answer"], de: ["Read"] });
    expect(settled({ sv: ["Read"] }, "sv", "Read")).toEqual({});
  });
});

describe("the texts paired with their translations", () => {
  it("are the prose's, an insert's surroundings among them, and not what is blank", () => {
    const chunks: Chunks = {
      ...(Object.fromEntries(CHUNKS.map((c) => [c, null])) as Chunks),
      instructions: { text: ["Read", { insert: "schema", before: "Answer as: ", after: " " }] },
      few_shot: {
        messages: [
          { role: "user", content: "Hi" },
          { role: "assistant", content: "" },
        ],
      },
      prompt: { segments: [{ slot: "vignette" }, "Answer"] },
      output: { guidance: "Briefly", json_schema: { description: "The answer" } },
      toolset: { guidance: "Use them" },
    };
    expect([...paired(chunks)]).toEqual(["Read", "Answer as: ", "Hi", "Answer", "Briefly", "Use them"]);
  });
});

describe("the chunks", () => {
  it("are the API's parts, but the translations, which are drafted by language, and the model, which is picked", () => {
    const document = JSON.parse(readFileSync(new URL("../../../openapi.json", import.meta.url), "utf8"));
    const parts = Object.keys(document.components.schemas.Parts.properties);
    expect(parts.filter((p) => p !== "translations" && p !== "model")).toEqual([...CHUNKS]);
  });
});

describe("the inserts offered", () => {
  const none = Object.fromEntries(CHUNKS.map((c) => [c, null])) as Chunks;
  const both = ["output_guidance", "tool_guidance"];

  it("are those placed nowhere else, where what they stand for is held", () => {
    const chunks: Chunks = {
      ...none,
      instructions: { kind: "chunk.instructions", text: ["Read.", { insert: "output_guidance" }] },
      prompt: { kind: "chunk.prompt", segments: [{ slot: "vignette" }] },
      output: { kind: "chunk.output", guidance: "Lines." },
    };
    expect(offered("prompt", chunks, both)).toEqual([]);
    expect(offered("instructions", chunks, both)).toEqual(["output_guidance"]);
    const tools = { ...chunks, toolset: { kind: "chunk.toolset", guidance: "Use them." } };
    expect(offered("prompt", tools, both)).toEqual(["tool_guidance"]);
  });
});
