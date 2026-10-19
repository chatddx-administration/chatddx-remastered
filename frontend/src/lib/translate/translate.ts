import { diffWords } from "diff";
import type { Words } from "$lib/thread/diff";

export type Entries = Record<string, string>;
export type Body = { part: string; body: Record<string, unknown> };
export type Part = { title: string; thread: number | null; head: number | null; mine: boolean; owner: string | null };
export type Request = Record<string, unknown> & { messages?: { role: string; content: string }[] };
export type Held = Part & { digest: string; body: { kind: "chunk.translations"; into: Record<string, Entries> } };
export type Configuration = {
  thread: number;
  head: number;
  latest: boolean;
  mine: boolean;
  owner: string | null;
  name: string;
  translations: string | null;
};
export type Translating = {
  into: string;
  language: string | null;
  texts: [string, string[]][];
  written: Request;
  request: Request;
  bodies: Body[];
  parts: Record<string, Part>;
  head: number | null;
  configuration: Configuration;
  translations: Held | null;
};

type Step = string | number;

// Mirroring src/chatddx/factors/request.py:_DATA and _NAMED: a schema's data, which compiling leaves
// untranslated, and the keys whose members are named.
const DATA = new Set(["enum", "const", "default", "examples"]);
const NAMED = new Set(["properties", "patternProperties", "$defs", "definitions", "dependentSchemas"]);

function found(node: unknown, text: string, at: Step[], into: Step[][]): void {
  if (node === text) {
    into.push(at);
  } else if (Array.isArray(node)) {
    node.forEach((v, i) => found(v, text, [...at, i], into));
  } else if (node !== null && typeof node === "object") {
    for (const [k, v] of Object.entries(node)) if (!DATA.has(k)) found(v, text, [...at, k], into);
  }
}

function schemaPlace(path: Step[]): string {
  const names: string[] = [];
  for (let i = 0; i < path.length - 1; i++) {
    const step = path[i];
    if (typeof step === "string" && NAMED.has(step)) names.push(String(path[++i]));
  }
  const last = String(path.at(-1));
  return ["schema", ...names].join(" › ") + ` · ${last}`;
}

function at(node: unknown, path: Step[]): unknown {
  let held = node;
  for (const step of path) held = (held as Record<Step, unknown> | undefined)?.[step];
  return held;
}

function around(path: Step[], body: Record<string, unknown>): string {
  const last = path.at(-1);
  if (last !== "before" && last !== "after") return "";
  const insert = at(body, [...path.slice(0, -1), "insert"]);
  return `${last} ‹${String(insert).replaceAll("_", " ")}›`;
}

export function place(path: Step[], body: Record<string, unknown>): string {
  const [first, second] = path;
  switch (body.kind) {
    case "chunk.few_shot": {
      const messages = (body.messages ?? []) as { role: string }[];
      const role = messages[Number(second)]?.role ?? "message";
      const nth = messages.slice(0, Number(second) + 1).filter((m) => m.role === role).length;
      return `${role} ${nth}`;
    }
    case "chunk.output":
      if (first === "json_schema") return schemaPlace(path.slice(1));
      if (first === "contract") return "the answer tool's description";
      return ["guidance", around(path, body)].filter(Boolean).join(", ");
    case "tool":
      if (first === "parameters") return `${String(body.name)}'s parameters, ${schemaPlace(path.slice(1))}`;
      return `${String(body.name)}'s description`;
    case "chunk.toolset":
      return "guidance";
    case undefined:
      return first === "between" ? "between appendices" : `${String(first)} the appendices`;
    default:
      return around(path, body);
  }
}

export function places(text: string, part: string, bodies: Body[]): string[] {
  const said: string[] = [];
  for (const b of bodies) {
    if (b.part !== part) continue;
    const paths: Step[][] = [];
    found(b.body, text, [], paths);
    for (const path of paths) {
      const label = place(path, b.body);
      if (!said.includes(label)) said.push(label);
    }
  }
  return said;
}

export function edges(text: string): [string, string] {
  const lead = /^\s*/.exec(text)?.[0] ?? "";
  if (lead === text) return [lead, ""];
  return [lead, /\s*$/.exec(text)?.[0] ?? ""];
}

export function unlike(source: string, translation: string): boolean {
  const [a, b] = edges(source);
  const [c, d] = edges(translation);
  return a !== c || b !== d;
}

