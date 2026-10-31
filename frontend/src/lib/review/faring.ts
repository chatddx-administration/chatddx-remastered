import type { Schemas } from "$lib/api/client";

type Fared = Schemas["Fared"];
type Row = Schemas["FaredRow"];

export type Group = { field: string | null; metrics: { at: number; rows: Row[] }[] };
export type Bin = { at: number; run: number; drawn: number; cases: number[] };

// Policy: so many bins between 0 and 1, so that a mean of four replicates falls on one of its own.
export const BINS = 20;

export function grouped(fared: Fared): Group[] {
  const found: Group[] = [];
  fared.metrics.forEach((metric, at) => {
    const rows = fared.rows.filter((r) => r.metric === at);
    if (!rows.length) return;
    let group = found.find((g) => g.field === metric.field);
    if (!group) found.push((group = { field: metric.field, metrics: [] }));
    group.metrics.push({ at, rows });
  });
  return found;
}

export function binned(row: Row): Bin[] {
  const bins = new Map<number, Bin>();
  row.values.forEach((value, i) => {
    const at = Math.round(Math.min(1, Math.max(0, value)) * BINS);
    const bin = bins.get(at) ?? { at, run: 0, drawn: 0, cases: [] };
    if (row.synthetic[i]) bin.drawn++;
    else bin.run++;
    bin.cases.push(row.cases[i] ?? i);
    bins.set(at, bin);
  });
  return [...bins.values()].sort((a, b) => a.at - b.at);
}

// Policy: the share of the other cases below this one, a tie counting as half, so that a case among equals sits mid-way.
export function below(row: Row): number {
  if (!row.shown || !row.values.length) return 0;
  const value = row.shown.value;
  const under = row.values.reduce((n, v) => n + (v < value ? 1 : v === value ? 0.5 : 0), 0);
  return under / row.values.length;
}
