import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { Schemas } from "$lib/api/client";
import { carried, choicesOf, keptWith, PARTS, type Picked, queryOf, replaced, tagged, whereSaveGoes } from "./logic";

const DIGEST = (n: number) => `sha256:${String(n).padStart(64, "0")}`;

function thread(id: number, name: string | null, owner: string | null, digest: string): Schemas["Thread"] {
  return {
    id,
    kind: "chunk.reasoning",
    word: "reasoning",
    name,
    title: name ?? `untitled ${id}`,
    owner,
    tags: [],
    language: null,
    translated: [],
    head: {
      id: id * 10,
      digest,
      compilation: null,
      based_on: null,
      by: owner ?? "nobody",
      at: "2026-10-13T12:00:00Z",
      labels: null,
    },
    outdated: false,
  };
}

function picked(given: Partial<Picked>): Picked {
  return Object.fromEntries(PARTS.map((p) => [p, given[p] ?? null])) as Picked;
}

describe("the parts", () => {
  it("are the API's, in its order", () => {
    const document = JSON.parse(readFileSync(new URL("../../../openapi.json", import.meta.url), "utf8"));
    expect(Object.keys(document.components.schemas.Parts.properties)).toEqual([...PARTS]);
  });
});

describe("a variation's address", () => {
  const base = picked({ prompt: DIGEST(1), output: DIGEST(2), reasoning: DIGEST(3) });

  it("names only what is replaced, an optional part taken out as empty", () => {
    const tried = { ...base, output: DIGEST(4), reasoning: null };
    expect(replaced(tried, base)).toEqual({ output: DIGEST(4), reasoning: null });
    const query = queryOf({ picked: tried, head: 7, under: null, tags: [] }, base, 7);
    expect(query.toString()).toBe(new URLSearchParams({ output: DIGEST(4), reasoning: "" }).toString());
  });

  it("names the edit only when it isn't the latest, and the handle and each tag", () => {
    const query = queryOf({ picked: base, head: 5, under: "qwen3-8b", tags: ["a", "b"] }, base, 7);
    expect([...query]).toEqual([
      ["head", "5"],
      ["under", "qwen3-8b"],
      ["tag", "a"],
      ["tag", "b"],
    ]);
    expect(queryOf({ picked: base, head: 7, under: null, tags: [] }, base, 7).toString()).toBe("");
  });

  it("keeps the Lab's own parameters from the address, and none of the variation's", () => {
    const query = queryOf({ picked: base, head: 5, under: null, tags: ["a"] }, base, 7);
    const kept = keptWith(query, "?head=3&tag=b&handle=qwen3-8b&family=1&family=2&by=s%3A0");
    expect([...kept]).toEqual([
      ["head", "5"],
      ["tag", "a"],
      ["handle", "qwen3-8b"],
      ["family", "1"],
      ["family", "2"],
      ["by", "s:0"],
    ]);
  });
});

describe("a part's choices", () => {
  it("are one per digest, the person's own first, others' by owner, and the other names it goes by", () => {
    const choices = choicesOf(
      [
        thread(1, "high", "archive", DIGEST(1)),
        thread(2, "high", "alice", DIGEST(1)),
        thread(3, "thinking", "alice", DIGEST(1)),
        thread(4, "off", "bob", DIGEST(2)),
        thread(5, "medium", "alice", DIGEST(3)),
      ],
      "alice",
      [
        { digest: DIGEST(9), title: "older" },
        { digest: DIGEST(2), title: "ignored" },
      ],
    );
    expect(choices).toEqual([
      { digest: DIGEST(2), text: "bob/off" },
      { digest: DIGEST(1), text: "high = thinking" },
      { digest: DIGEST(3), text: "medium" },
      { digest: DIGEST(9), text: "older" },
    ]);
  });
});

