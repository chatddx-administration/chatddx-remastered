<script lang="ts" module>
  import type { ScorerBody, Scoring } from "./scorers";

  export type { ScorerView } from "./scorers";
  export type Composing = Scoring & {
    scorer: {
      thread: number;
      head: number;
      digest: string;
      name: string;
      mode: "edit" | "fork";
      body: ScorerBody;
      labels: string[];
    } | null;
    blank: ScorerBody;
    case: string;
    runs: string[];
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import { api, type Schemas, why } from "$lib/api/client";
  import Saving from "$lib/editors/Saving.svelte";
  import type { Component } from "$lib/editors/writing";
  import type { Schema } from "$lib/schema/form";
  import { said, valued, withScorer } from "$lib/review/review";
  import JudgeAsked from "./JudgeAsked.svelte";
  import type { JudgeChoice } from "./judging";
  import ScorerViews from "./ScorerViews.svelte";
  import { answeredChoices, type ScorerView } from "./scorers";
  import { choices } from "./selectors";

  let {
    composing,
    schema,
    data,
    back,
    changed,
  }: {
    composing: Composing;
    schema: Schema;
    data: unknown;
    back: string;
    changed: (views: ScorerView[], labels: string[], titles: Record<string, string>) => void;
  } = $props();
  const given = untrack(() => composing);
  const start = given.scorer;
  const metrics = new Map(given.metrics.map((m) => [m.name, m]));

  let judges = $state<JudgeChoice[]>([...given.judges]);
  const titles = $derived({ ...given.titles, ...Object.fromEntries(judges.map((j) => [j.digest, j.name])) });

  let mode = $state<"edit" | "fork" | "new">(start ? start.mode : "new");
  let body = $state<ScorerBody>(structuredClone(start?.body ?? given.blank));
  let labels = $state<string[]>(start ? [...start.labels] : given.blank.views.map((_, i) => `view ${i}`));
  let tried = $state<Schemas["Tried"][] | null>(null);
  let problem = $state<string | null>(null);
  let tries = 0;

  const asked = $derived(choices(schema, data, "the whole expectation"));
  const answered = answeredChoices(given.outputs);

  function component(): Component {
    return $state.snapshot(body) as never;
  }

  function anew(): void {
    mode = "new";
    body = structuredClone(given.blank);
    labels = body.views.map((_, i) => `view ${i}`);
  }

  function values(at: number): { shown: string; title: string }[] {
    const unit = metrics.get(body.views[at]?.metric ?? "")?.unit ?? "";
    return (tried ?? []).map((t) => {
      const v = t.views[at];
      const detail = said(v?.detail).map(([k, text]) => (k ? `${k}: ${text}` : text));
      const shown = v?.judged ? "judged" : valued(v?.value ?? null, unit);
      return { shown, title: [`replicate ${t.replicate}`, ...detail].join("; ") };
    });
  }

  $effect(() => {
    changed($state.snapshot(body.views) as ScorerView[], $state.snapshot(labels), titles);
  });

  $effect(() => {
    const scorer = component();
    const expectation = JSON.parse(JSON.stringify(data ?? null)) as unknown;
    if (given.runs.length === 0) return;
    const at = ++tries;
    const timer = setTimeout(async () => {
      const got = await api.POST("/api/scorers/try", {
        body: { scorer, expectation: expectation as never, case: given.case, runs: given.runs },
      });
      if (at !== tries) return;
      if (got.data) {
        tried = got.data;
        problem = null;
      } else {
        tried = null;
        problem = why(got.error);
      }
    }, 450);
    return () => clearTimeout(timer);
  });
</script>

<section class="mb-4 rounded-lg border border-primary/30 bg-primary/5 p-3 text-xs" aria-label="Composing a scorer">
  <header class="mb-2 flex flex-wrap items-center gap-2">
    <h3 class="text-sm font-semibold">
      {mode === "new" ? "A new scorer" : mode === "edit" ? `Changing ${start?.name}` : `Making ${start?.name} yours`}
    </h3>
    {#if mode !== "new"}
      <button type="button" class="ml-auto rounded-md border border-border px-2 py-0.5 hover:bg-muted" onclick={anew}
        >Start a new one</button
      >
    {/if}
  </header>
  {#if given.runs.length}
    <p class="mb-2 text-muted-foreground">
      Each view is tried on your {given.runs.length === 1 ? "run" : `${given.runs.length} runs`} of this case as you
      change it or what you expect; nothing is kept until you save. A judged view is scored by its judge once the
      scorer is saved and the runs are scored again, in the record.
    </p>
  {:else}
    <p class="mb-2 text-muted-foreground">Run the case to try the views on its answers.</p>
  {/if}

  <ScorerViews
    bind:views={body.views}
    bind:labels
    bind:judges
    metrics={given.metrics}
    {asked}
    {answered}
    {titles}
    judging={given.judging}
    models={given.models}
    me={given.me}
  >
    {#snippet inline(at: number)}
      {#if tried}
        <span class="flex flex-wrap items-baseline gap-1" aria-label="Tried on your answers">
          <span class="text-muted-foreground">on your answers</span>
          {#each values(at) as v, i (i)}
            <span class="rounded bg-muted px-1.5 py-0.5 tabular-nums" title={v.title}>{v.shown}</span>
          {/each}
        </span>
      {/if}
    {/snippet}
    {#snippet below(view: ScorerView, _at: number, judge: JudgeChoice | undefined)}
      {#if view.judge}
        <JudgeAsked judge={view.judge} expectation={view.expectation ?? ""} {data} />
        {#if judge}
          <a class="text-primary hover:underline" href="/scoring/{judge.thread}">What it is asked is changed on Scoring</a>
        {/if}
      {/if}
    {/snippet}
  </ScorerViews>

  {#if problem}<p class="mt-2 text-destructive">{problem}</p>{/if}
  {#key mode}
    <Saving
      editing={{
        mode,
        thread: mode === "new" ? undefined : start?.thread,
        head: mode === "edit" ? start?.head : undefined,
        name: mode === "new" ? "" : (start?.name ?? ""),
      }}
      {component}
      digest={start?.digest}
      same={JSON.stringify(labels) === JSON.stringify(start?.labels)}
      labels={() => $state.snapshot(labels)}
      to={(saved) => withScorer(back, saved.thread)}
    />
  {/key}
</section>
