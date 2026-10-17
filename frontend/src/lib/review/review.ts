import type { Schemas } from "$lib/api/client";

export type Shown = { run: string; score: string | null; replicate: number; plan: boolean; anchor: number };

export type Review = {
  family: number;
  case: string;
  labels: string[];
  units: string[];
  answers: Shown[];
  previous: string | null;
  next: string | null;
};

export type Key = Pick<KeyboardEvent, "key" | "altKey" | "ctrlKey" | "metaKey" | "target">;

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
