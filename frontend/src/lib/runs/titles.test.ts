import { describe, expect, it } from "vitest";
import { speaking } from "$lib/locale";
import { runTitle } from "./titles";

const varied = {
  name: "plan",
  replaced: [
    { part: "prompt", title: "terse" },
    { part: "few_shot", title: null },
  ],
  at: "qwen3-8b-awq",
  case: null,
  cases: 4,
  translated: "sv",
  greedy: false,
  seeds: [7, 8],
};

describe("a run's title", () => {
  it("is what it ran and what its variation replaced, then its model, cases, language and seeds", () => {
    speaking({ tag: "en", messages: {} });
    expect(runTitle(varied)).toBe(
      "plan, prompt: terse, no few shot · qwen3-8b-awq · 4 cases · translated into Swedish · seeds 7, 8",
    );
    const one = { ...varied, replaced: [], case: "dutch-10", cases: 1, translated: null, greedy: true, seeds: [0] };
    expect(runTitle(one)).toBe("plan · qwen3-8b-awq · dutch-10 · greedy");
    expect(runTitle({ ...one, seeds: [0, 1, 2] })).toBe("plan · qwen3-8b-awq · dutch-10 · greedy, 3 replicates");
  });

  it("is said in the page's locale", () => {
    speaking({
      tag: "sv",
      messages: {
        "kind\u0004prompt": "prompt",
        "kind\u0004few shot": "exempel",
        "a part replaced\u0004%(part)s: %(title)s": "%(part)s: %(title)s",
        "a part replaced\u0004no %(part)s": "utan %(part)s",
        "%(num)s case": ["%(num)s fall", "%(num)s fall"],
        "translated into %(language)s": "översatt till %(language)s",
        "seed %(seeds)s": ["frö %(seeds)s", "frön %(seeds)s"],
      },
    });
    expect(runTitle(varied)).toBe(
      "plan, prompt: terse, utan exempel · qwen3-8b-awq · 4 fall · översatt till svenska · frön 7, 8",
    );
  });
});
