import type { Schemas } from "$lib/api/client";
import { tp } from "$lib/locale";

export type Viewing = { label: string; field: string | null; unit: string };
export type Evaluated = { run: string; seeds: number[]; greedy: boolean };
export type Configured = { configuration: number; name: string; runs: Evaluated[] };
export type Evaluating = {
  key: string;
  first: string | null;
  case: string;
  configurations: Configured[];
  fields: string[];
  scorers: Record<string, Viewing[]>;
};

export type Ended = Pick<Schemas["ItemEndedData"], "outcome" | "prompt_tokens" | "completion_tokens" | "why">;
export type Scored = Record<string, Record<string, number | null>>;

export type Replicate = { key: string; run: string; replicate: number; n: number; seed: number | null };

export function keyed(run: string, replicate: number): string {
  return `${run}:${replicate}`;
}

export function replicates(configured: Configured): Replicate[] {
  let n = 0;
  return configured.runs.flatMap((r) =>
    r.seeds.map((seed, replicate) => ({
      key: keyed(r.run, replicate),
      run: r.run,
      replicate,
      n: ++n,
      seed: r.greedy ? null : seed,
    })),
  );
}

export type Cell = { scorer: string; view: number; label: string; mean: number | null; unit: string };

export function cells(
  configured: Configured,
  field: string,
  scored: Scored,
  scorers: Record<string, Viewing[]>,
): Cell[] {
  const keys = replicates(configured).map((r) => r.key);
  const found = new Map<string, Cell & { values: number[] }>();
  for (const key of keys) {
    for (const [at, value] of Object.entries(scored[key] ?? {})) {
      const [scorer = "", view] = at.split("#");
      const viewing = scorers[scorer]?.[Number(view)];
      if (viewing?.field !== field) continue;
      const cell = found.get(at) ?? {
        scorer,
        view: Number(view),
        label: viewing.label,
        mean: null,
        unit: viewing.unit,
        values: [],
      };
      if (value !== null) cell.values.push(value);
      found.set(at, cell);
    }
  }
  return [...found.values()].map(({ values, ...cell }) => ({
    ...cell,
    mean: values.length ? values.reduce((a, b) => a + b, 0) / values.length : null,
  }));
}

export function valued(value: number | null, unit: string): string {
  if (value === null) return "—";
  return unit === "@" ? `@${Math.trunc(value)}` : value.toFixed(2);
}

export type Worded = "valid" | "salvaged" | "broken" | "stopped";

export function worded(outcome: Schemas["Outcome"]): Worded {
  switch (outcome) {
    case "valid":
    case "completed":
      return "valid";
    case "salvaged":
      return "salvaged";
    case "stopped":
      return "stopped";
    default:
      return "broken";
  }
}

export function said(word: Worded): string {
  switch (word) {
    case "valid":
      return tp("outcome", "valid");
    case "salvaged":
      return tp("outcome", "salvaged");
    case "stopped":
      return tp("outcome", "stopped");
    case "broken":
      return tp("outcome", "broken");
  }
}

export function shown(value: unknown): { code: string } | { text: string } {
  return typeof value === "string" ? { text: value } : { code: JSON.stringify(value, null, 2) };
}
