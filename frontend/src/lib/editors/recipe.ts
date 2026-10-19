import { type Part, PARTS } from "$lib/variation/logic";

export type Layout = { before: string; between: string; after: string };
export const LAYOUT: Layout = { before: "\n\n", between: "\n\n", after: "" };

export function missing(picks: Partial<Record<Part, string>>, optional: string[]): Part[] {
  return PARTS.filter((p) => !optional.includes(p) && !picks[p]);
}

export function recipeOf(purpose: string, picks: Partial<Record<Part, string>>, layout: Layout): Record<string, unknown> {
  const parts = Object.fromEntries(PARTS.filter((p) => picks[p]).map((p) => [p, picks[p]]));
  return { purpose, ...parts, appendix_layout: layout };
}
