<script lang="ts">
  import { t } from "$lib/locale";
  import SchemaField from "./SchemaField.svelte";
  import { authored, blank, chosen, deref, fieldName, type Schema, widget, without as leaving } from "./form";

  let {
    schema,
    root,
    value,
    set,
    label = "",
    quiet = false,
    framed = true,
    me,
    hidden = [],
    whole = false,
    headed = true,
  }: {
    schema: Schema;
    root: Schema;
    value: unknown;
    set: (v: unknown) => void;
    label?: string;
    quiet?: boolean;
    framed?: boolean;
    me?: string;
    hidden?: string[];
    whole?: boolean;
    headed?: boolean;
  } = $props();

  const shape = $derived(widget(schema, root));
  const about = $derived(deref(schema, root));
  const described = $derived(typeof about.description === "string" ? about.description : "");
  const said = $derived(quiet ? "" : described);
  const named = $derived(fieldName(label));
  const legend = $derived(headed ? named : "");
  const frame = $derived(
    !framed || (quiet && !legend) ? "space-y-3" : "space-y-3 rounded-lg border border-border/60 p-3",
  );
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

  function byMe(schema: Schema): boolean {
    return me !== undefined && authored(widget(schema, root), root);
  }

  function authorOf(item: unknown): string {
    const held = typeof item === "object" && item !== null ? (item as Record<string, unknown>).author : undefined;
    return typeof held === "string" ? held : "";
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
  <fieldset class={frame}>
    {#if legend}<legend class="px-1 text-sm font-medium" title={quiet ? described : undefined}>{legend}</legend>{/if}
    {#if said}<p class="text-xs text-muted-foreground">{said}</p>{/if}
    {#each shape.properties as p (p.name)}
      {#if hidden.includes(p.name)}{:else if whole || p.required || p.name in fields() || byMe(p.schema)}
        <div class="flex items-start gap-2">
          <div class="min-w-0 flex-1">
            <SchemaField
              schema={p.schema}
              {root}
              value={fields()[p.name]}
              set={(v) => set(v === undefined ? without(p.name) : { ...fields(), [p.name]: v })}
              label={p.name}
              {quiet}
              {me}
              {whole}
            />
          </div>
          {#if !whole && !p.required && !byMe(p.schema)}
            <button
              type="button"
              class="mt-6 rounded-md px-1.5 text-muted-foreground hover:bg-muted"
              aria-label={t("Leave out %(name)s", { name: fieldName(p.name) })}
              onclick={() => set(without(p.name))}>×</button
            >
          {/if}
        </div>
      {:else}
        <button
          type="button"
          class="mr-2 rounded-full border border-dashed border-border px-2.5 py-0.5 text-xs text-muted-foreground hover:bg-muted"
          onclick={() => set({ ...fields(), [p.name]: blank(p.schema, root) })}>+ {fieldName(p.name)}</button
        >
      {/if}
    {/each}
  </fieldset>
{:else if shape.is === "union"}
  {@const at = chosen(shape, value)}
  {@const rest = leaving(at.schema, shape.key)}
  <fieldset class={frame}>
    {#if legend}<legend class="px-1 text-sm font-medium" title={quiet ? described : undefined}>{legend}</legend>{/if}
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
        {me}
        {whole}
      />
    {/if}
  </fieldset>
{:else if shape.is === "or-none"}
  <fieldset class={frame}>
    {#if legend}<legend class="px-1 text-sm font-medium" title={quiet ? described : undefined}>{legend}</legend>{/if}
    {#if said}<p class="text-xs text-muted-foreground">{said}</p>{/if}
    <label class="flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={value === false}
        onchange={(e) => set(e.currentTarget.checked ? false : blank(shape.schema, root))}
      />
      {t("none expected")}
    </label>
    {#if value !== false}
      <SchemaField schema={shape.schema} {root} {value} {set} {quiet} {me} {whole} framed={false} />
    {/if}
  </fieldset>
{:else if shape.is === "list" && me !== undefined && authored(shape, root)}
  {@const mine = items().findIndex((x) => authorOf(x) === me)}
  <div class="space-y-2">
    {#if mine === -1 && !whole}
      <button
        type="button"
        class="rounded-full border border-dashed border-border px-2.5 py-0.5 text-xs text-muted-foreground hover:bg-muted"
        onclick={() => set([...items(), { ...(blank(shape.items, root) as Record<string, unknown>), author: me }])}
        >+ {named}</button
      >
    {:else}
      <div class="flex items-start gap-2">
        <div class="min-w-0 flex-1">
          <SchemaField
            schema={shape.items}
            {root}
            value={mine === -1
              ? { ...(blank(shape.items, root) as Record<string, unknown>), author: me }
              : items()[mine]}
            set={(v) => set(mine === -1 ? [...items(), v] : items().map((x, j) => (j === mine ? v : x)))}
            label={whole ? "" : named}
            {quiet}
            {me}
            {whole}
            hidden={["author"]}
          />
        </div>
        {#if !whole}
          <button
            type="button"
            class="mt-2 rounded-md px-1.5 text-muted-foreground hover:bg-muted"
            aria-label={t("Leave out %(name)s", { name: named })}
            onclick={() => {
              const left = items().filter((_, j) => j !== mine);
              set(left.length ? left : undefined);
            }}>×</button
          >
        {/if}
      </div>
    {/if}
    {#each items() as item, i (i)}
      {#if i !== mine}
        <details class="rounded-lg border border-border/60 px-3 py-2 text-sm">
          <summary class="cursor-pointer text-muted-foreground"
            >{t("%(field)s by %(author)s", { field: named, author: authorOf(item) })}</summary
          >
          <dl class="mt-2 grid grid-cols-[max-content_minmax(0,1fr)] gap-x-3 gap-y-1">
            {#each Object.entries(item as Record<string, unknown>).filter(([k]) => k !== "author") as [k, v] (k)}
              <dt class="text-muted-foreground">{fieldName(k)}</dt>
              <dd class="whitespace-pre-wrap break-words">{typeof v === "string" ? v : JSON.stringify(v)}</dd>
            {/each}
          </dl>
        </details>
      {/if}
    {/each}
  </div>
{:else if shape.is === "list"}
  <div class="space-y-2">
    {#if legend}<p class="text-sm font-medium" title={quiet ? described : undefined}>{legend}</p>{/if}
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
            {me}
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
        oninput={(e) => set(e.currentTarget.value)}></textarea>
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
        oninput={(e) => parsed(e.currentTarget.value)}></textarea>
      {#if broken}<span class="text-xs text-destructive">{t("Not JSON yet: %(error)s", { error: broken })}</span>{/if}
    {/if}
    {#if said}<span class="text-xs text-muted-foreground">{said}</span>{/if}
  </label>
{/if}
