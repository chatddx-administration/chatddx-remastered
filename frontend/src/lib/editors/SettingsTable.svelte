<script lang="ts">
  import { untrack } from "svelte";
  import { FIELD } from "$lib/utils";
  import { type Row, rowsOf, settingsOf } from "./chunks";

  let {
    settings,
    set,
    label,
  }: { settings: unknown; set: (settings: Record<string, unknown>) => void; label: string } = $props();

  let rows = $state<Row[]>(untrack(() => rowsOf(settings)));

  function changed(next: Row[]): void {
    rows = next;
    set(settingsOf(next));
  }
</script>

<div class="space-y-1" role="group" aria-label={label}>
  <p class="font-medium">{label}</p>
  {#each rows as row, at (at)}
    <div class="flex gap-2">
      <input
        class="{FIELD} w-48 font-mono"
        aria-label="{label}, key {at + 1}"
        value={row.key}
        oninput={(e) => changed(rows.map((r, i) => (i === at ? { ...r, key: e.currentTarget.value } : r)))}
      />
      <input
        class="{FIELD} min-w-0 flex-1 font-mono"
        aria-label="{label}, value {at + 1}"
        value={row.value}
        oninput={(e) => changed(rows.map((r, i) => (i === at ? { ...r, value: e.currentTarget.value } : r)))}
      />
      <button
        type="button"
        class="rounded-md px-2 text-muted-foreground hover:bg-muted"
        aria-label="Leave out {row.key || `setting ${at + 1}`}"
        onclick={() => changed(rows.filter((_, i) => i !== at))}>×</button
      >
    </div>
  {/each}
  <button
    type="button"
    class="rounded-md border border-dashed border-border px-2 py-0.5 text-muted-foreground hover:bg-muted"
    onclick={() => changed([...rows, { key: "", value: "" }])}>+ a setting</button
  >
  <p class="text-xs text-muted-foreground">A value is read as JSON where it is JSON, else as a text.</p>
</div>
