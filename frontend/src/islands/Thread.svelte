<script lang="ts" module>
  import type { Schemas } from "$lib/api/client";

  import type { AppendixEditing } from "$lib/editors/AppendixEditor.svelte";
  import type { ChunkEditing } from "$lib/editors/ChunkEditor.svelte";
  import type { ExpectationEditing } from "$lib/editors/ExpectationEditor.svelte";
  import type { TranslationsEditing } from "$lib/translate/TranslationsEditor.svelte";

  export type Version = Schemas["Edit"] & { body: Record<string, unknown> };
  export type Held = {
    word: string;
    versions: Version[];
    titles: Record<string, string>;
    editor: AppendixEditing | ChunkEditing | ExpectationEditing | TranslationsEditing | null;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import AppendixEditor from "$lib/editors/AppendixEditor.svelte";
  import ChunkEditor from "$lib/editors/ChunkEditor.svelte";
  import ExpectationEditor from "$lib/editors/ExpectationEditor.svelte";
  import Changed from "$lib/thread/Changed.svelte";
  import Holds from "$lib/thread/Holds.svelte";
  import TranslationsEditor from "$lib/translate/TranslationsEditor.svelte";

  let { held }: { held: Held } = $props();
  const given = untrack(() => held);
  const versions = given.versions;

  let at = $state(versions.length - 1);
  const shown = $derived(versions[at]);
  const before = $derived(at > 0 ? versions[at - 1] : undefined);

  function when(stamp: string): string {
    return stamp.slice(0, 16).replace("T", " ");
  }
</script>

<section class="glass-card mb-6 rounded-2xl p-5 sm:p-6">
  <div class="mb-4 flex flex-wrap items-center gap-3">
    <h2 class="text-lg font-semibold">What it holds</h2>
    <nav class="flex items-center gap-2 text-sm" aria-label="Versions">
      <button
        type="button"
        class="rounded-md border border-border px-2 py-0.5 hover:bg-muted disabled:opacity-40"
        disabled={at === 0}
        aria-label="The version before"
        onclick={() => (at -= 1)}>◀</button
      >
      <span class="font-medium">Version {at + 1} of {versions.length}</span>
      <button
        type="button"
        class="rounded-md border border-border px-2 py-0.5 hover:bg-muted disabled:opacity-40"
        disabled={at === versions.length - 1}
        aria-label="The version after"
        onclick={() => (at += 1)}>▶</button
      >
    </nav>
    {#if shown}
      <span class="text-sm text-muted-foreground">{when(shown.at)}, {shown.by}</span>
      <span class="font-mono text-xs text-muted-foreground">{shown.digest.slice(7, 19)}</span>
    {/if}
  </div>
  {#if shown}
    <Holds body={shown.body} titles={given.titles} />
    <h3 class="mt-6 mb-2 text-sm font-medium">What this version changed</h3>
    {#if before}
      <Changed before={before.body} after={shown.body} />
    {:else}
      <p class="text-sm text-muted-foreground">It is the first.</p>
    {/if}
  {/if}
</section>

{#if given.editor}
  {@const head = versions.at(-1)?.digest ?? null}
  <section id="edit" class="glass-card mb-6 rounded-2xl p-5 sm:p-6">
    <h2 class="mb-1 text-lg font-semibold">{given.editor.mode === "edit" ? "Change it" : "Make it yours"}</h2>
    <p class="mb-4 text-sm text-muted-foreground">
      {given.editor.mode === "edit"
        ? "From its latest version: saving makes the next."
        : "From its latest version, as a fork of your own."}
    </p>
    {#if given.editor.kind === "appendix"}
      <AppendixEditor editor={given.editor} digest={head} />
    {:else if given.editor.kind === "expectation"}
      <ExpectationEditor editor={given.editor} digest={head} />
    {:else if given.editor.kind === "translations"}
      <TranslationsEditor editor={given.editor} digest={head} />
    {:else if given.editor.kind === "chunk"}
      <ChunkEditor editor={given.editor} digest={head} />
    {/if}
  </section>
{/if}
