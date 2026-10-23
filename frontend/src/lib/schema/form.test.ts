import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { blank, deref, kept, type Schema, widget } from "./form";

const TARGETS = JSON.parse(
  readFileSync(new URL("../../../../worlds/test/_data/schemas/targets.json", import.meta.url), "utf8"),
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
    expect(blank(note, TARGETS)).toEqual({ author: "", comment: "" });
    const typed = {
      diagnosis: { pattern: "biliary & colic", text: "" },
      warning: false,
      notes: [{ author: "alice", comment: "Ok.", answer: "" }],
    };
    expect(kept(typed, TARGETS, TARGETS)).toEqual({
      diagnosis: { pattern: "biliary & colic" },
      warning: false,
      notes: [{ author: "alice", comment: "Ok." }],
    });
  });

  it("falls back on JSON for what it can't draw", () => {
    expect(widget({ oneOf: [{ type: "string" }, { type: "number" }] }, {}).is).toBe("json");
    expect(widget({}, {}).is).toBe("json");
    expect(widget({ type: "string", enum: ["a", "b"] }, {})).toEqual({ is: "choice", options: ["a", "b"] });
  });
});

const CONTRACT: Schema = {
  oneOf: [{ $ref: "#/$defs/Native" }, { $ref: "#/$defs/Tool" }],
  $defs: {
    Native: { type: "object", properties: { kind: { const: "native", type: "string" } } },
    Tool: {
      type: "object",
      required: ["name"],
      properties: {
        kind: { const: "tool", type: "string" },
        name: { type: "string" },
        description: { anyOf: [{ type: "string", minLength: 1 }, { type: "null" }], default: null },
      },
    },
  },
};

describe("a union told apart by a field each of its members fixes", () => {
  it("is picked by that field, and draws the picked member's fields", () => {
    const shape = widget(CONTRACT, CONTRACT);
    if (shape.is !== "union") throw new Error("a union");
    expect(shape.key).toBe("kind");
    expect(shape.options.map((o) => o.value)).toEqual(["native", "tool"]);
    expect(blank(CONTRACT, CONTRACT)).toEqual({ kind: "native" });
    expect(kept({ kind: "tool", name: "answer", description: "" }, CONTRACT, CONTRACT)).toEqual({
      kind: "tool",
      name: "answer",
    });
  });

  it("draws a value that may be none as the value", () => {
    const tool = deref({ $ref: "#/$defs/Tool" }, CONTRACT);
    const description = (tool.properties as Record<string, Schema>).description ?? {};
    expect(widget(description, CONTRACT)).toEqual({ is: "text", long: true });
  });
});
