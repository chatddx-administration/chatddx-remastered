<script lang="ts">
  import { api, type Schemas, why } from "$lib/api/client";

  let { judge, expectation, data }: { judge: string; expectation: string; data: unknown } = $props();

  let open = $state(false);
  let asked = $state<Schemas["Asked"] | null>(null);
  let problem = $state<string | null>(null);
  let sending = 0;

  type Said = { role: string; content: string };
  const messages = $derived(
    (Array.isArray(asked?.request.messages) ? asked.request.messages : []).filter(
      (m): m is Said => typeof m === "object" && m !== null && "content" in m,
    ),
  );

  $effect(() => {
    if (!open) return;
    const body = { judge, expectation, data: JSON.parse(JSON.stringify(data ?? null)) as never };
    const at = ++sending;
    const timer = setTimeout(async () => {
      const got = await api.POST("/api/judges/asked", { body });
      if (at !== sending) return;
      asked = got.data ?? null;
      problem = got.data ? null : why(got.error);
    }, 300);
    return () => clearTimeout(timer);
  });
</script>

<details bind:open class="rounded-md bg-muted/40 px-2 py-1">
  <summary class="cursor-pointer text-muted-foreground">What its judge is asked</summary>
  {#if problem}
    <p class="mt-1 text-destructive">{problem}</p>
  {:else if asked}
    <ol class="mt-1 space-y-1.5" aria-label="What its judge is asked">
      {#each messages as m, i (i)}
        <li>
          <span class="font-medium text-muted-foreground">{m.role}</span>
          <div class="mt-0.5 max-h-56 overflow-y-auto whitespace-pre-wrap rounded bg-background/70 p-2 font-mono text-[0.7rem] leading-relaxed">{m.content}</div>
        </li>
      {/each}
    </ol>
  {:else}
    <p class="mt-1 text-muted-foreground">…</p>
  {/if}
</details>
