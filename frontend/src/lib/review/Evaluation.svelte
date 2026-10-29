<script lang="ts">
  import { onMount, untrack } from "svelte";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import { api, type Schemas, why } from "$lib/api/client";
  import { t } from "$lib/locale";
  import { watch } from "$lib/runs/events";
  import { fieldName } from "$lib/schema/form";
  import {
    cells,
    type Ended,
    type Evaluating,
    keyed,
    replicates,
    said,
    type Scored,
    shown,
    valued,
    worded,
  } from "./evaluation";

  let { evaluation, settled }: { evaluation: Evaluating; settled: (runs: string[]) => void } = $props();

  type Seen = {
    given: Evaluating;
    runs: string[];
    ended: Record<string, Ended>;
    begun: Record<string, true>;
    scored: Scored;
    named: Record<string, string>;
    scorers: Record<string, string>;
    done: Record<string, true>;
    lost: Record<string, string>;
    read: Record<string, Schemas["ItemDetail"][] | string>;
  };

  function fresh(given: Evaluating): Seen {
    const runs = given.configurations.flatMap((c) => c.runs.map((r) => r.run));
    return { given, runs, ended: {}, begun: {}, scored: {}, named: {}, scorers: {}, done: {}, lost: {}, read: {} };
  }

  const first = untrack(() => evaluation.key);
  let seen = $state<Record<string, Seen>>({ [first]: fresh(untrack(() => evaluation)) });
  let showing = $state(first);
  let wanted = $state(first);
  const s = $derived(seen[showing] as Seen);
  let halting = $state(false);
  let unhalted = $state<string | null>(null);
  const open = $derived(s.runs.filter((r) => !s.done[r] && s.lost[r] === undefined));
  const complete = (at: Seen) => at.runs.every((r) => at.done[r] || at.lost[r] !== undefined);
  $effect(() => {
    if (!open.length) settled(s.runs);
  });
  $effect(() => {
    const at = seen[wanted];
    if (wanted !== showing && at && complete(at)) showing = wanted;
  });

  function heard(into: Seen, run: string, name: string, data: unknown): void {
    if (name === "item.started") {
      const at = data as Schemas["ItemStartedData"];
      into.begun[keyed(run, at.replicate)] = true;
    } else if (name === "item.ended") {
      const at = data as Schemas["ItemEndedData"];
      into.ended[keyed(run, at.replicate)] = at;
    } else if (name === "score.started") {
      const at = data as Schemas["ScoreStartedData"];
      into.scorers[at.score] = at.scorer;
      into.named[at.scorer] = at.name;
    } else if (name === "score.item") {
      const at = data as Schemas["ScoreItemData"];
      const scorer = into.scorers[at.score];
      if (scorer === undefined) return;
      const key = keyed(run, at.replicate);
      into.scored[key] = { ...into.scored[key], [`${scorer}#${at.view}`]: at.value };
    }
  }

  // Policy: so many streams at once and no more, so that the six connections a browser holds to a host over HTTP/1.1
  // leave room for the page's own requests, a halt's among them; a stream joined late tells the rows before it.
  const WATCHED = 4;
  const waiting: [string, string][] = [];
  let watching = 0;

  function pump(): void {
    while (watching < WATCHED) {
      const next = waiting.shift();
      if (next === undefined) return;
      const [at, run] = next;
      watching++;
      watch(run, (name, data) => heard(seen[at] as Seen, run, name, data))
        .then(() => ((seen[at] as Seen).done[run] = true))
        .catch((e: unknown) => ((seen[at] as Seen).lost[run] = e instanceof Error ? e.message : String(e)))
        .finally(() => {
          watching--;
          pump();
        });
    }
  }

  onMount(() => {
    waiting.push(...s.runs.map((r): [string, string] => [first, r]));
    pump();
  });

  // Policy: the values shown stay till the next evaluation's have come, so that the table doesn't empty and
  // jump between them; one under way shows as soon as it has had a moment to tell what it holds.
  const PATIENCE = 1500;

  export function show(next: Evaluating): void {
    const at = next.key;
    if (seen[at] === undefined) {
      seen[at] = fresh(next);
      waiting.unshift(...(seen[at] as Seen).runs.map((r): [string, string] => [at, r]));
      pump();
    }
    halting = false;
    unhalted = null;
    wanted = at;
    setTimeout(() => {
      if (wanted === at) showing = at;
    }, PATIENCE);
  }

  async function halt(): Promise<void> {
    halting = true;
    unhalted = null;
    const got = await Promise.all(open.map((run) => api.POST("/api/runs/{run}/halt", { params: { path: { run } } })));
    // Policy: as on the run page, a run with nothing left under way is halted already.
    const failed = got.find((g) => g.error !== undefined && g.response.status !== 409);
    if (failed) {
      unhalted = why(failed.error);
      halting = false;
    }
  }

  async function opened(run: string): Promise<void> {
    const at = s;
    if (at.read[run] !== undefined && at.done[run]) return;
    const got = await api.GET("/api/runs/{run}/items", {
      params: { path: { run }, query: { case: at.given.case } },
    });
    at.read[run] = got.data ?? why(got.error);
  }

  const tones: Record<string, string> = {
    valid: "border-success/30 bg-success/10 text-success",
    salvaged: "border-warning/30 bg-warning/10 text-warning",
    broken: "border-destructive/30 bg-destructive/10 text-destructive",
    stopped: "border-border bg-muted text-muted-foreground",
  };
