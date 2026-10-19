import type { Checked } from "$lib/editors/writing";
import { type Entries, entriesInto, textsOf, type Translating } from "./translate";

export type Live = {
  typed: Entries;
  left: string[];
  checking: string[];
  request: Translating["request"];
  found: Checked | null;
  asked: string | null;
};

export function live(translating: Translating): Live {
  const held = entriesInto(translating.translations, translating.into);
  const typed: Entries = {};
  for (const text of textsOf(translating.texts)) typed[text] = held[text] ?? "";
  const shared: Live = $state({ typed, left: [], checking: [], request: translating.request, found: null, asked: null });
  return shared;
}
