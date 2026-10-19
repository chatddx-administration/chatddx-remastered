import type { Schemas } from "$lib/api/client";
import type { Schema } from "$lib/schema/form";
import type { JudgeChoice } from "./JudgeForm.svelte";
import type { Judging, Serving } from "./judging";
import { type Choice, choices } from "./selectors";

export type ScorerView = {
  output?: string;
  expectation?: string;
  split?: string | null;
  metric: string;
  judge?: string | null;
  params?: Record<string, unknown>;
};
export type ScorerBody = {
  kind: "scorer";
  entry_point: string;
  version: number;
  expectation_schema: string;
  views: ScorerView[];
  resources?: string[];
  params?: Record<string, unknown>;
};
export type Output = { title: string | null; json_schema: Schema | null; by: string[] };
export type Scoring = {
  metrics: Schemas["Metric"][];
  outputs: Output[];
  judges: JudgeChoice[];
  titles: Record<string, string>;
  judging: Judging[];
  models: Serving[];
  me: string;
};

export function answeredChoices(outputs: Output[]): Choice[] {
  const seen = new Map<string, Choice>();
  for (const output of outputs) {
    for (const c of choices(output.json_schema, null, "the whole answer")) {
      const label = c.selector === "" ? c.label : `${output.title ?? "text"}: ${c.label}`;
      if (!seen.has(c.selector)) seen.set(c.selector, { ...c, label });
    }
  }
  return [...seen.values()];
}
