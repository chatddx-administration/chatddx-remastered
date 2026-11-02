import type { Schemas } from "$lib/api/client";

export type Saving =
  | { to: "nothing"; because: "nameless" | "unchanged" }
  | { to: "version"; version: number }
  | { to: "fork"; namesakes: number };

export function whereSaveGoes(given: {
  name: string;
  configuration: Schemas["ThreadDetail"];
  me: string;
  versions: number;
  latest: boolean;
  changed: boolean;
  configurations: Schemas["Thread"][];
}): Saving {
  const name = given.name.trim();
  if (!name) return { to: "nothing", because: "nameless" };
  const own = given.configuration.owner === given.me;
  const same = name === (given.configuration.name ?? given.configuration.title);
  if (own && given.latest && same) {
    return given.changed ? { to: "version", version: given.versions + 1 } : { to: "nothing", because: "unchanged" };
  }
  const namesakes = given.configurations.filter((t) => t.owner === given.me && (t.name ?? t.title) === name).length;
  return { to: "fork", namesakes };
}
