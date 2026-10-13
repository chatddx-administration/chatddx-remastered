<script lang="ts" module>
  import type { Mode } from "./writing";

  export type AppendixEditing = {
    kind?: "appendix";
    mode: Mode;
    thread?: number;
    head?: number;
    name: string;
    vignette: Record<string, unknown>;
    text: string;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import { Textarea } from "$lib/components/ui/textarea";
  import Findings from "./Findings.svelte";
  import Saving from "./Saving.svelte";
  import { type Checked, checked, type Component } from "./writing";

  let { editor, digest = null }: { editor: AppendixEditing; digest?: string | null } = $props();
  const given = untrack(() => editor);

  let text = $state(given.text);
  let found = $state<Checked | null>(null);
  let asked = 0;

  function component(): Component {
    return { kind: "appendix", vignette: given.vignette as never, text };
  }

  $effect(() => {
    void text;
    const sent = ++asked;
    const timer = setTimeout(async () => {
      const got = await checked(component());
      if (sent === asked) found = got;
    }, 350);
    return () => clearTimeout(timer);
  });
</script>

<div class="space-y-3">
  <Textarea bind:value={text} rows={6} aria-label="Its text" />
  <Findings {found} />
  <Saving
    editing={given}
    {component}
    unchanged={found !== null && "digest" in found && found.digest === digest}
    blocked={found !== null && "problem" in found}
    after={(n) => `The ${n === 1 ? "case" : `${n} cases`} that held it ${n === 1 ? "has a new one" : "have new ones"} with this version; carry your expectations over where they still hold.`}
  />
</div>
