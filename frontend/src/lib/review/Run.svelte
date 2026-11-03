<script lang="ts">
  import { tp } from "$lib/locale";
  import type { Edited } from "./edited.svelte";

  let { edited, form, held, leave }: { edited: Edited; form: HTMLFormElement; held: boolean; leave: () => void } =
    $props();

  let behind = $state(true);

  export function fared(run: boolean): void {
    behind = run;
  }

  // Policy: Run saves what is unsaved first, and runs the case it saved into.
  async function run(): Promise<void> {
    const back = form.querySelector<HTMLInputElement>('input[name="back"]');
    if (edited.pending) {
      const to = await edited.written(back?.value ?? location.pathname + location.search);
      if (to === null) return;
      if (back) back.value = to;
      const at = form.querySelector<HTMLInputElement>('input[name="case"]');
      if (at) at.value = edited.at;
    }
    leave();
    form.submit();
  }
</script>

<button
  type="button"
  class="run"
  disabled={held || edited.busy || (edited.pending ? !edited.ready : !behind)}
  onclick={() => void run()}>{tp("a button", "Run")}</button
>
