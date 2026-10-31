import type { Schemas } from "$lib/api/client";

export type Measuring = { fields: string[]; field: string | null };
export type Measured = Schemas["Measured"];
export type Text = Schemas["MeasuredText"];
export type Segment = { text: string; marked: boolean };

export class Measure {
  field = $state<string | null>(null);
  readonly fields: string[];
  private readonly moved: (field: string | null) => void;

  constructor(given: Measuring, moved: (field: string | null) => void) {
    this.fields = given.fields;
    this.field = given.field;
    this.moved = moved;
  }

  open(field: string): void {
    if (field !== this.field) this.moved(field);
  }

  close(): void {
    if (this.field !== null) this.moved(null);
  }
}

export type Shown = "missed" | "unscored" | "found";

export function shownAs(text: Text): Shown {
  return text.found === null ? "unscored" : text.found ? "found" : "missed";
}

export function kept(text: Text, shown: Set<Shown>, alternative: number | null): boolean {
  return shown.has(shownAs(text)) && (alternative === null || text.alternatives.includes(alternative));
}

// Duplication: src/chatddx/portal/scores.py:_segments marks a text alike.
export function segments(text: string, marks: { start: number; end: number }[]): Segment[] {
  const found: Segment[] = [];
  let at = 0;
  for (const mark of [...marks].sort((a, b) => a.start - b.start)) {
    const start = Math.max(mark.start, at);
    if (start > at) found.push({ text: text.slice(at, start), marked: false });
    if (mark.end > start) found.push({ text: text.slice(start, mark.end), marked: true });
    at = Math.max(at, mark.end);
  }
  if (at < text.length) found.push({ text: text.slice(at), marked: false });
  return found;
}

export function measuredAt(href: string, field: string | null): string {
  const url = new URL(href, "https://review.invalid");
  if (field === null) url.searchParams.delete("measure");
  else url.searchParams.set("measure", field);
  return url.pathname + url.search + url.hash;
}
