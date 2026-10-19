<script lang="ts">
  import TextSegments from "$lib/scorer/TextSegments.svelte";
  import { isSlot, merged, segmentsOf } from "$lib/scorer/texts";
  import { FIELD } from "$lib/utils";
  import { type Body, SLOTS_FOR, TEXT_INSERTS } from "../chunks";

  let { body, set }: { body: Body; set: (body: Body) => void } = $props();

  const purpose = $derived(String(body.purpose ?? "generation"));

  function purposed(next: string): void {
    const allowed = SLOTS_FOR[next] ?? [];
    const kept = segmentsOf(body.segments).filter((s) => !isSlot(s) || allowed.includes(s.slot));
    set({ ...body, purpose: next, segments: merged(kept) });
  }
</script>

<div class="space-y-3 text-sm">
  <label class="grid max-w-xs gap-1"
    ><span class="text-muted-foreground">Made for</span>
    <select class={FIELD} value={purpose} onchange={(e) => purposed(e.currentTarget.value)}>
      <option value="generation">a run's answer</option>
      <option value="judge">a judge</option>
    </select></label
  >
  <TextSegments
    label="Its text"
    segs={segmentsOf(body.segments)}
    set={(segs) => set({ ...body, segments: merged(segs) })}
    slots={SLOTS_FOR[purpose]}
    inserts={TEXT_INSERTS}
  />
</div>
