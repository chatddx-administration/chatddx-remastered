<script lang="ts">
  import { untrack } from "svelte";
  import type { Live } from "./live.svelte";
  import { marked, type Translating } from "./translate";

  let { translating, live }: { translating: Translating; live: Live } = $props();
  const given = untrack(() => translating);
  const now = untrack(() => live);

  const missing = $derived([...new Set(given.texts.filter((t) => !now.typed[t.text]).map((t) => t.text))]);
  const written = given.written.messages ?? [];
  const sent = $derived(now.request.messages ?? []);
  function rest(request: Translating["request"]): string {
    const { messages: _, ...others } = request;
    return JSON.stringify(others, null, 2);
  }
</script>

<p class="mb-3 text-xs text-muted-foreground">
  What it sends as written and into {given.into}, the case as a placeholder; a text without a translation goes as
  written, <mark class="rounded bg-warning/20 px-0.5 text-foreground">marked</mark>.
</p>
<div class="mb-1 grid grid-cols-2 gap-3 text-[0.7rem] uppercase tracking-wide text-muted-foreground">
  <span>As written</span><span>Into {given.into}</span>
</div>
{#each sent as message, i (i)}
  <div class="mb-2 rounded-lg bg-muted/40 p-2.5 text-sm">
    <div class="mb-1 text-xs font-medium text-muted-foreground">{message.role}</div>
    <div class="grid grid-cols-2 gap-3">
      <div class="whitespace-pre-wrap break-words text-muted-foreground">{written[i]?.content ?? ""}</div>
      <div class="whitespace-pre-wrap break-words">
        {#each marked(message.content, missing) as run, j (j)}{#if run.missing}<mark
              class="rounded bg-warning/20 px-0.5 text-foreground"
              title="not translated">{run.text}</mark
            >{:else}{run.text}{/if}{/each}
      </div>
    </div>
  </div>
{/each}
<details class="mt-3 text-sm">
  <summary class="cursor-pointer text-xs text-muted-foreground">The rest of the request</summary>
  <div class="mt-2 grid grid-cols-2 gap-3">
    <pre class="overflow-x-auto rounded-lg bg-muted/60 p-2 font-mono text-[0.7rem] leading-relaxed">{rest(given.written)}</pre>
    <pre class="overflow-x-auto rounded-lg bg-muted/60 p-2 font-mono text-[0.7rem] leading-relaxed">{rest(now.request)}</pre>
  </div>
</details>
