import { describe, expect, it } from "vitest";
import { added, replaced } from "./review";

describe("added", () => {
  it("adds what is typed, comma by comma, once and sorted", () => {
    expect(added(["copd", "swedish"], " akm, copd ,dutch,akm")).toEqual(["akm", "copd", "dutch", "swedish"]);
  });

  it("keeps the tags as they are when nothing new is typed", () => {
    const tags = ["copd"];
    expect(added(tags, " , copd")).toBe(tags);
  });
});

describe("replaced", () => {
  it("follows the case shown to the one that replaced it", () => {
    const back = "/review/3?case=old&tag=swedish";
    expect(replaced(back, "old", { old: "new" })).toBe("/review/3?case=new&tag=swedish");
    expect(replaced("/review/3", "old", { old: "new" })).toBe("/review/3?case=new");
    expect(replaced(back, "old", { other: "new" })).toBe(back);
  });
});
