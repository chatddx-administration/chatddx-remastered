<script lang="ts">
  import CircleCheckIcon from "@lucide/svelte/icons/circle-check";
  import CircleXIcon from "@lucide/svelte/icons/circle-x";
  import InfoIcon from "@lucide/svelte/icons/info";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import TriangleAlertIcon from "@lucide/svelte/icons/triangle-alert";
  import * as Alert from "$lib/components/ui/alert";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import * as NativeSelect from "$lib/components/ui/native-select";
  import { api, type Schemas, why } from "$lib/api/client";
  import { worded } from "$lib/kinds";
  import { listed as joined, t, th, tn, tp } from "$lib/locale";
  import {
    type Carriage,
    carried,
    choicesOf,
    keptWith,
    named,
    PARTS,
    type Part,
    type Picked,
    queryOf,
    replaced,
    tagged,
    whereSaveGoes,
  } from "$lib/variation/logic";
  import { untrack } from "svelte";
  import type { Props } from "$lib/variation/props";

  let { held }: { held: Props } = $props();
  const given = untrack(() => held);
  const { configuration, me, versions, base, optional, models, families } = given;
  const familyNames: Record<string, string> = Object.fromEntries(families.map((f) => [f.id, f.name]));
  const head = given.look.head.id;
  const latest = versions.at(-1)?.id ?? head;
  const version = versions.findIndex((v) => v.id === head) + 1;

  let look = $state(given.look);
  let picked = $state<Picked>(pickedOf(given.look));
  let under = $state<string | null>(given.under);
  let tags = $state<string[]>(given.tags);
  let runs = $state(given.runs);
  let looking = $state(false);
  let failure = $state<string | null>(null);
  let name = $state(configuration.name ?? configuration.title);
  let saving = $state(false);
  let unsaved = $state<string | null>(null);
  let picking = $state(false);
  let chosen = $state<number[]>([]);
  let narrowed = $state("");
  let seed = $state(given.look.seed);
  let replicates = $state(1);
  let scored = $state(true);
  let starting = $state(false);
  let unstarted = $state<string | null>(null);

  const choices = Object.fromEntries(
    PARTS.map((p) => [
      p,
      choicesOf(given.choices[p], me, [
        ...(base[p] ? [{ digest: base[p], title: null }] : []),
        ...(given.look.parts ?? []).flatMap((h) =>
          h.part === p && h.digest ? [{ digest: h.digest, title: h.title }] : [],
        ),
      ]),
    ]),
  ) as Record<Part, ReturnType<typeof choicesOf>>;
  const compiled = given.look.parts !== null;

  const changed = $derived(Object.keys(replaced(picked, base)).length > 0);
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
  const shown = $derived(Object.fromEntries((look.parts ?? []).map((p) => [p.part, p])));
  const sent = $derived(picking ? families.filter((f) => chosen.includes(f.id)) : tagged(families, tags));
  const carriages = $derived(carried(sent, look.languages));
  const sending = $derived(carriages.filter((c) => c.refused === null));
  const leftOut = $derived(carriages.filter((c) => c.refused !== null));
  const items = $derived(sending.reduce((n, c) => n + c.families.length, 0) * Math.max(1, replicates));
  const largest = $derived(Math.max(0, ...sending.map((c) => c.families.length)) * Math.max(1, replicates));
  const listed = $derived(
    families.filter((f) => f.name.toLowerCase().includes(narrowed.trim().toLowerCase())).slice(0, 200),
  );
  const scorers = $derived(
    look.reach.reduce((found, r) => found.set(r.name, [...(found.get(r.name) ?? []), r]), new Map<string, Schemas["Reach"][]>()),
  );

  function pickedOf(variation: Schemas["Variation"]): Picked {
    const found = Object.fromEntries((variation.parts ?? []).map((p) => [p.part, p.digest]));
    return Object.fromEntries(PARTS.map((p) => [p, found[p] ?? null])) as Picked;
  }

  function cases(n: number): string {
    return tn("%(n)s case", "%(n)s cases", n, { n });
  }

  function sends(): string {
    if (look.model === null) {
      return compiled ? t("It can't run until its model can.") : t("Pick a model to run it under.");
    }
    if (sent.length === 0) return t("Pick a case to run it on.");
    if (items === 0) return t("None of its cases can be sent.");
    const given = {
      items: tn("%(n)s item", "%(n)s items", items, { n: items }),
      model: look.model,
      seeds: tn("%(n)s seed drawn", "%(n)s seeds drawn", replicates, { n: replicates }),
    };
    if (replicates > 1 && look.greedy) {
      return t(
        "Sends %(items)s under %(model)s, one at a time, a replicate each under %(seeds)s; its sampling is greedy, so no seed is sent and its replicates send the same request, which measures the engine's nondeterminism.",
        given,
      );
    }
    if (replicates > 1) {
      return t("Sends %(items)s under %(model)s, one at a time, a replicate each under %(seeds)s.", given);
    }
    if (look.greedy) {
      return t("Sends %(items)s under %(model)s, one at a time; its sampling is greedy, so the seed isn't sent.", given);
    }
    return t("Sends %(items)s under %(model)s, one at a time.", given);
  }

  function carriage(c: Carriage): string {
    const given = {
      where: c.language === null ? t("in its own language") : t("in %(language)s", { language: c.language }),
      cases: cases(c.families.length),
    };
    if (c.translated && !c.known) return t("%(where)s, %(cases)s, translated, if it can be", given);
    if (c.translated) return t("%(where)s, %(cases)s, translated", given);
    if (!c.known) return t("%(where)s, %(cases)s, if it can be", given);
    return t("%(where)s, %(cases)s", given);
  }

  function saves(): string {
    if (goes.to === "nothing" && goes.because === "nameless") return t("Give it a name to save it.");
    if (goes.to === "nothing") return t("Nothing to save: this is the configuration as it is.");
    if (goes.to === "version") return t("Saves version %(n)s of this configuration.", { n: goes.version });
    return t("Saves a new configuration of yours, “%(name)s”, forked from version %(n)s of this one.", {
      name: name.trim(),
      n: version,
    });
  }

  function when(at: string): string {
    return at.slice(0, 16).replace("T", " ");
  }

  function relink(): void {
    for (const a of document.querySelectorAll<HTMLAnchorElement>("a[data-head]")) {
      const query = queryOf({ picked, head: Number(a.dataset.head), under, tags }, base, latest);
      a.href = `?${keptWith(query, location.search)}`;
    }
  }

  let asked = 0;
  async function refresh(): Promise<void> {
    const query = queryOf({ picked, head, under, tags }, base, latest);
    const sent = ++asked;
    looking = true;
    const got = await api.GET("/api/threads/{thread}/variation", {
      params: { path: { thread: configuration.id } },
      querySerializer: () => `${query}&seed=${look.seed}`,
    });
    if (sent !== asked) return;
    looking = false;
    if (!got.data) {
      failure = why(got.error);
      return;
    }
    failure = null;
    const moved = got.data.skeleton !== look.skeleton;
    look = got.data;
    history.replaceState(null, "", `?${keptWith(query, location.search)}`);
    relink();
    if (moved) {
      const found = await api.GET("/api/runs", {
        params: { query: { reaching: got.data.skeleton, limit: 20 } },
      });
      if (sent === asked && found.data) runs = found.data;
    }
  }

  function pick(part: Part, digest: string): void {
    picked[part] = digest || null;
    void refresh();
  }

  function handled(name: string): void {
    under = name || null;
    void refresh();
  }

  function retagged(tag: string): void {
    tags = tags.includes(tag) ? tags.filter((t) => t !== tag) : [...tags, tag];
    void refresh();
  }

  function toggled(family: number): void {
    chosen = chosen.includes(family) ? chosen.filter((f) => f !== family) : [...chosen, family];
  }

  async function run(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    if (look.model === null || sent.length === 0) return;
    starting = true;
    unstarted = null;
    const got = await api.POST("/api/runs", {
      body: {
        configuration: configuration.id,
        head,
        parts: replaced(picked, base),
        ...(compiled || under === null ? {} : { under }),
        families: sent.map((f) => f.id),
        ...(replicates > 1 ? { replicates } : { seeds: [seed] }),
        score: scored,
      },
    });
    if (!got.data) {
      unstarted = why(got.error);
      starting = false;
      return;
    }
    location.assign(`/runs/${got.data.runs[0]?.run}`);
  }

  async function save(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    const to = goes.to;
    if (to === "nothing") return;
    saving = true;
    unsaved = null;
    const parts = replaced(picked, base);
    const path = { thread: configuration.id };
    const got =
      to === "version"
        ? await api.POST("/api/threads/{thread}/edits", {
            params: { path },
            body: { head: latest, parts },
          })
        : await api.POST("/api/threads/{thread}/forks", {
            params: { path },
            body: { name: name.trim(), head, parts },
          });
    if (!got.data) {
      unsaved = why(got.error);
      saving = false;
      return;
    }
    const kept = to === "version" ? configuration.id : got.data.id;
    const query = queryOf({ picked: base, head: latest, under, tags }, base, latest);
    location.assign(`/lab/${kept}?${keptWith(query, location.search)}`);
  }
