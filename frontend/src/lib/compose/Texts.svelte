<script lang="ts">
  import { worded } from "$lib/kinds";
  import { displayLanguage, t } from "$lib/locale";
  import SchemaField from "$lib/schema/SchemaField.svelte";
  import TextSegments from "$lib/scorer/TextSegments.svelte";
  import { merged, type Seg, segmentsOf, textOf } from "$lib/scorer/texts";
  import {
    blank,
    type Body,
    type Chunk,
    type Chunks,
    counted,
    type Drafted,
    type Into,
    offered,
    TEXTS,
  } from "./drafting";

  let {
    chunks,
    drafted,
    language,
    into,
    texts,
    waiting,
    set,
    translate,
    dropped,
  }: {
    chunks: Chunks;
    drafted: Drafted;
    language: string | null;
    into: Into;
    texts: Record<string, string[]>;
    waiting: boolean;
    set: (part: Chunk, body: Body | null) => void;
    translate: (language: string, text: string, said: string) => void;
    dropped: (language: string) => void;
  } = $props();

  let tab = $state<string | null>(null);
  const languages = $derived(Object.keys(into).sort());
  const shown = $derived(tab !== null && tab in into ? tab : null);

  function field(part: Chunk, name: string, value: unknown): void {
    const held = chunks[part];
    if (held) set(part, { ...held, [name]: value });
  }

  function segs(part: Chunk, name: string): Seg[] {
    return segmentsOf(chunks[part]?.[name] ?? "");
  }

  function guidance(part: Chunk, given: Seg[]): void {
    const text = textOf(given);
    field(part, "guidance", text === "" ? null : text);
  }
</script>

<section class="mb-6 border-t border-border/60 pt-4" aria-label={t("Its texts")}>
  <h2 class="mb-3 text-lg font-semibold">{t("Its texts")}</h2>
  <nav class="mb-4 flex flex-wrap items-center gap-1 border-b border-border/60 text-sm" aria-label={t("Languages")}>
    <button
      type="button"
      class="-mb-px border-b-2 px-3 py-1.5 {shown === null ? 'border-primary font-medium' : 'border-transparent'}"
      aria-current={shown === null ? "page" : undefined}
      onclick={() => (tab = null)}>{language ? displayLanguage(language) : t("As written")}</button
    >
    {#each languages as l (l)}
      {@const [done, all] = counted(texts, into[l] ?? {})}
      <button
        type="button"
        class="-mb-px border-b-2 px-3 py-1.5 {shown === l ? 'border-primary font-medium' : 'border-transparent'}"
        aria-current={shown === l ? "page" : undefined}
        onclick={() => (tab = l)}
        >{displayLanguage(l)} <span class="text-xs text-muted-foreground">{done}/{all}</span></button
      >
    {/each}
  </nav>

  {#if shown === null}
    <div class="space-y-5 text-sm">
      <div>
        <h3 class="mb-1.5 font-medium">{worded("instructions")}</h3>
        {#if chunks.instructions}
          <div class="flex items-start gap-2">
            <div class="min-w-0 flex-1">
              <TextSegments
                segs={segs("instructions", "text")}
                set={(s) => field("instructions", "text", textOf(s))}
                inserts={offered("instructions", chunks, drafted.inserts.instructions ?? [])}
                label={worded("instructions")}
                quiet
              />
            </div>
            <button
              type="button"
              class="rounded-md px-1.5 text-muted-foreground hover:bg-muted"
              aria-label={t("Leave out %(name)s", { name: worded("instructions") })}
              onclick={() => set("instructions", null)}>×</button
            >
          </div>
        {:else}
          <button type="button" class="text-xs" onclick={() => set("instructions", blank("instructions"))}
            >+ {worded("instructions")}</button
          >
        {/if}
      </div>

      <div>
        <h3 class="mb-1.5 font-medium">{worded("few_shot")}</h3>
        {#if chunks.few_shot}
          <div class="flex items-start gap-2">
            <div class="min-w-0 flex-1">
              <SchemaField
                schema={drafted.schemas.few_shot}
                root={drafted.schemas.few_shot}
                value={chunks.few_shot}
                set={(v) => set("few_shot", v as Body)}
                hidden={["kind"]}
                framed={false}
                quiet
              />
            </div>
            <button
              type="button"
              class="rounded-md px-1.5 text-muted-foreground hover:bg-muted"
              aria-label={t("Leave out %(name)s", { name: worded("few_shot") })}
              onclick={() => set("few_shot", null)}>×</button
            >
          </div>
        {:else}
          <button type="button" class="text-xs" onclick={() => set("few_shot", blank("few_shot"))}
            >+ {worded("few_shot")}</button
          >
        {/if}
      </div>

      <div>
        <h3 class="mb-1.5 font-medium">{worded("prompt")}</h3>
        {#if chunks.prompt}
          <TextSegments
            segs={segs("prompt", "segments")}
            set={(s) => field("prompt", "segments", merged(s))}
            slots={drafted.slots[String(chunks.prompt.purpose ?? "generation")] ?? []}
            inserts={offered("prompt", chunks, drafted.inserts.prompt ?? [])}
            label={worded("prompt")}
            quiet
          />
        {/if}
      </div>

      {#if chunks.output}
        <div>
          <h3 class="mb-1.5 font-medium">{t("Output guidance")}</h3>
          <TextSegments
            segs={segs("output", "guidance")}
            set={(s) => guidance("output", s)}
            inserts={offered("output", chunks, drafted.inserts.output ?? [])}
            label={t("Output guidance")}
            quiet
          />
        </div>
      {/if}

      {#if chunks.toolset}
        <div>
          <h3 class="mb-1.5 font-medium">{t("Tool guidance")}</h3>
          <textarea
            class="w-full rounded-md border border-input bg-transparent px-2 py-1 [field-sizing:content]"
            rows="1"
            aria-label={t("Tool guidance")}
            value={String(chunks.toolset.guidance ?? "")}
            oninput={(e) => field("toolset", "guidance", e.currentTarget.value || null)}></textarea>
        </div>
      {/if}
    </div>
  {:else}
    {@const entries = into[shown] ?? {}}
    <div class="space-y-5 text-sm">
      {#each TEXTS.filter((p) => texts[p]?.length) as part (part)}
        <div>
          <h3 class="mb-1.5 font-medium">
            {part === "appendix_layout" ? t("How appendices are laid out") : worded(part)}
          </h3>
          <ol class="space-y-3">
            {#each texts[part] ?? [] as text (text)}
              <li class="grid gap-1">
                <p class="whitespace-pre-wrap rounded-md bg-muted/40 px-2 py-1 text-muted-foreground">{text}</p>
                <textarea
                  class="w-full rounded-md border border-input bg-transparent px-2 py-1 [field-sizing:content]"
                  rows="1"
                  aria-label={t("Into %(language)s: %(text)s", { language: displayLanguage(shown), text })}
                  disabled={waiting}
                  value={entries[text] ?? ""}
                  oninput={(e) => translate(shown, text, e.currentTarget.value)}></textarea>
              </li>
            {/each}
          </ol>
        </div>
      {:else}
        <p class="text-muted-foreground">{t("Nothing to translate.")}</p>
      {/each}
      <button type="button" class="text-xs" onclick={() => dropped(shown)}
        >{t("Translate it into %(language)s no more", { language: displayLanguage(shown) })}</button
      >
    </div>
  {/if}
</section>
