<script lang="ts" module>
  import type { Editing } from "./writing";

  export type ExpectationEditing = Omit<Editing, "name"> & {
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
  import TriangleAlertIcon from "@lucide/svelte/icons/triangle-alert";
  import { refusal, t } from "$lib/locale";
  import type { Edited, Wrote } from "$lib/review/edited.svelte";
  import { blank, fieldName, glimpse, kept, pruned, widget } from "$lib/schema/form";
  import SchemaField from "$lib/schema/SchemaField.svelte";
  import Findings from "./Findings.svelte";
  import { type Checked, checked, type Component, saved } from "./writing";

  let {
    editor,
    edited,
    restored = () => undefined,
  }: { editor: ExpectationEditing; edited: Edited; restored?: () => void } = $props();
  const given = untrack(() => editor);
  const root = given.json_schema;
  const shape = widget(root, root);
  const sections = shape.is === "object" ? shape.properties : null;

  let data = $state(given.data ?? blank(root, root));
  let last = untrack(() => $state.snapshot(data));
  let at = $state({ mode: given.mode, thread: given.thread, head: given.head });
  let found = $state<Checked | null>(null);
  let asked = 0;

  function component(from: unknown = data): Component {
    return {
      kind: "expectation",
      case: given.case,
      expectation_schema: given.schema,
      data: (pruned(kept(from, root, root), root, root) ?? {}) as never,
    };
  }

  // Policy: one begun from what another case of the family expects is unsaved as it is shown.
  let first = $state(given.mode === "new" && given.data != null ? "" : untrack(() => JSON.stringify(component())));
  const touched = $derived(JSON.stringify($state.snapshot(component())) !== first);

  export function load(value: unknown): void {
    data = value ?? blank(root, root);
  }

  export function holds(value: unknown): boolean {
    return JSON.stringify($state.snapshot(component())) === JSON.stringify(component(value ?? blank(root, root)));
  }

  const unreadable = $derived.by(() => {
    const by = new Map<string, string[]>();
    if (found === null || "problem" in found || !sections) return by;
    for (const f of found.findings) {
      const at = f.params.field;
      if (f.code !== "expectation.unreadable" || typeof at !== "string") continue;
      if (!sections.some((p) => p.name === at)) continue;
      by.set(at, [...(by.get(at) ?? []), f.wording === null ? f.message : refusal(f.message, f.wording, f.params)]);
    }
    return by;
  });
  const rest = $derived(
    found === null || "problem" in found
      ? found
      : {
          ...found,
          findings: found.findings.filter(
            (f) => f.code !== "expectation.unreadable" || !unreadable.has(String(f.params.field)),
          ),
        },
  );

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
    pending: () => touched,
    ready: () =>
      !touched ||
      (found !== null && !("problem" in found) && !found.findings.some((f) => f.code === "expectation.unreadable")),
    save: async (): Promise<Wrote> => {
      if (touched) {
        const sent = $state.snapshot(component()) as Component;
        const got = await saved({ ...given, ...at, name: "" }, "", sent);
        if (!("to" in got)) {
          if (got.moved === null) return { problem: got.problem };
          at.head = got.moved;
          return {
            problem: t("%(problem)s. What you typed is kept: save again to make it the version after the latest.", {
              problem: got.problem,
            }),
          };
        }
        at = { mode: "edit", thread: got.thread, head: got.head };
        first = JSON.stringify(sent);
        last = $state.snapshot(data);
      }
      return {};
    },
    restore: () => {
      data = structuredClone(last);
      restored();
    },
  });
</script>

<div class="space-y-3">
  {#if sections}
    {#each sections as p (p.name)}
      {@const wrong = unreadable.get(p.name)}
      <details class="group rounded-lg border border-border/60">
        <summary
          class="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-sm [&::-webkit-details-marker]:hidden"
        >
          <ChevronRightIcon class="size-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-90" />
          <span class="font-medium">{fieldName(p.name)}</span>
          <span class="min-w-0 flex-1 truncate text-xs text-muted-foreground">{held(fields()[p.name])}</span>
          {#if wrong}
            <TriangleAlertIcon
              class="size-4 shrink-0 text-destructive group-open:hidden"
              role="img"
              aria-label={t("Not as a scorer reads it")}
            />
          {/if}
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
          {#each wrong ?? [] as said, i (i)}
            <p class="mt-2 flex gap-2 text-sm text-destructive">
              <TriangleAlertIcon class="mt-0.5 size-4 shrink-0" /><span>{said}</span>
            </p>
          {/each}
        </div>
      </details>
    {/each}
  {:else}
    <SchemaField schema={root} {root} value={data} set={(v) => (data = v)} quiet whole me={given.me} />
  {/if}
  {#if at.mode !== "new" || touched}<Findings found={rest} />{/if}
</div>
