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

  let { evaluation }: { evaluation: Evaluating } = $props();
  const given = untrack(() => evaluation);
  const runs = given.configurations.flatMap((c) => c.runs.map((r) => r.run));

  let ended = $state<Record<string, Ended>>({});
  let begun = $state<Record<string, true>>({});
  let scored = $state<Scored>({});
  let named = $state<Record<string, string>>({});
  let done = $state<Record<string, true>>({});
  let lost = $state<Record<string, string>>({});
  let read = $state<Record<string, Schemas["ItemDetail"][] | string>>({});
  const scorers = new Map<string, string>();

  function heard(run: string, name: string, data: unknown): void {
    if (name === "item.started") {
      const at = data as Schemas["ItemStartedData"];
      begun[keyed(run, at.replicate)] = true;
    } else if (name === "item.ended") {
      const at = data as Schemas["ItemEndedData"];
      ended[keyed(run, at.replicate)] = at;
    } else if (name === "score.started") {
      const at = data as Schemas["ScoreStartedData"];
      scorers.set(at.score, at.scorer);
      named[at.scorer] = at.name;
    } else if (name === "score.item") {
      const at = data as Schemas["ScoreItemData"];
      const scorer = scorers.get(at.score);
      if (scorer === undefined) return;
      const key = keyed(run, at.replicate);
      scored[key] = { ...scored[key], [`${scorer}#${at.view}`]: at.value };
    }
  }

  onMount(() => {
    for (const run of runs) {
      watch(run, (name, data) => heard(run, name, data))
        .then(() => (done[run] = true))
        .catch((e: unknown) => (lost[run] = e instanceof Error ? e.message : String(e)));
    }
  });

  async function opened(run: string): Promise<void> {
    if (read[run] !== undefined && done[run]) return;
    const got = await api.GET("/api/runs/{run}/items", {
      params: { path: { run }, query: { case: given.case } },
    });
    read[run] = got.data ?? why(got.error);
  }

  const tones: Record<string, string> = {
    valid: "border-success/30 bg-success/10 text-success",
    salvaged: "border-warning/30 bg-warning/10 text-warning",
    broken: "border-destructive/30 bg-destructive/10 text-destructive",
    stopped: "border-border bg-muted text-muted-foreground",
  };
</script>

<div class="overflow-x-auto">
  <table class="w-full text-sm">
    <thead>
      <tr class="text-left text-[0.7rem] tracking-wide text-muted-foreground uppercase">
        <th class="py-2 pr-3 font-medium">{t("Configuration")}</th>
        {#each given.fields as field (field)}<th class="px-3 py-2 font-medium">{fieldName(field)}</th>{/each}
      </tr>
    </thead>
    <tbody>
      {#each given.configurations as c (c.configuration)}
        {@const finished = c.runs.every((r) => done[r.run])}
        <tr class="border-t border-border/60 align-top">
          <th scope="row" class="py-2 pr-3 text-left font-medium">
            {c.name}
            {#if !finished}<LoaderCircleIcon class="ml-1 inline size-3.5 animate-spin text-muted-foreground" />{/if}
          </th>
          {#each given.fields as field (field)}
            {@const found = cells(c, field, scored, given.scorers)}
            <td class="px-3 py-2">
              {#each found as cell (`${cell.scorer}#${cell.view}`)}
                {@const twice = found.filter((other) => other.label === cell.label).length > 1}
                <div class="flex justify-between gap-2" title={named[cell.scorer]}>
                  <span class="text-muted-foreground"
                    >{twice && named[cell.scorer] ? `${named[cell.scorer]} › ${cell.label}` : cell.label}</span
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

{#each Object.entries(lost) as [run, problem] (run)}
  <p role="alert" class="mt-3 text-sm text-destructive">{problem} <a href="/runs/{run}">{t("Its run")}</a></p>
{/each}

<div class="mt-6 space-y-1.5">
  {#each given.configurations as c (c.configuration)}
    {#each replicates(c) as r (r.key)}
      {@const item = ended[r.key]}
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
            <span class="text-xs text-muted-foreground">{begun[r.key] ? t("under way") : t("queued")}</span>
          {/if}
        </summary>
        <div class="border-t border-border/60 px-3 py-2 text-sm">
          {#if typeof read[r.run] === "string"}
            <p class="text-destructive">{read[r.run]}</p>
          {:else if read[r.run] === undefined}
            <LoaderCircleIcon class="size-4 animate-spin text-muted-foreground" />
          {:else}
            {@const detail = (read[r.run] as Schemas["ItemDetail"][]).find((d) => d.replicate === r.replicate)}
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
