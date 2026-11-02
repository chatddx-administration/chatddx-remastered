<script lang="ts">
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import TriangleAlertIcon from "@lucide/svelte/icons/triangle-alert";
  import * as Alert from "$lib/components/ui/alert";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import { api, why } from "$lib/api/client";
  import { t, tn } from "$lib/locale";
  import { type Body, type Chunk, cleaned, kept as keptLanguages, same } from "$lib/compose/drafting";
  import { whereSaveGoes } from "$lib/compose/logic";
  import type { Props } from "$lib/compose/props";
  import Settings from "$lib/compose/Settings.svelte";
  import Texts from "$lib/compose/Texts.svelte";
  import { untrack } from "svelte";

  let { held }: { held: Props } = $props();
  const given = untrack(() => held);
  const { configuration, me, versions, head, optional, drafted } = given;
  const latest = versions.at(-1)?.id ?? head;
  const version = versions.findIndex((v) => v.id === head) + 1;

  let chunks = $state(structuredClone(drafted?.chunks));
  let model = $state(drafted?.model ?? null);
  let into = $state(structuredClone(drafted?.into ?? {}));
  let texts = $state(structuredClone(drafted?.texts ?? {}));
  let baseline = $state.snapshot(drafted?.chunks);
  let drafting: ReturnType<typeof setTimeout> | null = null;
  let draftingNow: Promise<void> | null = null;
  let draftFailure = $state<string | null>(null);
  let waiting = $state(false);
  let name = $state(configuration.name ?? configuration.title);
  let saving = $state(false);
  let unsaved = $state<string | null>(null);

  const changed = $derived(
    given.varied ||
      !same(chunks, drafted?.chunks) ||
      model !== (drafted?.model ?? null) ||
      !same(cleaned(into), cleaned(drafted?.into ?? {})),
  );
  const goes = $derived(
    whereSaveGoes({
      name,
      configuration,
      me,
      versions: versions.length,
      latest: head === latest,
      changed,
      configurations: given.configurations,
    }),
  );

  function saves(): string {
    if (goes.to === "nothing" && goes.because === "nameless") return t("Give it a name to save it.");
    if (goes.to === "nothing") return t("Nothing to save: this is the configuration as it is.");
    if (goes.to === "version") return t("Saves version %(n)s of this configuration.", { n: goes.version });
    return t("Saves a new configuration of yours, “%(name)s”, forked from version %(n)s of this one.", {
      name: name.trim(),
      n: version,
    });
  }

  function set(part: Chunk, body: Body | null): void {
    if (!chunks) return;
    chunks[part] = body;
    if (drafting !== null) clearTimeout(drafting);
    waiting = true;
    drafting = setTimeout(() => {
      drafting = null;
      draftingNow = draft();
    }, 400);
  }

  // Policy: a text's translations follow it as it is typed, so the translations are drafted on the server alongside
  // the chunks, and aren't typed in meanwhile.
  let drafts = 0;
  async function draft(): Promise<void> {
    const sent = ++drafts;
    const after = $state.snapshot(chunks);
    const got = await api.POST("/api/threads/{thread}/drafts", {
      params: { path: { thread: configuration.id } },
      body: { head, before: baseline ?? {}, after: after ?? {}, translations: cleaned($state.snapshot(into)) },
    });
    if (sent !== drafts) return;
    waiting = false;
    if (!got.data) {
      draftFailure = why(got.error);
      return;
    }
    draftFailure = null;
    texts = got.data.texts;
    into = keptLanguages(into, got.data.translations);
    baseline = after;
  }

  async function settled(): Promise<void> {
    if (drafting !== null) {
      clearTimeout(drafting);
      drafting = null;
      draftingNow = draft();
    }
    await draftingNow;
  }

  function translate(language: string, text: string, said: string): void {
    into[language] = { ...into[language], [text]: said };
  }

  function dropped(language: string): void {
    const { [language]: _, ...rest } = into;
    into = rest;
  }

  async function save(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    const to = goes.to;
    if (to === "nothing") return;
    saving = true;
    unsaved = null;
    await settled();
    if (draftFailure !== null) {
      unsaved = draftFailure;
      saving = false;
      return;
    }
    const got = await api.POST("/api/threads/{thread}/saves", {
      params: { path: { thread: configuration.id } },
      body: {
        head: to === "version" ? latest : head,
        ...(to === "fork" ? { name: name.trim() } : {}),
        chunks: $state.snapshot(chunks) ?? {},
        ...(model !== null && model !== drafted?.model ? { model } : {}),
        translations: cleaned($state.snapshot(into)),
      },
    });
    if (!got.data) {
      unsaved = why(got.error);
      saving = false;
      return;
    }
    location.assign(`/compose/${got.data.id}`);
  }
</script>

{#if chunks && drafted}
  <Texts {chunks} {drafted} language={configuration.language} {into} {texts} {waiting} {set} {translate} {dropped} />
  <Settings
    {chunks}
    {drafted}
    {optional}
    {model}
    models={given.modelChoices}
    {set}
    pick={(m) => {
      model = m || null;
    }}
  />
  {#if draftFailure}
    <Alert.Root variant="destructive" class="mb-4">
      <TriangleAlertIcon />
      <Alert.Description>{draftFailure}</Alert.Description>
    </Alert.Root>
  {/if}

  <section class="mb-6 border-t border-border/60 pt-4" aria-label={t("Saving it")}>
    <form class="space-y-3" onsubmit={save}>
      <div class="space-y-1.5">
        <Label for="saved-name">{t("Name")}</Label>
        <Input id="saved-name" bind:value={name} class="max-w-md" autocomplete="off" />
      </div>
      <p class="text-sm" aria-live="polite">
        {saves()}
        {#if goes.to === "fork" && goes.namesakes}
          <span class="text-warning">
            {tn(
              "You have one named so already; names needn't be unique.",
              "You have %(n)s named so already; names needn't be unique.",
              goes.namesakes,
              { n: goes.namesakes },
            )}
          </span>
        {/if}
      </p>
      {#if unsaved}
        <Alert.Root variant="destructive">
          <TriangleAlertIcon />
          <Alert.Description>{unsaved}</Alert.Description>
        </Alert.Root>
      {/if}
      <Button type="submit" disabled={goes.to === "nothing" || saving || waiting}>
        {#if saving}<LoaderCircleIcon class="animate-spin" />{/if}
        {t("Save")}
      </Button>
    </form>
  </section>
{:else}
  <p class="mb-6 text-sm text-muted-foreground">{t("It holds no recipe, so its parts can't be changed here.")}</p>
{/if}
