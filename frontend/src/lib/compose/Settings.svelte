<script lang="ts">
  import * as NativeSelect from "$lib/components/ui/native-select";
  import type { Schemas } from "$lib/api/client";
  import { worded } from "$lib/kinds";
  import { t } from "$lib/locale";
  import SchemaField from "$lib/schema/SchemaField.svelte";
  import { blank, type Body, type Chunk, type Chunks, type Drafted } from "./drafting";

  let {
    chunks,
    drafted,
    optional,
    model,
    models,
    set,
    pick,
  }: {
    chunks: Chunks;
    drafted: Drafted;
    optional: string[];
    model: string | null;
    models: Schemas["Thread"][];
    set: (part: Chunk, body: Body | null) => void;
    pick: (model: string) => void;
  } = $props();

  // Policy: the guidance of an output and a toolset is text, drafted with the other texts and translated with them.
  const SHOWN: { part: Chunk; hidden: string[] }[] = [
    { part: "sampling", hidden: ["kind"] },
    { part: "reasoning", hidden: ["kind"] },
    { part: "passthrough", hidden: ["kind"] },
    { part: "output", hidden: ["kind", "guidance"] },
    { part: "toolset", hidden: ["kind", "guidance"] },
  ];
</script>

<section class="mb-6 border-t border-border/60 pt-4" aria-label={t("Its settings")}>
  <h2 class="mb-4 text-lg font-semibold">{t("Its settings")}</h2>
  <div class="space-y-4 text-sm">
    <label class="grid max-w-md gap-1">
      <span class="font-medium">{worded("model")}</span>
      <NativeSelect.Root size="sm" value={model ?? ""} onchange={(e) => pick(e.currentTarget.value)}>
        {#if model === null}<NativeSelect.Option value="">—</NativeSelect.Option>{/if}
        {#each models as m (m.id)}
          <NativeSelect.Option value={m.head.digest}>{m.name ?? m.title}</NativeSelect.Option>
        {/each}
      </NativeSelect.Root>
    </label>
    {#each SHOWN as { part, hidden } (part)}
      {@const held = chunks[part]}
      {#if held === null}
        <button
          type="button"
          class="mr-2 rounded-full border border-dashed border-border px-2.5 py-0.5 text-xs text-muted-foreground hover:bg-muted"
          onclick={() => set(part, blank(part))}>+ {worded(part)}</button
        >
      {:else}
        <div class="flex items-start gap-2">
          <div class="min-w-0 flex-1">
            <SchemaField
              schema={drafted.schemas[part]}
              root={drafted.schemas[part]}
              value={held}
              set={(v) => set(part, v as Body)}
              label={worded(part)}
              {hidden}
              quiet
            />
          </div>
          {#if optional.includes(part)}
            <button
              type="button"
              class="mt-2 rounded-md px-1.5 text-muted-foreground hover:bg-muted"
              aria-label={t("Leave out %(name)s", { name: worded(part) })}
              onclick={() => set(part, null)}>×</button
            >
          {/if}
        </div>
      {/if}
    {/each}
  </div>
</section>
