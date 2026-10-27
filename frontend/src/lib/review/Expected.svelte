<script lang="ts">
  import { untrack } from "svelte";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import { Button } from "$lib/components/ui/button";
  import ExpectationEditor from "$lib/editors/ExpectationEditor.svelte";
  import { saved } from "$lib/editors/writing";
  import { t } from "$lib/locale";
  import type { ExpectationEditing } from "$lib/editors/ExpectationEditor.svelte";
  import Changed from "$lib/thread/Changed.svelte";
  import type { Expecting } from "./review";

  let { expected, editor, back }: { expected: Expecting; editor: ExpectationEditing; back: string } = $props();
  const given = untrack(() => expected);

  let shown = $state(given.history.length - 1);
  const version = $derived(given.history[shown]);
  const before = $derived(shown > 0 ? given.history[shown - 1] : undefined);
  let busy = $state(false);
  let problem = $state<string | null>(null);

  async function restore(): Promise<void> {
    if (!version) return;
    busy = true;
    problem = null;
    const component = {
      kind: "expectation",
      case: editor.case,
      expectation_schema: editor.schema,
      data: version.data,
    };
    const got = await saved(editor, editor.name, component as never);
    busy = false;
    if ("to" in got) location.assign(back);
    else problem = got.problem;
  }

  function when(stamp: string): string {
    return stamp.slice(0, 16).replace("T", " ");
  }
</script>

<ExpectationEditor {editor} digest={given.digest} opened={true} quiet to={() => back} />

{#if version}
  <details class="mt-4 text-sm">
    <summary class="cursor-pointer text-xs text-muted-foreground">
      {t("Version %(n)s of %(of)s, %(at)s", {
        n: given.history.length,
        of: given.history.length,
        at: when(given.history.at(-1)?.at ?? ""),
      })}
    </summary>
    <div class="mt-2 rounded-lg border border-border/60 p-3">
      <nav class="mb-2 flex items-center gap-2 text-xs" aria-label={t("Versions")}>
        <button
          type="button"
          class="rounded-md border border-border px-2 py-0.5 hover:bg-muted disabled:opacity-40"
          disabled={shown === 0}
          aria-label={t("The version before")}
          onclick={() => (shown -= 1)}>◀</button
        >
        <span class="font-medium">{t("Version %(at)s of %(last)s", { at: shown + 1, last: given.history.length })}</span
        >
        <button
          type="button"
          class="rounded-md border border-border px-2 py-0.5 hover:bg-muted disabled:opacity-40"
          disabled={shown === given.history.length - 1}
          aria-label={t("The version after")}
          onclick={() => (shown += 1)}>▶</button
        >
        <span class="text-muted-foreground">{when(version.at)}, {version.by}</span>
        {#if shown !== given.history.length - 1}
          <Button size="xs" variant="outline" class="ml-auto" disabled={busy} onclick={restore}>
            {#if busy}<LoaderCircleIcon class="animate-spin" />{/if}
            {t("Restore")}
          </Button>
        {/if}
      </nav>
      {#if problem}<p class="mb-2 text-xs text-destructive">{problem}</p>{/if}
      {#if before}
        <Changed before={before.data} after={version.data} />
      {:else}
        <p class="text-xs text-muted-foreground">{t("It is the first.")}</p>
      {/if}
    </div>
  </details>
{/if}