describe("the cases a run is sent", () => {
  const family = (id: number, tags: string[]): Schemas["Family"] => ({
    id,
    name: `f${id}`,
    owner: "archive",
    tags,
    language: "en",
    case: DIGEST(id),
  });
  const families = [family(1, ["a"]), family(2, ["b"]), family(3, ["a", "b"]), family(4, [])];

  it("are those with any of the tags, or every one without a tag", () => {
    expect(tagged(families, ["a"]).map((f) => f.id)).toEqual([1, 3]);
    expect(tagged(families, ["a", "b"]).map((f) => f.id)).toEqual([1, 2, 3]);
    expect(tagged(families, []).map((f) => f.id)).toEqual([1, 2, 3, 4]);
  });
});

describe("the languages a run is sent in", () => {
  const family = (id: number, language: string | null): Schemas["Family"] => ({
    id,
    name: `f${id}`,
    owner: "archive",
    tags: [],
    language,
    case: DIGEST(id),
  });
  const look: Schemas["Carried"][] = [
    { language: "en", families: [1, 4], translated: false, skeleton: DIGEST(10), refused: null, untranslated: false },
    { language: "sv", families: [2], translated: true, skeleton: DIGEST(11), refused: null, untranslated: false },
    {
      language: "de",
      families: [3],
      translated: false,
      skeleton: null,
      refused: "no translations into de",
      untranslated: true,
    },
  ];

  it("are the look's, a family picked beyond it going as its language's, or unknown", () => {
    const sent = [family(3, "de"), family(2, "sv"), family(5, "sv"), family(6, null), family(7, "fi")];
    const said = carried(sent, look).map((c) => [c.language, c.families.map((f) => f.id), c.translated, c.known]);
    expect(said).toEqual([
      ["en", [6], false, true],
      ["sv", [2, 5], true, true],
      ["de", [3], false, true],
      ["fi", [7], false, false],
    ]);
    expect(carried(sent, look)[2]?.refused).toBe("no translations into de");
  });

  it("are each family's own, unknown, when the look has none", () => {
    expect(carried([family(1, "sv")], []).map((c) => [c.language, c.families.length, c.known])).toEqual([
      ["sv", 1, false],
    ]);
  });
});

describe("where a save goes", () => {
  const configuration = (owner: string, name: string | null): Schemas["ThreadDetail"] => ({
    ...thread(1, name, owner, DIGEST(1)),
    kind: "skeleton",
    word: "configuration",
    description: null,
    collaborators: [],
    forked_from: null,
    recipe: null,
    deleted: false,
  });
  const configurations = [thread(1, "plan", "alice", DIGEST(1)), thread(2, "terse", "alice", DIGEST(2))];
  const given = {
    name: "plan",
    configuration: configuration("alice", "plan"),
    me: "alice",
    versions: 2,
    latest: true,
    changed: true,
    configurations,
  };

  it("is a new version of the person's own, on its latest version and under its name", () => {
    expect(whereSaveGoes(given)).toEqual({ to: "version", version: 3 });
    expect(whereSaveGoes({ ...given, name: "  plan " })).toEqual({ to: "version", version: 3 });
    expect(whereSaveGoes({ ...given, changed: false })).toEqual({ to: "nothing", because: "unchanged" });
  });

  it("is a fork otherwise, counting the person's own of that name", () => {
    expect(whereSaveGoes({ ...given, latest: false })).toEqual({ to: "fork", namesakes: 1 });
    expect(whereSaveGoes({ ...given, name: "terse" })).toEqual({ to: "fork", namesakes: 1 });
    expect(whereSaveGoes({ ...given, name: "fresh" })).toEqual({ to: "fork", namesakes: 0 });
    const others = { ...given, configuration: configuration("archive", "plan"), changed: false };
    expect(whereSaveGoes(others)).toEqual({ to: "fork", namesakes: 1 });
  });

  it("is nowhere without a name", () => {
    expect(whereSaveGoes({ ...given, name: "  " })).toEqual({ to: "nothing", because: "nameless" });
  });
});
