import type { Schemas } from "$lib/api/client";
import type { AppendixEditing } from "$lib/editors/AppendixEditor.svelte";
import type { ExpectationEditing } from "$lib/editors/ExpectationEditor.svelte";
import { t, tn, tp } from "$lib/locale";
import type { Progress } from "$lib/runs/progress";
import type { Composing } from "$lib/scorer/Composer.svelte";

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
  previous: string | null;
  next: string | null;
};

export type Read = { label: string; metric: string; measures: string | null; judge: string | null; expectation: string };
export type Version = { at: string; by: string; digest: string; data: unknown };
export type Expecting = {
  editor: ExpectationEditing | null;
  digest: string | null;
  history: Version[];
  views: Read[];
  composing: Composing | null;
};

type Key = Pick<KeyboardEvent, "key" | "altKey" | "ctrlKey" | "metaKey" | "target">;

const TYPED = new Set(["INPUT", "TEXTAREA", "SELECT"]);

export function stepped(pressed: Key, review: Pick<Review, "previous" | "next">): string | null {
  if (pressed.altKey || pressed.ctrlKey || pressed.metaKey) return null;
  const target = pressed.target as { tagName?: string; isContentEditable?: boolean } | null;
  if (target && (TYPED.has(target.tagName ?? "") || target.isContentEditable)) return null;
  if (pressed.key === "j") return review.next;
  if (pressed.key === "k") return review.previous;
  return null;
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

// Presentation only: it places a view beside the field it reads; what it picks is POST /api/picks's to say.
export function fieldOf(selector: string): string | null {
  if (selector.startsWith("/")) {
    const [first = ""] = selector.slice(1).split("/");
    return first.replaceAll("~1", "/").replaceAll("~0", "~");
  }
  const found = /^\$(?:\.([A-Za-z_][\w-]*)|\[\s*(['"])(.*?)\2\s*\])/.exec(selector);
  return found ? (found[1] ?? found[3] ?? null) : null;
}

export function shortly(items: unknown[], room = 90): string {
  return items.map((item) => clipped(texted(item), room)).join(" · ");
}

function texted(item: unknown): string {
  if (typeof item === "string") return item;
  if (Array.isArray(item)) return item.map(texted).join("; ");
  if (item !== null && typeof item === "object") {
    return Object.entries(item)
      .map(([key, value]) => `${key.replaceAll("_", " ")}: ${texted(value)}`)
      .join(", ");
  }
  return JSON.stringify(item);
}

function clipped(text: string, room: number): string {
  const flat = text.replace(/\s+/g, " ").trim();
  return flat.length > room ? `${flat.slice(0, room - 1).trimEnd()}…` : flat;
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

export function withScorer(back: string, thread: number): string {
  const url = new URL(back, "https://review.invalid");
  url.searchParams.set("scorer", String(thread));
  return url.pathname + url.search;
}
