import { describe, expect, it } from "vitest";
import { found, paged } from "./paging";

const rows = ["Sepsis at the door", "chest pain", "Septic shock, again", "stroke"];

describe("found", () => {
  it("keeps every row when nothing is typed", () => {
    expect(found(rows, (r) => r, "  ")).toEqual(rows);
  });

  it("keeps the rows that say every word typed, whatever its case", () => {
    expect(found(rows, (r) => r, "SEP")).toEqual(["Sepsis at the door", "Septic shock, again"]);
    expect(found(rows, (r) => r, "sep  again")).toEqual(["Septic shock, again"]);
    expect(found(rows, (r) => r, "sep pain")).toEqual([]);
  });
});

describe("paged", () => {
  const many = Array.from({ length: 7 }, (_, i) => i);

  it("shows a page at a time and says which is last", () => {
    expect(paged(many, 0, 3)).toEqual({ shown: [0, 1, 2], at: 0, last: 2 });
    expect(paged(many, 2, 3)).toEqual({ shown: [6], at: 2, last: 2 });
  });

  it("keeps a page asked for within those there are", () => {
    expect(paged(many, 9, 3).at).toBe(2);
    expect(paged(many, -1, 3).at).toBe(0);
    expect(paged([], 4, 3)).toEqual({ shown: [], at: 0, last: 0 });
  });
});
