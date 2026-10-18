import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { seedsOf, startingParams, verdictAt } from "./judging";

const read = (name: string) =>
  JSON.parse(readFileSync(new URL(`../../../../worlds/sample/_data/schemas/${name}`, import.meta.url), "utf8"));
const VERDICT = read("verdict.json");
const GRADE = read("grade.json");
const AT = { type: "object", properties: { at: { type: "string" } }, required: ["at"] };
const AT_MAX = { type: "object", properties: { at: { type: "string" }, max: { type: "number" } } };

describe("seedsOf", () => {
  it("reads seeds as typed, and says what is wrong with them", () => {
    expect(seedsOf("1, 2 3")).toEqual([1, 2, 3]);
    expect(seedsOf(" ")).toBe("a judge has a seed or more");
    expect(seedsOf("1, x")).toBe("seeds are whole numbers, 0 or more");
    expect(seedsOf("2, 2")).toBe("each seed once");
  });
});

describe("startingParams", () => {
  it("reads a verdict at the judge's first field that isn't text", () => {
    expect(verdictAt(VERDICT)).toEqual(["/meets", "/why"]);
    expect(startingParams(AT, VERDICT)).toEqual({ at: "/meets" });
  });

  it("takes the field's maximum as the most points", () => {
    expect(startingParams(AT_MAX, GRADE)).toEqual({ at: "/points", max: 2 });
    expect(startingParams(AT_MAX, null)).toEqual({ max: 1 });
  });
});
