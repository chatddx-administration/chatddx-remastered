import { describe, expect, it } from "vitest";
import { LAYOUT, missing, recipeOf } from "./recipe";

describe("a recipe being picked", () => {
  it("says the parts it still needs", () => {
    const optional = ["instructions", "few_shot", "reasoning", "passthrough", "translations", "toolset"];
    expect(missing({}, optional)).toEqual(["prompt", "output", "sampling", "model"]);
    expect(missing({ prompt: "p", output: "o", sampling: "s", model: "m" }, optional)).toEqual([]);
  });

  it("holds the parts picked, its purpose and its layout", () => {
    const picks = { prompt: "p", output: "o", sampling: "s", model: "m", reasoning: undefined };
    expect(recipeOf("judge", picks, LAYOUT)).toEqual({
      purpose: "judge",
      prompt: "p",
      output: "o",
      sampling: "s",
      model: "m",
      appendix_layout: { before: "\n\n", between: "\n\n", after: "" },
    });
  });
});

