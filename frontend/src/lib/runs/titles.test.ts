import { describe, expect, it } from "vitest";
import { speaking } from "$lib/locale";
import { caseTitle, runTitle } from "./titles";

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
  it("is its cases in their language, what it ran and what its variation replaced, its model and its seeds", () => {
    speaking({ tag: "en", messages: {} });
    expect(runTitle(varied)).toBe(
      "4 Swedish cases with `plan` (prompt: terse, no few shot) on qwen3-8b-awq (seeds 7, 8)",
    );
    const alone = { name: "dutch-10", appendices: [], earlier: false };
    const one = { ...varied, replaced: [], case: alone, cases: 1, translated: null, greedy: true, seeds: [0] };
    expect(runTitle(one)).toBe("dutch-10 with `plan` on qwen3-8b-awq (greedy)");
    expect(runTitle({ ...one, seeds: [0, 1, 2] })).toBe("dutch-10 with `plan` on qwen3-8b-awq (greedy, 3 replicates)");
    expect(runTitle({ ...one, translated: "sv" })).toBe("dutch-10 in Swedish with `plan` on qwen3-8b-awq (greedy)");
    const appended = { ...alone, appendices: ["labs", "ultrasound"], earlier: true };
    expect(runTitle({ ...one, case: appended })).toBe(
      "dutch-10 + 2 appendices (earlier) with `plan` on qwen3-8b-awq (greedy)",
    );
    expect(caseTitle(appended)).toBe("dutch-10 with labs and ultrasound (earlier)");
  });

  it("is said in the page's locale", () => {
    speaking({
      tag: "sv",
      messages: {
        "kind\u0004prompt": "prompt",
        "kind\u0004few shot": "exempel",
        "a part replaced\u0004%(part)s: %(title)s": "%(part)s: %(title)s",
        "a part replaced\u0004no %(part)s": "utan %(part)s",
        "%(num)s %(language)s case": ["%(num)s %(language)s fall", "%(num)s %(language)s fall"],
        "%(cases)s with %(configuration)s on %(model)s (%(seeds)s)":
          "%(cases)s med %(configuration)s på %(model)s (%(seeds)s)",
        "seed %(seeds)s": ["seed %(seeds)s", "seeds %(seeds)s"],
        "%(case)s with %(appendices)s": "%(case)s med %(appendices)s",
      },
    });
    expect(runTitle(varied)).toBe(
      "4 svenska fall med `plan` (prompt: terse, utan exempel) på qwen3-8b-awq (seeds 7, 8)",
    );
    expect(caseTitle({ name: "akm-01", appendices: ["blodgas", "röntgen"], earlier: false })).toBe(
      "akm-01 med blodgas och röntgen",
    );
  });
});
