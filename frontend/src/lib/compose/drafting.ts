import type { Schema } from "$lib/schema/form";

export const CHUNKS = [
  "instructions",
  "few_shot",
  "prompt",
  "output",
  "sampling",
  "reasoning",
  "passthrough",
  "toolset",
] as const;

export type Chunk = (typeof CHUNKS)[number];
export type Body = Record<string, unknown>;
export type Chunks = Record<Chunk, Body | null>;
export type Into = Record<string, Record<string, string>>;

export type Drafted = {
  model: string;
  chunks: Chunks;
  into: Into;
  texts: Record<string, string[]>;
  schemas: Record<Chunk, Schema>;
  inserts: Record<string, string[]>;
  slots: Record<string, string[]>;
};

// Dependency: src/chatddx/factors/request.py:texts orders a recipe's texts by these parts.
export const TEXTS = ["instructions", "few_shot", "prompt", "output", "appendix_layout", "toolset"] as const;

export function cleaned(into: Into): Into {
  const found: Into = {};
  for (const [language, entries] of Object.entries(into)) {
    const kept = Object.entries(entries).filter(([text, said]) => text.trim() && said.trim());
    if (kept.length) found[language] = Object.fromEntries(kept);
  }
  return found;
}

export function kept(into: Into, given: Into): Into {
  return { ...Object.fromEntries(Object.keys(into).map((l) => [l, {}])), ...given };
}

export function counted(texts: Record<string, string[]>, entries: Record<string, string>): [number, number] {
  const all = [...new Set(Object.values(texts).flat())];
  return [all.filter((t) => entries[t]?.trim()).length, all.length];
}

export function same(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export function blank(part: Chunk): Body {
  switch (part) {
    case "instructions":
      return { kind: "chunk.instructions", role: "system", text: "" };
    case "few_shot":
      return {
        kind: "chunk.few_shot",
        messages: [
          { role: "user", content: "" },
          { role: "assistant", content: "" },
        ],
      };
    case "reasoning":
      return { kind: "chunk.reasoning" };
    case "passthrough":
      return { kind: "chunk.passthrough", body: {} };
    case "toolset":
      return { kind: "chunk.toolset", tools: [] };
    default:
      return { kind: `chunk.${part}` };
  }
}

// Dependency: src/chatddx/factors/request.py:compile_request refuses a guidance inserted in both the instructions and the
// prompt, and fills one in only where it is held.
const STANDS_FOR: Record<string, (chunks: Chunks) => boolean> = {
  output_guidance: (c) => c.output?.guidance != null,
  tool_guidance: (c) => c.toolset?.guidance != null,
};

function placed(body: Body | null, name: string): string[] {
  const held = body?.[name];
  if (!Array.isArray(held)) return [];
  return held.flatMap((s) =>
    typeof s === "object" && s !== null && "insert" in s ? [String((s as { insert: unknown }).insert)] : [],
  );
}

export function offered(part: Chunk, chunks: Chunks, inserts: string[]): string[] {
  const elsewhere = [
    ...(part === "instructions" ? [] : placed(chunks.instructions, "text")),
    ...(part === "prompt" ? [] : placed(chunks.prompt, "segments")),
  ];
  return inserts.filter((i) => !elsewhere.includes(i) && (STANDS_FOR[i]?.(chunks) ?? true));
}
