import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

export type Schemas = components["schemas"];

export const api = createClient<paths>();

export function why(error: unknown): string {
  const failure = error as Partial<Schemas["Error"]> | undefined;
  const detail = failure?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => JSON.stringify(d)).join("; ");
  return "the server didn't say why";
}
