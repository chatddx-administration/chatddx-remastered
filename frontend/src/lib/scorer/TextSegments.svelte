<script lang="ts">
  import { editable, INSERTS, isInsert, isSlot, merged, type Seg, SLOTS } from "./texts";

  let {
    segs,
    set,
    slots = [],
    inserts = [],
    label,
  }: { segs: Seg[]; set: (segs: Seg[]) => void; slots?: string[]; inserts?: string[]; label: string } = $props();

  const shown = $derived(editable(segs));
  const missing = $derived([
    ...slots.filter((s) => !segs.some((g) => isSlot(g) && g.slot === s)).map((s) => ({ slot: s }) as Seg),
    ...inserts.filter((i) => !segs.some((g) => isInsert(g) && g.insert === i)).map((i) => ({ insert: i }) as Seg),
  ]);

  function named(s: Seg): string {
    if (isSlot(s)) return SLOTS[s.slot] ?? s.slot;
    if (isInsert(s)) return INSERTS[s.insert] ?? s.insert;
    return "";
  }

  function typed(at: number, text: string): void {
    set(merged(shown.map((s, i) => (i === at ? text : s))));
  }
</script>

<div class="space-y-1" role="group" aria-label={label}>
  <p class="font-medium">{label}</p>
  {#each shown as s, at (at)}
    {#if typeof s === "string"}
      <textarea
        class="w-full rounded-md border border-input bg-transparent px-2 py-1 [field-sizing:content]"
        rows="1"
        aria-label="{label}, text {Math.floor(at / 2) + 1}"
        value={s}
        oninput={(e) => typed(at, e.currentTarget.value)}
      ></textarea>
    {:else}
      <span class="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-primary">
        ‹{named(s)}›
        <button
          type="button"
          class="rounded-full px-1 hover:bg-primary/20"
          aria-label="Leave out {named(s)}"
          onclick={() => set(merged(shown.filter((_, i) => i !== at)))}>×</button
        >
      </span>
    {/if}
  {/each}
  {#if missing.length}
    <div class="flex flex-wrap gap-1">
      {#each missing as m, i (i)}
        <button
          type="button"
          class="rounded-full border border-dashed border-border px-2 py-0.5 text-muted-foreground hover:bg-muted"
          onclick={() => set(merged([...segs, m]))}>+ ‹{named(m)}›</button
        >
      {/each}
    </div>
  {/if}
</div>
