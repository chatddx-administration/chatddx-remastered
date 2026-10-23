<script lang="ts">
  import type { Snippet } from "svelte";
  import { t, th } from "$lib/locale";
  import SchemaField from "./SchemaField.svelte";
  import { blank, chosen, deref, type Schema, widget, without as leaving } from "./form";

  let {
    schema,
    root,
    value,
    set,
    label = "",
    beside,
    quiet = false,
  }: {
    schema: Schema;
    root: Schema;
    value: unknown;
    set: (v: unknown) => void;
    label?: string;
    beside?: Snippet<[string]>;
    quiet?: boolean;
  } = $props();

  const shape = $derived(widget(schema, root));
  const about = $derived(deref(schema, root));
  const described = $derived(typeof about.description === "string" ? about.description : "");
  const said = $derived(quiet ? "" : described);
  const named = $derived(label.replaceAll("_", " "));
  let typed = $state<string | null>(null);
  let broken = $state<string | null>(null);

  function fields(): Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value)
      ? (value as Record<string, unknown>)
      : {};
  }

  function items(): unknown[] {
    return Array.isArray(value) ? value : [];
  }

  function without(name: string): Record<string, unknown> {
    return Object.fromEntries(Object.entries(fields()).filter(([k]) => k !== name));
  }

  function parsed(text: string): void {
    typed = text;
    try {
      set(JSON.parse(text));
      broken = null;
    } catch (e) {
      broken = e instanceof Error ? e.message : String(e);
    }
  }
</script>

