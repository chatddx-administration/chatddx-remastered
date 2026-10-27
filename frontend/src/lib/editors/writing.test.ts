import { describe, expect, it } from "vitest";
import { said } from "./writing";

describe("where a save goes", () => {
  it("is a new version of one's own, unless nothing changed", () => {
    expect(said({ mode: "edit", name: "x" }, "x", false)).toBe("Saves a new version of it.");
    expect(said({ mode: "edit", name: "x" }, "x", true)).toBe("");
  });

  it("is a new thread, or a fork, named", () => {
    expect(said({ mode: "new", name: "" }, " plan ", false)).toBe("Writes “plan”, a new thread of your own.");
    expect(said({ mode: "fork", name: "" }, "mine", false)).toBe("Saves it as “mine”, a fork of your own.");
    expect(said({ mode: "fork", name: "" }, "  ", false)).toBe("Give it a name to save it.");
  });
});
