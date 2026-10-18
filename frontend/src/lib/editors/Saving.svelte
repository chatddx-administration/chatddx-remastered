<script lang="ts">
  import { untrack } from "svelte";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { type Component, type Editing, type Labelled, type Saved, said, saved } from "./writing";

  let {
    editing,
    component,
    unchanged,
    blocked,
    after,
    to,
    labels,
  }: {
    editing: Editing;
    component: () => Component;
    unchanged: boolean;
    blocked: boolean;
    after?: (cases: number) => string;
    to?: (saved: Extract<Saved, { to: string }>) => string;
    labels?: () => Labelled;
  } = $props();

  let name = $state(untrack(() => editing.name));
  let head = $state(untrack(() => editing.head));
  let busy = $state(false);
  let problem = $state<string | null>(null);
  let note = $state<string | null>(null);

  const nameless = $derived(editing.mode !== "edit" && !name.trim());

  async function save(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    busy = true;
    problem = null;
    const got = await saved({ ...editing, head }, name, component(), labels?.());
    busy = false;
    if ("to" in got) {
      const where = to ? to(got) : got.to;
      const cases = Object.keys(got.cases).length;
      if (cases && after) {
        note = after(cases);
        setTimeout(() => location.assign(where), 2500);
      } else location.assign(where);
      return;
    }
    problem = got.problem;
    if (got.moved !== null) {
      head = got.moved;
      problem += ". What you typed is kept: save again to make it the version after the latest.";
    }
  }
</script>

<form class="mt-4 space-y-3" onsubmit={save}>
  {#if editing.mode !== "edit"}
    <label class="grid max-w-md gap-1 text-sm">
      <span class="font-medium">Name</span>
      <Input bind:value={name} autocomplete="off" />
    </label>
  {/if}
  <p class="text-sm" aria-live="polite">{said(editing, name, unchanged)}</p>
  {#if problem}<p class="text-sm text-destructive">{problem}</p>{/if}
  {#if note}<p class="text-sm text-success">{note}</p>{/if}
  <Button type="submit" disabled={busy || blocked || nameless || (editing.mode === "edit" && unchanged)}>
    {#if busy}<LoaderCircleIcon class="animate-spin" />{/if}
    Save
  </Button>
</form>
