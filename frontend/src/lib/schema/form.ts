export type Schema = Record<string, unknown>;

type Widget =
  | { is: "object"; properties: { name: string; schema: Schema; required: boolean }[] }
  | { is: "text"; long: boolean }
  | { is: "number"; integer: boolean }
  | { is: "boolean" }
  | { is: "choice"; options: unknown[] }
  | { is: "list"; items: Schema }
  | { is: "or-none"; schema: Schema }
  | { is: "json" };

function held(value: unknown): value is Schema {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function deref(schema: Schema, root: Schema): Schema {
  const ref = schema.$ref;
  if (typeof ref !== "string") return schema;
  const found = ref
    .replace(/^#\//, "")
    .split("/")
    .reduce<unknown>((at, key) => (held(at) ? at[key] : undefined), root);
  if (!held(found)) return {};
  const { $ref: _, ...rest } = schema;
  return deref({ ...found, ...rest }, root);
}

export function widget(given: Schema, root: Schema): Widget {
  const schema = deref(given, root);
  const alternatives = schema.oneOf ?? (schema.properties ? undefined : schema.anyOf);
  if (Array.isArray(alternatives)) {
    const none = alternatives.filter((a) => held(a) && a.const === false);
    const others = alternatives.filter((a): a is Schema => held(a) && a.const !== false);
    if (none.length === 1 && others.length === 1 && others[0]) return { is: "or-none", schema: others[0] };
    return { is: "json" };
  }
  if (Array.isArray(schema.enum)) return { is: "choice", options: schema.enum };
  switch (schema.type) {
    case "object": {
      if (!held(schema.properties)) return { is: "json" };
      const required = Array.isArray(schema.required) ? schema.required : [];
      return {
        is: "object",
        properties: Object.entries(schema.properties).map(([name, s]) => ({
          name,
          schema: held(s) ? s : {},
          required: required.includes(name),
        })),
      };
    }
    case "string":
      return { is: "text", long: schema.pattern === undefined && schema.format === undefined };
    case "integer":
    case "number":
      return { is: "number", integer: schema.type === "integer" };
    case "boolean":
      return { is: "boolean" };
    case "array":
      return held(schema.items) ? { is: "list", items: schema.items } : { is: "json" };
    default:
      return { is: "json" };
  }
}

export function blank(schema: Schema, root: Schema): unknown {
  const shape = widget(schema, root);
  switch (shape.is) {
    case "object":
      return Object.fromEntries(shape.properties.filter((p) => p.required).map((p) => [p.name, blank(p.schema, root)]));
    case "text":
      return "";
    case "number":
      return 0;
    case "boolean":
      return false;
    case "choice":
      return shape.options[0] ?? null;
    case "list":
      return [];
    case "or-none":
      return blank(shape.schema, root);
    case "json":
      return null;
  }
}

export function kept(value: unknown, schema: Schema, root: Schema): unknown {
  const shape = widget(schema, root);
  if (shape.is === "object" && held(value)) {
    const out: Record<string, unknown> = {};
    for (const p of shape.properties) {
      if (!(p.name in value)) continue;
      const v = kept(value[p.name], p.schema, root);
      if (!p.required && v === "") continue;
      out[p.name] = v;
    }
    for (const [k, v] of Object.entries(value)) if (!(k in out) && !shape.properties.some((p) => p.name === k)) out[k] = v;
    return out;
  }
  if (shape.is === "list" && Array.isArray(value)) return value.map((v) => kept(v, shape.items, root));
  if (shape.is === "or-none" && value !== false) return kept(value, shape.schema, root);
  return value;
}
