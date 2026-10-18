import { describe, expect, it } from "vitest";
import { asked, editable, fillText, filled, merged, segmentsOf, textOf } from "./texts";

const GUIDED = { insert: "output_guidance", before: "\n\n" };

describe("segments", () => {
  it("are edited with a text before, between and after each slot or insert", () => {
    expect(editable([{ slot: "completion" }])).toEqual(["", { slot: "completion" }, ""]);
    expect(editable(["a", { slot: "completion" }, { slot: "expectation" }])).toEqual([
      "a",
      { slot: "completion" },
      "",
      { slot: "expectation" },
      "",
    ]);
  });

  it("are stored as the canonical form keeps them", () => {
    expect(textOf(["a", "b", ""])).toBe("ab");
    expect(textOf(["a", GUIDED, ""])).toEqual(["a", GUIDED]);
    expect(merged(["", { slot: "completion" }, "x", "y"])).toEqual([{ slot: "completion" }, "xy"]);
    expect(segmentsOf("plain")).toEqual(["plain"]);
    expect(segmentsOf(null)).toEqual([""]);
  });

  it("fill an insert with what surrounds it only when there is something to place", () => {
    expect(filled(["a", GUIDED], { output_guidance: "Say yes." })).toBe("a\n\nSay yes.");
    expect(filled(["a", GUIDED], { output_guidance: "" })).toBe("a");
  });
});

describe("fillText", () => {
  it("writes picks as the scoring pass fills a judge's slot", () => {
    expect(fillText(["one"])).toBe("one");
    expect(fillText(["one", "two"])).toBe("one\ntwo");
    expect(fillText([{ pattern: "x" }])).toBe('{\n  "pattern": "x"\n}');
  });
});

describe("asked", () => {
  it("reads as the judge would be asked, the guidance where the instructions place it", () => {
    const said = asked(
      { role: "system", segs: ["Judge it.", GUIDED] },
      ["Answer:\n", { slot: "completion" }, "\nNote:\n", { slot: "expectation" }],
      ["Say whether it meets the note."],
      ["Chock."],
    );
    expect(said).toEqual([
      { role: "system", content: "Judge it.\n\nSay whether it meets the note." },
      { role: "user", content: "Answer:\n‹completion›\nNote:\nChock." },
    ]);
  });

  it("places guidance nothing inserts after the instructions, or alone where there are none", () => {
    const prompt = ["Answer:\n", { slot: "completion" }];
    expect(asked({ role: "developer", segs: ["Judge it."] }, prompt, ["Say why."], null)[0]).toEqual({
      role: "developer",
      content: "Judge it.\n\nSay why.",
    });
    expect(asked(null, prompt, ["Say why."], null)).toEqual([
      { role: "system", content: "Say why." },
      { role: "user", content: "Answer:\n‹completion›" },
    ]);
    expect(asked(null, [...prompt, GUIDED], ["Say why."], null)).toEqual([
      { role: "user", content: "Answer:\n‹completion›\n\nSay why." },
    ]);
  });
});
