<script lang="ts">
  import { untrack } from "svelte";
  import { api, type Schemas, why } from "$lib/api/client";
  import ExpectationEditor from "$lib/editors/ExpectationEditor.svelte";
  import type { ExpectationEditing } from "$lib/editors/ExpectationEditor.svelte";
  import Changed from "$lib/thread/Changed.svelte";
  import { type Expecting, fieldOf, type Read, shortly } from "./review";

  let { expected, editor, back }: { expected: Expecting; editor: ExpectationEditing; back: string } = $props();
  const given = untrack(() => expected);
  const views = given.views.map((view, at) => ({ view, at, field: fieldOf(view.expectation) }));

  let data = $state<unknown>(untrack(() => editor.data));
  let picks = $state<Schemas["Picked"][] | null>(null);
  let problem = $state<string | null>(null);
  let asked = 0;

  const written = $derived(
    typeof data === "object" && data !== null && !Array.isArray(data) ? new Set(Object.keys(data)) : new Set<string>(),
  );
  const elsewhere = $derived(views.filter((v) => v.field === null || !written.has(v.field)));

  let shown = $state(given.history.length - 1);
  const version = $derived(given.history[shown]);
  const before = $derived(shown > 0 ? given.history[shown - 1] : undefined);

  $effect(() => {
    const document = JSON.parse(JSON.stringify(data ?? null)) as unknown;
    if (views.length === 0) return;
    const sent = ++asked;
    const timer = setTimeout(async () => {
      const got = await api.POST("/api/picks", {
        body: { document: document as never, selectors: views.map((v) => v.view.expectation) },
      });
      if (sent !== asked) return;
      if (got.data) {
        picks = got.data;
        problem = null;
      } else problem = why(got.error);
    }, 300);
    return () => clearTimeout(timer);
  });

  function when(stamp: string): string {
    return stamp.slice(0, 16).replace("T", " ");
  }
</script>

{#snippet reads(view: Read, at: number)}
  {@const picked = picks?.[at]}
  <div class="flex flex-wrap items-baseline gap-x-1.5">
    <span class="font-medium text-primary">{view.label}</span>
    <span class="text-muted-foreground" title={view.measures ?? ""}
      >{view.metric.replaceAll("_", " ")}{view.judge ? ` · judge ${view.judge}` : ""}</span
    >
    {#if !picked}
      <span class="text-muted-foreground">…</span>
    {:else if picked.problem}
      <span class="text-destructive">{picked.problem}</span>
    {:else if !picked.items?.length}
      <span class="text-warning">reads nothing</span>
    {:else}
      <span class="min-w-0 text-muted-foreground">reads <span class="text-foreground">{shortly(picked.items)}</span></span>
    {/if}
  </div>
{/snippet}

{#snippet beside(field: string)}
  {@const here = views.filter((v) => v.field === field)}
  {#if here.length}
    <ul class="ml-2 space-y-0.5 border-l-2 border-primary/30 pl-2 text-xs" aria-label="What reads {field.replaceAll('_', ' ')}">
      {#each here as v (v.at)}<li>{@render reads(v.view, v.at)}</li>{/each}
    </ul>
  {/if}
{/snippet}

<ExpectationEditor {editor} digest={given.digest} opened={true} quiet changed={(d) => (data = d)} {beside} to={() => back} />

{#if problem}<p class="mt-2 text-xs text-destructive">{problem}</p>{/if}
{#if elsewhere.length}
  <div class="mt-4 rounded-lg bg-muted/40 p-2.5">
    <p class="mb-1 text-xs font-medium text-muted-foreground">Read elsewhere, or of what isn't written</p>
    <ul class="space-y-0.5 text-xs">
      {#each elsewhere as v (v.at)}<li>{@render reads(v.view, v.at)}</li>{/each}
    </ul>
  </div>
{/if}

{#if version}
  <details class="mt-4 text-sm">
    <summary class="cursor-pointer text-xs text-muted-foreground">
      Version {given.history.length} of {given.history.length}, {when(given.history.at(-1)?.at ?? "")}: what each changed
    </summary>
    <div class="mt-2 rounded-lg border border-border/60 p-3">
      <nav class="mb-2 flex items-center gap-2 text-xs" aria-label="Versions">
        <button type="button" class="rounded-md border border-border px-2 py-0.5 hover:bg-muted disabled:opacity-40" disabled={shown === 0} aria-label="The version before" onclick={() => (shown -= 1)}>◀</button>
        <span class="font-medium">Version {shown + 1} of {given.history.length}</span>
        <button type="button" class="rounded-md border border-border px-2 py-0.5 hover:bg-muted disabled:opacity-40" disabled={shown === given.history.length - 1} aria-label="The version after" onclick={() => (shown += 1)}>▶</button>
        <span class="text-muted-foreground">{when(version.at)}, {version.by}</span>
      </nav>
      {#if before}
        <Changed before={before.data} after={version.data} />
      {:else}
        <p class="text-xs text-muted-foreground">It is the first.</p>
      {/if}
    </div>
  </details>
{/if}
