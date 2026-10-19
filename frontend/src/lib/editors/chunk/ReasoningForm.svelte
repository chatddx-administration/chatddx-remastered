<script lang="ts">
  import SettingsTable from "../SettingsTable.svelte";
  import { type Body, EFFORTS, FIELD, LEVELS, numberOf, typedOf } from "../chunks";

  let { body, set }: { body: Body; set: (body: Body) => void } = $props();

  const leveled = $derived(body.level !== null && body.level !== undefined);

  function moded(level: boolean): void {
    const budget = body.thinking_token_budget ?? null;
    set(level ? { kind: body.kind, level: "default", thinking_token_budget: budget } : { kind: body.kind, thinking_token_budget: budget });
  }
</script>

<div class="space-y-3 text-sm">
  <fieldset class="flex flex-wrap gap-4">
    <legend class="sr-only">How it asks</legend>
    <label class="flex items-center gap-2"><input type="radio" checked={leveled} onchange={() => moded(true)} /> A level, worked out from the model's facts</label>
    <label class="flex items-center gap-2"><input type="radio" checked={!leveled} onchange={() => moded(false)} /> Settings, sent as they are</label>
  </fieldset>
  <div class="flex flex-wrap gap-3">
    {#if leveled}
      <label class="grid gap-1"
        ><span class="text-muted-foreground">Level</span>
        <select class={FIELD} value={body.level} onchange={(e) => set({ ...body, level: e.currentTarget.value })}>
          {#each LEVELS as l (l)}<option value={l}>{l}</option>{/each}
        </select></label
      >
    {:else}
      <label class="grid gap-1"
        ><span class="font-mono text-xs text-muted-foreground">reasoning_effort</span>
        <select class={FIELD} value={body.effort ?? ""} onchange={(e) => set({ ...body, effort: e.currentTarget.value || null })}>
          <option value="">not sent</option>
          {#each EFFORTS as l (l)}<option value={l}>{l}</option>{/each}
        </select></label
      >
    {/if}
    <label class="grid gap-1"
      ><span class="font-mono text-xs text-muted-foreground">thinking_token_budget</span>
      <input
        class="{FIELD} font-mono"
        inputmode="numeric"
        value={typedOf(body.thinking_token_budget)}
        oninput={(e) => set({ ...body, thinking_token_budget: numberOf(e.currentTarget.value) })}
      /></label
    >
  </div>
  {#if !leveled}
    <SettingsTable label="chat_template_kwargs" settings={body.chat_template_kwargs ?? {}} set={(s) => set({ ...body, chat_template_kwargs: s })} />
  {/if}
</div>
