<script lang="ts">
  let { body, titles }: { body: Record<string, unknown>; titles: Record<string, string> } = $props();

  const DIGEST = /^sha256:[0-9a-f]{64}$/;
  const fields = $derived(Object.entries(body).filter(([k]) => k !== "kind" && k !== "v"));
</script>

<dl class="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-[max-content_1fr]">
  {#each fields as [name, value] (name)}
    <dt class="text-muted-foreground">{name.replaceAll("_", " ")}</dt>
    <dd class="min-w-0">
      {#if typeof value === "string" && DIGEST.test(value)}
        <span>{titles[value] ?? "a component"}</span>
        <span class="ml-1 font-mono text-xs text-muted-foreground">{value.slice(7, 19)}</span>
      {:else if typeof value === "string"}
        <div class="whitespace-pre-wrap break-words">{value}</div>
      {:else if value === null || typeof value !== "object"}
        <span>{value === null ? "—" : String(value)}</span>
      {:else}
        <pre class="overflow-x-auto rounded-lg bg-muted/60 p-3 font-mono text-xs leading-relaxed">{JSON.stringify(value, null, 2)}</pre>
      {/if}
    </dd>
  {/each}
</dl>
