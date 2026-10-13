<script lang="ts" module>
  export type Live = { run: string; titles: Record<string, string> };
</script>

<script lang="ts">
  import { onMount, untrack } from "svelte";
  import InfoIcon from "@lucide/svelte/icons/info";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import TriangleAlertIcon from "@lucide/svelte/icons/triangle-alert";
  import { Badge } from "$lib/components/ui/badge";
  import { watch } from "$lib/runs/events";
  import { begun, fold, type Item, tally } from "$lib/runs/progress";

  let { live }: { live: Live } = $props();
  const given = untrack(() => live);

  let progress = $state(begun());
  let lost = $state<string | null>(null);
  const counted = $derived(tally(progress));
  const scoring = $derived(progress.scorings.length > 0);

  onMount(() => {
    watch(given.run, (name, data) => fold(progress, name, data))
      .then(() => setTimeout(() => location.reload(), 800))
      .catch((e: unknown) => {
        lost = e instanceof Error ? e.message : String(e);
      });
  });

  function titled(item: Item): string {
    const title = given.titles[item.case] ?? item.case.slice(7, 19);
    return item.replicate ? `${title} #${item.replicate}` : title;
  }

  function doing(item: Item): string {
    if (item.phase === "waiting") return "waiting";
    if (item.phase === "ended") return `${item.sent} in, ${item.received} out`;
    const what = item.kind === "reasoning" ? "thinking" : item.kind === "tool_call" ? "calling a tool" : "writing";
    return item.kind === null ? "sent" : `${what}, ${item.tokens} tokens`;
  }
</script>

<section class="glass-card mb-6 rounded-2xl p-5 sm:p-6" aria-live="polite">
  <div class="mb-4 flex flex-wrap items-center gap-3">
    <h2 class="text-lg font-semibold">Under way</h2>
    {#if progress.done}
      <span class="text-sm text-muted-foreground">
        {progress.done.halted ? "Halted" : "Done"}; showing what it came to…
      </span>
    {:else}
      <LoaderCircleIcon class="size-4 animate-spin text-muted-foreground" aria-hidden="true" />
      <span class="text-sm text-muted-foreground">{scoring ? "Scoring" : "Sending"}</span>
    {/if}
  </div>

  {#if lost}
    <p class="mb-4 text-sm text-destructive">{lost}. Reload the page to see how far it has come.</p>
  {/if}

  {#if counted.of}
    <div class="mb-2 h-2 overflow-hidden rounded-full bg-muted">
      <div
        class="h-full bg-primary transition-[width]"
        style:width="{(100 * counted.ended) / counted.of}%"
        role="progressbar"
        aria-valuemin="0"
        aria-valuemax={counted.of}
        aria-valuenow={counted.ended}
        aria-label="Items ended"
      ></div>
    </div>
    <p class="mb-4 flex flex-wrap items-center gap-2 text-sm">
      <span>{counted.ended} of {counted.of} items ended</span>
      {#each counted.outcomes as [outcome, n] (outcome)}<Badge variant="outline">{outcome} {n}</Badge>{/each}
    </p>

    <div class="space-y-1.5">
      {#each progress.items as item (`${item.case}#${item.replicate}`)}
        <details class="rounded-lg border border-border/60 bg-background/40 px-3 py-2">
          <summary class="flex cursor-pointer flex-wrap items-center gap-x-3 gap-y-1 text-sm">
            <span class="font-medium">{titled(item)}</span>
            {#if item.outcome}<Badge variant={item.outcome === "valid" || item.outcome === "completed" ? "secondary" : "destructive"}>{item.outcome}</Badge>{/if}
            {#if item.phase === "sending"}<LoaderCircleIcon class="size-3.5 animate-spin text-muted-foreground" aria-hidden="true" />{/if}
            <span class="text-muted-foreground">{doing(item)}</span>
            {#if item.tools}<span class="text-muted-foreground">{item.tools} tool {item.tools === 1 ? "call" : "calls"}</span>{/if}
            {#if item.why}<span class="text-muted-foreground">{item.why}</span>{/if}
          </summary>
          {#if item.text.reasoning}
            <p class="mt-2 text-xs font-medium text-muted-foreground">Thinking</p>
            <div class="mt-1 max-h-48 overflow-y-auto whitespace-pre-wrap font-mono text-xs text-muted-foreground">{item.text.reasoning}</div>
          {/if}
          {#if item.text.content || item.text.tool_call}
            <p class="mt-2 text-xs font-medium text-muted-foreground">Answer</p>
            <div class="mt-1 max-h-72 overflow-y-auto whitespace-pre-wrap font-mono text-xs">{item.text.content}{item.text.tool_call}</div>
          {/if}
          {#if item.phase === "waiting"}<p class="mt-2 text-xs text-muted-foreground">Not sent yet.</p>{/if}
          {#if item.phase === "ended" && !item.text.content && !item.text.reasoning}
            <p class="mt-2 text-xs text-muted-foreground">It ended before this page followed it; its answer is on the run's page once it is done.</p>
          {/if}
        </details>
      {/each}
    </div>
  {/if}

  {#if scoring}
    <h3 class="mt-6 mb-2 text-sm font-medium">Scoring</h3>
    <ul class="space-y-1.5 text-sm">
      {#each progress.scorings as s, i (s.scorer)}
        {@const after = progress.scorings.slice(i + 1).some((t) => t.score !== null)}
        <li class="flex flex-wrap items-center gap-x-3">
          <span class="font-medium">{s.name}</span>
          {#if s.score === null}
            <span class="text-muted-foreground">waiting</span>
          {:else}
            {#if !after && progress.scores === null}<LoaderCircleIcon class="size-3.5 animate-spin text-muted-foreground" aria-hidden="true" />{/if}
            <span class="text-muted-foreground">{s.scored} scored{s.views ? ` over ${s.views} ${s.views === 1 ? "view" : "views"}` : ""}</span>
            {#if s.asked}<span class="text-muted-foreground">judges answered {s.answered} of {s.asked}</span>{/if}
          {/if}
        </li>
      {/each}
    </ul>
  {/if}

  {#if progress.noted.length || progress.errors.length}
    <ul class="mt-6 space-y-1.5 text-sm">
      {#each progress.noted as finding, i (i)}
        <li class="flex gap-2">
          {#if finding.level === "warning"}<TriangleAlertIcon class="mt-0.5 size-4 shrink-0 text-warning" />{:else}<InfoIcon class="mt-0.5 size-4 shrink-0 text-primary" />{/if}
          <span>{finding.message}</span>
        </li>
      {/each}
      {#each progress.errors as error, i (i)}
        <li class="flex gap-2 text-destructive"><TriangleAlertIcon class="mt-0.5 size-4 shrink-0" /><span>{error}</span></li>
      {/each}
    </ul>
  {/if}
</section>
