<script lang="ts">
  import { untrack } from "svelte";
  import TextSegments from "$lib/scorer/TextSegments.svelte";
  import { segmentsOf, textOf } from "$lib/scorer/texts";
  import { FIELD } from "$lib/utils";
  import { type Body, jsonOf } from "../chunks";

  type Contract = { kind: string; name?: string; description?: string | null };

  let { body, set }: { body: Body; set: (body: Body) => void } = $props();

  const contract = $derived((body.contract ?? { kind: "text" }) as Contract);
  const ops = $derived((Array.isArray(body.schema_ops) ? body.schema_ops : []) as string[]);
  let schema = $state(untrack(() => (body.json_schema ? JSON.stringify(body.json_schema, null, 2) : "")));
  const read = $derived(jsonOf(schema));

  function contracted(kind: string): void {
    const next: Contract = kind === "tool" ? { kind, name: contract.name ?? "answer" } : { kind };
    set({ ...body, contract: next });
  }

  function described(name: string | undefined, description: string): void {
    set({ ...body, contract: { kind: "tool", name, ...(description.trim() ? { description } : {}) } });
  }

  // Policy: As chunks.ts:numberOf, a schema that isn't JSON is sent as typed, for the check to refuse with why.
  function schemaTyped(text: string): void {
    schema = text;
    const got = jsonOf(text);
    set({ ...body, json_schema: "value" in got ? got.value : text });
  }
</script>

<div class="space-y-3 text-sm">
  <div class="flex flex-wrap gap-3">
    <label class="grid gap-1"
      ><span class="text-muted-foreground">The answer comes</span>
      <select class={FIELD} value={contract.kind} onchange={(e) => contracted(e.currentTarget.value)}>
        <option value="native">as JSON the engine holds to the schema</option>
        <option value="tool">as a tool call's arguments</option>
        <option value="text">as text</option>
      </select></label
    >
    {#if contract.kind === "tool"}
      <label class="grid gap-1"
        ><span class="text-muted-foreground">The tool's name</span>
        <input class="{FIELD} font-mono" value={contract.name ?? ""} oninput={(e) => described(e.currentTarget.value, contract.description ?? "")} /></label
      >
      <label class="grid min-w-64 flex-1 gap-1"
        ><span class="text-muted-foreground">Its description</span>
        <input class={FIELD} value={contract.description ?? ""} oninput={(e) => described(contract.name, e.currentTarget.value)} /></label
      >
    {/if}
  </div>
  <label class="grid gap-1"
    ><span class="text-muted-foreground"
      >Its JSON Schema{contract.kind === "text" ? ", which a text answer may leave out" : ""}</span
    >
    <textarea
      class="min-h-32 rounded-md border border-input bg-transparent px-2 py-1 font-mono text-xs [field-sizing:content]"
      value={schema}
      oninput={(e) => schemaTyped(e.currentTarget.value)}
    ></textarea></label
  >
  {#if "problem" in read}<p class="text-destructive">Not JSON: {read.problem}</p>{/if}
  <label class="flex items-center gap-2"
    ><input
      type="checkbox"
      checked={ops.includes("inline_refs@1")}
      onchange={(e) => set({ ...body, schema_ops: e.currentTarget.checked ? ["inline_refs@1"] : [] })}
    />
    <span>Send the schema with its <span class="font-mono">$ref</span>s inlined (<span class="font-mono">inline_refs@1</span>)</span></label
  >
  <TextSegments
    label="What it is told to answer"
    segs={segmentsOf(body.guidance ?? "")}
    set={(segs) => {
      const text = textOf(segs);
      set({ ...body, guidance: text === "" ? null : text });
    }}
    inserts={["schema"]}
  />
</div>
