<script lang="ts">
  import { untrack } from "svelte";
  import { places, type Translating, unlike, visible } from "./translate";

  let { translating }: { translating: Translating } = $props();
  const given = untrack(() => translating);

  const groups = (() => {
    const found = new Map<string, Translating["texts"]>();
    for (const t of given.texts) found.set(t.part, [...(found.get(t.part) ?? []), t]);
    return [...found.entries()];
  })();
  const unused = Object.entries(given.unused);
  // Compromise: a chunk serving several configurations holds many texts another uses, so they come folded.
  const FEW = 5;
</script>

<div class="mb-2 grid grid-cols-2 gap-3 text-[0.7rem] uppercase tracking-wide text-muted-foreground">
  <span>Written in {given.language ?? "no language known"}</span><span>Into {given.into}</span>
</div>
{#each groups as [part, texts] (part)}
  {@const held = given.parts[part]}
  <section class="mb-4">
    <h2 class="mb-1.5 text-xs font-medium text-muted-foreground">
      {part.replaceAll("_", " ")} ·
      {#if held?.thread}<a class="text-primary hover:underline" href="/threads/{held.thread}">{held.title}</a>{:else}{held?.title}{/if}
    </h2>
    {#each texts as t (t.text)}
      {@const where = places(t.text, part, given.bodies).filter(Boolean)}
      <div class="border-t border-border/60 py-1.5">
        {#if where.length}<div class="mb-0.5 text-[0.7rem] text-muted-foreground">{where.join("; ")}</div>{/if}
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div class="whitespace-pre-wrap break-words">{visible(t.text)}</div>
          {#if t.translation === null}
            <div class="rounded-md border border-dashed border-warning/50 px-2 text-warning">missing</div>
          {:else}
            <div>
              <div class="whitespace-pre-wrap break-words">{visible(t.translation)}</div>
              {#if unlike(t.text, t.translation)}
                <p class="mt-0.5 text-xs text-warning">Its leading or trailing whitespace isn't its source's.</p>
              {/if}
            </div>
          {/if}
        </div>
      </div>
    {/each}
  </section>
{/each}
{#if unused.length}
  <details open={unused.length <= FEW}>
    <summary class="mb-1.5 cursor-pointer text-xs font-medium text-muted-foreground">
      Not used by it: {unused.length}, of a text it doesn't hold
    </summary>
    {#each unused as [text, translation] (text)}
      <div class="grid grid-cols-2 gap-3 border-t border-border/60 py-1.5 text-sm text-muted-foreground">
        <div class="whitespace-pre-wrap break-words">{visible(text)}</div>
        <div class="whitespace-pre-wrap break-words">{visible(translation)}</div>
      </div>
    {/each}
  </details>
{/if}
