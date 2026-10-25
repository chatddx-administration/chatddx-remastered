<script lang="ts">
  import { tp } from "$lib/locale";
  import { FIELD } from "$lib/utils";
  import { type Choice, chosen } from "./selectors";

  let { choices, value, set, label }: { choices: Choice[]; value: string; set: (v: string) => void; label: string } =
    $props();

  const picked = $derived(chosen(value, choices));
  let typing = $state(false);
  const typed = $derived(typing || picked === undefined);
</script>

<div class="grid content-start gap-1">
  <span class="text-muted-foreground" aria-hidden="true">{label}</span>
  <select
    aria-label={label}
    class="{FIELD} min-w-0"
    value={typed ? "typed" : picked?.selector}
    onchange={(e) => {
      const now = e.currentTarget.value;
      typing = now === "typed";
      if (!typing) set(now);
    }}
  >
    {#each choices as c (c.selector)}<option value={c.selector}>{c.label}</option>{/each}
    <option value="typed">{tp("a selector", "typed…")}</option>
  </select>
  {#if typed}
    <input
      class="{FIELD} font-mono text-xs"
      aria-label={tp("a selector", "%(label)s, typed", { label })}
      {value}
      oninput={(e) => set(e.currentTarget.value)}
    />
  {/if}
</div>
