import { describe, expect, it } from "vitest";
import { speaking } from "$lib/locale";
import { why } from "./client";

describe("why a request was refused", () => {
  it("is said by its wording, and what isn't worded is passed on as it is", () => {
    speaking({
      tag: "sv",
      messages: {
        "refusal\u0004a fork is named": "en förgrening har ett namn",
        "That can't be done": "Det går inte",
        "%(title)s. Pass this on to ops, as it is: %(pass_on)s":
          "%(title)s. Skicka det här vidare som det är: %(pass_on)s",
      },
    });
    expect(why({ detail: "a fork is named", code: "refused", wording: "a fork is named", params: {} })).toBe(
      "en förgrening har ett namn",
    );
    expect(why({ detail: "no tool named x", code: "refused", wording: "no tool named %(tool)s", params: {} })).toBe(
      "no tool named x",
    );
    expect(why({ detail: "slots used twice", code: "refused" })).toBe(
      "Det går inte. Skicka det här vidare som det är: slots used twice",
    );
  });
});
