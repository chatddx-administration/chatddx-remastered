import { diffArrays, diffLines, diffWords } from "diff";
import type { Schemas } from "$lib/api/client";

type Message = Schemas["PreviewMessage"];
type Stretch = Schemas["Stretch"];
export type Piece = { value: string; added: boolean; removed: boolean };
export type Row =
  | { was: "same"; message: Message }
  | { was: "changed"; message: Message; words: Piece[] }
  | { was: "added"; message: Message }
  | { was: "removed"; message: Message };

export function read(run: Stretch, slots: Record<string, string>, appendix: (n: number) => string): string {
  if (run.slot) return `‹${slots[run.slot] ?? run.slot}›`;
  if (run.appendix) return `‹${appendix(run.appendix)}›`;
  return run.text ?? "";
}

function pieces(changes: { value: string; added?: boolean; removed?: boolean }[]): Piece[] {
  return changes.map((c) => ({ value: c.value, added: !!c.added, removed: !!c.removed }));
}

// Policy: messages are matched whole, by role and text, so that a message added or taken out marks itself alone; a run
// of them taken out where as many are added is each changed in its place, word by word.
export function rows(before: Message[], after: Message[], said: (m: Message) => string): Row[] {
  const key = (m: Message) => `${m.role}\n${said(m)}`;
  const found: Row[] = [];
  let a = 0;
  let b = 0;
  let paired = false;
  const parts = diffArrays(before.map(key), after.map(key));
  for (const [i, part] of parts.entries()) {
    const n = part.value.length;
    if (paired) {
      paired = false;
      continue;
    }
    const next = parts.at(i + 1);
    if (part.removed && next?.added && next.value.length === n) {
      const now = after.slice(b, b + n);
      for (const [k, was] of before.slice(a, a + n).entries()) {
        const is = now.at(k) ?? was;
        if (was.role === is.role) {
          found.push({ was: "changed", message: is, words: pieces(diffWords(said(was), said(is))) });
        } else {
          found.push({ was: "removed", message: was }, { was: "added", message: is });
        }
      }
      a += n;
      b += n;
      paired = true;
    } else if (part.removed) {
      found.push(...before.slice(a, a + n).map((message) => ({ was: "removed" as const, message })));
      a += n;
    } else if (part.added) {
      found.push(...after.slice(b, b + n).map((message) => ({ was: "added" as const, message })));
      b += n;
    } else {
      found.push(...after.slice(b, b + n).map((message) => ({ was: "same" as const, message })));
      a += n;
      b += n;
    }
  }
  return found;
}

// Policy: the body as sent is JSON but for its texts' line breaks, which break its lines, so that a message reads as it
// is written.
export function pretty(value: unknown): string {
  return JSON.stringify(value, null, 2).replace(/\\\\|\\n/g, (m) => (m === "\\n" ? "\n" : m));
}

export function lines(before: unknown, after: unknown): Piece[] {
  return pieces(diffLines(pretty(before), pretty(after)));
}

export type Overlaid = { removed: string } | { run: Stretch; text: string; added: boolean };

// Policy: a message changed word by word keeps its runs, each cut where the words added start and end, and what was taken
// out stands where it was; a slot or an appendix is shown once, where it starts.
export function overlaid(runs: Stretch[], words: Piece[], said: (run: Stretch) => string): Overlaid[] {
  const queue = runs.map((run) => ({ run, left: said(run).length, whole: said(run).length })).filter((q) => q.left);
  const found: Overlaid[] = [];
  for (const w of words) {
    if (w.removed) {
      found.push({ removed: w.value });
      continue;
    }
    let taken = 0;
    while (taken < w.value.length) {
      const q = queue.at(0);
      if (!q) break;
      const n = Math.min(q.left, w.value.length - taken);
      const text = w.value.slice(taken, taken + n);
      if (!(q.run.slot || q.run.appendix) || q.left === q.whole) found.push({ run: q.run, text, added: w.added });
      q.left -= n;
      taken += n;
      if (q.left === 0) queue.shift();
    }
  }
  return found;
}
