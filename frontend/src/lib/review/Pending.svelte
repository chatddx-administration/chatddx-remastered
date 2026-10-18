<script lang="ts">
  import { onMount, untrack } from "svelte";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import { watch } from "$lib/runs/events";
  import { begun, fold } from "$lib/runs/progress";
  import { doing } from "./review";

  let { run, described, done }: { run: string; described: string; done: () => void } = $props();
  const given = untrack(() => ({ run, described, done }));

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
  <a class="text-primary hover:underline" href="/runs/{given.run}">{given.described}</a>
  <span class={lost ? "text-destructive" : "text-muted-foreground"}>{said}</span>
  {#if progress.done}<a class="text-primary hover:underline" href={location.pathname + location.search}>Show it</a>{/if}
</div>