</script>

{#if open.length}
  <div class="mb-3 flex flex-wrap items-center gap-3 text-sm">
    <button class="primary danger" disabled={halting} onclick={halt}>{t("Halt")}</button>
    {#if unhalted}<span role="alert" class="text-destructive">{unhalted}</span>{/if}
  </div>
{/if}

<div class="overflow-x-auto">
  <table class="w-full text-sm">
    <thead>
      <tr class="text-left text-[0.7rem] tracking-wide text-muted-foreground uppercase">
        <th class="py-2 pr-3 font-medium">{t("Configuration")}</th>
        {#each s.given.fields as field (field)}<th class="px-3 py-2 font-medium">{fieldName(field)}</th>{/each}
      </tr>
    </thead>
    <tbody>
      {#each s.given.configurations as c (c.configuration)}
        {@const finished = c.runs.every((r) => s.done[r.run])}
        <tr class="border-t border-border/60 align-top">
          <th scope="row" class="py-2 pr-3 text-left font-medium">
            {c.name}
            {#if !finished}<LoaderCircleIcon class="ml-1 inline size-3.5 animate-spin text-muted-foreground" />{/if}
          </th>
          {#each s.given.fields as field (field)}
            {@const found = cells(c, field, s.scored, s.given.scorers)}
            <td class="px-3 py-2">
              {#each found as cell (`${cell.scorer}#${cell.view}`)}
                {@const twice = found.filter((other) => other.label === cell.label).length > 1}
                <div class="flex justify-between gap-2" title={s.named[cell.scorer]}>
                  <span class="text-muted-foreground"
                    >{twice && s.named[cell.scorer] ? `${s.named[cell.scorer]} › ${cell.label}` : cell.label}</span
                  >
                  <span class="tabular-nums">{valued(cell.mean, cell.unit)}</span>
                </div>
              {:else}
                <span class="text-muted-foreground">{finished ? "—" : "…"}</span>
              {/each}
            </td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>

{#each Object.entries(s.lost) as [run, problem] (run)}
  <p role="alert" class="mt-3 text-sm text-destructive">{problem} <a href="/runs/{run}">{t("Its run")}</a></p>
{/each}

<div class="mt-6 space-y-1.5">
  {#each s.given.configurations as c (c.configuration)}
    {#each replicates(c) as r (r.key)}
      {@const item = s.ended[r.key]}
      <details class="rounded-lg border border-border/60" ontoggle={(e) => e.currentTarget.open && opened(r.run)}>
        <summary
          class="grid cursor-pointer grid-cols-[minmax(0,1fr)_auto_auto_auto] items-center gap-3 px-3 py-2 text-sm"
        >
          <span class="min-w-0 truncate font-medium">{c.name}</span>
          <span class="text-xs text-muted-foreground tabular-nums"
            >#{r.n}{r.seed === null ? "" : ` · ${t("seed %(seed)s", { seed: r.seed })}`}</span
          >
          <span class="text-xs text-muted-foreground tabular-nums">
            {#if item}{t("%(prompt)s + %(completion)s tokens", {
                prompt: item.prompt_tokens,
                completion: item.completion_tokens,
              })}{/if}
          </span>
          {#if item}
            <span
              class="inline-flex rounded-full border px-2 py-0.5 text-xs font-medium {tones[worded(item.outcome)]}"
              title={item.why ?? undefined}>{said(worded(item.outcome))}</span
            >
          {:else}
            <span class="text-xs text-muted-foreground">{s.begun[r.key] ? t("under way") : t("queued")}</span>
          {/if}
        </summary>
        <div class="border-t border-border/60 px-3 py-2 text-sm">
          <div class="mb-2 text-xs"><a href="/runs/{r.run}">{t("Its run")}</a></div>
          {#if typeof s.read[r.run] === "string"}
            <p class="text-destructive">{s.read[r.run]}</p>
          {:else if s.read[r.run] === undefined}
            <LoaderCircleIcon class="size-4 animate-spin text-muted-foreground" />
          {:else}
            {@const detail = (s.read[r.run] as Schemas["ItemDetail"][]).find((d) => d.replicate === r.replicate)}
            {#if !detail}
              <p class="text-muted-foreground">{t("Nothing has come back yet.")}</p>
            {:else}
              {#if detail.answer.problem}<p class="mb-2 text-warning">{detail.answer.problem}</p>{/if}
              {@const output = shown(detail.answer.value)}
              {#if "code" in output}
                <pre class="overflow-x-auto rounded-md bg-muted/60 p-3 font-mono text-xs"><code>{output.code}</code
                  ></pre>
              {:else}
                <p class="whitespace-pre-wrap">{output.text}</p>
              {/if}
            {/if}
          {/if}
        </div>
      </details>
    {/each}
  {/each}
</div>
