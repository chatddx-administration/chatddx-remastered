import { describe, expect, it } from "vitest";
import { lines, overlaid, pretty, rows } from "./diffing";

const m = (role: string, text: string) => ({ role, runs: [{ text, untranslated: false }] });
const said = (x: { runs: { text?: string | null }[] }) => x.runs.map((r) => r.text ?? "").join("");

describe("the messages against those saved", () => {
  it("stand as they are where unchanged, and are changed word by word in their place", () => {
    const found = rows([m("system", "Be terse."), m("user", "Hi")], [m("system", "Be brief."), m("user", "Hi")], said);
    expect(found.map((r) => r.was)).toEqual(["changed", "same"]);
    const changed = found.at(0);
    const words = changed?.was === "changed" ? changed.words : [];
    expect(words.filter((w) => w.added).map((w) => w.value)).toEqual(["brief"]);
  });

  it("mark one added or taken out alone", () => {
    const found = rows([m("system", "S"), m("user", "U")], [m("system", "S"), m("user", "E"), m("user", "U")], said);
    expect(found.map((r) => r.was)).toEqual(["same", "added", "same"]);
    expect(rows([m("user", "E"), m("user", "U")], [m("user", "U")], said).map((r) => r.was)).toEqual([
      "removed",
      "same",
    ]);
  });
});

describe("the body against the one saved", () => {
  it("is marked by line", () => {
    const found = lines({ temperature: 0.7, top_p: 1 }, { temperature: 0.5, top_p: 1 });
    expect(found.filter((p) => p.removed).map((p) => p.value.trim())).toEqual(['"temperature": 0.7,']);
    expect(found.filter((p) => p.added).map((p) => p.value.trim())).toEqual(['"temperature": 0.5,']);
  });
});

describe("a message changed word by word", () => {
  it("keeps its runs, cut where the words added start and end", () => {
    const runs = [
      { text: "Be brief. ", origin: "instructions" },
      { slot: "vignette" },
      { text: "Answer.", origin: "output_guidance" },
    ];
    const read = (r: { text?: string | null; slot?: string | null }) => (r.slot ? "‹v›" : (r.text ?? ""));
    const words = [
      { value: "Be ", added: false, removed: false },
      { value: "terse.", added: false, removed: true },
      { value: "brief.", added: true, removed: false },
      { value: " ‹v›Answer.", added: false, removed: false },
    ];
    expect(overlaid(runs, words, read)).toEqual([
      { run: runs[0], text: "Be ", added: false },
      { removed: "terse." },
      { run: runs[0], text: "brief.", added: true },
      { run: runs[0], text: " ", added: false },
      { run: runs[1], text: "‹v›", added: false },
      { run: runs[2], text: "Answer.", added: false },
    ]);
  });
});

describe("the body as sent", () => {
  it("breaks its lines where its texts do, and keeps a backslash written", () => {
    expect(pretty({ content: "a\nb\\n" })).toBe('{\n  "content": "a\nb\\\\n"\n}');
  });
});
