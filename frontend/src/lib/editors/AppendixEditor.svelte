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
  import { t, tn } from "$lib/locale";
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
  <Textarea bind:value={text} rows={6} aria-label={t("Its text")} />
  <Saving
    editing={given}
    {component}
    {digest}
    {to}
    after={(n) =>
      tn(
        "The case that held it has a new one with this version; carry your expectations over where they still hold.",
        "The %(n)s cases that held it have new ones with this version; carry your expectations over where they still hold.",
        n,
        { n },
      )}
  />
</div>
