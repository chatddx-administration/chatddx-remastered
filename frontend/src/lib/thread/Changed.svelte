<script lang="ts">
  import { t, tp } from "$lib/locale";
  import { changes } from "./diff";

  let { before, after }: { before: unknown; after: unknown } = $props();
  const found = $derived(changes(before, after));

  function shown(value: unknown): string {
    return typeof value === "string" ? value : JSON.stringify(value);
  }
</script>

{#if found.length === 0}
  <p class="text-sm text-muted-foreground">{t("Nothing of what it holds; only what is said of it, or its labels.")}</p>
{:else}
  <ul class="space-y-2 text-sm">
    {#each found as change (change.path)}
      <li>
        <span class="font-mono text-xs text-muted-foreground">{change.path}</span>
        {#if change.was === "added"}
          <span class="text-success">{tp("change", "added")}</span>
          <div class="mt-0.5 whitespace-pre-wrap break-words font-mono text-xs">{shown(change.after)}</div>
        {:else if change.was === "removed"}
          <span class="text-destructive">{tp("change", "removed")}</span>
          <div class="mt-0.5 whitespace-pre-wrap break-words font-mono text-xs line-through">
            {shown(change.before)}
          </div>
        {:else if change.words}
          <div class="mt-0.5 whitespace-pre-wrap break-words">
            {#each change.words as w, i (i)}{#if w.added}<ins class="bg-success/15 text-success no-underline"
                  >{w.value}</ins
                >{:else if w.removed}<del class="bg-destructive/10 text-destructive">{w.value}</del
                >{:else}{w.value}{/if}{/each}
          </div>
        {:else}
          <div class="mt-0.5 font-mono text-xs">
            <del class="bg-destructive/10 text-destructive">{shown(change.before)}</del>
            → <ins class="bg-success/15 text-success no-underline">{shown(change.after)}</ins>
          </div>
        {/if}
      </li>
    {/each}
  </ul>
{/if}
