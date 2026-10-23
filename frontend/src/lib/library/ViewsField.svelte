<script lang="ts">
  import { untrack } from "svelte";
  import type { Schema } from "$lib/schema/form";
  import type { JudgeChoice } from "$lib/scorer/judging";
  import ScorerViews from "$lib/scorer/ScorerViews.svelte";
  import { answeredChoices, type ScorerView, type Scoring } from "$lib/scorer/scorers";
  import { choices } from "$lib/scorer/selectors";

  let {
    views: given,
    labels: named,
    schema,
    scoring,
    changed,
  }: {
    views: ScorerView[];
    labels: string[];
    schema: Schema | null;
    scoring: Scoring;
    changed: (views: ScorerView[], labels: string[]) => void;
  } = $props();
  const held = untrack(() => scoring);
  let views = $state(structuredClone(untrack(() => given)));
  let labels = $state([...untrack(() => named)]);
  let judges = $state<JudgeChoice[]>([...held.judges]);
  const titles = $derived({ ...held.titles, ...Object.fromEntries(judges.map((j) => [j.digest, j.name])) });
  const asked = choices(untrack(() => schema), null, "the whole expectation");
  const answered = answeredChoices(held.outputs);

  $effect(() => {
    changed($state.snapshot(views), $state.snapshot(labels));
  });
</script>

<div class="text-xs">
  <ScorerViews
    bind:views
    bind:labels
    bind:judges
    metrics={held.metrics}
    {asked}
    {answered}
    {titles}
    judging={held.judging}
    models={held.models}
    me={held.me}
  />
</div>
