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
  import {
    choicesOf,
    named,
    PARTS,
    type Part,
    type Picked,
    queryOf,
    replaced,
    whereSaveGoes,
  } from "$lib/variation/logic";
  import { untrack } from "svelte";
  import type { Props } from "$lib/variation/props";

  let { held }: { held: Props } = $props();
  const given = untrack(() => held);
  const { configuration, me, versions, base, optional, endpoints, variants, families } = given;
  const head = given.look.head.id;
  const latest = versions.at(-1)?.id ?? head;
  const version = versions.findIndex((v) => v.id === head) + 1;

  let look = $state(given.look);
  let picked = $state<Picked>(pickedOf(given.look));
  let endpoint = $state<string | null>(given.endpoint);
  let tags = $state<string[]>(given.tags);
  let runs = $state(given.runs);
  let looking = $state(false);
  let failure = $state<string | null>(null);
  let name = $state(configuration.name ?? configuration.title);
  let saving = $state(false);
  let unsaved = $state<string | null>(null);

  const groups = Object.fromEntries(
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
  const fitting = $derived(endpoint === null ? undefined : variants[endpoint]);
  const scorers = $derived(
    look.reach.reduce((found, r) => found.set(r.name, [...(found.get(r.name) ?? []), r]), new Map<string, Schemas["Reach"][]>()),
  );

  function pickedOf(variation: Schemas["Variation"]): Picked {
    const found = Object.fromEntries((variation.parts ?? []).map((p) => [p.part, p.digest]));
    return Object.fromEntries(PARTS.map((p) => [p, found[p] ?? null])) as Picked;
  }

  function when(at: string): string {
    return at.slice(0, 16).replace("T", " ");
  }

  function relink(): void {
    for (const a of document.querySelectorAll<HTMLAnchorElement>("a[data-head]")) {
      const query = queryOf({ picked, head: Number(a.dataset.head), endpoint, tags }, base, latest);
      a.href = `?${query}`;
    }
  }

  let asked = 0;
  async function refresh(): Promise<void> {
    const query = queryOf({ picked, head, endpoint, tags }, base, latest);
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
    history.replaceState(null, "", `?${query}`);
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

  function at(name: string): void {
    endpoint = name || null;
    void refresh();
  }

  function tagged(tag: string): void {
    tags = tags.includes(tag) ? tags.filter((t) => t !== tag) : [...tags, tag];
    void refresh();
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
    const query = queryOf({ picked: base, head: latest, endpoint, tags }, base, latest);
    location.assign(`/configurations/${kept}?${query}`);
  }
</script>

<section class="glass-card mb-6 rounded-2xl p-5 sm:p-6">
  <div class="mb-4 flex flex-wrap items-center gap-3">
    <h2 class="text-lg font-semibold">Trying it</h2>
    {#if looking}<LoaderCircleIcon class="size-4 animate-spin text-muted-foreground" aria-label="Looking" />{/if}
  </div>
  <p class="mb-1 text-sm">
    <span class="font-medium">{look.label}</span>{#if version !== versions.length}<span
        class="text-muted-foreground">, on version {version}</span
      >{/if}
  </p>
  <p class="mb-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
    <span class="font-mono">{look.skeleton.slice(7, 19)}</span>
    {#if look.greedy}<Badge variant="secondary">greedy: no seed is sent</Badge>{/if}
    {#if look.held_by && (changed || head !== latest)}
      <span>
        This is
        <a class="text-primary hover:underline" href="/configurations/{look.held_by.id}">{named(look.held_by, me)}</a>
        already.
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
          <th class="pb-2 pr-4 font-medium">Part</th>
          <th class="pb-2 pr-4 font-medium">Chunk</th>
          <th class="pb-2 font-medium">Holds</th>
        </tr>
      </thead>
      <tbody>
        {#each PARTS as part (part)}
          <tr class="border-t border-border/60">
            <td class="whitespace-nowrap py-2 pr-4 align-top font-medium">
              <label for="part-{part}">{part.replace("_", " ")}</label>
            </td>
            <td class="py-2 pr-4 align-top">
              <div class="flex items-center gap-2">
                <NativeSelect.Root
                  id="part-{part}"
                  size="sm"
                  class="max-w-md"
                  value={picked[part] ?? ""}
                  onchange={(e) => pick(part, e.currentTarget.value)}
                >
                  {#if optional.includes(part) || picked[part] === null}
                    <NativeSelect.Option value="">None</NativeSelect.Option>
                  {/if}
                  {#each groups[part] as group (group.label)}
                    <NativeSelect.OptGroup label={group.label}>
                      {#each group.choices as choice (choice.digest)}
                        <NativeSelect.Option value={choice.digest}>
                          {choice.text}{choice.digest === base[part] ? " (its own)" : ""}
                        </NativeSelect.Option>
                      {/each}
                    </NativeSelect.OptGroup>
                  {/each}
                </NativeSelect.Root>
                {#if picked[part] !== base[part]}<Badge variant="outline">replaced</Badge>{/if}
              </div>
            </td>
            <td class="py-2 align-top text-muted-foreground">{shown[part]?.summary ?? ""}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</section>

<section class="glass-card mb-6 rounded-2xl p-5 sm:p-6">
  <h2 class="mb-4 text-lg font-semibold">What it makes</h2>
  <div class="mb-4 flex flex-wrap items-end gap-4">
    <div class="space-y-1.5">
      <Label for="endpoint">At the endpoint</Label>
      <NativeSelect.Root id="endpoint" size="sm" value={endpoint ?? ""} onchange={(e) => at(e.currentTarget.value)}>
        <NativeSelect.Option value="">None: no lints</NativeSelect.Option>
        {#each endpoints as e (e.name)}
          <NativeSelect.Option value={e.name} disabled={e.problem !== null}>
            {e.name}{e.model ? ` (${e.model})` : ""}
          </NativeSelect.Option>
        {/each}
      </NativeSelect.Root>
    </div>
    {#if fitting && fitting.id !== configuration.id}
      <p class="text-sm text-muted-foreground">
        <a class="text-primary hover:underline" href="/configurations/{fitting.id}?endpoint={encodeURIComponent(endpoint ?? '')}">{named(fitting, me)}</a>
        is made for this endpoint's model.
      </p>
    {/if}
  </div>
  {#if given.everyTag.length}
    <div class="mb-4">
      <p class="mb-1.5 text-sm font-medium">Over the cases tagged</p>
      <div class="flex flex-wrap gap-1.5">
        {#each given.everyTag as tag (tag)}
          <button
            type="button"
            class="rounded-full border px-2.5 py-0.5 text-xs {tags.includes(tag) ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:bg-muted'}"
            aria-pressed={tags.includes(tag)}
            onclick={() => tagged(tag)}>{tag}</button
          >
        {/each}
      </div>
      <p class="mt-1.5 text-xs text-muted-foreground">
        {tags.length ? "Any of these." : "None picked: every case you see."}
      </p>
    </div>
  {/if}

  <h3 class="mb-2 text-sm font-medium">What the lints say</h3>
  {#if look.findings === null}
    <p class="text-sm text-muted-foreground">Pick an endpoint to lint it there.</p>
  {:else if look.findings.length === 0}
    <p class="text-sm text-muted-foreground">Nothing.</p>
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

  <h3 class="mt-6 mb-2 text-sm font-medium">What scorers can read</h3>
  {#if look.reach.length === 0}
    <p class="text-sm text-muted-foreground">No scorer reads it.</p>
  {:else}
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="text-left text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th class="pb-2 pr-4 font-medium">Scorer</th>
            <th class="pb-2 pr-4 font-medium">View</th>
            <th class="pb-2 pr-4 font-medium">Offered</th>
            <th class="pb-2 font-medium">Cases</th>
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
                    <CircleCheckIcon class="size-4 text-success" aria-label="offered" />
                  {:else}
                    <CircleXIcon class="size-4 text-muted-foreground" aria-label="not offered" />
                  {/if}
                </td>
                <td class="py-2 align-top text-muted-foreground">
                  {#if !view.offered}
                    Not read from this output.
                  {:else}
                    {view.cases - view.missing.length - view.choosing.length} of {view.cases} cases have an expectation
                    for it
                  {/if}
                  {#if view.missing.length}
                    <details class="mt-1">
                      <summary class="cursor-pointer text-xs">{view.missing.length} without one</summary>
                      <p class="mt-1 text-xs">
                        {#each view.missing as family, j (family)}<a class="text-primary hover:underline" href="/families/{family}">{families[family] ?? family}</a>{j < view.missing.length - 1 ? ", " : ""}{/each}
                      </p>
                    </details>
                  {/if}
                  {#if view.choosing.length}
                    <p class="mt-1 text-xs text-warning">
                      Several to choose from:
                      {#each view.choosing as family, j (family)}<a class="hover:underline" href="/families/{family}">{families[family] ?? family}</a>{j < view.choosing.length - 1 ? ", " : ""}{/each}
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
    <summary class="cursor-pointer text-sm font-medium">The request it would send</summary>
    <pre class="mt-2 overflow-x-auto font-mono text-xs leading-relaxed">{JSON.stringify(look.request, null, 2)}</pre>
  </details>
</section>

<section class="glass-card mb-6 rounded-2xl p-5 sm:p-6">
  <h2 class="mb-4 text-lg font-semibold">Saving it</h2>
  <form class="space-y-3" onsubmit={save}>
    <div class="space-y-1.5">
      <Label for="saved-name">Name</Label>
      <Input id="saved-name" bind:value={name} class="max-w-md" autocomplete="off" />
    </div>
    <p class="text-sm" aria-live="polite">
      {#if goes.to === "nothing" && goes.because === "nameless"}
        Give it a name to save it.
      {:else if goes.to === "nothing"}
        Nothing to save: this is the configuration as it is.
      {:else if goes.to === "version"}
        Saves version {goes.version} of this configuration.
      {:else}
        Saves a new configuration of yours, “{name.trim()}”, forked from version {version} of this one.
        {#if goes.namesakes}
          <span class="text-warning">
            You have {goes.namesakes === 1 ? "one" : goes.namesakes} named so already; names needn't be unique.
          </span>
        {/if}
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
      Save
    </Button>
  </form>
</section>

<section class="glass-card mb-6 rounded-2xl p-5 sm:p-6">
  <h2 class="mb-4 text-lg font-semibold">Its runs</h2>
  {#if runs.length === 0}
    <p class="text-sm text-muted-foreground">No runs of it.</p>
  {:else}
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="text-left text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th class="pb-2 pr-4 font-medium">Started</th>
            <th class="pb-2 pr-4 font-medium">Run</th>
            <th class="pb-2 pr-4 font-medium">Endpoint</th>
            <th class="pb-2 font-medium">Finished</th>
          </tr>
        </thead>
        <tbody>
          {#each runs as run (run.id)}
            <tr class="border-t border-border/60">
              <td class="whitespace-nowrap py-2 pr-4 align-top text-muted-foreground">{when(run.at)}</td>
              <td class="py-2 pr-4 align-top">
                <a href="/runs/{run.id}" class="text-primary hover:underline">{run.described}</a>
              </td>
              <td class="whitespace-nowrap py-2 pr-4 align-top">{run.endpoint ?? "—"}</td>
              <td class="py-2 align-top">{run.finished ? "yes" : "no"}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</section>
