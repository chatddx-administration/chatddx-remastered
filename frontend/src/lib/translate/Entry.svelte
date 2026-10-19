<script lang="ts">
  import type { Snippet } from "svelte";
  import { unlike, visible } from "./translate";

  let {
    text,
    value = $bindable(),
    places = [],
    left = false,
    oninput,
    children,
  }: {
    text: string;
    value: string;
    places?: string[];
    left?: boolean;
    oninput?: () => void;
    children?: Snippet;
  } = $props();

  const rows = $derived(Math.max(1, (value || text).split("\n").length));
</script>

<div class="border-t border-border/60 py-1.5">
  {#if places.length}<div class="mb-0.5 text-[0.7rem] text-muted-foreground">{places.join("; ")}</div>{/if}
  <div class="grid grid-cols-2 gap-3 text-sm">
    <div class="whitespace-pre-wrap break-words {left ? 'text-muted-foreground line-through' : ''}">{visible(text)}</div>
    <div>
      <textarea
        bind:value
        {rows}
        {oninput}
        disabled={left}
        aria-label="Its translation"
        class="block w-full resize-y rounded-md border field-sizing-content bg-transparent px-2 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 disabled:opacity-50 {value
          ? 'border-input'
          : 'border-dashed border-warning/60'}"
      ></textarea>
      {#if value && unlike(text, value)}
        <p class="mt-0.5 text-xs text-warning">Its leading or trailing whitespace isn't its source's.</p>
      {/if}
      {@render children?.()}
    </div>
  </div>
</div>
