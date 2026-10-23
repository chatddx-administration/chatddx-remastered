import type { Schemas } from "$lib/api/client";
import { t, tp } from "$lib/locale";
import type { Schema } from "$lib/schema/form";
import type { JudgeChoice, Judging, Serving } from "./judging";
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
type Output = { title: string | null; json_schema: Schema | null; by: string[] };
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
    for (const c of choices(output.json_schema, null, t("the whole answer"))) {
      const label =
        c.selector === ""
          ? c.label
          : t("%(output)s: %(selected)s", { output: output.title ?? tp("an output", "text"), selected: c.label });
      if (!seen.has(c.selector)) seen.set(c.selector, { ...c, label });
    }
  }
  return [...seen.values()];
}
