<script lang="ts" module>
  import type { Schema } from "$lib/schema/form";
  import type { Texts } from "./rewriting";

  export type Judging = {
    digest: string;
    thread: number;
    name: string;
    owner: string | null;
    output_schema: Schema | null;
  };
  export type Serving = { name: string; weights: string };
  export type JudgeChoice = {
    digest: string;
    thread: number;
    name: string;
    owner: string | null;
    configuration: string;
    model: string | null;
    seeds: number[];
    output_schema: Schema | null;
    head?: number;
    body?: Record<string, unknown>;
    texts?: Texts | null;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import { api, why } from "$lib/api/client";
  import Findings from "$lib/editors/Findings.svelte";
  import { type Checked, checked, type Component } from "$lib/editors/writing";
  import { FIELD } from "$lib/utils";
  import { seedsOf } from "./judging";

  let {
    me,
    judging,
    models,
    made,
    left,
  }: {
    me: string;
    judging: Judging[];
    models: Serving[];
    made: (judge: JudgeChoice) => void;
    left: () => void;
  } = $props();
  const given = untrack(() => ({ judging, models }));

  let name = $state("");
  let configuration = $state(given.judging[0]?.digest ?? "");
  let model = $state(given.models[0]?.name ?? "");
  let seeds = $state("1");
  let found = $state<Checked | null>(null);
  let problem = $state<string | null>(null);
  let busy = $state(false);
  let asked = 0;

  const read = $derived(seedsOf(seeds));

  function component(): Component | null {
    const weights = given.models.find((m) => m.name === model)?.weights;
    if (!configuration || !weights || typeof read === "string") return null;
    return { kind: "judge", skeleton: configuration, model: weights, seeds: read, fill: "text@1" } as never;
  }

  $effect(() => {
    const sent = component();
    if (sent === null) return;
    const at = ++asked;
    const timer = setTimeout(async () => {
      const got = await checked(sent);
      if (at === asked) found = got;
    }, 350);
    return () => clearTimeout(timer);
  });

  async function save(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    const sent = component();
    if (sent === null || !name.trim()) return;
    busy = true;
    const got = await api.POST("/api/threads", { body: { component: sent, name: name.trim() } });
    busy = false;
    if (!got.data) {
      problem = why(got.error);
      return;
    }
    const from = given.judging.find((j) => j.digest === configuration);
    made({
      digest: got.data.head.digest,
      thread: got.data.id,
      name: got.data.name ?? name.trim(),
      owner: got.data.owner,
      configuration: from?.name ?? "",
      model,
      seeds: typeof read === "string" ? [] : read,
      output_schema: from?.output_schema ?? null,
    });
  }
</script>

<form class="space-y-2 rounded-lg border border-dashed border-border p-2.5" onsubmit={save} aria-label="A new judge">
  <p class="font-medium">A new judge</p>
  <div class="grid gap-2 sm:grid-cols-2">
    <label class="grid gap-1"><span class="text-muted-foreground">Name</span><input class={FIELD} bind:value={name} /></label>
    <label class="grid gap-1"
      ><span class="text-muted-foreground">Its request, a judge configuration</span>
      <select class={FIELD} bind:value={configuration}>
        {#each given.judging as j (j.thread)}<option value={j.digest}>{(j.owner && j.owner !== me ? `${j.owner}/` : "") + j.name}</option>{/each}
      </select></label
    >
    <label class="grid gap-1"
      ><span class="text-muted-foreground">Asked under the model</span>
      <select class={FIELD} bind:value={model}>
        {#each given.models as m (m.name)}<option value={m.name}>{m.name}</option>{/each}
      </select></label
    >
    <label class="grid gap-1"
      ><span class="text-muted-foreground">Seeds, a call each</span><input class="{FIELD} font-mono" bind:value={seeds} /></label
    >
  </div>
  {#if typeof read === "string"}<p class="text-destructive">{read}</p>{/if}
  <Findings {found} />
  {#if problem}<p class="text-destructive">{problem}</p>{/if}
  <div class="flex gap-2">
    <button
      class="rounded-md bg-primary px-3 py-1 font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
      disabled={busy || !name.trim() || component() === null || (found !== null && "problem" in found)}
      >Save the judge</button
    >
    <button type="button" class="rounded-md border border-border px-3 py-1 hover:bg-muted" onclick={left}>Not now</button>
  </div>
</form>
