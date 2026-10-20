<script lang="ts" module>
  import type { Editing } from "./writing";

  export type AppendixEditing = Editing & {
    kind?: "appendix";
    vignette: Record<string, unknown>;
    text: string;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import { Textarea } from "$lib/components/ui/textarea";
  import Saving from "./Saving.svelte";
  import type { Component, Saved } from "./writing";

  let {
    editor,
    digest = null,
    to,
  }: {
    editor: AppendixEditing;
    digest?: string | null;
    to?: (saved: Extract<Saved, { to: string }>) => string;
  } = $props();
  const given = untrack(() => editor);

  let text = $state(given.text);

  function component(): Component {
    return { kind: "appendix", vignette: given.vignette as never, text };
  }
</script>

<div class="space-y-3">
  <Textarea bind:value={text} rows={6} aria-label="Its text" />
  <Saving
    editing={given}
    {component}
    {digest}
    {to}
    after={(n) => `The ${n === 1 ? "case" : `${n} cases`} that held it ${n === 1 ? "has a new one" : "have new ones"} with this version; carry your expectations over where they still hold.`}
  />
</div>
