<script lang="ts" module>
  import type { Mode } from "$lib/editors/writing";
  import type { Entries } from "./translate";

  export type TranslationsEditing = {
    kind: "translations";
    mode: Mode;
    thread?: number;
    head?: number;
    name: string;
    into: Record<string, Entries>;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import Findings from "$lib/editors/Findings.svelte";
  import Saving from "$lib/editors/Saving.svelte";
  import { type Checked, checked, type Component } from "$lib/editors/writing";
  import Entry from "./Entry.svelte";
  import { type Left, leftOut } from "./translate";

  let { editor, digest = null }: { editor: TranslationsEditing; digest?: string | null } = $props();
  const given = untrack(() => editor);
  const languages = Object.keys(given.into);

  let into = $state(languages[0] ?? "");
  const typed = $state(structuredClone(given.into));
  let left = $state<Left>({});
  let found = $state<Checked | null>(null);
  let asked = 0;

  function component(): Component {
    return { kind: "chunk.translations", into: leftOut(typed, left) };
  }

  function leave(text: string): void {
    const now = left[into] ?? [];
    left[into] = now.includes(text) ? now.filter((t) => t !== text) : [...now, text];
  }

  $effect(() => {
    void JSON.stringify([typed, left]);
    const sent = ++asked;
    const timer = setTimeout(async () => {
      const got = await checked(component());
      if (sent === asked) found = got;
    }, 350);
    return () => clearTimeout(timer);
  });
</script>

<div class="space-y-3">
  <p class="text-sm text-muted-foreground">
    Each entry is a text exactly as a chunk holds it and its translation. Which texts a configuration still lacks is said
    on its <a class="text-primary hover:underline" href="/translate">Translate</a> page.
  </p>
  {#if languages.length > 1}
    <nav class="flex flex-wrap gap-1 text-xs" aria-label="Languages">
      {#each languages as language (language)}
        <button
          type="button"
          aria-current={language === into ? "page" : undefined}
          class="rounded-full border px-2.5 py-0.5 {language === into
            ? 'border-primary/30 bg-primary/10 text-primary'
            : 'border-border text-muted-foreground hover:text-foreground'}"
          onclick={() => (into = language)}>{language}</button
        >
      {/each}
    </nav>
  {/if}
  <div>
    {#each Object.keys(given.into[into] ?? {}) as text (`${into}\u0000${text}`)}
      {@const out = (left[into] ?? []).includes(text)}
      <Entry {text} bind:value={(typed[into] as Entries)[text] as string} left={out}>
        <button type="button" class="mt-0.5 text-xs text-primary hover:underline" onclick={() => leave(text)}>
          {out ? "Keep it" : "Leave it out"}
        </button>
      </Entry>
    {/each}
  </div>
  <Findings {found} />
  <Saving
    editing={given}
    {component}
    unchanged={found !== null && "digest" in found && found.digest === digest}
    blocked={found !== null && "problem" in found}
  />
</div>
