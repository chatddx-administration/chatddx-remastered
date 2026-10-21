import { deref, type Schema } from "$lib/schema/form";

export type Choice = { label: string; selector: string };

const MEMBER = /^[A-Za-z_][\w]*$/;

function held(value: unknown): value is Schema {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function named(name: string): string {
  return name.replaceAll("_", " ");
}

function member(name: string): string {
  return MEMBER.test(name) ? `.${name}` : `['${quoted(name)}']`;
}

function quoted(text: string): string {
  return text.replaceAll("\\", "\\\\").replaceAll("'", "\\'");
}

function pointer(path: string[]): string {
  return path.map((p) => `/${p.replaceAll("~", "~0").replaceAll("/", "~1")}`).join("");
}

function shaped(schema: Schema, root: Schema): Schema {
  const found = deref(schema, root);
  const alternatives = found.oneOf ?? (found.properties ? undefined : found.anyOf);
  if (!Array.isArray(alternatives)) return found;
  const others = alternatives.filter((a): a is Schema => held(a) && a.const !== false);
  return others.length === 1 && others[0] ? deref(others[0], root) : found;
}

function properties(schema: Schema): [string, Schema][] {
  return held(schema.properties)
    ? Object.entries(schema.properties).map(([k, s]) => [k, held(s) ? s : {}] as [string, Schema])
    : [];
}

function strings(items: Schema, root: Schema): string[] {
  const required = Array.isArray(items.required) ? items.required : [];
  return properties(items)
    .filter(([name, s]) => required.includes(name) && shaped(s, root).type === "string")
    .map(([name]) => name);
}

export function choices(schema: Schema | null, data: unknown, whole: string): Choice[] {
  const found: Choice[] = [{ label: whole, selector: "" }];
  if (!schema) return found;
  walk(schema, schema, held(data) ? data : {}, [], found);
  return found;
}

function walk(schema: Schema, root: Schema, data: Record<string, unknown>, path: string[], found: Choice[]): void {
  for (const [name, given] of properties(shaped(schema, root))) {
    const at = [...path, name];
    const label = at.map(named).join(" › ");
    const shape = shaped(given, root);
    found.push({ label, selector: pointer(at) });
    if (shape.type === "object" && path.length === 0) {
      const inner = held(data[name]) ? (data[name] as Record<string, unknown>) : {};
      walk(shape, root, inner, at, found);
    }
    if (shape.type === "array" && held(shape.items) && path.length === 0) {
      listed(name, shaped(shape.items, root), root, Array.isArray(data[name]) ? data[name] : [], found);
    }
  }
}

function listed(name: string, items: Schema, root: Schema, values: unknown[], found: Choice[]): void {
  const each = `$${member(name)}[*]`;
  found.push({ label: `each of ${named(name)}`, selector: each });
  const fields = properties(items).map(([field]) => field);
  for (const field of fields) found.push({ label: `each of ${named(name)} › ${named(field)}`, selector: `${each}${member(field)}` });
  for (const by of strings(items, root)) {
    const seen = new Set(values.filter(held).map((v) => v[by]).filter((v): v is string => typeof v === "string"));
    for (const value of seen) {
      const which = `$${member(name)}[?@${member(by)} == '${quoted(value)}']`;
      for (const field of fields.filter((f) => f !== by)) {
        found.push({ label: `${named(name)} where ${named(by)} is ${value} › ${named(field)}`, selector: `${which}${member(field)}` });
      }
    }
  }
}

// Policy: a simple dotted path and the JSON Pointer to the same place pick the same, so either finds its choice.
export function same(selector: string): string {
  const dotted = /^\$((?:\.[A-Za-z_]\w*)+)$/.exec(selector);
  return dotted?.[1] ? pointer(dotted[1].slice(1).split(".")) : selector;
}

export function chosen(selector: string, among: Choice[]): Choice | undefined {
  const wanted = same(selector);
  return among.find((c) => same(c.selector) === wanted);
}
