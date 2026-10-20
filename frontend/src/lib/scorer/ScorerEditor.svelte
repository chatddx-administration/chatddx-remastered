<script lang="ts" module>
  import type { Editing } from "$lib/editors/writing";
  import type { Schema } from "$lib/schema/form";
  import type { ScorerBody, Scoring } from "./scorers";

  export type ScorerEditing = Editing & Scoring & {
    kind: "scorer";
    body: ScorerBody;
    labels: string[];
    schemas: { digest: string; name: string; json_schema: Schema }[];
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import Saving from "$lib/editors/Saving.svelte";
  import type { Component } from "$lib/editors/writing";
  import { FIELD } from "$lib/utils";
  import type { JudgeChoice } from "./judging";
  import ScorerViews from "./ScorerViews.svelte";
  import { answeredChoices } from "./scorers";
  import { choices } from "./selectors";

  let { editor, digest = null }: { editor: ScorerEditing; digest?: string | null } = $props();
  const given = untrack(() => editor);
  const answered = answeredChoices(given.outputs);

  let body = $state<ScorerBody>(structuredClone(given.body));
  let labels = $state<string[]>([...given.labels]);
  let judges = $state<JudgeChoice[]>([...given.judges]);

  const schema = $derived(given.schemas.find((s) => s.digest === body.expectation_schema)?.json_schema ?? null);
  const reads = $derived(choices(schema, null, "the whole expectation"));
  const titles = $derived({ ...given.titles, ...Object.fromEntries(judges.map((j) => [j.digest, j.name])) });

  function component(): Component {
    return $state.snapshot(body) as never;
  }
</script>

<div class="space-y-3 text-sm">
  <label class="grid max-w-md gap-1"
    ><span class="text-muted-foreground">What it is held to, an expectation schema</span>
    <select class={FIELD} bind:value={body.expectation_schema}>
      {#each given.schemas as s (s.digest)}<option value={s.digest}>{s.name}</option>{/each}
    </select></label
  >
  <div class="text-xs">
    <ScorerViews
      bind:views={body.views}
      bind:labels
      bind:judges
      metrics={given.metrics}
      asked={reads}
      {answered}
      {titles}
      judging={given.judging}
      models={given.models}
      me={given.me}
    />
  </div>
  <p class="text-muted-foreground">
    A view picks from what is expected and from the answer as its expectation schema and the configurations you see
    allow. To try it on answers, compose it beside a case on the Review page.
  </p>
  <Saving
    editing={given}
    {component}
    {digest}
    same={JSON.stringify(labels) === JSON.stringify(given.labels)}
    labels={() => $state.snapshot(labels)}
  />
</div>
