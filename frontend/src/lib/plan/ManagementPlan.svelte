<script lang="ts">
  import BookOpenIcon from "@lucide/svelte/icons/book-open";
  import ExternalLinkIcon from "@lucide/svelte/icons/external-link";
  import ListChecksIcon from "@lucide/svelte/icons/list-checks";
  import ShieldAlertIcon from "@lucide/svelte/icons/shield-alert";
  import * as Alert from "$lib/components/ui/alert";
  import DiagnosisCard from "./DiagnosisCard.svelte";
  import ManagementSection from "./ManagementSection.svelte";
  import { siteOf } from "./sources";
  import type { ManagementPlan } from "./types";

  let { plan }: { plan: ManagementPlan } = $props();
</script>

<div class="space-y-6">
  {#if plan.acute_warning}
    <Alert.Root variant="destructive" class="animate-scale-in rounded-2xl border-destructive/30 bg-destructive/5">
      <ShieldAlertIcon />
      <Alert.Title class="font-display text-lg font-bold">Acute warning</Alert.Title>
      <Alert.Description>{plan.acute_warning}</Alert.Description>
    </Alert.Root>
  {/if}

  {#if plan.diagnoses?.length}
    <section class="space-y-4">
      <div class="flex animate-slide-up items-center gap-3" style:animation-delay="50ms">
        <div class="rounded-xl bg-primary/10 p-2"><ListChecksIcon class="size-5 text-primary" /></div>
        <h3 class="text-xl font-bold text-foreground">Differential diagnoses</h3>
        <span class="rounded-full bg-primary/10 px-2.5 py-1 text-sm font-semibold text-primary">
          {plan.diagnoses.length}
        </span>
      </div>
      <div class="space-y-3">
        {#each plan.diagnoses as diagnosis, index (index)}
          <DiagnosisCard {diagnosis} {index} />
        {/each}
      </div>
    </section>
  {/if}

  {#if plan.management}
    <ManagementSection management={plan.management} />
  {/if}

  {#if plan.sources?.length}
    <section class="glass-card animate-slide-up rounded-2xl p-5" style:animation-delay="300ms">
      <div class="flex items-start gap-4">
        <div class="shrink-0 rounded-xl bg-accent/10 p-2.5"><BookOpenIcon class="size-5 text-accent" /></div>
        <div class="flex-1">
          <h3 class="mb-3 font-semibold text-foreground">Medical sources</h3>
          <div class="flex flex-wrap gap-2">
            {#each plan.sources as source, i (i)}
              {@const site = siteOf(source)}
              {#if site}
                <a
                  href={site}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="inline-flex items-center gap-1.5 rounded-lg bg-muted px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-primary/10 hover:text-primary"
                >
                  {source}
                  <ExternalLinkIcon class="size-3" />
                </a>
              {:else}
                <span class="rounded-lg bg-muted px-3 py-1.5 text-sm text-muted-foreground">{source}</span>
              {/if}
            {/each}
          </div>
        </div>
      </div>
    </section>
  {/if}

  <p class="animate-fade-in border-t border-border/30 pt-6 text-center text-xs text-muted-foreground">
    This information is for educational and reference purposes only and does not replace clinical judgment.
  </p>
</div>
