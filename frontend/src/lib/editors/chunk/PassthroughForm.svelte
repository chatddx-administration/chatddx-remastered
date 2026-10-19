<script lang="ts">
  import SettingsTable from "../SettingsTable.svelte";
  import type { Body } from "../chunks";

  let { body, set }: { body: Body; set: (body: Body) => void } = $props();
</script>

<div class="text-sm">
  <SettingsTable label="What it adds to the request's body" settings={body.body ?? {}} set={(s) => set({ ...body, body: s })} />
</div>
