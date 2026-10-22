import { diffWords } from "diff";

type Words = { value: string; added: boolean; removed: boolean }[];

export type Change =
  | { path: string; was: "added"; after: unknown }
  | { path: string; was: "removed"; before: unknown }
  | { path: string; was: "changed"; before: unknown; after: unknown; words: Words | null };

type Held = Record<string, unknown>;

function held(value: unknown): value is Held {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function same(a: unknown, b: unknown): boolean {
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((x, i) => same(x, b[i]));
  if (held(a) && held(b)) {
    const keys = Object.keys(a);
    return keys.length === Object.keys(b).length && keys.every((k) => k in b && same(a[k], b[k]));
  }
  return a === b;
}

export function changes(before: unknown, after: unknown, path = ""): Change[] {
  if (same(before, after)) return [];
  if (held(before) && held(after)) {
    const keys = [...Object.keys(after), ...Object.keys(before).filter((k) => !(k in after))];
    return keys.flatMap((k): Change[] => {
      const at = `${path}/${k}`;
      if (!(k in before)) return [{ path: at, was: "added", after: after[k] }];
      if (!(k in after)) return [{ path: at, was: "removed", before: before[k] }];
      return changes(before[k], after[k], at);
    });
  }
  if (Array.isArray(before) && Array.isArray(after) && before.length === after.length) {
    return before.flatMap((b, i) => changes(b, after[i], `${path}/${i}`));
  }
  const words =
    typeof before === "string" && typeof after === "string"
      ? diffWords(before, after).map((p) => ({ value: p.value, added: !!p.added, removed: !!p.removed }))
      : null;
  return [{ path: path || "/", was: "changed", before, after, words }];
}
