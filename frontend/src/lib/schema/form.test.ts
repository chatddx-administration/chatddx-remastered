import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { blank, deref, kept, type Schema, widget } from "./form";

const TARGETS = JSON.parse(
  readFileSync(new URL("../../../../worlds/sample/_data/schemas/targets.json", import.meta.url), "utf8"),
) as Schema;
const at = (name: string) => (TARGETS.properties as Record<string, Schema>)[name] ?? {};

describe("a form drawn from a JSON Schema", () => {
  it("draws the targets' fields, each as what it holds", () => {
    const shape = widget(TARGETS, TARGETS);
    if (shape.is !== "object") throw new Error("an object");
    expect(shape.properties.map((p) => [p.name, p.required])).toEqual([
      ["diagnosis", true],
      ["warning", false],
      ["disposition", false],
      ["dont_miss", false],
      ["notes", false],
    ]);
    expect(widget(at("diagnosis"), TARGETS).is).toBe("object");
    expect(widget(at("warning"), TARGETS).is).toBe("or-none");
    expect(widget(at("notes"), TARGETS).is).toBe("list");
    expect(deref(at("diagnosis"), TARGETS).properties).toHaveProperty("pattern");
  });

  it("offers a blank of each, and leaves out what an optional text left empty", () => {
    expect(blank(TARGETS, TARGETS)).toEqual({ diagnosis: {} });
    const note = deref((at("notes") as { items: Schema }).items, TARGETS);
    expect(blank(note, TARGETS)).toEqual({ author: "", language: "", comment: "" });
    const typed = {
      diagnosis: { pattern: "biliary & colic", text: "" },
      warning: false,
      notes: [{ author: "alice", language: "en", comment: "Ok.", answer: "" }],
    };
    expect(kept(typed, TARGETS, TARGETS)).toEqual({
      diagnosis: { pattern: "biliary & colic" },
      warning: false,
      notes: [{ author: "alice", language: "en", comment: "Ok." }],
    });
  });

  it("falls back on JSON for what it can't draw", () => {
    expect(widget({ oneOf: [{ type: "string" }, { type: "number" }] }, {}).is).toBe("json");
    expect(widget({}, {}).is).toBe("json");
    expect(widget({ type: "string", enum: ["a", "b"] }, {})).toEqual({ is: "choice", options: ["a", "b"] });
  });
});
