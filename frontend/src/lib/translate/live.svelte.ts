import type { Checked } from "$lib/editors/writing";
import type { Entries, Translating } from "./translate";

export type Live = {
  typed: Entries;
  left: string[];
  checking: string[];
  request: Translating["request"];
  found: Checked | null;
  asked: string | null;
};

export function live(translating: Translating): Live {
  const typed: Entries = {};
  for (const t of translating.texts) typed[t.text] = t.translation ?? "";
  const shared: Live = $state({ typed, left: [], checking: [], request: translating.request, found: null, asked: null });
  return shared;
}
