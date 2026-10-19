export type Body = Record<string, unknown>;
export type Tool = { digest: string; name: string };

export const FIELD = "h-8 rounded-md border border-input bg-transparent px-2";

// Duplication: src/chatddx/catalog/model.py:LANGUAGE_KINDS, those of them a chunk editor writes.
export const LANGUAGED = new Set(["chunk.instructions", "chunk.few_shot", "chunk.prompt", "chunk.output", "chunk.toolset"]);

// Duplication: src/chatddx/factors/request.py:SLOTS_BY_PURPOSE and INSERTS_BY_KIND.
export const SLOTS_FOR: Record<string, string[]> = {
  generation: ["vignette", "appendices"],
  judge: ["vignette", "appendices", "completion", "expectation"],
};
export const TEXT_INSERTS = ["output_guidance", "tool_guidance"];

// Duplication: src/chatddx/factors/facts.py:Effort, and src/chatddx/factors/request.py:Reasoning.effort.
export const LEVELS = ["default", "off", "on", "minimal", "low", "medium", "high", "xhigh"];
export const EFFORTS = ["none", "minimal", "low", "medium", "high"];

export const SAMPLED = [
  "temperature",
  "top_p",
  "top_k",
  "min_p",
  "presence_penalty",
  "frequency_penalty",
  "repetition_penalty",
] as const;

export function blank(kind: string): Body {
  switch (kind) {
    case "chunk.instructions":
      return { kind, role: "system", text: "" };
    case "chunk.few_shot":
      return {
        kind,
        messages: [
          { role: "user", content: "" },
          { role: "assistant", content: "" },
        ],
      };
    case "chunk.prompt":
      return { kind, purpose: "generation", segments: [{ slot: "vignette" }] };
    case "chunk.output":
      return { kind, contract: { kind: "text" } };
    case "chunk.sampling":
      return { kind, recommended: true };
    case "chunk.reasoning":
      return { kind, level: "default" };
    case "chunk.passthrough":
      return { kind, body: {} };
    case "chunk.toolset":
      return { kind, tools: [], max_rounds: 5 };
    default:
      return { kind };
  }
}

// Policy: Anything typed that isn't a number is sent as typed, for the check to refuse with why.
export function numberOf(text: string): unknown {
  const t = text.trim();
  if (!t) return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : t;
}

export function typedOf(value: unknown): string {
  return value === null || value === undefined ? "" : String(value);
}

export type Row = { key: string; value: string };

// Policy: A text that would read as JSON is quoted, so that "5" stays a text and 5 a number.
export function shown(value: unknown): string {
  if (typeof value === "string") {
    try {
      JSON.parse(value);
      return JSON.stringify(value);
    } catch {
      return value;
    }
  }
  return JSON.stringify(value);
}

export function valueOf(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export function rowsOf(settings: unknown): Row[] {
  if (typeof settings !== "object" || settings === null) return [];
  return Object.entries(settings).map(([key, value]) => ({ key, value: shown(value) }));
}

export function settingsOf(rows: Row[]): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const { key, value } of rows) if (key.trim()) out[key.trim()] = valueOf(value);
  return out;
}

export type Parsed = { value: unknown } | { problem: string };

export function jsonOf(text: string, empty: unknown = null): Parsed {
  if (!text.trim()) return { value: empty };
  try {
    return { value: JSON.parse(text) };
  } catch (e) {
    return { problem: e instanceof Error ? e.message : String(e) };
  }
}

export function stopsOf(text: string): string[] {
  return text.split("\n").filter((line) => line !== "");
}

export function moved<T>(list: T[], at: number, by: -1 | 1): T[] {
  const to = at + by;
  if (to < 0 || to >= list.length) return list;
  return list.map((x, i) => (i === at ? list[to] : i === to ? list[at] : x)) as T[];
}
