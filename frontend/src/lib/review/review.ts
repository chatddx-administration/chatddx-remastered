import type { Schemas } from "$lib/api/client";
import type { AppendixEditing } from "$lib/editors/AppendixEditor.svelte";
import type { ExpectationEditing } from "$lib/editors/ExpectationEditor.svelte";
import type { Telling } from "$lib/review/About.svelte";
import { t, tn, tp } from "$lib/locale";
import type { Progress } from "$lib/runs/progress";

export type Shown = { run: string; score: string | null; replicate: number; plan: boolean; anchor: number };

export type Review = {
  family: number;
  case: string;
  labels: string[];
  units: string[];
  answers: Shown[];
  expected: Expecting;
  appendices: ({ editor: AppendixEditing; digest: string } | null)[];
  back: string;
  pending: { run: string; titled: Schemas["Titled"] }[];
  about: Telling;
};

export type Version = { at: string; by: string; digest: string; data: unknown };
export type Expecting = {
  editor: ExpectationEditing | null;
  digest: string | null;
  history: Version[];
};

export function added(tags: string[], typed: string): string[] {
  const fresh = typed
    .split(",")
    .map((tag) => tag.trim())
    .filter((tag, at, all) => tag && !tags.includes(tag) && all.indexOf(tag) === at);
  return fresh.length ? [...tags, ...fresh].sort() : tags;
}

export type Viewed = { label: string; value: string; said: [string, string][]; calls: number };

export function viewed(
  items: Schemas["ScoreItemDetail"][],
  replicate: number,
  labels: string[],
  units: string[],
): Viewed[] {
  const mine = new Map(items.filter((i) => i.replicate === replicate).map((i) => [i.view, i]));
  return labels.map((label, view) => {
    const held = mine.get(view);
    const calls = Array.isArray(held?.judge_calls) ? held.judge_calls.length : 0;
    return { label, value: valued(held?.value ?? null, units[view] ?? ""), said: said(held?.detail), calls };
  });
}

export function valued(value: number | null, unit: string): string {
  if (value === null) return "—";
  return unit === "@" ? `@${Math.trunc(value)}` : value.toFixed(2);
}

export function said(detail: unknown): [string, string][] {
  if (detail === null || detail === undefined) return [];
  if (typeof detail !== "object" || Array.isArray(detail)) return [["", text(detail)]];
  return Object.entries(detail).map(([key, value]) => [key, text(value)]);
}

function text(value: unknown): string {
  return typeof value === "string" ? value : JSON.stringify(value);
}

export function replaced(back: string, current: string, cases: Record<string, string>): string {
  const now = cases[current];
  if (!now) return back;
  const url = new URL(back, "https://review.invalid");
  url.searchParams.set("case", now);
  return url.pathname + url.search;
}

export function doing(progress: Progress): string {
  if (progress.done) return progress.done.halted ? tp("a run under way", "halted") : tp("a run under way", "done");
  const scoring = progress.scorings.filter((s) => s.score !== null);
  if (scoring.length) {
    const n = scoring.reduce((sum, s) => sum + s.scored, 0);
    const asked = scoring.reduce((sum, s) => sum + s.asked, 0);
    const answered = scoring.reduce((sum, s) => sum + s.answered, 0);
    const scored = tn("%(n)s scored", "%(n)s scored", n, { n });
    if (!asked) return t("scoring: %(scored)s", { scored });
    const judges = tn("judges answered %(answered)s of %(asked)s", "judges answered %(answered)s of %(asked)s", asked, {
      answered,
      asked,
    });
    return t("scoring: %(scored)s, %(judges)s", { scored, judges });
  }
  if (!progress.items.length) return tp("a run under way", "queued");
  const of = progress.items.length;
  const ended = tn("%(ended)s of %(of)s ended", "%(ended)s of %(of)s ended", of, {
    ended: progress.items.filter((i) => i.phase === "ended").length,
    of,
  });
  const now = progress.items.find((i) => i.phase === "sending");
  if (!now?.kind) return ended;
  const n = now.tokens;
  const sending =
    now.kind === "reasoning"
      ? tn("thinking: %(n)s token", "thinking: %(n)s tokens", n, { n })
      : tn("writing: %(n)s token", "writing: %(n)s tokens", n, { n });
  return t("%(ended)s, %(sending)s", { ended, sending });
}
