<script lang="ts">
  import { t } from "$lib/locale";

  let {
    value,
    set,
    label,
    rows = 4,
  }: { value: unknown; set: (value: unknown) => void; label: string; rows?: number } = $props();

  let typed = $state<string | null>(null);
  let broken = $state(false);
  const shown = $derived(typed ?? JSON.stringify(value ?? {}, null, 2));

  function input(text: string): void {
    typed = text;
    try {
      const parsed: unknown = JSON.parse(text);
      broken = false;
      set(parsed);
    } catch {
      broken = true;
    }
  }
</script>

<div class="grid gap-1">
  <textarea
    class="w-full rounded-md border bg-transparent px-2 py-1 font-mono text-xs {broken
      ? 'border-destructive'
      : 'border-input'}"
    {rows}
    aria-label={label}
    aria-invalid={broken}
    value={shown}
    oninput={(e) => input(e.currentTarget.value)}
    onblur={() => {
      if (!broken) typed = null;
    }}></textarea>
  {#if broken}<p class="text-xs text-destructive">{t("Not JSON yet: it is kept as it was till it is.")}</p>{/if}
</div>
