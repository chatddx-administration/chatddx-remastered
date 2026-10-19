<script lang="ts">
  import { untrack } from "svelte";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import { api, why } from "$lib/api/client";
  import { Button } from "$lib/components/ui/button";
  import Findings from "$lib/editors/Findings.svelte";
  import { checked } from "$lib/editors/writing";
  import Entry from "./Entry.svelte";
  import type { Live } from "./live.svelte";
  import { saved } from "./saving";
  import {
    closest,
    entriesInto,
    entriesOf,
    places,
    savedTo,
    textsOf,
    type Translating,
    translationsOf,
    type Unchanged,
    unusedOf,
  } from "./translate";

  let { translating, live }: { translating: Translating; live: Live } = $props();
  const given = untrack(() => translating);
  const now = untrack(() => live);

  const leftover = unusedOf(entriesInto(given.translations, given.into), given.texts);
  const unused = Object.keys(leftover);
  // Compromise: a chunk serving several configurations holds many texts another uses, so they come folded.
  const FEW = 5;

  const kept = $derived(
    Object.fromEntries(Object.entries(leftover).filter(([text]) => !now.left.includes(text))),
  );
  const entries = $derived(entriesOf(now.typed, kept));
  const body = $derived(translationsOf(given.translations, given.into, entries));
  const missing = $derived(textsOf(given.texts).filter((text) => !now.typed[text]).length);
  const digest = $derived(now.found && "digest" in now.found ? now.found.digest : null);
  const unchanged: Unchanged = $derived({
    translations: digest !== null && digest === given.translations?.digest,
    configuration: digest !== null && digest === given.configuration.translations,
  });

  let busy = $state(false);
  let problem = $state<string | null>(null);

  $effect(() => {
    const sent = JSON.stringify(entries);
    const held = body;
    const timer = setTimeout(async () => {
      now.asked = sent;
      const [found, translated] = await Promise.all([
        held ? checked(held) : Promise.resolve(null),
        api.POST("/api/threads/{thread}/translation", {
          params: { path: { thread: given.configuration.thread } },
          body: { into: given.into, head: given.head, entries: JSON.parse(sent) as Record<string, string> },
        }),
      ]);
      if (now.asked !== sent) return;
      now.found = held ? found : { problem: "Translations hold at least one language: write a translation to save them." };
      if (translated.data) now.request = translated.data;
      else now.found = { problem: why(translated.error) };
    }, 400);
    return () => clearTimeout(timer);
  });

  function started(text: string, translation: string): void {
    now.typed[text] = translation;
    if (!now.checking.includes(text)) now.checking.push(text);
  }

  function edited(text: string): void {
    now.checking = now.checking.filter((t) => t !== text);
  }

  function leave(text: string): void {
    now.left = now.left.includes(text) ? now.left.filter((t) => t !== text) : [...now.left, text];
  }

  async function save(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    if (!body) return;
    busy = true;
    problem = null;
    const got = await saved(given.translations, given.configuration, body, given.into, unchanged);
    busy = false;
    if ("to" in got) location.assign(got.to);
    else problem = `${got.problem}. What you typed is kept here.`;
  }
</script>

<div class="mb-2 grid grid-cols-2 gap-3 text-[0.7rem] uppercase tracking-wide text-muted-foreground">
  <span>Written in {given.language ?? "no language known"}</span>
  <span>Into {given.into} <span class="normal-case {missing ? 'text-warning' : 'text-success'}">· {missing ? `${missing} missing` : "every text translated"}</span></span>
</div>
{#each given.texts as [part, texts] (part)}
  {@const held = given.parts[part]}
  <section class="mb-4">
    <h2 class="mb-1.5 text-xs font-medium text-muted-foreground">
      {part.replaceAll("_", " ")} ·
      {#if held?.thread}<a class="text-primary hover:underline" href="/threads/{held.thread}">{held.title}</a>{:else}{held?.title}{/if}
    </h2>
    {#each texts as text (text)}
      {@const offer = now.typed[text] ? null : closest(text, kept)}
      <Entry
        {text}
        bind:value={now.typed[text] as string}
        places={places(text, part, given.bodies).filter(Boolean)}
        oninput={() => edited(text)}
      >
        {#if offer}
          <div class="mt-1 rounded-md bg-muted/50 p-2 text-xs">
            <p class="text-muted-foreground">An unused entry of a text much like it:</p>
            <p class="mt-0.5 whitespace-pre-wrap break-words">{#each offer.words as w, i (i)}{#if w.added}<ins class="bg-success/15 text-success no-underline">{w.value}</ins>{:else if w.removed}<del class="bg-destructive/10 text-destructive">{w.value}</del>{:else}{w.value}{/if}{/each}</p>
            <p class="mt-0.5 whitespace-pre-wrap break-words">→ {offer.translation}</p>
            <button type="button" class="mt-1 text-primary hover:underline" onclick={() => started(text, offer.translation)}>Start from its translation</button>
          </div>
        {/if}
        {#if now.checking.includes(text)}
          <p class="mt-0.5 text-xs text-warning">Started from a similar text's translation: check it against this one.</p>
        {/if}
      </Entry>
    {/each}
  </section>
{/each}
{#if unused.length}
  <details open={unused.length <= FEW}>
    <summary class="mb-1.5 cursor-pointer text-xs font-medium text-muted-foreground">
      Not used by it: {unused.length}, of a text it doesn't hold; kept unless left out, as another configuration may use them
    </summary>
    {#each unused as text (text)}
      {@const left = now.left.includes(text)}
      <Entry {text} value={leftover[text] ?? ""} {left}>
        <button type="button" class="mt-0.5 text-xs text-primary hover:underline" onclick={() => leave(text)}>
          {left ? "Keep it" : "Leave it out"}
        </button>
      </Entry>
    {/each}
  </details>
{/if}

<form class="mt-5 space-y-2 border-t border-border pt-4" onsubmit={save}>
  <Findings found={now.found} />
  <p class="text-sm" aria-live="polite">
    {now.found === null ? "Checking…" : savedTo(given.translations, given.configuration, unchanged)}
  </p>
  {#if problem}<p class="text-sm text-destructive">{problem}</p>{/if}
  <Button
    type="submit"
    disabled={busy ||
      !body ||
      now.found === null ||
      "problem" in now.found ||
      (unchanged.translations && unchanged.configuration)}
  >
    {#if busy}<LoaderCircleIcon class="animate-spin" />{/if}
    Save
  </Button>
</form>
