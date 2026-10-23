import type { Schema } from "$lib/schema/form";
import type { Scoring } from "$lib/scorer/scorers";
import { merged, type Seg, segmentsOf, textOf } from "$lib/scorer/texts";

export type Editor =
  | { name: string; as: "texts"; inserts: string[]; slots: Record<string, string[]> }
  | { name: string; as: "schema"; of?: string; schema?: Schema }
  | { name: string; as: "views"; of: string }
  | { name: string; as: "json"; expects: "object" | "array" | null };

export type Editing = {
  fields: Editor[];
  held: Record<string, unknown>;
  schemas: Record<string, Schema>;
  scoring: Scoring | null;
};

export type Read = { ok: true; value: unknown } | { ok: false };

export function read(text: string): Read {
  try {
    return { ok: true, value: JSON.parse(text) as unknown };
  } catch {
    return { ok: false };
  }
}

export function written(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

// Dependency: an either-field's text box and its "as." select, as src/chatddx/portal/templates/fields.html draws them.
export function segsOf(text: string, asText: boolean | null): Seg[] | null {
  if (asText) return [text];
  const found = read(text);
  return found.ok ? segmentsOf(found.value) : null;
}

export function textOfSegs(segs: Seg[], either: boolean): { asText: boolean; text: string } {
  if (!either) return { asText: false, text: written(merged(segs)) };
  const text = textOf(segs);
  return typeof text === "string" ? { asText: true, text } : { asText: false, text: written(text) };
}

export function labelled(held: unknown, views: number): { views: string[]; rest: Record<string, unknown> } {
  const given =
    typeof held === "object" && held !== null && !Array.isArray(held) ? (held as Record<string, unknown>) : {};
  const named = Array.isArray(given.views) ? given.views.map((v) => (typeof v === "string" ? v : "")) : [];
  return {
    views: Array.from({ length: views }, (_, i) => named[i] || `view ${i}`),
    rest: Object.fromEntries(Object.entries(given).filter(([k]) => k !== "views")),
  };
}

export function misread(text: string, expects: "object" | "array" | null): string | null {
  if (!text.trim()) return null;
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch (e) {
    return `It isn't JSON yet: ${e instanceof Error ? e.message : String(e)}`;
  }
  if (expects === "object" && (typeof value !== "object" || value === null || Array.isArray(value))) {
    return "It is to be an object, between { and }.";
  }
  if (expects === "array" && !Array.isArray(value)) return "It is to be a list, between [ and ].";
  return null;
}
