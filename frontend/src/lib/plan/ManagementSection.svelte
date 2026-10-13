<script lang="ts">
  import ArrowRightIcon from "@lucide/svelte/icons/arrow-right";
  import BeakerIcon from "@lucide/svelte/icons/beaker";
  import PillIcon from "@lucide/svelte/icons/pill";
  import { Badge } from "$lib/components/ui/badge";
  import { groupLabs } from "./labs";
  import type { Management, Priority } from "./types";

  let { management }: { management: Management } = $props();

  const PRIORITY: Record<Priority, string> = {
    urgent: "border-destructive/30 bg-destructive/10 text-destructive",
    prompt: "border-warning/30 bg-warning/10 text-warning",
    elective: "border-border bg-muted text-muted-foreground",
  };
</script>

<section class="animate-slide-up space-y-4" style:animation-delay="200ms">
  <div class="flex items-center gap-3">
    <div class="rounded-xl bg-accent/10 p-2"><ArrowRightIcon class="size-5 text-accent" /></div>
    <h3 class="text-xl font-bold text-foreground">Management</h3>
  </div>

  {#if management.workup?.length}
    <div class="glass-card space-y-4 rounded-2xl p-5">
      <div class="flex items-center gap-3">
        <div class="rounded-xl bg-primary/10 p-2"><BeakerIcon class="size-5 text-primary" /></div>
        <h4 class="text-lg font-semibold text-foreground">Workup</h4>
      </div>
      <div class="space-y-4 text-sm">
        {#each management.workup as item, i (i)}
          {@const investigations = item.investigations ?? []}
          {@const labs = item.type?.toLowerCase().includes("lab") ? groupLabs(investigations) : null}
          <div>
            <div class="mb-1 flex items-center gap-2">
              <span class="font-semibold text-foreground">{item.type}</span>
              {#if item.priority}
                <Badge variant="outline" class={PRIORITY[item.priority]}>{item.priority}</Badge>
              {/if}
            </div>
            <div class="space-y-0.5">
              {#if labs?.grouped.length}
                {#each labs.grouped as [group, tests] (group)}
                  <p class="text-muted-foreground">
                    <span class="font-medium text-foreground">{group}:</span>
                    {tests.join(", ")}
                  </p>
                {/each}
                {#if labs.ungrouped.length}
                  <p class="text-muted-foreground">{labs.ungrouped.join(", ")}</p>
                {/if}
              {:else}
                {#each investigations as investigation, j (j)}
                  <p class="text-muted-foreground">{investigation}</p>
                {/each}
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if management.empirical_treatment?.length}
    <div class="glass-card space-y-4 rounded-2xl p-5">
      <div class="flex items-center gap-3">
        <div class="rounded-xl bg-accent/10 p-2"><PillIcon class="size-5 text-accent" /></div>
        <h4 class="text-lg font-semibold text-foreground">Empirical treatment</h4>
      </div>
      <div class="space-y-1 text-sm">
        {#each management.empirical_treatment as treatment, i (i)}
          <p class="text-muted-foreground">
            <span class="font-medium text-foreground">{treatment.indication}:</span>
            {treatment.treatment}
            {#if treatment.important}
              <span class="ml-1 text-warning">⚠ {treatment.important}</span>
            {/if}
          </p>
        {/each}
      </div>
    </div>
  {/if}

  {#if management.disposition}
    <div class="glass-card rounded-2xl p-5">
      <div class="flex items-start gap-4">
        <div class="shrink-0 rounded-xl bg-primary/10 p-2.5"><ArrowRightIcon class="size-5 text-primary" /></div>
        <div>
          <h4 class="mb-2 font-semibold text-foreground">Disposition</h4>
          <p class="text-muted-foreground">{management.disposition}</p>
        </div>
      </div>
    </div>
  {/if}
</section>
