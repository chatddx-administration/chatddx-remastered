<script lang="ts" module>
  import type { Schemas } from "$lib/api/client";
  import type { Schema } from "$lib/schema/form";
  import type { JudgeChoice, Judging, Serving } from "./JudgeForm.svelte";

  export type ScorerView = {
    output?: string;
    expectation?: string;
    split?: string | null;
    metric: string;
    judge?: string | null;
    params?: Record<string, unknown>;
  };
  export type ScorerBody = {
    kind: "scorer";
    entry_point: string;
    version: number;
    expectation_schema: string;
    views: ScorerView[];
    resources?: string[];
    params?: Record<string, unknown>;
  };
  export type Composing = {
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
    metrics: Schemas["Metric"][];
    outputs: { title: string | null; json_schema: Schema | null; by: string[] }[];
    judges: JudgeChoice[];
    titles: Record<string, string>;
    judging: Judging[];
    models: Serving[];
    me: string;
    case: string;
    runs: string[];
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import { api, why } from "$lib/api/client";
  import Findings from "$lib/editors/Findings.svelte";
  import Saving from "$lib/editors/Saving.svelte";
  import { type Checked, checked, type Component } from "$lib/editors/writing";
  import { said, valued, withScorer } from "$lib/review/review";
  import JudgeAsked from "./JudgeAsked.svelte";
  import JudgeForm from "./JudgeForm.svelte";
  import JudgeTexts from "./JudgeTexts.svelte";
  import { startingParams, verdictAt } from "./judging";
  import { type Choice, choices } from "./selectors";
  import SelectorPicker from "./SelectorPicker.svelte";

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
  const unjudged = given.metrics.filter((m) => !m.judged);
  const named: Record<string, string> = { at: "Its verdict at", max: "Out of" };

  let judges = $state<JudgeChoice[]>([...given.judges]);
  let writing = $state<number | null>(null);
  let rewriting = $state<number | null>(null);
  const titles = $derived({ ...given.titles, ...Object.fromEntries(judges.map((j) => [j.digest, j.name])) });

  let mode = $state<"edit" | "fork" | "new">(start ? start.mode : "new");
  let body = $state<ScorerBody>(structuredClone(start?.body ?? given.blank));
  let labels = $state<string[]>(start ? [...start.labels] : given.blank.views.map((_, i) => `view ${i}`));
  let found = $state<Checked | null>(null);
  let tried = $state<Schemas["Tried"][] | null>(null);
  let problem = $state<string | null>(null);
  let checks = 0;
  let tries = 0;

  const asked = $derived(choices(schema, data, "the whole expectation"));
  const answered: Choice[] = (() => {
    const seen = new Map<string, Choice>();
    for (const output of given.outputs) {
      for (const c of choices(output.json_schema, null, "the whole answer")) {
        const label = c.selector === "" ? c.label : `${output.title ?? "text"}: ${c.label}`;
        if (!seen.has(c.selector)) seen.set(c.selector, { ...c, label });
      }
    }
    return [...seen.values()];
  })();

  const unchanged = $derived(
    mode === "edit" &&
      start !== null &&
      found !== null &&
      "digest" in found &&
      found.digest === start.digest &&
      JSON.stringify(labels) === JSON.stringify(start.labels),
  );

  function component(): Component {
    return $state.snapshot(body) as never;
  }

  function anew(): void {
    mode = "new";
    body = structuredClone(given.blank);
    labels = body.views.map((_, i) => `view ${i}`);
  }

  function added(): void {
    body.views.push({ metric: unjudged[0]?.name ?? "", expectation: "", output: "" });
    labels.push(`view ${labels.length}`);
  }

  function moved(at: number, by: number): void {
    const to = at + by;
    const [view] = body.views.splice(at, 1);
    const [label] = labels.splice(at, 1);
    if (view === undefined || label === undefined) return;
    body.views.splice(to, 0, view);
    labels.splice(to, 0, label);
  }

  function dropped(at: number): void {
    body.views.splice(at, 1);
    labels.splice(at, 1);
  }

  function judgeOf(view: ScorerView): JudgeChoice | undefined {
    return judges.find((j) => j.digest === view.judge);
  }

  function metricked(view: ScorerView, name: string): void {
    const metric = metrics.get(name);
    view.metric = name;
    if (!metric?.judged) {
      view.judge = null;
      view.params = {};
      return;
    }
    judged(view, judgeOf(view) ?? judges[0]);
  }

  function judged(view: ScorerView, judge: JudgeChoice | undefined): void {
    view.judge = judge?.digest ?? null;
    const params = metrics.get(view.metric)?.params ?? {};
    view.params = startingParams(params, judge?.output_schema ?? null);
  }

  function takes(view: ScorerView, param: string): boolean {
    const properties = metrics.get(view.metric)?.params?.properties;
    return typeof properties === "object" && properties !== null && param in properties;
  }

  function points(view: ScorerView): [string, Schema][] {
    const params = metrics.get(view.metric)?.params?.properties;
    if (typeof params !== "object" || params === null) return [];
    return Object.entries(params as Record<string, Schema>).filter(([name]) => name !== "at");
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
    const sent = component();
    const at = ++checks;
    const timer = setTimeout(async () => {
      const got = await checked(sent);
      if (at === checks) found = got;
    }, 350);
    return () => clearTimeout(timer);
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

  <ol class="space-y-2">
    {#each body.views as view, at (at)}
      {@const metric = metrics.get(view.metric)}
      {@const judge = judgeOf(view)}
      <li class="space-y-2 rounded-lg border border-border/60 bg-background/60 p-2.5">
        <div class="flex items-center gap-2">
          <input
            class="h-8 min-w-0 flex-1 rounded-md border border-input bg-transparent px-2 font-medium"
            aria-label="Its label"
            bind:value={labels[at]}
          />
          <button type="button" class="rounded px-1.5 hover:bg-muted disabled:opacity-40" aria-label="Move it up" disabled={at === 0} onclick={() => moved(at, -1)}>↑</button>
          <button type="button" class="rounded px-1.5 hover:bg-muted disabled:opacity-40" aria-label="Move it down" disabled={at === body.views.length - 1} onclick={() => moved(at, 1)}>↓</button>
          <button type="button" class="rounded px-1.5 hover:bg-muted disabled:opacity-40" aria-label="Leave it out" disabled={body.views.length === 1} onclick={() => dropped(at)}>×</button>
        </div>
        <div class="grid gap-2 sm:grid-cols-2">
          <SelectorPicker
            choices={asked}
            value={view.expectation ?? ""}
            set={(v) => (view.expectation = v)}
            label="Reads of what is expected"
          />
          <div class="grid content-start gap-1">
            <SelectorPicker choices={answered} value={view.output ?? ""} set={(v) => (view.output = v)} label="Reads of the answer" />
            <label class="flex items-center gap-2">
              <input
                type="checkbox"
                checked={view.split === "lines@1"}
                onchange={(e) => (view.split = e.currentTarget.checked ? "lines@1" : null)}
              />
              line by line, as a list
            </label>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <span class="flex items-center gap-2">
            <span class="text-muted-foreground" aria-hidden="true">Compared by</span>
            <select
              aria-label="Compared by"
              class="h-8 rounded-md border border-input bg-transparent px-2"
              title={metric?.measures ?? ""}
              value={view.metric}
              onchange={(e) => metricked(view, e.currentTarget.value)}
            >
              {#each given.metrics as m (m.name)}
                <option value={m.name} title={m.measures}>{m.name.replaceAll("_", " ")}{m.judged ? ", by a judge" : ""}</option>
              {/each}
            </select>
          </span>
          {#if metric?.judged}
            <span class="flex items-center gap-2">
              <span class="text-muted-foreground" aria-hidden="true">Judge</span>
              <select
                aria-label="Judge"
                class="h-8 max-w-56 rounded-md border border-input bg-transparent px-2"
                value={writing === at ? "new" : (view.judge ?? "")}
                onchange={(e) => {
                  const picked = e.currentTarget.value;
                  if (picked === "new") writing = at;
                  else {
                    writing = null;
                    judged(view, judges.find((j) => j.digest === picked));
                  }
                }}
              >
                {#if !judge && view.judge}<option value={view.judge}>{titles[view.judge] ?? "its judge"}</option>{/if}
                {#each judges as j (j.thread)}
                  <option value={j.digest}>{(j.owner && j.owner !== given.me ? `${j.owner}/` : "") + j.name}: {j.configuration}{j.model ? ` under ${j.model}` : ""}, {j.seeds.length === 1 ? "1 seed" : `${j.seeds.length} seeds`}</option>
                {/each}
                <option value="new">a new judge…</option>
              </select>
            </span>
          {/if}
          {#if metric?.judged && judge}
            {#if takes(view, "at")}
              <span class="min-w-48">
                <SelectorPicker
                  choices={verdictAt(judge.output_schema).map((p) => ({ label: p.slice(1).replaceAll("/", " › ").replaceAll("_", " "), selector: p }))}
                  value={typeof view.params?.at === "string" ? view.params.at : ""}
                  set={(v) => (view.params = { ...view.params, at: v })}
                  label={named.at ?? "at"}
                />
              </span>
            {/if}
            {#each points(view) as [name, param] (name)}
              <label class="flex items-center gap-2">
                <span class="text-muted-foreground">{named[name] ?? name.replaceAll("_", " ")}</span>
                <input
                  type="number"
                  step={param.type === "integer" ? 1 : "any"}
                  class="h-8 w-20 rounded-md border border-input bg-transparent px-2"
                  value={typeof view.params?.[name] === "number" ? view.params[name] : ""}
                  oninput={(e) => (view.params = { ...view.params, [name]: Number(e.currentTarget.value) })}
                />
              </label>
            {/each}
          {/if}
          {#if tried}
            <span class="flex flex-wrap items-baseline gap-1" aria-label="Tried on your answers">
              <span class="text-muted-foreground">on your answers</span>
              {#each values(at) as v, i (i)}
                <span class="rounded bg-muted px-1.5 py-0.5 tabular-nums" title={v.title}>{v.shown}</span>
              {/each}
            </span>
          {/if}
        </div>
        {#if writing === at}
          <JudgeForm
            me={given.me}
            judging={given.judging}
            models={given.models}
            made={(j) => {
              judges.push(j);
              writing = null;
              judged(view, j);
            }}
            left={() => (writing = null)}
          />
        {/if}
        {#if metric?.judged && view.judge}
          {#if rewriting === at && judge?.texts && judge.body && judge.head !== undefined}
            <JudgeTexts
              judge={{ ...judge, texts: judge.texts, body: judge.body, head: judge.head }}
              expectation={view.expectation ?? ""}
              {data}
              me={given.me}
              made={(j) => {
                const known = judges.findIndex((k) => k.thread === j.thread);
                if (known === -1) judges.push(j);
                else judges[known] = j;
                const was = view.judge;
                for (const v of body.views) if (v.judge === was) v.judge = j.digest;
                rewriting = null;
              }}
              left={() => (rewriting = null)}
            />
          {:else}
            <JudgeAsked judge={view.judge} expectation={view.expectation ?? ""} {data} />
            {#if judge?.texts}
              <button
                type="button"
                class="rounded-md border border-border px-2.5 py-0.5 hover:bg-muted"
                onclick={() => (rewriting = at)}>Change what it is asked</button
              >
            {/if}
          {/if}
        {/if}
      </li>
    {/each}
  </ol>
  <button
    type="button"
    class="mt-2 rounded-full border border-dashed border-border px-2.5 py-0.5 text-muted-foreground hover:bg-muted"
    onclick={added}>+ a view</button
  >

  {#if problem}<p class="mt-2 text-destructive">{problem}</p>{/if}
  <div class="mt-2"><Findings {found} /></div>
  {#key mode}
    <Saving
      editing={{
        mode,
        thread: mode === "new" ? undefined : start?.thread,
        head: mode === "edit" ? start?.head : undefined,
        name: mode === "new" ? "" : (start?.name ?? ""),
      }}
      {component}
      {unchanged}
      blocked={found !== null && "problem" in found}
      labels={() => $state.snapshot(labels)}
      to={(saved) => withScorer(back, saved.thread)}
    />
  {/key}
</section>
