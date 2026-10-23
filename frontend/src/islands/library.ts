import { mount, unmount } from "svelte";
import { type Editing, type Editor, labelled, misread, read, segsOf, textOfSegs, written } from "$lib/library/editors";
import SchemaInput from "$lib/library/SchemaInput.svelte";
import TextsField from "$lib/library/TextsField.svelte";
import ViewsField from "$lib/library/ViewsField.svelte";
import type { ScorerView } from "$lib/scorer/scorers";

type Shown = ReturnType<typeof mount>;
type Drawable = Exclude<Editor, { as: "json" }>;
type Drawn = { draw: (target: HTMLElement) => Shown; raw: HTMLElement[] } | string;

const held = document.getElementById("library-props");
if (held) {
  const editing = JSON.parse(held.textContent ?? "null") as Editing;
  for (const editor of editing.fields) {
    if (editor.as === "json") checked(editor.name, editor.expects);
    else enhanced(editor, editing);
  }
}

// Policy: a JSON box says as it is typed in what keeps it from being sent, and the form
// isn't sent while it does, rather than coming back refused.
function checked(name: string, expects: "object" | "array" | null): void {
  const area = document.querySelector<HTMLTextAreaElement>(`textarea[name="f.${name}"]`);
  if (!area) return;
  const why = document.createElement("p");
  why.className = "mt-1 text-xs text-warning";
  why.hidden = true;
  area.after(why);
  const said = (): string | null => {
    const found = misread(area.value, expects);
    why.textContent = found ?? "";
    why.hidden = found === null;
    area.setAttribute("aria-invalid", String(found !== null));
    return found;
  };
  area.addEventListener("input", said);
  area.form?.addEventListener("submit", (sent) => {
    if (said() === null) return;
    sent.preventDefault();
    area.focus();
  });
}

function picked(name: string, editing: Editing): string {
  const select = document.querySelector<HTMLSelectElement>(`select[name="f.${name}"]`);
  if (select) return select.value;
  const given = editing.held[name];
  return typeof given === "string" ? given : "";
}

function following(editor: Drawable): string[] {
  if (editor.as === "texts") return Object.keys(editor.slots).length ? ["purpose"] : [];
  return editor.as === "views" || editor.of ? [editor.of ?? ""] : [];
}

// Policy: the text box stays the form's, so that it posts as it does without scripts; an editor writes into it only
// what is changed in it, so that a form sent as it is writes nothing.
function enhanced(editor: Drawable, editing: Editing): void {
  const area = document.querySelector<HTMLTextAreaElement>(`textarea[name="f.${editor.name}"]`);
  if (!area) return;
  const as = document.querySelector<HTMLSelectElement>(`select[name="as.${editor.name}"]`);
  const box = document.createElement("div");
  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "mt-1 text-xs text-primary hover:underline";
  const why = document.createElement("p");
  why.className = "mt-1 text-xs text-warning";
  (as ?? area).before(box);
  area.after(toggle, why);
  let shown: Shown | null = null;
  let raw: HTMLElement[] = [area, ...(as ? [as] : [])];

  const opened = (): string | null => {
    const made = drawn(editor, editing, area, as);
    if (typeof made === "string") return made;
    if (shown) void unmount(shown);
    box.replaceChildren();
    shown = made.draw(box);
    raw = made.raw;
    for (const r of raw) r.hidden = true;
    box.hidden = false;
    toggle.textContent = "Write it as JSON";
    why.hidden = true;
    return null;
  };
  const closed = (said: string | null): void => {
    if (shown) void unmount(shown);
    shown = null;
    box.hidden = true;
    for (const r of raw) r.hidden = false;
    toggle.textContent = "Back to the form";
    why.textContent = said ?? "";
    why.hidden = said === null;
  };

  const tried = (): void => {
    const said = opened();
    if (said !== null) closed(said);
  };

  toggle.addEventListener("click", () => (shown ? closed(null) : tried()));
  tried();
  for (const name of following(editor)) {
    document.querySelector(`select[name="f.${name}"]`)?.addEventListener("change", () => {
      if (shown || !why.hidden) tried();
    });
  }
}

function drawn(editor: Drawable, editing: Editing, area: HTMLTextAreaElement, as: HTMLSelectElement | null): Drawn {
  const raw = [area, ...(as ? [as] : [])];
  switch (editor.as) {
    case "texts": {
      const segs = segsOf(area.value, as ? as.value === "text" : null);
      if (!segs) return "What it holds isn't JSON the form can show: set it right here first.";
      const slots = editor.slots[picked("purpose", editing)] ?? [];
      const changed = (s: Parameters<typeof textOfSegs>[0]): void => {
        const made = textOfSegs(s, as !== null);
        if (as) as.value = made.asText ? "text" : "json";
        area.value = made.text;
      };
      const label = editor.name.replaceAll("_", " ");
      return {
        draw: (target) =>
          mount(TextsField, { target, props: { segs, slots, inserts: editor.inserts, label, changed } }),
        raw,
      };
    }
    case "schema": {
      const schema = editor.schema ?? editing.schemas[picked(editor.of ?? "", editing)];
      if (!schema) return "Pick its expectation schema first, and the form shows what it holds.";
      const found = area.value.trim() ? read(area.value) : { ok: true as const, value: null };
      if (!found.ok) return "What it holds isn't JSON the form can show: set it right here first.";
      const changed = (v: unknown): void => {
        area.value = written(v);
      };
      const label = editor.name.replaceAll("_", " ");
      return {
        draw: (target) => mount(SchemaInput, { target, props: { schema, value: found.value, label, changed } }),
        raw,
      };
    }
    case "views": {
      const scoring = editing.scoring;
      const found = area.value.trim() ? read(area.value) : { ok: true as const, value: [] };
      if (!scoring || !found.ok || !Array.isArray(found.value)) {
        return "What it holds isn't JSON the form can show: set it right here first.";
      }
      const views = found.value as ScorerView[];
      const naming = document.querySelector<HTMLTextAreaElement>('textarea[name="labels"]');
      const given = naming ? read(naming.value) : null;
      const { views: labels, rest } = labelled(given?.ok ? given.value : null, views.length);
      const was = written([views, labels]);
      let touched = false;
      const schema = editing.schemas[picked(editor.of, editing)] ?? null;
      const changed = (now: ScorerView[], named: string[]): void => {
        touched ||= written([now, named]) !== was;
        if (!touched) return;
        area.value = written(now);
        if (naming) naming.value = written({ ...rest, views: named });
      };
      const shown = naming?.closest("label");
      return {
        draw: (target) => mount(ViewsField, { target, props: { views, labels, schema, scoring, changed } }),
        raw: [...raw, ...(shown ? [shown] : [])],
      };
    }
  }
}
