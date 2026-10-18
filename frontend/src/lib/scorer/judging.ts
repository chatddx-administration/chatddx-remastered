import type { Schema } from "$lib/schema/form";
import { choices } from "./selectors";

export function seedsOf(text: string): number[] | string {
  const given = text.split(/[\s,]+/).filter(Boolean);
  if (!given.length) return "a judge has a seed or more";
  const seeds = given.map(Number);
  if (seeds.some((s) => !Number.isInteger(s) || s < 0)) return "seeds are whole numbers, 0 or more";
  if (new Set(seeds).size !== seeds.length) return "each seed once";
  return seeds;
}

export function verdictAt(schema: Schema | null): string[] {
  return choices(schema, null, "").filter((c) => c.selector.startsWith("/")).map((c) => c.selector);
}

function field(schema: Schema | null, at: string): Schema | null {
  const name = at.slice(1).split("/")[0] ?? "";
  const properties = schema?.properties;
  if (typeof properties !== "object" || properties === null) return null;
  const found = (properties as Record<string, unknown>)[name];
  return typeof found === "object" && found !== null ? (found as Schema) : null;
}

// Starting params for a judged view: its verdict at the judge's first field that isn't text, and, when the metric
// takes a most, that field's maximum.
export function startingParams(params: Schema, schema: Schema | null): Record<string, unknown> {
  const wanted = typeof params.properties === "object" && params.properties !== null ? params.properties : {};
  const found: Record<string, unknown> = {};
  const at = verdictAt(schema).find((a) => field(schema, a)?.type !== "string" && !a.slice(1).includes("/"));
  if ("at" in wanted && at) found.at = at;
  if ("max" in wanted) {
    const most = at ? field(schema, at)?.maximum : undefined;
    found.max = typeof most === "number" && most > 0 ? most : 1;
  }
  return found;
}
