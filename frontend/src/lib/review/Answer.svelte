<script lang="ts">
  import { onMount, untrack } from "svelte";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import { api, type Schemas, why } from "$lib/api/client";
  import ManagementPlan from "$lib/plan/ManagementPlan.svelte";
  import { isPlan } from "$lib/plan/types";
  import { type Shown, type Viewed, viewed } from "./review";

  let {
    answer,
    case: picked,
    labels,
    units,
  }: { answer: Shown; case: string; labels: string[]; units: string[] } = $props();
  const given = untrack(() => answer);

  let item = $state<Schemas["ItemDetail"] | null>(null);
  let views = $state<Viewed[]>([]);
  let problem = $state<string | null>(null);
  let read = $state(false);

  onMount(async () => {
    const run = given.run;
    const query = { case: untrack(() => picked) };
    const [items, scored] = await Promise.all([
      api.GET("/api/runs/{run}/items", { params: { path: { run }, query } }),
      given.score === null
        ? null
        : api.GET("/api/runs/{run}/scores/{score}/items", { params: { path: { run, score: given.score }, query } }),
    ]);
    read = true;
    if (!items.data) {
      problem = why(items.error);
      return;
    }
    item = items.data.find((i) => i.replicate === given.replicate) ?? null;
    if (scored?.data) views = viewed(scored.data.items, given.replicate, untrack(() => labels), untrack(() => units));
    else if (scored) problem = why(scored.error);
  });
</script>

{#if !read}
  <p class="flex items-center gap-2 text-muted-foreground">
    <LoaderCircleIcon class="size-4 animate-spin" aria-hidden="true" /> The answer…
  </p>
{:else}
  {#if problem}<p class="mb-2 text-destructive">{problem}</p>{/if}
  {#if item}
    {@const value = item.answer.value}
    {#if item.why}<p class="mb-2 text-muted-foreground">{item.why}</p>{/if}
    {#if item.answer.problem}
      <p class="mb-2 text-warning">{item.answer.problem}{item.answer.salvaged ? " (cut short)" : ""}</p>
    {/if}
    {#if value === null || value === undefined}
      <p class="text-muted-foreground">Nothing could be read.</p>
    {:else if typeof value === "string"}
      <div class="whitespace-pre-wrap rounded-lg bg-muted/60 p-3">{value}</div>
    {:else if given.plan && isPlan(value)}
      <ManagementPlan plan={value} />
    {:else}
      <pre class="overflow-x-auto rounded-lg bg-muted/60 p-3 font-mono text-xs leading-relaxed">{JSON.stringify(value, null, 2)}</pre>
    {/if}
  {/if}
  {#if views.length}
    <dl class="mt-3 grid grid-cols-[max-content_max-content_minmax(0,1fr)] gap-x-3 gap-y-1 text-xs">
      {#each views as v (v.label)}
        <dt class="font-medium">{v.label}</dt>
        <dd class="text-right tabular-nums">{v.value}</dd>
        <dd class="min-w-0 text-muted-foreground">
          {#each v.said as [key, text], i (i)}<span class="mr-2">{key ? `${key}: ` : ""}{text}</span>{/each}
          {#if v.calls}<span>{v.calls} judge call{v.calls === 1 ? "" : "s"}</span>{/if}
        </dd>
      {/each}
    </dl>
  {/if}
  <a class="mt-2 inline-block text-xs text-primary hover:underline" href="/runs/{given.run}#item-{given.anchor}">On its run's page</a>
{/if}
