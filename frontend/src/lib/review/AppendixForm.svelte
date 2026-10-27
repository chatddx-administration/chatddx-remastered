<script lang="ts">
  import { t } from "$lib/locale";

  let { name = $bindable(), text = $bindable() }: { name: string; text: string } = $props();
</script>

<article class="grid gap-2 rounded-lg border border-dashed border-border p-3 text-sm">
  <label class="grid gap-1">
    <span class="text-muted-foreground">{t("Name")}</span>
    <input bind:value={name} class="h-9 rounded-md border border-input bg-transparent px-2.5" />
  </label>
  <label class="grid gap-1">
    <span class="text-muted-foreground">{t("Text, as it is added to the vignette")}</span>
    <textarea
      bind:value={text}
      rows="3"
      class="rounded-md border border-input bg-transparent px-2.5 py-1.5 [field-sizing:content]"></textarea>
  </label>
</article>
