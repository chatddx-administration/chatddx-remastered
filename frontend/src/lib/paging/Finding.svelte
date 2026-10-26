<script lang="ts">
  import { t } from "$lib/locale";

  // Policy: a list in the browser is found in as it is typed, and its Enter sends no form it
  // sits in; one on the server when its search is sent.
  let {
    query = $bindable(""),
    label = t("Find"),
    placeholder = t("Find by what it says"),
    shown,
    of,
    onchanged,
    onsent,
  }: {
    query?: string;
    label?: string;
    placeholder?: string;
    shown?: number;
    of?: number;
    onchanged?: () => void;
    onsent?: (query: string) => void;
  } = $props();
</script>

{#snippet searched()}
  <input
    type="search"
    bind:value={query}
    oninput={() => onchanged?.()}
    onkeydown={(pressed) => {
      if (!onsent && pressed.key === "Enter") pressed.preventDefault();
    }}
    aria-label={label}
    {placeholder}
    class="h-9 min-w-0 flex-1 basis-60 rounded-md border border-input bg-transparent px-2.5"
  />
  {#if onsent}<button>{t("Find")}</button>{/if}
  {#if shown !== undefined && of !== undefined}
    <span class="text-muted-foreground" aria-live="polite">{t("%(shown)s of %(of)s", { shown, of })}</span>
  {/if}
{/snippet}

{#if onsent}
  <form
    role="search"
    class="mb-3 flex flex-wrap items-center gap-2 text-sm"
    onsubmit={(sent) => {
      sent.preventDefault();
      onsent(query);
    }}
  >
    {@render searched()}
  </form>
{:else}
  <div role="search" class="mb-3 flex flex-wrap items-center gap-2 text-sm">{@render searched()}</div>
{/if}
