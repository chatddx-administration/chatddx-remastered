import createClient from "openapi-fetch";
import { refusal, t, whoops } from "$lib/locale";
import type { components, paths } from "./schema";

export type Schemas = components["schemas"];

export const api = createClient<paths>();

function titled(code: Schemas["Error"]["code"] | undefined): string {
  const titles: Partial<Record<Schemas["Error"]["code"], string>> = {
    not_found: t("Not found"),
    not_allowed: t("Not allowed"),
    cross_site: t("Refused"),
    unauthenticated: t("Sign in"),
    refused: t("That can't be done"),
    unprocessable: t("That can't be done"),
    conflict: t("A conflict"),
    moved_on: t("It has moved on"),
    ambiguous: t("That names several"),
    over_quota: t("Over the day's quota"),
  };
  return (code && titles[code]) ?? t("Something went wrong");
}

// Policy: what a person can cause is worded, and what isn't worded they couldn't have
// caused, so it is passed on as it is.
export function why(error: unknown): string {
  const failure = error as Partial<Schemas["Error"]> | undefined;
  const detail = failure?.detail;
  if (typeof detail === "string" && failure?.code === "whoops") {
    return t("%(message)s Pass this on to ops, as it is: %(pass_on)s", {
      message: whoops(detail),
      pass_on: failure.pass_on ?? "",
    });
  }
  if (typeof detail === "string" && failure?.wording) return refusal(detail, failure.wording, failure.params ?? {});
  if (detail === undefined) return t("the server didn't say why");
  return t("%(title)s. Pass this on to ops, as it is: %(pass_on)s", {
    title: titled(failure?.code),
    pass_on: typeof detail === "string" ? detail : detail.map((d) => JSON.stringify(d)).join("; "),
  });
}
