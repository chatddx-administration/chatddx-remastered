import type { Schema } from "$lib/schema/form";
import { isInsert, segmentsOf } from "$lib/scorer/texts";

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
  tools: Record<string, Body>;
};

export type Stale = Record<string, string[]>;

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

function own(text: unknown): string[] {
  return typeof text === "string" && text.trim() ? [text] : [];
}

function keysOf(text: unknown): string[] {
  return segmentsOf(text).flatMap((s) =>
    typeof s === "string" ? own(s) : isInsert(s) ? [...own(s.before), ...own(s.after)] : [],
  );
}

export type Message = { role: string; content: string };

export function messagesOf(body: Body | null): Message[] {
  const held = body?.messages;
  return Array.isArray(held) ? (held as Message[]) : [];
}

// Dependency: src/chatddx/factors/request.py:own_texts, the texts of the prose Compose pairs with their translations;
// the rest of what it finds, a schema's and the tools' among them, is listed as it is.
export function paired(chunks: Chunks): Set<string> {
  return new Set([
    ...(chunks.instructions ? keysOf(chunks.instructions.text) : []),
    ...messagesOf(chunks.few_shot).flatMap((m) => own(m.content)),
    ...(chunks.prompt ? keysOf(chunks.prompt.segments) : []),
    ...(chunks.output?.guidance != null ? keysOf(chunks.output.guidance) : []),
    ...own(chunks.toolset?.guidance),
  ]);
}

// Policy: a translation the server carried over to a text that changed is to be looked over, as it was written for
// the text before; the client alone keeps that, till it is typed in or said to read right.
export function restaled(stale: Stale, before: Into, after: Into): Stale {
  const found: Stale = {};
  for (const [language, entries] of Object.entries(after)) {
    const was = before[language] ?? {};
    const kept = (stale[language] ?? []).filter((k) => k in entries);
    const moved = Object.keys(entries).filter((k) => !(k in was) && !kept.includes(k));
    if (kept.length || moved.length) found[language] = [...kept, ...moved];
  }
  return found;
}

export function settled(stale: Stale, language: string, text: string): Stale {
  const left = (stale[language] ?? []).filter((k) => k !== text);
  const { [language]: _, ...rest } = stale;
  return left.length ? { ...rest, [language]: left } : rest;
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
