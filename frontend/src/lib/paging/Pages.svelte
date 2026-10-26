<script lang="ts">
  import { t, tp } from "$lib/locale";

  // Policy: a list in the browser knows its last page; one on the server only whether
  // there is a next.
  let {
    at,
    last,
    more = false,
    onpage,
  }: { at: number; last?: number; more?: boolean; onpage: (at: number) => void } = $props();
  const next = $derived(last === undefined ? more : at < last);
</script>

<nav aria-label={tp("of a list", "Pages")} class="mt-3 flex flex-wrap items-center gap-3 text-sm">
  <button type="button" class="view" disabled={at === 0} onclick={() => onpage(at - 1)}>{t("Previous")}</button>
  <span class="text-muted-foreground"
    >{last === undefined
      ? t("page %(at)s", { at: at + 1 })
      : t("page %(at)s of %(of)s", { at: at + 1, of: last + 1 })}</span
  >
  <button type="button" class="view" disabled={!next} onclick={() => onpage(at + 1)}>{t("Next")}</button>
</nav>
