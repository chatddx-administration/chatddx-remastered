<script lang="ts">
  import { untrack } from "svelte";
  import { blank, kept, type Schema, widget } from "$lib/schema/form";
  import SchemaField from "$lib/schema/SchemaField.svelte";

  let {
    schema,
    value,
    label,
    changed,
  }: { schema: Schema; value: unknown; label: string; changed: (value: unknown) => void } = $props();
  const root = untrack(() => schema);
  let data = $state(untrack(() => value ?? blank(root, root)));
  const named = widget(root, root).is === "list" ? untrack(() => label) : "";
</script>

<SchemaField
  schema={root}
  {root}
  value={data}
  label={named}
  set={(v) => {
    data = v;
    changed(kept(v, root, root));
  }}
/>
