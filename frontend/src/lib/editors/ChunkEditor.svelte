<script lang="ts" module>
  import type { Schemas } from "$lib/api/client";
  import type { Body } from "./chunks";
  import type { Mode } from "./writing";

  export type ChunkEditing = {
    kind: "chunk";
    chunk: string;
    mode: Mode;
    thread?: number;
    head?: number;
    name: string;
    body: Body | null;
    language: string | null;
    languaged: boolean;
    tools: Schemas["Thread"][];
    me: string;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import { FIELD } from "$lib/utils";
  import FewShotForm from "./chunk/FewShotForm.svelte";
  import InstructionsForm from "./chunk/InstructionsForm.svelte";
  import OutputForm from "./chunk/OutputForm.svelte";
  import PassthroughForm from "./chunk/PassthroughForm.svelte";
  import PromptForm from "./chunk/PromptForm.svelte";
  import ReasoningForm from "./chunk/ReasoningForm.svelte";
  import SamplingForm from "./chunk/SamplingForm.svelte";
  import ToolsetForm from "./chunk/ToolsetForm.svelte";
  import { blank, jsonOf } from "./chunks";
  import Findings from "./Findings.svelte";
  import Saving from "./Saving.svelte";
  import { type Checked, checked, type Component } from "./writing";

  let { editor, digest = null }: { editor: ChunkEditing; digest?: string | null } = $props();
  const given = untrack(() => editor);

  let body = $state<Body>(given.body ?? blank(given.chunk));
  let language = $state(given.language ?? "");
  let asJson = $state(false);
  let json = $state("");
  let found = $state<Checked | null>(null);
  let asked = 0;

  const read = $derived(asJson ? jsonOf(json) : null);
  const forms: Record<string, typeof InstructionsForm> = {
    "chunk.instructions": InstructionsForm,
    "chunk.prompt": PromptForm,
    "chunk.few_shot": FewShotForm,
    "chunk.output": OutputForm,
    "chunk.sampling": SamplingForm,
    "chunk.reasoning": ReasoningForm,
    "chunk.passthrough": PassthroughForm,
  };
  const Form = $derived(forms[given.chunk]);

  function set(next: Body): void {
    body = { ...next, kind: given.chunk };
  }

  function switched(): void {
    if (asJson) {
      if (read && "value" in read && typeof read.value === "object" && read.value !== null) set(read.value as Body);
      asJson = false;
    } else {
      json = JSON.stringify(body, null, 2);
      asJson = true;
    }
  }

  function component(): Component {
    return body as Component;
  }

  $effect(() => {
    if (asJson && read && "value" in read && typeof read.value === "object" && read.value !== null) set(read.value as Body);
  });

  $effect(() => {
    const sent = ++asked;
    const now = JSON.parse(JSON.stringify(body)) as Component;
    const timer = setTimeout(async () => {
      const got = await checked(now);
      if (sent === asked) found = got;
    }, 350);
    return () => clearTimeout(timer);
  });
</script>

<div class="space-y-3">
  <div class="flex justify-end">
    <button type="button" class="text-xs text-primary hover:underline" onclick={switched}>
      {asJson ? "Back to the form" : "As JSON"}
    </button>
  </div>
  {#if asJson}
    <textarea
      class="min-h-48 w-full rounded-md border border-input bg-transparent px-2 py-1 font-mono text-xs [field-sizing:content]"
      aria-label="It, as JSON"
      bind:value={json}
    ></textarea>
    {#if read && "problem" in read}<p class="text-sm text-destructive">Not JSON: {read.problem}</p>{/if}
  {:else if given.chunk === "chunk.toolset"}
    <ToolsetForm {body} {set} tools={given.tools} me={given.me} />
  {:else if Form}
    <Form {body} {set} />
  {/if}
  {#if given.languaged}
    <label class="grid max-w-xs gap-1 text-sm"
      ><span class="text-muted-foreground">The language its text is written in, such as en</span>
      <input class="{FIELD} font-mono" bind:value={language} autocomplete="off" /></label
    >
  {/if}
  <Findings {found} />
  <Saving
    editing={given}
    {component}
    language={() => (given.languaged && language.trim() ? language.trim() : null)}
    unchanged={found !== null && "digest" in found && found.digest === digest}
    blocked={found === null || "problem" in found || (read !== null && "problem" in read)}
  />
</div>
