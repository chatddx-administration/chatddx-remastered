import type { Schemas } from "$lib/api/client";
import { displayLanguage } from "$lib/locale";

type Broken = Schemas["Broken"];
type Version = Schemas["BrokenVersion"];
type Point = Schemas["BrokenPoint"];

export type Group = { field: string | null; views: number[] };

export function grouped(broken: Broken): Group[] {
  const found: Group[] = [];
  broken.views.forEach((view, at) => {
    let group = found.find((g) => g.field === view.field);
    if (!group) found.push((group = { field: view.field, views: [] }));
    group.views.push(at);
  });
  return found;
}

export function named(version: Version): string {
  return version.versions.map((v) => `v${v}`).join(", ");
}

// Policy: a version's gatherings spread across its column by when they ran, so that a version run again
// later sits to the right of its first.
export function spread(points: Point[]): number[] {
  if (points.length < 2) return points.map(() => 0);
  const order = points.map((p, i) => [Date.parse(p.at), i] as const).sort((a, b) => a[0] - b[0]);
  const found = points.map(() => 0);
  order.forEach(([, i], k) => (found[i] = k / (points.length - 1) - 0.5));
  return found;
}

export function estimated(version: Version, view: number): string {
  const e = version.estimates[view];
  const said = e
    ? `${named(version)}: ${e.mean.toFixed(2)}${e.half === null ? "" : ` ±${e.half.toFixed(2)}`} (n=${e.n})`
    : `${named(version)}: —`;
  const d = version.paired[view];
  return d ? `${said}, Δ ${differs(d)}` : said;
}

export function differs(d: Schemas["Estimated"]): string {
  return `${d.mean >= 0 ? "+" : "−"}${Math.abs(d.mean).toFixed(2)} (n=${d.n})`;
}

export function languages(point: Point): string {
  return point.languages.map((l) => `${l.language === null ? "—" : displayLanguage(l.language)} ${l.cases}`).join(", ");
}

export function mean(values: (number | null)[]): number | null {
  const held = values.filter((v): v is number => v !== null);
  return held.length ? held.reduce((a, b) => a + b, 0) / held.length : null;
}