</script>

<section class="mb-6 border-t border-border/60 pt-4">
  <div class="mb-4 flex flex-wrap items-center gap-3">
    <h2 class="text-lg font-semibold">{t("Trying it")}</h2>
    {#if looking}<LoaderCircleIcon class="size-4 animate-spin text-muted-foreground" aria-label={t("Looking")} />{/if}
  </div>
  <p class="mb-1 text-sm">
    {#if version !== versions.length}
      {@html th('<span class="font-medium">%(label)s</span><span class="text-muted-foreground">, on version %(n)s</span>', {
        label: look.label,
        n: version,
      })}
    {:else}
      <span class="font-medium">{look.label}</span>
    {/if}
  </p>
  <p class="mb-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
    <span class="font-mono">{look.skeleton.slice(7, 19)}</span>
    {#if look.greedy}<Badge variant="secondary">{t("greedy: no seed is sent")}</Badge>{/if}
    {#if look.held_by && (changed || head !== latest)}
      <span>
        {@html th('This is <a class="text-primary hover:underline" href="/lab/%(id)s">%(name)s</a> already.', {
          id: look.held_by.id,
          name: named(look.held_by, me),
        })}
      </span>
    {/if}
  </p>

  {#if failure}
    <Alert.Root variant="destructive" class="mb-4">
      <TriangleAlertIcon />
      <Alert.Description>{failure}</Alert.Description>
    </Alert.Root>
  {/if}

  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead class="text-left text-xs uppercase tracking-wide text-muted-foreground">
        <tr>
          <th class="pb-2 pr-4 font-medium">{t("Part")}</th>
          <th class="pb-2 font-medium">{t("Chunk")}</th>
        </tr>
      </thead>
      <tbody>
        {#each PARTS as part (part)}
          <tr class="border-t border-border/60">
            <td class="whitespace-nowrap py-2 pr-4 align-top font-medium">
              <label for="part-{part}">{worded(part)}</label>
            </td>
            <td class="py-2 align-top">
              <div class="flex items-center gap-2">
                <NativeSelect.Root
                  id="part-{part}"
                  size="sm"
                  class="w-full max-w-md"
                  value={picked[part] ?? ""}
                  onchange={(e) => pick(part, e.currentTarget.value)}
                >
                  {#if optional.includes(part) || picked[part] === null}
                    <NativeSelect.Option value="">{tp("no chunk", "None")}</NativeSelect.Option>
                  {/if}
                  {#each choices[part] as choice (choice.digest)}
                    <NativeSelect.Option value={choice.digest}>
                      {choice.digest === base[part] ? t("%(chunk)s (its own)", { chunk: choice.text }) : choice.text}
                    </NativeSelect.Option>
                  {/each}
                </NativeSelect.Root>
                {#if picked[part] !== base[part]}<Badge variant="outline">{tp("a part", "replaced")}</Badge>{/if}
              </div>
              {#if shown[part]?.summary || shown[part]?.landed}
                <p class="mt-1 text-xs text-muted-foreground">
                  {shown[part]?.summary ?? ""}
                  {#if shown[part]?.landed}
                    <span class="font-medium text-foreground">→ {shown[part]?.landed}</span>
                    {#each shown[part]?.nearest ?? [] as reason (reason)}
                      <span class="block text-warning">{t("its nearest: %(reason)s", { reason })}</span>
                    {/each}
                  {/if}
                </p>
              {/if}
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</section>

<section class="mb-6 border-t border-border/60 pt-4">
  <h2 class="mb-4 text-lg font-semibold">{t("What it makes")}</h2>
  <div class="mb-4 flex flex-wrap items-end gap-4">
    {#if !compiled}
      <div class="space-y-1.5">
        <Label for="model">{t("Under the model")}</Label>
        <NativeSelect.Root id="model" size="sm" value={under ?? ""} onchange={(e) => handled(e.currentTarget.value)}>
          <NativeSelect.Option value="">{t("None: no lints")}</NativeSelect.Option>
          {#each models as m (m)}
            <NativeSelect.Option value={m}>{m}</NativeSelect.Option>
          {/each}
        </NativeSelect.Root>
      </div>
    {/if}
    {#if look.model !== null}
      <p class="text-sm text-muted-foreground">{t("Runs under %(model)s.", { model: look.model })}</p>
    {:else if compiled || under !== null}
      <p class="text-sm text-warning">{look.problem}</p>
    {/if}
  </div>
  {#if !given.judged && given.everyTag.length}
    <div class="mb-4">
      <p class="mb-1.5 text-sm font-medium">{t("Over the cases tagged")}</p>
      <div class="flex flex-wrap gap-1.5">
        {#each given.everyTag as tag (tag)}
          <button
            type="button"
            class="rounded-full border px-2.5 py-0.5 text-xs {tags.includes(tag) ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:bg-muted'}"
            aria-pressed={tags.includes(tag)}
            onclick={() => retagged(tag)}>{tag}</button
          >
        {/each}
      </div>
      <p class="mt-1.5 text-xs text-muted-foreground">
        {tags.length ? t("Any of these.") : t("None picked: every case you see.")}
      </p>
    </div>
  {/if}

  <h3 class="mb-2 text-sm font-medium">{t("What the lints say")}</h3>
  {#if look.findings === null}
    <p class="text-sm text-muted-foreground">{compiled ? t("No lints while it can't run.") : t("Pick a model to lint it under.")}</p>
  {:else if look.findings.length === 0}
    <p class="text-sm text-muted-foreground">{tp("no lints", "Nothing.")}</p>
  {:else}
    <ul class="space-y-1.5 text-sm">
      {#each look.findings as finding, i (i)}
        <li class="flex gap-2">
          {#if finding.level === "warning"}
            <TriangleAlertIcon class="mt-0.5 size-4 shrink-0 text-warning" />
          {:else}
            <InfoIcon class="mt-0.5 size-4 shrink-0 text-primary" />
          {/if}
          <span>{finding.message} <span class="text-xs text-muted-foreground">{finding.code}</span></span>
        </li>
      {/each}
    </ul>
  {/if}

  <h3 class="mt-6 mb-2 text-sm font-medium">{t("What scorers can read")}</h3>
  {#if look.reach.length === 0}
    <p class="text-sm text-muted-foreground">{t("No scorer reads it.")}</p>
  {:else}
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="text-left text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th class="pb-2 pr-4 font-medium">{t("Scorer")}</th>
            <th class="pb-2 pr-4 font-medium">{t("View")}</th>
            <th class="pb-2 pr-4 font-medium">{t("Offered")}</th>
            <th class="pb-2 font-medium">{t("Cases")}</th>
          </tr>
        </thead>
        <tbody>
          {#each [...scorers] as [scorer, views] (scorer)}
            {#each views as view, i (view.view)}
              <tr class="border-t border-border/60">
                <td class="py-2 pr-4 align-top font-medium">{i === 0 ? scorer : ""}</td>
                <td class="py-2 pr-4 align-top">{view.label}</td>
                <td class="py-2 pr-4 align-top">
                  {#if view.offered}
                    <CircleCheckIcon class="size-4 text-success" aria-label={t("offered")} />
                  {:else}
                    <CircleXIcon class="size-4 text-muted-foreground" aria-label={t("not offered")} />
                  {/if}
                </td>
                <td class="py-2 align-top text-muted-foreground">
                  {#if !view.offered}
                    {t("Not read from this output.")}
                  {:else}
                    {tn(
                      "%(have)s of %(n)s case has an expectation for it",
                      "%(have)s of %(n)s cases have an expectation for it",
                      view.cases,
                      { have: view.cases - view.missing.length - view.choosing.length, n: view.cases },
                    )}
                  {/if}
                  {#if view.missing.length}
                    <details class="mt-1">
                      <summary class="cursor-pointer text-xs">
                        {tn("%(n)s without one", "%(n)s without one", view.missing.length, { n: view.missing.length })}
                      </summary>
                      <p class="mt-1 text-xs">
                        {#each view.missing as family, j (family)}<a class="text-primary hover:underline" href="/cases/{family}">{familyNames[family] ?? family}</a>{j < view.missing.length - 1 ? ", " : ""}{/each}
                      </p>
                    </details>
                  {/if}
                  {#if view.choosing.length}
                    <p class="mt-1 text-xs text-warning">
                      {t("Several to choose from:")}
                      {#each view.choosing as family, j (family)}<a class="hover:underline" href="/cases/{family}">{familyNames[family] ?? family}</a>{j < view.choosing.length - 1 ? ", " : ""}{/each}
                    </p>
                  {/if}
                </td>
              </tr>
            {/each}
          {/each}
        </tbody>
      </table>
    </div>
  {/if}

  <details class="mt-6 rounded-lg border border-border/60 bg-background/40 p-3">
    <summary class="cursor-pointer text-sm font-medium">{t("The request it would send")}</summary>
    <pre class="mt-2 overflow-x-auto font-mono text-xs leading-relaxed">{JSON.stringify(look.request, null, 2)}</pre>
  </details>
</section>

{#if !given.judged}
<section class="mb-6 border-t border-border/60 pt-4">
  <h2 class="mb-4 text-lg font-semibold">{t("Running it")}</h2>
  <form class="space-y-4" onsubmit={run}>
    <fieldset class="space-y-2">
      <legend class="mb-1.5 text-sm font-medium">{t("On the cases")}</legend>
      <label class="flex items-center gap-2 text-sm">
        <input type="radio" name="cases" checked={!picking} onchange={() => (picking = false)} />
        {tags.length
          ? t("tagged %(tags)s (%(n)s)", { tags: joined(tags, "disjunction"), n: tagged(families, tags).length })
          : t("every one you see (%(n)s)", { n: tagged(families, tags).length })}
      </label>
      <label class="flex items-center gap-2 text-sm">
        <input type="radio" name="cases" checked={picking} onchange={() => (picking = true)} />
        {t("of the families picked (%(n)s)", { n: chosen.length })}
      </label>
      {#if picking}
        <div class="ml-6 space-y-2">
          {#if chosen.length}
            <div class="flex flex-wrap gap-1.5">
              {#each families.filter((f) => chosen.includes(f.id)) as f (f.id)}
                <button
                  type="button"
                  class="rounded-full border border-primary bg-primary/10 px-2.5 py-0.5 text-xs text-primary hover:bg-primary/20"
                  aria-label={t("Leave out %(name)s", { name: f.name })}
                  onclick={() => toggled(f.id)}>{f.name} ×</button
                >
              {/each}
            </div>
          {/if}
          <Input
            bind:value={narrowed}
            placeholder={t("Find a family by name")}
            class="max-w-sm"
            aria-label={t("Find a family")}
          />
          <div class="max-h-48 max-w-sm overflow-y-auto rounded-md border border-border p-2 text-sm">
            {#each listed as f (f.id)}
              <label class="flex items-center gap-2 py-0.5">
                <input type="checkbox" checked={chosen.includes(f.id)} onchange={() => toggled(f.id)} />
                {f.name}
              </label>
            {:else}
              <p class="text-muted-foreground">{t("No family by that name.")}</p>
            {/each}
          </div>
        </div>
      {/if}
    </fieldset>
    <div class="flex flex-wrap items-end gap-4">
      <div class="space-y-1.5">
        <Label for="run-seed">{t("Seed")}</Label>
        <Input id="run-seed" type="number" min="0" bind:value={seed} disabled={replicates > 1} class="w-36" />
      </div>
      <div class="space-y-1.5">
        <Label for="run-replicates">{t("Replicates")}</Label>
        <Input id="run-replicates" type="number" min="1" bind:value={replicates} class="w-24" />
      </div>
      <label class="flex items-center gap-2 pb-2 text-sm">
        <input type="checkbox" bind:checked={scored} />
        {t("Score it when it's done")}
      </label>
    </div>
    <p class="text-sm" aria-live="polite">
      {sends()}
      {#if look.model !== null && sent.length > 0 && items > 0 && largest > given.itemsPerRun}
        <span class="text-warning">
          {tn("A run holds at most %(n)s.", "A run holds at most %(n)s.", given.itemsPerRun, { n: given.itemsPerRun })}
        </span>
      {/if}
    </p>
    {#if sent.length > 0 && (carriages.length > 1 || carriages.some((c) => c.translated || !c.known))}
      <p class="text-sm" aria-live="polite">
        {sending.length > 1
          ? t("A run per language: %(runs)s.", { runs: sending.map(carriage).join("; ") })
          : t("%(run)s.", { run: sending.map(carriage).join("; ") })}
      </p>
    {/if}
    {#if leftOut.length}
      <ul class="space-y-1 text-sm text-warning" aria-live="polite">
        {#each leftOut as c (c.language)}
          <li>
            {t("Left out: %(cases)s in %(language)s, as %(refused)s.", {
              cases: cases(c.families.length),
              language: c.language ?? "",
              refused: c.refused ?? "",
            })}
          </li>
        {/each}
      </ul>
    {/if}
    {#if unstarted}
      <Alert.Root variant="destructive">
        <TriangleAlertIcon />
        <Alert.Description>{unstarted}</Alert.Description>
      </Alert.Root>
    {/if}
    <Button
      type="submit"
      disabled={look.model === null || items === 0 || largest > given.itemsPerRun || starting || failure !== null}
    >
      {#if starting}<LoaderCircleIcon class="animate-spin" />{/if}
      {t("Run it")}
    </Button>
  </form>
</section>
{/if}

<section class="mb-6 border-t border-border/60 pt-4">
  <h2 class="mb-4 text-lg font-semibold">{t("Saving it")}</h2>
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
    <Button type="submit" disabled={goes.to === "nothing" || saving || failure !== null}>
      {#if saving}<LoaderCircleIcon class="animate-spin" />{/if}
      {t("Save")}
    </Button>
  </form>
</section>

{#if !given.judged}
<section class="mb-6 border-t border-border/60 pt-4">
  <h2 class="mb-4 text-lg font-semibold">{t("Its runs")}</h2>
  {#if runs.length === 0}
    <p class="text-sm text-muted-foreground">{t("No runs of it.")}</p>
  {:else}
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="text-left text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th class="pb-2 pr-4 font-medium">{t("Started")}</th>
            <th class="pb-2 pr-4 font-medium">{t("Run")}</th>
            <th class="pb-2 pr-4 font-medium">{t("Model")}</th>
            <th class="pb-2 font-medium">{t("Finished")}</th>
          </tr>
        </thead>
        <tbody>
          {#each runs as run (run.id)}
            <tr class="border-t border-border/60">
              <td class="whitespace-nowrap py-2 pr-4 align-top text-muted-foreground">{when(run.at)}</td>
              <td class="py-2 pr-4 align-top">
                <a href="/runs/{run.id}" class="text-primary hover:underline">{run.described}</a>
              </td>
              <td class="whitespace-nowrap py-2 pr-4 align-top">{run.model ?? "—"}</td>
              <td class="py-2 align-top">{run.finished ? tp("a run finished", "yes") : tp("a run finished", "no")}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</section>
{/if}
