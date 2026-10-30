<script lang="ts" module>
  export type Appended = {
    digest: string;
    title: string;
    text: string;
    vignette: Record<string, unknown>;
    thread: number | null;
    head: number | null;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import PencilIcon from "@lucide/svelte/icons/pencil";
  import { api, why } from "$lib/api/client";
  import { written } from "$lib/editors/writing";
  import { t } from "$lib/locale";
  import AppendixForm from "./AppendixForm.svelte";
  import type { Edited, Wrote } from "./edited.svelte";

  let {
    appendices,
    family,
    case: start,
    edited,
  }: { appendices: Appended[]; family: number; case: string; edited: Edited } = $props();
  const given = untrack(() => appendices);

  let drafts = $state(given.map((a) => ({ name: a.title, text: a.text })));
  let saved = $state(given.map((a) => ({ name: a.title, text: a.text })));
  let open = $state<number | "new" | null>(null);
  let name = $state("");
  let text = $state("");
  const heads = given.map((a) => a.head);
  const held = given.map((a) => a.digest);
  let at = untrack(() => start);
  let made: string | null = null;

  const retexted = (i: number): boolean => given[i]?.thread !== null && drafts[i]?.text !== saved[i]?.text;
  const renamed = (i: number): boolean => given[i]?.thread !== null && drafts[i]?.name.trim() !== saved[i]?.name;
  const changed = (i: number): boolean => retexted(i) || renamed(i);
  const begun = $derived(open === "new" && (name.trim() !== "" || text.trim() !== ""));

  untrack(() => edited).join({
    rank: 2,
    pending: () => given.some((_, i) => changed(i)) || begun,
    opened: () => open !== null,
    ready: () =>
      drafts.every((d, i) => !changed(i) || (d.text !== "" && d.name.trim() !== "")) &&
      (!begun || (name.trim() !== "" && text !== "")),
    save: async (): Promise<Wrote> => {
      for (const [i, a] of given.entries()) {
        if (a.thread === null) continue;
        if (retexted(i)) {
          const got = await written(
            { thread: a.thread, head: heads[i] ?? 0, mine: true, name: a.title },
            { component: { kind: "appendix", vignette: a.vignette as never, text: drafts[i]?.text ?? "" } },
          );
          if ("problem" in got) {
            if (got.moved !== null) heads[i] = got.moved;
            return { problem: got.problem };
          }
          heads[i] = got.head;
          held[i] = got.digest;
          saved[i] = { name: saved[i]?.name ?? "", text: drafts[i]?.text ?? "" };
          at = got.cases[at] ?? at;
        }
        if (renamed(i)) {
          const named = drafts[i]?.name.trim() ?? "";
          const got = await api.PATCH("/api/threads/{thread}", {
            params: { path: { thread: a.thread } },
            body: { name: named },
          });
          if (!got.data) return { problem: why(got.error) };
          saved[i] = { name: named, text: saved[i]?.text ?? "" };
        }
      }
      if (begun) {
        if (made === null) {
          const got = await api.POST("/api/families/{family}/appendices", {
            params: { path: { family } },
            body: { name: name.trim(), text },
          });
          if (!got.data) return { problem: why(got.error) };
          made = got.data.head.digest;
        }
        const got = await api.POST("/api/families/{family}/cases", {
          params: { path: { family } },
          body: { appendices: [...held, made] },
        });
        if (!got.data) return { problem: why(got.error) };
        at = got.data.case;
      }
      return { case: at };
    },
    restore: () => {
      drafts = saved.map((s) => ({ ...s }));
      open = null;
      name = "";
      text = "";
    },
  });
</script>

{#each drafts as draft, i (given[i]?.digest)}
  {@const own = given[i]?.thread != null}
  {#if open === i}
    <AppendixForm bind:name={draft.name} bind:text={draft.text} />
  {:else}
    <article class="rounded-lg border-l-2 border-primary/50 bg-primary/5 px-3 py-2 text-sm">
      <header class="mb-1 flex items-center justify-between gap-2 text-xs font-medium text-muted-foreground">
        <h3 class="min-w-0 break-words">{draft.name}</h3>
        {#if own && open === null}
          <button
            type="button"
            class="icon"
            aria-label={t("Change it")}
            title={t("Change it")}
            onclick={() => (open = i)}><PencilIcon class="size-3.5" /></button
          >
        {/if}
      </header>
      <p class="whitespace-pre-wrap">{draft.text}</p>
    </article>
  {/if}
{/each}
{#if open === "new"}
  <AppendixForm bind:name bind:text />
{:else if open === null}
  <button
    type="button"
    class="w-full cursor-pointer rounded-lg border border-dashed border-border p-3 text-left text-sm font-medium hover:bg-muted"
    onclick={() => (open = "new")}>{t("Add an appendix")}</button
  >
{/if}
