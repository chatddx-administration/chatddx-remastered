import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { type Chunks, CHUNKS, cleaned, counted, kept, offered } from "./drafting";

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
