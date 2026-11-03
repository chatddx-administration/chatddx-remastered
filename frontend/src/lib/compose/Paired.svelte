<script lang="ts">
  import type { Snippet } from "svelte";
  import { t } from "$lib/locale";
  import { editable, INSERTS, isInsert, isSlot, merged, type Seg, SLOTS } from "$lib/scorer/texts";

  let {
    segs,
    was,
    set,
    label,
    said,
  }: {
    segs: Seg[];
    was: Seg[];
    set: (segs: Seg[]) => void;
    label: string;
    said: Snippet<[string, string | null]>;
  } = $props();

  const shown = $derived(editable(segs));
  const before = $derived(editable(was));

  function named(s: Seg): string {
    if (isSlot(s)) return SLOTS[s.slot] ?? s.slot;
    if (isInsert(s)) return INSERTS[s.insert] ?? s.insert;
    return "";
  }

  function typed(at: number, text: string): void {
    set(merged(shown.map((s, i) => (i === at ? text : s))));
  }

  function around(s: Seg, side: "before" | "after"): string {
    return isInsert(s) ? (s[side] ?? "") : "";
  }
</script>

<div class="space-y-2" role="group" aria-label={label}>
  {#each shown as s, at (at)}
    {@const then = before[at] ?? null}
    {#if typeof s === "string"}
      <div class="grid gap-2 @3xl:grid-cols-2">
        <textarea
          class="w-full rounded-md border border-input bg-transparent px-2 py-1 [field-sizing:content]"
          rows="1"
          aria-label={t("%(label)s, text %(n)s", { label, n: Math.floor(at / 2) + 1 })}
          value={s}
          oninput={(e) => typed(at, e.currentTarget.value)}></textarea>
        {#if s.trim()}{@render said(s, typeof then === "string" ? then : null)}{/if}
      </div>
    {:else}
      <div class="grid gap-2 @3xl:grid-cols-2">
        <span class="w-fit rounded-full bg-primary/10 px-2 py-0.5 text-primary">‹{named(s)}›</span>
        <span class="hidden w-fit rounded-full bg-primary/10 px-2 py-0.5 text-primary @3xl:inline" aria-hidden="true"
          >‹{named(s)}›</span
        >
      </div>
      {#each ["before", "after"] as const as side (side)}
        {@const text = around(s, side)}
        {#if text.trim()}
          <div class="grid gap-2 @3xl:grid-cols-2">
            <p class="whitespace-pre-wrap rounded-md bg-muted/40 px-2 py-1 text-muted-foreground">
              <span class="text-xs">{side === "before" ? t("Before it:") : t("After it:")}</span>
              {text}
            </p>
            {@render said(text, then === null ? null : around(then, side) || null)}
          </div>
        {/if}
      {/each}
    {/if}
  {/each}
</div>
