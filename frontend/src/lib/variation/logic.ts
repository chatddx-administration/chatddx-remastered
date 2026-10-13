import type { Schemas } from "$lib/api/client";

export const PARTS = [
  "instructions",
  "few_shot",
  "prompt",
  "output",
  "sampling",
  "reasoning",
  "passthrough",
  "translations",
  "toolset",
] as const;

export type Part = (typeof PARTS)[number];
export type Picked = Record<Part, string | null>;

export type State = {
  picked: Picked;
  head: number;
  endpoint: string | null;
  tags: string[];
};

export function replaced(picked: Picked, base: Picked): Partial<Picked> {
  return Object.fromEntries(PARTS.filter((p) => picked[p] !== base[p]).map((p) => [p, picked[p]]));
}

export function queryOf(state: State, base: Picked, latest: number): URLSearchParams {
  const query = new URLSearchParams();
  for (const [part, digest] of Object.entries(replaced(state.picked, base))) {
    query.append(part, digest ?? "");
  }
  if (state.head !== latest) query.append("head", String(state.head));
  if (state.endpoint !== null) query.append("endpoint", state.endpoint);
  for (const tag of state.tags) query.append("tag", tag);
  return query;
}

export function named(thread: Schemas["Thread"], me: string): string {
  const name = thread.name ?? thread.title;
  return thread.owner === me || thread.owner === null ? name : `${thread.owner}/${name}`;
}

export function madeFor(name: string): string {
  return /\s\(([^()]+)\)$/.exec(name)?.[1] ?? "";
}

export type Choice = { digest: string; text: string };
export type Group = { label: string; choices: Choice[] };

export function choicesOf(
  threads: Schemas["Thread"][],
  me: string,
  held: { digest: string; title: string | null }[],
): Group[] {
  const own = [...threads].sort((a, b) => Number(b.owner === me) - Number(a.owner === me));
  const found = new Map<string, { first: string; names: string[] }>();
  for (const thread of own) {
    const name = thread.name ?? thread.title;
    const seen = found.get(thread.head.digest);
    if (seen === undefined) found.set(thread.head.digest, { first: named(thread, me), names: [name] });
    else if (!seen.names.includes(name)) seen.names.push(name);
  }
  for (const { digest, title } of held) {
    if (!found.has(digest)) {
      const name = title ?? digest.slice(7, 19);
      found.set(digest, { first: name, names: [name] });
    }
  }
  const groups = new Map<string, Choice[]>();
  for (const [digest, { first, names }] of found) {
    const label = madeFor(first);
    const also = names.slice(1).map((n) => (label && madeFor(n) === label ? n.slice(0, -label.length - 3) : n));
    const text = also.length ? `${first} = ${also.join(", ")}` : first;
    groups.set(label, [...(groups.get(label) ?? []), { digest, text }]);
  }
  return [...groups]
    .sort(([a], [b]) => (a === "" ? -1 : b === "" ? 1 : a.localeCompare(b)))
    .map(([label, choices]) => ({
      label: label || "Made for any model",
      choices: choices.sort((a, b) => a.text.localeCompare(b.text)),
    }));
}

export type Saving =
  | { to: "nothing"; because: "nameless" | "unchanged" }
  | { to: "version"; version: number }
  | { to: "fork"; namesakes: number };

export function whereSaveGoes(given: {
  name: string;
  configuration: Schemas["ThreadDetail"];
  me: string;
  versions: number;
  latest: boolean;
  changed: boolean;
  configurations: Schemas["Thread"][];
}): Saving {
  const name = given.name.trim();
  if (!name) return { to: "nothing", because: "nameless" };
  const own = given.configuration.owner === given.me;
  const same = name === (given.configuration.name ?? given.configuration.title);
  if (own && given.latest && same) {
    return given.changed
      ? { to: "version", version: given.versions + 1 }
      : { to: "nothing", because: "unchanged" };
  }
  const namesakes = given.configurations.filter(
    (t) => t.owner === given.me && (t.name ?? t.title) === name,
  ).length;
  return { to: "fork", namesakes };
}
