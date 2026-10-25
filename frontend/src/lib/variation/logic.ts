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
  "model",
] as const;

export type Part = (typeof PARTS)[number];
export type Picked = Record<Part, string | null>;

type State = {
  picked: Picked;
  head: number;
  under: string | null;
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
  if (state.under !== null) query.append("under", state.under);
  for (const tag of state.tags) query.append("tag", tag);
  return query;
}

// Duplication: src/chatddx/portal/lab.py:FARING names the Lab's own parameters too.
const FARING = ["handle", "family", "by"];

export function keptWith(query: URLSearchParams, search: string): URLSearchParams {
  const held = new URLSearchParams(search);
  const found = new URLSearchParams(query);
  for (const key of FARING) for (const value of held.getAll(key)) found.append(key, value);
  return found;
}

export function named(thread: Schemas["Thread"], me: string): string {
  const name = thread.name ?? thread.title;
  return thread.owner === me || thread.owner === null ? name : `${thread.owner}/${name}`;
}

export type Choice = { digest: string; text: string };

export function choicesOf(
  threads: Schemas["Thread"][],
  me: string,
  held: { digest: string; title: string | null }[],
): Choice[] {
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
  return [...found]
    .map(([digest, { first, names }]) => ({
      digest,
      text: names.length > 1 ? `${first} = ${names.slice(1).join(", ")}` : first,
    }))
    .sort((a, b) => a.text.localeCompare(b.text));
}

export function tagged(families: Schemas["Family"][], tags: string[]): Schemas["Family"][] {
  return tags.length ? families.filter((f) => f.tags.some((t) => tags.includes(t))) : families;
}

export type Carriage = {
  language: string | null;
  families: Schemas["Family"][];
  translated: boolean;
  refused: string | null;
  untranslated: boolean;
  known: boolean;
};

// Policy: the look's languages are of the families it was asked about, not of those picked beyond them.
export function carried(sent: Schemas["Family"][], languages: Schemas["Carried"][]): Carriage[] {
  const byFamily = new Map<number, Schemas["Carried"]>();
  languages.forEach((c) => c.families.forEach((f) => byFamily.set(f, c)));
  const byLanguage = new Map(languages.map((c) => [c.language, c]));
  const written = languages.find((c) => !c.translated && c.refused === null);
  const groups = new Map<string, Carriage>();
  for (const f of sent) {
    const c = byFamily.get(f.id) ?? byLanguage.get(f.language) ?? (f.language === null ? written : undefined);
    const language = c === undefined ? f.language : c.language;
    const key = `${c === undefined ? "?" : ""}${language}`;
    const group = groups.get(key) ?? {
      language,
      families: [],
      translated: c?.translated ?? false,
      refused: c?.refused ?? null,
      untranslated: c?.untranslated ?? false,
      known: c !== undefined,
    };
    group.families.push(f);
    groups.set(key, group);
  }
  const order = (g: Carriage) => {
    const at = languages.findIndex((c) => c.language === g.language);
    return g.known && at >= 0 ? at : languages.length;
  };
  return [...groups.values()].sort((a, b) => order(a) - order(b));
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
    return given.changed ? { to: "version", version: given.versions + 1 } : { to: "nothing", because: "unchanged" };
  }
  const namesakes = given.configurations.filter((t) => t.owner === given.me && (t.name ?? t.title) === name).length;
  return { to: "fork", namesakes };
}
