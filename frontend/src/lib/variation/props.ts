import type { Schemas } from "$lib/api/client";
import type { Part, Picked } from "./logic";

export type Props = {
  configuration: Schemas["ThreadDetail"];
  judged: boolean;
  me: string;
  versions: Schemas["Edit"][];
  base: Picked;
  optional: Part[];
  look: Schemas["Variation"];
  under: string | null;
  tags: string[];
  choices: Record<Part, Schemas["Thread"][]>;
  configurations: Schemas["Thread"][];
  models: string[];
  everyTag: string[];
  families: Schemas["Family"][];
  itemsPerRun: number;
  runs: Schemas["Run"][];
};
