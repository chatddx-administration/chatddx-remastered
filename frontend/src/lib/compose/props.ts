import type { Schemas } from "$lib/api/client";
import type { Drafted } from "./drafting";

export type Props = {
  configuration: Schemas["ThreadDetail"];
  me: string;
  versions: Schemas["Edit"][];
  head: number;
  varied: boolean;
  optional: string[];
  modelChoices: Schemas["Thread"][];
  drafted: Drafted | null;
  configurations: Schemas["Thread"][];
};
