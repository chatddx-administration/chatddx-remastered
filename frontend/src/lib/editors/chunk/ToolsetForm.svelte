<script lang="ts">
  import type { Schemas } from "$lib/api/client";
  import { FIELD } from "$lib/utils";
  import { choicesOf } from "$lib/variation/logic";
  import { type Body, numberOf, typedOf } from "../chunks";

  let { body, set, tools, me }: { body: Body; set: (body: Body) => void; tools: Schemas["Thread"][]; me: string } = $props();

  const held = $derived((Array.isArray(body.tools) ? body.tools : []) as string[]);
  const offered = $derived(choicesOf(tools, me, held.map((digest) => ({ digest, title: null }))));

  function picked(digest: string, on: boolean): void {
    set({ ...body, tools: on ? [...held, digest] : held.filter((d) => d !== digest) });
  }
</script>

<div class="space-y-3 text-sm">
  <fieldset class="space-y-1">
    <legend class="font-medium">Its tools</legend>
    {#each offered as c (c.digest)}
      <label class="flex items-center gap-2"><input type="checkbox" checked={held.includes(c.digest)} onchange={(e) => picked(c.digest, e.currentTarget.checked)} /> {c.text}</label>
    {:else}
      <p class="text-muted-foreground">No tool you see: tools are shipped by developers.</p>
    {/each}
  </fieldset>
  <label class="grid gap-1"
    ><span class="text-muted-foreground">Its guidance, said where the instructions or the prompt insert it</span>
    <textarea
      class="rounded-md border border-input bg-transparent px-2 py-1 [field-sizing:content]"
      rows="2"
      value={typedOf(body.guidance)}
      oninput={(e) => set({ ...body, guidance: e.currentTarget.value || null })}
    ></textarea></label
  >
  <label class="grid max-w-xs gap-1"
    ><span class="text-muted-foreground">Tool rounds, at most</span>
    <input class="{FIELD} font-mono" inputmode="numeric" value={typedOf(body.max_rounds)} oninput={(e) => set({ ...body, max_rounds: numberOf(e.currentTarget.value) })} /></label
  >
</div>