{#if shape.is === "object"}
  <fieldset class={quiet && !named ? "space-y-3" : "space-y-3 rounded-lg border border-border/60 p-3"}>
    {#if named}<legend class="px-1 text-sm font-medium" title={quiet ? described : undefined}>{named}</legend>{/if}
    {#if said}<p class="text-xs text-muted-foreground">{said}</p>{/if}
    {#each shape.properties as p (p.name)}
      {#if p.required || p.name in fields()}
        <div class="flex items-start gap-2">
          <div class="min-w-0 flex-1">
            <SchemaField
              schema={p.schema}
              {root}
              value={fields()[p.name]}
              set={(v) => set({ ...fields(), [p.name]: v })}
              label={p.name}
              {quiet}
            />
          </div>
          {#if !p.required}
            <button
              type="button"
              class="mt-6 rounded-md px-1.5 text-muted-foreground hover:bg-muted"
              aria-label={t("Leave out %(name)s", { name: p.name.replaceAll("_", " ") })}
              onclick={() => set(without(p.name))}>×</button
            >
          {/if}
        </div>
        {@render beside?.(p.name)}
      {:else}
        <button
          type="button"
          class="mr-2 rounded-full border border-dashed border-border px-2.5 py-0.5 text-xs text-muted-foreground hover:bg-muted"
          onclick={() => set({ ...fields(), [p.name]: blank(p.schema, root) })}>+ {p.name.replaceAll("_", " ")}</button
        >
      {/if}
    {/each}
  </fieldset>
{:else if shape.is === "union"}
  {@const at = chosen(shape, value)}
  {@const rest = leaving(at.schema, shape.key)}
  <fieldset class={quiet && !named ? "space-y-3" : "space-y-3 rounded-lg border border-border/60 p-3"}>
    {#if named}<legend class="px-1 text-sm font-medium" title={quiet ? described : undefined}>{named}</legend>{/if}
    {#if said}<p class="text-xs text-muted-foreground">{said}</p>{/if}
    <label class="grid gap-1 text-sm">
      <span class="font-medium">{shape.key.replaceAll("_", " ")}</span>
      <select
        class="h-9 rounded-md border border-input bg-transparent px-2.5"
        aria-label={shape.key.replaceAll("_", " ")}
        value={String(at.value)}
        onchange={(e) => {
          const picked = shape.options.find((o) => String(o.value) === e.currentTarget.value);
          if (picked) set({ [shape.key]: picked.value, ...(blank(picked.schema, root) as Record<string, unknown>) });
        }}
      >
        {#each shape.options as o (String(o.value))}<option value={String(o.value)}>{String(o.value)}</option>{/each}
      </select>
    </label>
    {#if Object.keys(rest.properties ?? {}).length}
      <SchemaField
        schema={rest}
        {root}
        {value}
        set={(v) => set({ ...(v as Record<string, unknown>), [shape.key]: at.value })}
        {quiet}
      />
    {/if}
  </fieldset>
{:else if shape.is === "or-none"}
  <div class="space-y-2">
    <label class="flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={value === false}
        onchange={(e) => set(e.currentTarget.checked ? false : blank(shape.schema, root))}
      />
      <span
        >{@html th('<span class="font-medium" title="%(about)s">%(field)s</span>: none expected', {
          about: quiet ? described : "",
          field: named,
        })}</span
      >
    </label>
    {#if said}<p class="text-xs text-muted-foreground">{said}</p>{/if}
    {#if value !== false}
      <SchemaField schema={shape.schema} {root} {value} {set} label={named} {quiet} />
    {/if}
  </div>
{:else if shape.is === "list"}
  <div class="space-y-2">
    <p class="text-sm font-medium" title={quiet ? described : undefined}>{named}</p>
    {#if said}<p class="text-xs text-muted-foreground">{said}</p>{/if}
    {#each items() as item, i (i)}
      <div class="flex items-start gap-2">
        <div class="min-w-0 flex-1">
          <SchemaField
            schema={shape.items}
            {root}
            value={item}
            set={(v) => set(items().map((x, j) => (j === i ? v : x)))}
            label="{named} {i + 1}"
            {quiet}
          />
        </div>
        <button
          type="button"
          class="mt-2 rounded-md px-1.5 text-muted-foreground hover:bg-muted"
          aria-label={t("Leave out %(name)s", { name: `${named} ${i + 1}` })}
          onclick={() => set(items().filter((_, j) => j !== i))}>×</button
        >
      </div>
    {/each}
    <button
      type="button"
      class="rounded-full border border-dashed border-border px-2.5 py-0.5 text-xs text-muted-foreground hover:bg-muted"
      onclick={() => set([...items(), blank(shape.items, root)])}>+ {named}</button
    >
  </div>
{:else}
  <label class="grid gap-1 text-sm">
    {#if named}<span class="font-medium" title={quiet ? described : undefined}>{named}</span>{/if}
    {#if shape.is === "text" && shape.long}
      <textarea
        rows="2"
        class="rounded-md border border-input bg-transparent px-2.5 py-1.5 {quiet ? '[field-sizing:content]' : ''}"
        value={typeof value === "string" ? value : ""}
        oninput={(e) => set(e.currentTarget.value)}
      ></textarea>
    {:else if shape.is === "text"}
      <input
        class="h-9 rounded-md border border-input bg-transparent px-2.5"
        value={typeof value === "string" ? value : ""}
        oninput={(e) => set(e.currentTarget.value)}
      />
    {:else if shape.is === "number"}
      <input
        type="number"
        step={shape.integer ? 1 : "any"}
        class="h-9 w-40 rounded-md border border-input bg-transparent px-2.5"
        value={typeof value === "number" ? value : 0}
        oninput={(e) => set(Number(e.currentTarget.value))}
      />
    {:else if shape.is === "boolean"}
      <input type="checkbox" checked={value === true} onchange={(e) => set(e.currentTarget.checked)} />
    {:else if shape.is === "choice"}
      <select
        class="h-9 w-fit rounded-md border border-input bg-transparent px-2.5"
        aria-label={named || undefined}
        value={JSON.stringify(value)}
        onchange={(e) => set(JSON.parse(e.currentTarget.value))}
      >
        {#each shape.options as option (JSON.stringify(option))}
          <option value={JSON.stringify(option)}>{String(option)}</option>
        {/each}
      </select>
    {:else}
      <textarea
        rows="4"
        class="rounded-md border border-input bg-transparent px-2.5 py-1.5 font-mono text-xs"
        value={typed ?? JSON.stringify(value, null, 2)}
        oninput={(e) => parsed(e.currentTarget.value)}
      ></textarea>
      {#if broken}<span class="text-xs text-destructive">{t("Not JSON yet: %(error)s", { error: broken })}</span>{/if}
    {/if}
    {#if said}<span class="text-xs text-muted-foreground">{said}</span>{/if}
  </label>
{/if}
