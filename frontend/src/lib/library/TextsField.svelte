<script lang="ts">
  import { untrack } from "svelte";
  import TextSegments from "$lib/scorer/TextSegments.svelte";
  import type { Seg } from "$lib/scorer/texts";

  let {
    segs: given,
    slots,
    inserts,
    label,
    changed,
  }: { segs: Seg[]; slots: string[]; inserts: string[]; label: string; changed: (segs: Seg[]) => void } = $props();
  let segs = $state(untrack(() => given));
</script>

<TextSegments
  {segs}
  set={(s) => {
    segs = s;
    changed(s);
  }}
  {slots}
  {inserts}
  {label}
  quiet
/>
