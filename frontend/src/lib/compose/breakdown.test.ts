import { describe, expect, it } from "vitest";
import type { Schemas } from "$lib/api/client";
import { differs, estimated, grouped, languages, mean, named, spread } from "./breakdown";

function point(at: string): Schemas["BrokenPoint"] {
  return {
    started: "00000000-0000-0000-0000-000000000000",
    at,
    version: 1,
    means: [],
    spread: [],
    alike: 0,
    compared: 0,
    languages: [],
    failed: 0,
    seconds: 1,
    tokens: null,
    stale: false,
  };
}

describe("how a configuration fared", () => {
  it("is grouped by the field each view reads, in the order the views come", () => {
    const view = (field: string | null) => ({ scorer: "s", view: 0, label: "l", field });
    const broken = {
      name: "plan",
      tag: "akm",
      cases: 2,
      views: [view("diagnosis"), view("warning"), view("diagnosis")],
      versions: [],
      peers: [],
    };
    expect(grouped(broken)).toEqual([
      { field: "diagnosis", views: [0, 2] },
      { field: "warning", views: [1] },
    ]);
  });

  it("names a pooled version by each version that compiles to it", () => {
    const version = { digest: "d", versions: [2, 5], estimates: [], paired: [], points: [] };
    expect(named(version)).toBe("v2, v5");
  });

  it("spreads a version's gatherings by when they ran", () => {
    expect(spread([point("2026-01-02T00:00:00Z"), point("2026-01-01T00:00:00Z")])).toEqual([0.5, -0.5]);
    expect(spread([point("2026-01-01T00:00:00Z")])).toEqual([0]);
  });

  it("gives a version's estimate and how it differs from the one before", () => {
    const version = {
      digest: "d",
      versions: [3],
      estimates: [{ mean: 0.625, half: 0.08, n: 40 }, null],
      paired: [{ mean: -0.1, half: 0.05, n: 20 }, null],
      points: [],
    };
    expect(estimated(version, 0)).toBe("v3: 0.63 ±0.08 (n=40), Δ −0.10 (n=20)");
    expect(estimated(version, 1)).toBe("v3: —");
    expect(differs({ mean: 0.2, half: null, n: 1 })).toBe("+0.20 (n=1)");
    expect(mean([0.5, null, 1])).toBe(0.75);
    expect(mean([null])).toBeNull();
  });

  it("counts a baseline's cases by the language each was sent in", () => {
    const held = {
      ...point("2026-01-01T00:00:00Z"),
      languages: [
        { language: null, cases: 1 },
        { language: "sv", cases: 18 },
      ],
    };
    expect(languages(held)).toBe("— 1, Swedish 18");
  });
});
