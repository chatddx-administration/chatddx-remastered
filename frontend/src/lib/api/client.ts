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

export function follow(
  run: string,
  on: { [event: string]: (data: unknown) => void },
): Promise<void> {
  return new Promise((resolve, reject) => {
    const events = new EventSource(`/api/runs/${run}/events`);
    for (const [name, handle] of Object.entries(on)) {
      events.addEventListener(name, (e) => handle(JSON.parse((e as MessageEvent<string>).data)));
    }
    events.addEventListener("error", (e) => {
      if (e instanceof MessageEvent || events.readyState !== EventSource.CLOSED) return;
      reject(new Error("the run's events stopped coming"));
    });
    events.addEventListener("done", () => {
      events.close();
      resolve();
    });
  });
}
