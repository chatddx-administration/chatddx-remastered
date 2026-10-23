<script lang="ts">
  import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
  import ChevronUpIcon from "@lucide/svelte/icons/chevron-up";
  import SirenIcon from "@lucide/svelte/icons/siren";
  import TrendingUpIcon from "@lucide/svelte/icons/trending-up";
  import { Badge } from "$lib/components/ui/badge";
  import { t, tp } from "$lib/locale";
  import { cn } from "$lib/utils";
  import type { Diagnosis, Probability } from "./types";

  let { diagnosis, index }: { diagnosis: Diagnosis; index: number } = $props();

  let expanded = $state(false);

  const PROBABILITY: Record<Probability, { badge: string; bar: string; label: string }> = {
    high: {
      badge: "border-destructive/30 bg-destructive/10 text-destructive",
      bar: "bg-gradient-to-r from-destructive to-destructive/80",
      label: tp("probability", "High"),
    },
    medium: {
      badge: "border-warning/30 bg-warning/10 text-warning",
      bar: "bg-gradient-to-r from-warning to-warning/80",
      label: tp("probability", "Medium"),
    },
    low: {
      badge: "border-border bg-muted text-muted-foreground",
      bar: "bg-gradient-to-r from-muted-foreground/50 to-muted-foreground/30",
      label: tp("probability", "Low"),
    },
  };

  const shown = $derived(PROBABILITY[diagnosis.probability ?? "low"] ?? PROBABILITY.low);
</script>

<div class="group animate-slide-up" style:animation-delay="{index * 80}ms">
  <div
    class="pane overflow-hidden rounded-2xl transition-all duration-300 hover:shadow-2xl hover:shadow-primary/10"
  >
    <div class={cn("h-1", shown.bar)}></div>
    <button
      type="button"
      class="w-full p-5 text-left enabled:cursor-pointer"
      disabled={!diagnosis.short_rationale}
      aria-expanded={expanded}
      onclick={() => (expanded = !expanded)}
    >
      <div class="flex items-start justify-between gap-4">
        <div class="min-w-0 flex-1">
          <div class="mb-2 flex items-center gap-3">
            <span
              class="flex size-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 font-display text-sm font-bold text-primary"
            >
              {index + 1}
            </span>
            <h3
              class="text-lg font-semibold text-foreground transition-colors group-hover:text-primary"
            >
              {diagnosis.diagnosis}
            </h3>
          </div>
          <div class="ml-11 flex flex-wrap items-center gap-2">
            <Badge variant="outline" class={shown.badge}>
              <TrendingUpIcon />
              {shown.label}
            </Badge>
            {#if diagnosis.critical}
              <Badge variant="outline" class="border-destructive/30 bg-destructive/10 text-destructive">
                <SirenIcon />
                {t("Critical")}
              </Badge>
            {/if}
          </div>
        </div>
        {#if diagnosis.short_rationale}
          <span class="rounded-xl p-2 text-muted-foreground transition-colors group-hover:text-foreground">
            {#if expanded}<ChevronUpIcon size={20} />{:else}<ChevronDownIcon size={20} />{/if}
          </span>
        {/if}
      </div>
    </button>
    {#if expanded && diagnosis.short_rationale}
      <div class="animate-fade-in border-t border-border/30 p-5">
        <p class="leading-relaxed text-muted-foreground">{diagnosis.short_rationale}</p>
      </div>
    {/if}
  </div>
</div>
