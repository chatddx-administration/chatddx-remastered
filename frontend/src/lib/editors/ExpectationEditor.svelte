<script lang="ts" module>
  import type { Editing } from "./writing";

  export type ExpectationEditing = Editing & {
    kind?: "expectation";
    case: string;
    schema: string;
    json_schema: Record<string, unknown>;
    data: unknown;
  };
</script>

<script lang="ts">
  import { type Snippet, untrack } from "svelte";
  import { blank, kept } from "$lib/schema/form";
  import SchemaField from "$lib/schema/SchemaField.svelte";
  import Saving from "./Saving.svelte";
  import type { Component, Saved } from "./writing";

  let {
    editor,
    digest = null,
    opened,
    changed,
    beside,
    quiet = false,
    to,
  }: {
    editor: ExpectationEditing;
    digest?: string | null;
    opened?: boolean;
    changed?: (data: unknown) => void;
    beside?: Snippet<[string]>;
    quiet?: boolean;
    to?: (saved: Extract<Saved, { to: string }>) => string;
  } = $props();
  const given = untrack(() => editor);
  const root = given.json_schema;

  let open = $state(untrack(() => opened) ?? given.mode !== "new");
  let data = $state(given.data ?? blank(root, root));

  function component(): Component {
    return { kind: "expectation", case: given.case, expectation_schema: given.schema, data: kept(data, root, root) as never };
  }

  $effect(() => {
    if (changed) changed(kept(data, root, root));
  });
</script>

{#if !open}
  <button
    type="button"
    class="rounded-md bg-primary px-3 py-1 text-sm font-medium text-primary-foreground hover:bg-primary/90"
    onclick={() => (open = true)}>Write yours</button
  >
{:else}
  <div class="space-y-3">
    <SchemaField schema={root} {root} value={data} set={(v) => (data = v)} {beside} {quiet} />
    <Saving editing={given} {component} {digest} {to} />
  </div>
{/if}
