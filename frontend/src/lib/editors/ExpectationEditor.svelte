<script lang="ts" module>
  import type { Editing } from "./writing";

  export type ExpectationEditing = Editing & {
    kind?: "expectation";
    case: string;
    schema: string;
    json_schema: Record<string, unknown>;
    data: unknown;
    me?: string;
  };
</script>

<script lang="ts">
  import { untrack } from "svelte";
  import ChevronRightIcon from "@lucide/svelte/icons/chevron-right";
  import { api, why } from "$lib/api/client";
  import { Input } from "$lib/components/ui/input";
  import { t } from "$lib/locale";
  import type { Edited, Wrote } from "$lib/review/edited.svelte";
  import { blank, fieldName, glimpse, kept, pruned, widget } from "$lib/schema/form";
  import SchemaField from "$lib/schema/SchemaField.svelte";
  import Findings from "./Findings.svelte";
  import { type Checked, checked, type Component, said, saved } from "./writing";

  let { editor, edited }: { editor: ExpectationEditing; edited: Edited } = $props();
  const given = untrack(() => editor);
  const root = given.json_schema;
  const shape = widget(root, root);
  const sections = shape.is === "object" ? shape.properties : null;

  let data = $state(given.data ?? blank(root, root));
  let name = $state(given.name);
  let named = $state(given.name);
  let at = $state({ mode: given.mode, thread: given.thread, head: given.head });
  let found = $state<Checked | null>(null);
  let asked = 0;

  function component(): Component {
    return {
      kind: "expectation",
      case: given.case,
      expectation_schema: given.schema,
      data: (pruned(kept(data, root, root), root, root) ?? {}) as never,
    };
  }

  // Policy: one begun from what another case of the family expects is unsaved as it is shown.
  let first = $state(given.mode === "new" && given.data != null ? "" : untrack(() => JSON.stringify(component())));
  const touched = $derived(JSON.stringify($state.snapshot(component())) !== first);
  const renamed = $derived(at.mode === "edit" && name.trim() !== named);

  function fields(): Record<string, unknown> {
    return typeof data === "object" && data !== null && !Array.isArray(data) ? (data as Record<string, unknown>) : {};
  }

  function set(key: string, value: unknown): void {
    const { [key]: _, ...rest } = fields();
    data = value === undefined ? rest : { ...fields(), [key]: value };
  }

  function held(value: unknown): string {
    return value === false ? t("none expected") : glimpse(value).join(" · ");
  }

  $effect(() => {
    const sent = $state.snapshot(component());
    const now = ++asked;
    const timer = setTimeout(async () => {
      const got = await checked(sent as Component);
      if (now === asked) found = got;
    }, 350);
    return () => clearTimeout(timer);
  });

  untrack(() => edited).join({
    rank: 1,
    pending: () => touched || renamed,
    ready: () => (!touched || (found !== null && !("problem" in found))) && name.trim() !== "",
    save: async (): Promise<Wrote> => {
      if (touched) {
        const sent = $state.snapshot(component()) as Component;
        const got = await saved({ ...given, ...at }, name, sent);
        if (!("to" in got)) {
          if (got.moved === null) return { problem: got.problem };
          at.head = got.moved;
          return {
            problem: t("%(problem)s. What you typed is kept: save again to make it the version after the latest.", {
              problem: got.problem,
            }),
          };
        }
        if (at.mode !== "edit") named = name.trim();
        at = { mode: "edit", thread: got.thread, head: got.head };
        first = JSON.stringify(sent);
      }
      if (renamed && at.thread !== undefined) {
        const got = await api.PATCH("/api/threads/{thread}", {
          params: { path: { thread: at.thread } },
          body: { name: name.trim() },
        });
        if (!got.data) return { problem: why(got.error) };
        named = name.trim();
      }
      return {};
    },
  });
</script>

<div class="space-y-3">
  <label class="grid gap-1 text-sm">
    <span class="font-medium">{t("Name")}</span>
    <Input bind:value={name} autocomplete="off" />
  </label>
  {#if sections}
    {#each sections as p (p.name)}
      <details class="group rounded-lg border border-border/60">
        <summary
          class="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-sm [&::-webkit-details-marker]:hidden"
        >
          <ChevronRightIcon class="size-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-90" />
          <span class="font-medium">{fieldName(p.name)}</span>
          <span class="min-w-0 flex-1 truncate text-xs text-muted-foreground">{held(fields()[p.name])}</span>
        </summary>
        <div class="px-3 pb-3">
          <SchemaField
            schema={p.schema}
            {root}
            value={fields()[p.name]}
            set={(v) => set(p.name, v)}
            label={p.name}
            headed={false}
            quiet
            whole
            me={given.me}
          />
        </div>
      </details>
    {/each}
  {:else}
    <SchemaField schema={root} {root} value={data} set={(v) => (data = v)} quiet whole me={given.me} />
  {/if}
  {#if at.mode !== "new" || touched}<Findings {found} />{/if}
  {#if at.mode === "edit" || (touched && !name.trim())}
    <p class="text-sm" aria-live="polite">{said({ ...given, ...at }, name, !touched)}</p>
  {/if}
</div>
