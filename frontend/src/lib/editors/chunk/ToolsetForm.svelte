<script lang="ts">
  import { type Body, FIELD, numberOf, type Tool, typedOf } from "../chunks";

  let { body, set, tools }: { body: Body; set: (body: Body) => void; tools: Tool[] } = $props();

  const held = $derived((Array.isArray(body.tools) ? body.tools : []) as string[]);
  const offered = $derived([...tools, ...held.filter((d) => !tools.some((t) => t.digest === d)).map((d) => ({ digest: d, name: `${d.slice(7, 19)}, an earlier version` }))]);

  function picked(digest: string, on: boolean): void {
    set({ ...body, tools: on ? [...held, digest] : held.filter((d) => d !== digest) });
  }
</script>

<div class="space-y-3 text-sm">
  <fieldset class="space-y-1">
    <legend class="font-medium">Its tools</legend>
    {#each offered as t (t.digest)}
      <label class="flex items-center gap-2"><input type="checkbox" checked={held.includes(t.digest)} onchange={(e) => picked(t.digest, e.currentTarget.checked)} /> {t.name}</label>
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
