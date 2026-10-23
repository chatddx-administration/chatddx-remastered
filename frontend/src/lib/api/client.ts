import createClient from "openapi-fetch";
import { t, whoops } from "$lib/locale";
import type { components, paths } from "./schema";

export type Schemas = components["schemas"];

export const api = createClient<paths>();

export function why(error: unknown): string {
  const failure = error as Partial<Schemas["Error"]> | undefined;
  const detail = failure?.detail;
  if (typeof detail === "string" && failure?.code === "whoops") {
    return t("%(message)s Pass this on to ops, as it is: %(pass_on)s", {
      message: whoops(detail),
      pass_on: failure.pass_on ?? "",
    });
  }
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => JSON.stringify(d)).join("; ");
  return t("the server didn't say why");
}
