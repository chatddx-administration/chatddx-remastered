import type { ExpectationEditing } from "$lib/editors/ExpectationEditor.svelte";
import type { Telling } from "$lib/review/About.svelte";
import type { Appended } from "$lib/review/Appendices.svelte";
import type { Measuring } from "$lib/review/measure.svelte";

export type Review = {
  family: number;
  case: string;
  expected: Expecting;
  appendices: Appended[];
  back: string;
  schema: string | null;
  measure: Measuring;
  about: Telling;
};

export type Version = { at: string; by: string; digest: string; data: unknown };
export type Expecting = {
  editor: ExpectationEditing | null;
  history: Version[];
};

export function added(tags: string[], typed: string): string[] {
  const fresh = typed
    .split(",")
    .map((tag) => tag.trim())
    .filter((tag, at, all) => tag && !tags.includes(tag) && all.indexOf(tag) === at);
  return fresh.length ? [...tags, ...fresh].sort() : tags;
}

export function replaced(back: string, current: string, cases: Record<string, string>): string {
  const now = cases[current];
  if (!now) return back;
  const url = new URL(back, "https://review.invalid");
  url.searchParams.set("case", now);
  return url.pathname + url.search;
}