function shownEdge(edge: string): string {
  return edge.replaceAll(" ", "·").replaceAll("\t", "⇥");
}

export function visible(text: string): string {
  const [lead, trail] = edges(text);
  const core = text.slice(lead.length, text.length - trail.length);
  return (shownEdge(lead) + core + shownEdge(trail)).replaceAll("\n", "⏎\n");
}

export type Run = { text: string; missing: boolean };

export function marked(content: string, missing: string[]): Run[] {
  const sought = [...new Set(missing.filter((m) => m.trim()))].sort((a, b) => b.length - a.length);
  const runs: Run[] = [];
  const push = (text: string, isMissing: boolean) => {
    const last = runs.at(-1);
    if (last && last.missing === isMissing && !isMissing) last.text += text;
    else runs.push({ text, missing: isMissing });
  };
  let i = 0;
  while (i < content.length) {
    const hit = sought.find((m) => content.startsWith(m, i));
    if (hit) {
      push(hit, true);
      i += hit.length;
    } else {
      push(content[i] ?? "", false);
      i += 1;
    }
  }
  return runs;
}


export function entriesInto(held: Held | null, into: string): Entries {
  return { ...(held?.body.into[into] ?? {}) };
}

export function textsOf(texts: Translating["texts"]): string[] {
  return [...new Set(texts.flatMap(([, found]) => found))];
}

export function unusedOf(entries: Entries, texts: Translating["texts"]): Entries {
  const held = new Set(textsOf(texts));
  return Object.fromEntries(Object.entries(entries).filter(([text]) => !held.has(text)));
}

export type Offer = { text: string; translation: string; words: Words };

// Policy: an entry under half of whose words are the text's is too far off to start from.
const NEAR = 0.5;

export function closest(text: string, unused: Entries): Offer | null {
  let best: (Offer & { score: number }) | null = null;
  for (const [was, translation] of Object.entries(unused)) {
    const parts = diffWords(was, text);
    const kept = parts.filter((p) => !p.added && !p.removed).reduce((n, p) => n + p.value.length, 0);
    const score = kept / Math.max(was.length, text.length, 1);
    if (score >= NEAR && (best === null || score > best.score)) {
      const words = parts.map((p) => ({ value: p.value, added: !!p.added, removed: !!p.removed }));
      best = { text: was, translation, words, score };
    }
  }
  return best && { text: best.text, translation: best.translation, words: best.words };
}

export function entriesOf(typed: Entries, kept: Entries): Entries {
  const found: Entries = { ...kept };
  for (const [text, translation] of Object.entries(typed)) {
    if (translation) found[text] = translation;
    else delete found[text];
  }
  return found;
}

export function translationsOf(held: Held | null, into: string, entries: Entries): Held["body"] | null {
  const languages = { ...(held?.body.into ?? {}) };
  if (Object.keys(entries).length) languages[into] = entries;
  else delete languages[into];
  return Object.keys(languages).length ? { kind: "chunk.translations", into: languages } : null;
}

function writes(at: { mine: boolean; owner: string | null }, name: string, latest = true): string {
  if (at.mine && latest) return `a new version of your ${name}`;
  return `a fork of ${at.owner ? `${at.owner}'s ` : ""}${name} as your own`;
}

export type Unchanged = { translations: boolean; configuration: boolean };

export function savedTo(held: Held | null, configuration: Configuration, unchanged: Unchanged): string {
  const said: string[] = [];
  if (!unchanged.translations) {
    said.push(held?.thread != null ? writes(held, held.title) : `new translations of your own, ${configuration.name}`);
  }
  if (!unchanged.configuration) {
    const what = writes(configuration, configuration.name, configuration.latest);
    said.push(unchanged.translations ? what : `${what}, holding them`);
  }
  return said.length ? `Saves ${said.join(", and ")}.` : "Nothing to save: it holds these already.";
}

export type Left = Record<string, string[]>;

export function leftOut(into: Record<string, Entries>, left: Left): Record<string, Entries> {
  const found: Record<string, Entries> = {};
  for (const [language, entries] of Object.entries(into)) {
    const kept = Object.entries(entries).filter(([text, t]) => t && !(left[language] ?? []).includes(text));
    if (kept.length) found[language] = Object.fromEntries(kept);
  }
  return found;
}
