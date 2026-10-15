import type { Schemas } from "$lib/api/client";
import type { Part, Picked } from "./logic";

export type Props = {
  configuration: Schemas["ThreadDetail"];
  me: string;
  versions: Schemas["Edit"][];
  base: Picked;
  optional: Part[];
  look: Schemas["Variation"];
  endpoint: string | null;
  tags: string[];
  choices: Record<Part, Schemas["Thread"][]>;
  configurations: Schemas["Thread"][];
  endpoints: Schemas["Endpoint"][];
  everyTag: string[];
  families: Schemas["Family"][];
  itemsPerRun: number;
  runs: Schemas["Run"][];
};
