// Dependency: a list as the pages rendered on the server find in and page it
// (src/chatddx/portal/templates/base.html): the rows that say every word typed, whatever
// its case, a page of them at a time.
export function found<T>(items: T[], said: (item: T) => string, query: string): T[] {
  const words = query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return items;
  return items.filter((item) => {
    const text = said(item).toLocaleLowerCase();
    return words.every((word) => text.includes(word));
  });
}

export function paged<T>(items: T[], at: number, rows: number): { shown: T[]; at: number; last: number } {
  const last = Math.max(0, Math.ceil(items.length / rows) - 1);
  const held = Math.min(Math.max(0, at), last);
  return { shown: items.slice(held * rows, (held + 1) * rows), at: held, last };
}
