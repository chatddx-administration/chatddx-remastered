<script lang="ts">
  import { onMount, untrack } from "svelte";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import { t } from "$lib/locale";
  import { watch } from "$lib/runs/events";
  import { begun, fold } from "$lib/runs/progress";
  import { runTitle } from "$lib/runs/titles";
  import type { Schemas } from "$lib/api/client";
  import { doing } from "./review";

  let { run, titled, done }: { run: string; titled: Schemas["Titled"]; done: () => void } = $props();
  const given = untrack(() => ({ run, titled, done }));

  let progress = $state(begun());
  let lost = $state<string | null>(null);
  const said = $derived(lost ?? doing(progress));

  onMount(() => {
    watch(given.run, (name, data) => fold(progress, name, data))
      .then(() => given.done())
      .catch((e: unknown) => {
        lost = e instanceof Error ? e.message : String(e);
      });
  });
</script>

<div class="flex flex-wrap items-center gap-x-2" aria-live="polite">
  {#if !progress.done && !lost}<LoaderCircleIcon class="size-3.5 animate-spin text-muted-foreground" aria-hidden="true" />{/if}
  <a class="text-primary hover:underline" href="/runs/{given.run}">{runTitle(given.titled)}</a>
  <span class={lost ? "text-destructive" : "text-muted-foreground"}>{said}</span>
  {#if progress.done}<a class="text-primary hover:underline" href={location.pathname + location.search}>{t("Show it")}</a>{/if}
</div>
