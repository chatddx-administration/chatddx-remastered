import { describe, expect, it } from "vitest";
import { flipped, kept, pickedIn, shown } from "./filtering";

describe("a case shown under what is picked", () => {
  it("holds each tag picked and any language picked", () => {
    const picked = { tags: ["targets", "swedish"], languages: ["sv", "en"] };
    expect(shown(["swedish", "targets", "akm"], "sv", picked)).toBe(true);
    expect(shown(["targets"], "sv", picked)).toBe(false);
    expect(shown(["swedish", "targets"], "de", picked)).toBe(false);
    expect(shown([], "", { tags: [], languages: [] })).toBe(true);
  });
});

describe("what is picked", () => {
  it("is flipped a value at a time", () => {
    expect(flipped(["a"], "b")).toEqual(["a", "b"]);
    expect(flipped(["a", "b"], "a")).toEqual(["b"]);
  });

  it("is read from an address and kept in another, the rest of it as it is", () => {
    expect(pickedIn("?tag=a&case=c&tag=b&language=sv")).toEqual({ tags: ["a", "b"], languages: ["sv"] });
    const picked = { tags: ["x y"], languages: [] };
    expect(kept("/review/3?case=c&tag=a&language=sv#record", picked)).toBe("/review/3?case=c&tag=x+y#record");
  });
});
