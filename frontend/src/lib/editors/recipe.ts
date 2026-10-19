// Duplication: src/chatddx/factors/request.py:RECIPE_PARTS, and the parts Recipe requires.
export const PARTS = [
  "instructions",
  "few_shot",
  "prompt",
  "output",
  "sampling",
  "reasoning",
  "passthrough",
  "translations",
  "toolset",
  "model",
] as const;
export type Part = (typeof PARTS)[number];
export const REQUIRED: Part[] = ["prompt", "output", "sampling", "model"];

export type Layout = { before: string; between: string; after: string };
export const LAYOUT: Layout = { before: "\n\n", between: "\n\n", after: "" };

export function missing(picks: Partial<Record<Part, string>>): Part[] {
  return REQUIRED.filter((p) => !picks[p]);
}

export function recipeOf(purpose: string, picks: Partial<Record<Part, string>>, layout: Layout): Record<string, unknown> {
  const parts = Object.fromEntries(PARTS.filter((p) => picks[p]).map((p) => [p, picks[p]]));
  return { purpose, ...parts, appendix_layout: layout };
}
