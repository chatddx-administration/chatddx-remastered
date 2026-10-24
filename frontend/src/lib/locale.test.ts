import { describe, expect, it } from "vitest";
import { languageName, listed, localized, refusal, speaking, t, th, tn, tnp, tp, whoops } from "./locale";

describe("a message", () => {
  it("is said as it is written where the page's catalog doesn't hold it", () => {
    speaking({ tag: "en", messages: {} });
    expect(t("it's %(name)s's", { name: "alice" })).toBe("it's alice's");
    expect(t("all %%, none %(n)s", { n: 0 })).toBe("all %, none 0");
    expect(tn("%(n)s run", "%(n)s runs", 1, { n: 1 })).toBe("1 run");
    expect(tn("%(n)s run", "%(n)s runs", 0, { n: 0 })).toBe("0 runs");
    expect(whoops("It broke.")).toBe("It broke.");
  });

  it("is said in the page's locale where its catalog holds it", () => {
    speaking({
      tag: "sv",
      messages: {
        Hello: "Hej",
        "%(n)s run": ["%(n)s körning", "%(n)s körningar"],
        "whoops\u0004It broke.": "Det gick sönder.",
        "outcome\u0004valid": "giltig",
        "outcome\u0004%(num)s valid": ["%(num)s giltig", "%(num)s giltiga"],
      },
    });
    expect(t("Hello")).toBe("Hej");
    expect(tn("%(n)s run", "%(n)s runs", 1, { n: 1 })).toBe("1 körning");
    expect(tn("%(n)s run", "%(n)s runs", 2, { n: 2 })).toBe("2 körningar");
    expect(t("Goodbye")).toBe("Goodbye");
    expect(whoops("It broke.")).toBe("Det gick sönder.");
    expect(tp("outcome", "valid")).toBe("giltig");
    expect(t("valid")).toBe("valid");
    expect(tnp("outcome", "%(num)s valid", "%(num)s valid", 3, { num: 3 })).toBe("3 giltiga");
  });

  it("holding markup, escapes what is put into it", () => {
    speaking({ tag: "en", messages: {} });
    expect(th('<a href="/runs/%(run)s">%(name)s</a>', { run: 1, name: "<b>&'\"" })).toBe(
      '<a href="/runs/1">&#60;b&#62;&#38;&#39;&#34;</a>',
    );
    expect(listed(["a", "b", "c"], "disjunction")).toBe("a, b, or c");
    expect(listed(["a", "b"])).toBe("a and b");
  });

  it("from below the portal, is said by its code where the page's catalog holds it, else as it comes", () => {
    speaking({
      tag: "sv",
      messages: {
        "run.incomplete\u0004%(num)s item missing": ["%(num)s post saknas", "%(num)s poster saknas"],
        "case.drift\u0004the vignette differs": "vinjetten skiljer sig",
      },
    });
    const found: Parameters<typeof localized>[0][] = [
      {
        code: "run.incomplete",
        message: "1 item missing",
        wording: ["%(num)s item missing", "%(num)s items missing"],
        params: { num: 1 },
      },
      { code: "case.drift", message: "the vignette differs", wording: "the vignette differs", params: {} },
      {
        code: "vllm.temperature_clamped",
        message: "vLLM 0.24 raises temperature 1e-05 to 0.01",
        wording: "vLLM 0.24 raises temperature %(temperature)s to 0.01",
        params: { temperature: 0.00001 },
      },
      { code: "call.failed", message: "the server didn't answer", wording: null, params: {} },
    ];
    expect(found.map(localized)).toEqual([
      "1 post saknas",
      "vinjetten skiljer sig",
      "vLLM 0.24 raises temperature 1e-05 to 0.01",
      "the server didn't answer",
    ]);
  });

  it("names a language by its name in the page's locale, as what is worded does", () => {
    const worded = "no translations into %(into)s, nor %(languages)s";
    const given = { into: "sv", languages: "en, pt-BR" };
    speaking({ tag: "en", messages: {} });
    expect(["sv", "pt-BR", "x"].map(languageName)).toEqual(["Swedish", "Portuguese (Brazil)", "x"]);
    expect(refusal("no translations into sv", worded, given)).toBe(
      "no translations into Swedish, nor English and Portuguese (Brazil)",
    );
    expect(refusal("no case a", "no case %(case)s", { case: "a" })).toBe("no case a");
    speaking({
      tag: "sv",
      messages: { [`refusal\u0004${worded}`]: "inga översättningar till %(into)s, eller %(languages)s" },
    });
    expect(languageName("en")).toBe("engelska");
    expect(refusal("no translations into sv", worded, given)).toBe(
      "inga översättningar till svenska, eller engelska och portugisiska (Brasilien)",
    );
  });

  it("fails on a placeholder given nothing, as the server's do", () => {
    expect(() => t("%(n)s yours")).toThrow("%(n)s");
  });
});
