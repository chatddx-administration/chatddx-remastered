<script lang="ts" module>
  import type { Mode } from "$lib/editors/writing";
  import type { Judging, Serving } from "./judging";

  export type JudgeEditing = {
    kind: "judge";
    mode: Mode;
    thread?: number;
    head?: number;
    name: string;
    body: { skeleton: string; model: string; seeds: number[]; fill?: string } | null;
    configuration: string | null;
    handle: string | null;
    behind: boolean;
    problem: string | null;
    judging: Judging[];
    models: Serving[];
    me: string;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import Findings from "$lib/editors/Findings.svelte";
  import Saving from "$lib/editors/Saving.svelte";
  import { type Checked, checked, type Component } from "$lib/editors/writing";
  import JudgeFields from "./JudgeFields.svelte";
  import { configurationChoices, type Holding, madeFor, modelChoices, modelHint, seedsOf } from "./judging";

  let { editor, digest = null }: { editor: JudgeEditing; digest?: string | null } = $props();
  const given = untrack(() => editor);
  const held: Holding | null = given.body && {
    skeleton: given.body.skeleton,
    configuration: given.configuration ?? given.body.skeleton,
    weights: given.body.model,
    handle: given.handle,
  };

  const start = given.body?.skeleton ?? given.judging[0]?.digest ?? "";
  const fitting = madeFor(given.judging, given.models);
  let configuration = $state(start);
  let weights = $state(given.body?.model ?? fitting[start] ?? given.models[0]?.weights ?? "");
  let seeds = $state((given.body?.seeds ?? [1]).join(", "));
  let found = $state<Checked | null>(null);
  let asked = 0;

  const read = $derived(seedsOf(seeds));
  const following = $derived(given.behind && weights !== given.body?.model);

  function component(): Component | null {
    if (!configuration || !weights || typeof read === "string") return null;
    const fill = given.body?.fill ?? "text@1";
    return { kind: "judge", skeleton: configuration, model: weights, seeds: read, fill } as never;
  }

  $effect(() => {
    const now = component();
    if (now === null) return;
    const sent = ++asked;
    const timer = setTimeout(async () => {
      const got = await checked(now);
      if (sent === asked) found = got;
    }, 350);
    return () => clearTimeout(timer);
  });
</script>

<div class="space-y-3 text-sm">
  <div class="grid gap-2 sm:grid-cols-3">
    <JudgeFields
      configurations={configurationChoices(given.judging, given.me, held)}
      models={modelChoices(given.models, held)}
      made={fitting}
      hint={following ? null : modelHint(given.handle, given.behind, given.problem)}
      bind:configuration
      bind:weights
      bind:seeds
    />
  </div>
  {#if typeof read === "string"}<p class="text-destructive">{read}</p>{/if}
  <Findings {found} />
  {#if given.mode !== "new"}
    <p class="text-muted-foreground">
      A scorer asks the version of a judge it names, so the scorers asking this one keep asking the version they ask until
      they are changed.
    </p>
  {/if}
  <Saving
    editing={given}
    component={() => component() as Component}
    unchanged={found !== null && "digest" in found && found.digest === digest}
    blocked={component() === null || found === null || "problem" in found}
  />
</div>
