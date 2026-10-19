import { describe, expect, it } from "vitest";
import { answeredChoices } from "./scorers";

describe("answeredChoices", () => {
  it("offers the whole answer once and each output's fields by its title", () => {
    const plan = {
      title: "plan",
      json_schema: { type: "object", properties: { diagnoses: { type: "array", items: { type: "string" } } } },
      by: ["native"],
    };
    const again = { ...plan, by: ["native-tools"] };
    const found = answeredChoices([plan, again, { title: null, json_schema: null, by: ["lines"] }]);
    expect(found[0]).toEqual({ label: "the whole answer", selector: "" });
    expect(found.filter((c) => c.selector === "")).toHaveLength(1);
    expect(found.some((c) => c.label.startsWith("plan: ") && c.selector === "/diagnoses")).toBe(true);
    expect(new Set(found.map((c) => c.selector)).size).toBe(found.length);
  });
});
