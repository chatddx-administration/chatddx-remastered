<script lang="ts">
  import InfoIcon from "@lucide/svelte/icons/info";
  import TriangleAlertIcon from "@lucide/svelte/icons/triangle-alert";
  import { localized, t } from "$lib/locale";
  import type { Checked } from "./writing";

  let { found }: { found: Checked | null } = $props();
</script>

{#if found && "problem" in found}
  <p class="flex gap-2 text-sm text-destructive">
    <TriangleAlertIcon class="mt-0.5 size-4 shrink-0" /><span class="whitespace-pre-wrap">{found.problem}</span>
  </p>
{:else if found && found.findings.length}
  <ul class="space-y-1 text-sm">
    {#each found.findings as finding, i (i)}
      <li class="flex gap-2">
        {#if finding.level === "warning"}<TriangleAlertIcon
            class="mt-0.5 size-4 shrink-0 text-warning"
          />{:else}<InfoIcon class="mt-0.5 size-4 shrink-0 text-primary" />{/if}
        <span>{localized(finding)} <span class="text-xs text-muted-foreground">{finding.code}</span></span>
      </li>
    {/each}
  </ul>
{:else if found}
  <p class="text-sm text-muted-foreground">{t("Nothing to say of it.")}</p>
{/if}
