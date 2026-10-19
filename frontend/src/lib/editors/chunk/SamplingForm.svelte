<script lang="ts">
  import { type Body, FIELD, numberOf, SAMPLED, stopsOf, typedOf } from "../chunks";

  let { body, set }: { body: Body; set: (body: Body) => void } = $props();

  const stops = $derived((Array.isArray(body.stop) ? body.stop : []) as string[]);
</script>

<div class="space-y-3 text-sm">
  <label class="flex items-center gap-2"
    ><input type="checkbox" checked={body.recommended === true} onchange={(e) => set({ ...body, recommended: e.currentTarget.checked })} />
    <span>Start from the sampling the model's makers recommend, with what is set below over it</span></label
  >
  <div class="grid gap-2 sm:grid-cols-4">
    {#each SAMPLED as key (key)}
      <label class="grid gap-1"
        ><span class="font-mono text-xs text-muted-foreground">{key}</span>
        <input class="{FIELD} font-mono" inputmode="decimal" value={typedOf(body[key])} oninput={(e) => set({ ...body, [key]: numberOf(e.currentTarget.value) })} /></label
      >
    {/each}
    <label class="grid gap-1"
      ><span class="font-mono text-xs text-muted-foreground">max output tokens</span>
      <input
        class="{FIELD} font-mono"
        inputmode="numeric"
        value={typedOf(body.max_output_tokens)}
        oninput={(e) => set({ ...body, max_output_tokens: numberOf(e.currentTarget.value) })}
      /></label
    >
    <label class="grid gap-1 sm:col-span-2"
      ><span class="text-xs text-muted-foreground">sent as</span>
      <select
        class="{FIELD} font-mono"
        value={body.max_tokens_key ?? "max_completion_tokens"}
        onchange={(e) => set({ ...body, max_tokens_key: e.currentTarget.value })}
      >
        <option value="max_completion_tokens">max_completion_tokens</option>
        <option value="max_tokens">max_tokens</option>
      </select></label
    >
  </div>
  <label class="grid gap-1"
    ><span class="text-muted-foreground">Stop sequences, one a line</span>
    <textarea
      class="rounded-md border border-input bg-transparent px-2 py-1 font-mono text-xs [field-sizing:content]"
      rows="2"
      value={stops.join("\n")}
      oninput={(e) => set({ ...body, stop: stopsOf(e.currentTarget.value) })}
    ></textarea></label
  >
  <p class="text-xs text-muted-foreground">A temperature of 0 is greedy, and leaves top_p, top_k and min_p out.</p>
</div>
