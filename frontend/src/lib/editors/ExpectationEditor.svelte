<script lang="ts" module>
  import type { Mode } from "./writing";

  export type ExpectationEditing = {
    kind?: "expectation";
    mode: Mode;
    thread?: number;
    head?: number;
    name: string;
    case: string;
    schema: string;
    json_schema: Record<string, unknown>;
    data: unknown;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import { blank, kept } from "$lib/schema/form";
  import SchemaField from "$lib/schema/SchemaField.svelte";
  import Findings from "./Findings.svelte";
  import Saving from "./Saving.svelte";
  import { type Checked, checked, type Component } from "./writing";

  let { editor, digest = null }: { editor: ExpectationEditing; digest?: string | null } = $props();
  const given = untrack(() => editor);
  const root = given.json_schema;

  let open = $state(given.mode !== "new");
  let data = $state(given.data ?? blank(root, root));
  let found = $state<Checked | null>(null);
  let asked = 0;

  function component(): Component {
    return { kind: "expectation", case: given.case, expectation_schema: given.schema, data: kept(data, root, root) as never };
  }

  $effect(() => {
    if (!open) return;
    JSON.stringify(data);
    const sent = ++asked;
    const timer = setTimeout(async () => {
      const got = await checked(component());
      if (sent === asked) found = got;
    }, 350);
    return () => clearTimeout(timer);
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
    <SchemaField schema={root} {root} value={data} set={(v) => (data = v)} />
    <Findings {found} />
    <Saving
      editing={given}
      {component}
      unchanged={found !== null && "digest" in found && found.digest === digest}
      blocked={found !== null && "problem" in found}
    />
  </div>
{/if}
