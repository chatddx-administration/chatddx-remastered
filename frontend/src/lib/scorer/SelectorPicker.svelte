<script lang="ts">
  import { type Choice, chosen } from "./selectors";

  let { choices, value, set, label }: { choices: Choice[]; value: string; set: (v: string) => void; label: string } =
    $props();

  const picked = $derived(chosen(value, choices));
  let typing = $state(false);
  const typed = $derived(typing || picked === undefined);
  const field = "h-8 rounded-md border border-input bg-transparent px-2";
</script>

<div class="grid content-start gap-1">
  <span class="text-muted-foreground" aria-hidden="true">{label}</span>
  <select
      aria-label={label}
      class="{field} min-w-0"
      value={typed ? "typed" : picked?.selector}
      onchange={(e) => {
        const now = e.currentTarget.value;
        typing = now === "typed";
        if (!typing) set(now);
      }}
    >
      {#each choices as c (c.selector)}<option value={c.selector}>{c.label}</option>{/each}
      <option value="typed">typed…</option>
    </select>
  {#if typed}
    <input
      class="{field} font-mono text-xs"
      aria-label="{label}, typed"
      {value}
      oninput={(e) => set(e.currentTarget.value)}
    />
  {/if}
</div>
