<script lang="ts">
  import TextSegments from "$lib/scorer/TextSegments.svelte";
  import { segmentsOf, textOf } from "$lib/scorer/texts";
  import { type Body, FIELD, TEXT_INSERTS } from "../chunks";

  let { body, set }: { body: Body; set: (body: Body) => void } = $props();
</script>

<div class="space-y-3 text-sm">
  <label class="grid max-w-xs gap-1"
    ><span class="text-muted-foreground">Sent as</span>
    <select class={FIELD} value={body.role ?? "system"} onchange={(e) => set({ ...body, role: e.currentTarget.value })}>
      <option value="system">a system message</option>
      <option value="developer">a developer message</option>
    </select></label
  >
  <TextSegments
    label="Its text"
    segs={segmentsOf(body.text)}
    set={(segs) => set({ ...body, text: textOf(segs) })}
    inserts={TEXT_INSERTS}
  />
</div>
