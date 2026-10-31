import { describe, expect, it } from "vitest";
import type { Schemas } from "$lib/api/client";
import { below, binned, grouped, said, ticks } from "./faring";

function row(metric: number, values: number[], shown: number | null): Schemas["FaredRow"] {
  return {
    metric,
    configuration: 0,
    cases: values.map((_, i) => i),
    values,
    synthetic: values.map(() => false),
    shown: shown === null ? null : { value: shown, synthetic: false, replicates: [] },
  };
}

describe("how a case fares", () => {
  it("is grouped by the field each view reads, in the order the views come", () => {
    const metric = (field: string | null) => ({ scorer: "s", view: 0, label: "l", field });
    const fared = {
      synthetic: false,
      run: false,
      configurations: [],
      cases: [],
      metrics: [metric("diagnosis"), metric("warning"), metric("diagnosis"), metric(null)],
      rows: [row(0, [], 1), row(1, [], 1), row(2, [], 1)],
    };
    expect(grouped(fared).map((g) => [g.field, g.metrics.map((m) => m.at)])).toEqual([
      ["diagnosis", [0, 2]],
      ["warning", [1]],
    ]);
  });

  it("is told as the share of the other cases below it, a tie as half", () => {
    expect(below(row(0, [0, 0.5, 1, 1], 1))).toBe(0.75);
    expect(below(row(0, [0, 0.25], 0.5))).toBe(1);
    expect(below(row(0, [0.5, 0.5], 0.5))).toBe(0.5);
    expect(below(row(0, [0.5], null))).toBe(0);
  });

  it("bins the other cases by their means, those run apart from those drawn", () => {
    const at = { ...row(0, [0.25, 0.25, 1, 0.26, 0], null), synthetic: [false, true, true, false, true] };
    expect(binned(at)).toEqual([
      { at: 0, run: 0, drawn: 1, cases: [4] },
      { at: 5, run: 2, drawn: 1, cases: [0, 1, 3] },
      { at: 20, run: 0, drawn: 1, cases: [2] },
    ]);
  });

  it("ticks each replicate scored, those alike side by side about their value", () => {
    const replicate = (value: number | null, n: number) => ({ value, href: value === null ? null : `/s/${n}` });
    const shown = {
      value: 0.5,
      synthetic: false,
      replicates: [replicate(1, 0), replicate(0, 1), replicate(1, 2), replicate(null, 3), replicate(1, 4)],
    };
    expect(ticks(shown)).toEqual([
      { value: 1, href: "/s/0", n: 1, offset: -1 },
      { value: 0, href: "/s/1", n: 2, offset: 0 },
      { value: 1, href: "/s/2", n: 3, offset: 0 },
      { value: 1, href: "/s/4", n: 5, offset: 1 },
    ]);
  });

  it("says why a configuration is behind, a refusal as the server worded it", () => {
    expect(said({ why: "changed" })).toBe("its configuration has changed since it ran");
    const refusal = {
      detail: "tools can't be cleared yet",
      code: "refused" as const,
      wording: "tools can't be cleared yet",
    };
    expect(said({ why: "refused", refusal })).toBe("tools can't be cleared yet");
  });
});
