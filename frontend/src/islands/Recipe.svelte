<script lang="ts" module>
  import type { Schemas } from "$lib/api/client";

  export type RecipeProps = {
    purpose: string;
    me: string;
    optional: string[];
    choices: Record<string, Schemas["Thread"][]>;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import { api, why } from "$lib/api/client";
  import { Button } from "$lib/components/ui/button";
  import Findings from "$lib/editors/Findings.svelte";
  import { LAYOUT, type Layout, missing, recipeOf } from "$lib/editors/recipe";
  import { type Checked, written } from "$lib/editors/writing";
  import { FIELD } from "$lib/utils";
  import { choicesOf, type Part, PARTS } from "$lib/variation/logic";

  let { props }: { props: RecipeProps } = $props();
  const given = untrack(() => props);

  let picks = $state<Partial<Record<Part, string>>>({});
  let layout = $state<Layout>({ ...LAYOUT });
  let name = $state("");
  let found = $state<Checked | null>(null);
  let busy = $state(false);
  let problem = $state<string | null>(null);
  let asked = 0;

  const lacking = $derived(missing(picks, given.optional));
  const recipe = $derived(recipeOf(given.purpose, picks, layout));

  $effect(() => {
    const sent = ++asked;
    const now = JSON.parse(JSON.stringify(recipe)) as Record<string, never>;
    if (lacking.length) {
      found = null;
      return;
    }
    const timer = setTimeout(async () => {
      const got = await api.POST("/api/recipes/check", { body: now });
      if (sent === asked) found = got.data ? got.data : { problem: why(got.error) };
    }, 350);
    return () => clearTimeout(timer);
  });

  async function save(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    busy = true;
    problem = null;
    const got = await written({ thread: null, name: name.trim() }, { recipe });
    busy = false;
    if ("problem" in got) problem = got.problem;
    else location.assign(`/configurations/${got.thread}`);
  }
</script>

<form class="space-y-3 text-sm" onsubmit={save} aria-label="A new configuration">
  <div class="grid gap-2 sm:grid-cols-2">
    {#each PARTS as part (part)}
      <label class="grid gap-1"
        ><span class="text-muted-foreground">{part.replace("_", " ")}{given.optional.includes(part) ? "" : ", required"}</span>
        <select class={FIELD} value={picks[part] ?? ""} onchange={(e) => (picks = { ...picks, [part]: e.currentTarget.value || undefined })}>
          <option value="">{given.optional.includes(part) ? "none" : "pick one"}</option>
          {#each choicesOf(given.choices[part] ?? [], given.me, []) as c (c.digest)}<option value={c.digest}>{c.text}</option>{/each}
        </select></label
      >
    {/each}
  </div>
  <details>
    <summary class="cursor-pointer text-muted-foreground">How the appendices join the vignette</summary>
    <div class="mt-2 grid gap-2 sm:grid-cols-3">
      {#each ["before", "between", "after"] as const as at (at)}
        <label class="grid gap-1"
          ><span class="text-muted-foreground">{at}</span>
          <textarea class="rounded-md border border-input bg-transparent px-2 py-1 font-mono text-xs" rows="2" bind:value={layout[at]}></textarea></label
        >
      {/each}
    </div>
  </details>
  {#if lacking.length}
    <p class="text-muted-foreground">Pick its {lacking.map((p) => p.replace("_", " ")).join(", ")} to see what it makes.</p>
  {:else}
    {#if found && "digest" in found}<p class="text-muted-foreground">It compiles to <span class="font-mono text-xs">{found.digest.slice(7, 19)}</span>.</p>{/if}
    <Findings {found} />
  {/if}
  <label class="grid max-w-md gap-1"><span class="font-medium">Name</span><input class={FIELD} bind:value={name} autocomplete="off" /></label>
  <p aria-live="polite">{name.trim() ? `Writes “${name.trim()}”, a new configuration of your own.` : "Give it a name to save it."}</p>
  {#if problem}<p class="text-destructive">{problem}</p>{/if}
  <Button type="submit" disabled={busy || !name.trim() || found === null || "problem" in found}>
    {#if busy}<LoaderCircleIcon class="animate-spin" />{/if}
    Save
  </Button>
</form>
