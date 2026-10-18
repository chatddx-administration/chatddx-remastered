export type Slot = { slot: string };
export type Insert = { insert: string; before?: string; after?: string };
export type Seg = string | Slot | Insert;

export const SLOTS: Record<string, string> = {
  completion: "the answer",
  expectation: "what the view reads of the expectation",
  vignette: "the vignette",
  appendices: "the appendices",
};

export const INSERTS: Record<string, string> = {
  output_guidance: "what it is told to answer",
  tool_guidance: "its tools' guidance",
  schema: "the answer's schema",
};

export function isSlot(s: Seg): s is Slot {
  return typeof s === "object" && "slot" in s;
}

export function isInsert(s: Seg): s is Insert {
  return typeof s === "object" && "insert" in s;
}

export function segmentsOf(text: unknown): Seg[] {
  if (typeof text === "string") return [text];
  if (Array.isArray(text)) return text.filter((s): s is Seg => typeof s === "string" || (typeof s === "object" && s !== null));
  return [""];
}

export function merged(segs: Seg[]): Seg[] {
  const out: Seg[] = [];
  for (const s of segs) {
    const last = out.at(-1);
    if (typeof s === "string" && typeof last === "string") out[out.length - 1] = last + s;
    else out.push(s);
  }
  return out.filter((s) => s !== "");
}

// Duplication: As src/chatddx/factors/request.py:_text keeps a Text, so that a text left as it was compares equal to
// the one stored.
export function textOf(segs: Seg[]): string | Seg[] {
  const kept = merged(segs);
  return kept.every((s) => typeof s === "string") ? kept.join("") : kept;
}

export function editable(segs: Seg[]): Seg[] {
  const out: Seg[] = [];
  for (const s of merged(segs)) {
    if (typeof s !== "string" && typeof out.at(-1) !== "string") out.push("");
    out.push(s);
  }
  if (typeof out.at(-1) !== "string") out.push("");
  return out;
}

export function filled(segs: Seg[], fills: Record<string, string>): string {
  return merged(segs)
    .map((s) => {
      if (typeof s === "string") return s;
      if (isSlot(s)) return fills[s.slot] ?? `‹${s.slot}›`;
      const text = fills[s.insert] ?? "";
      return text ? `${s.before ?? ""}${text}${s.after ?? ""}` : "";
    })
    .join("");
}

// Duplication: src/chatddx/factors/scoring.py:fill_text's "text@1": one text as it is, texts a line each, anything
// else as JSON.
export function fillText(items: unknown[]): string {
  const value = items.length === 1 ? items[0] : items;
  if (typeof value === "string") return value;
  if (Array.isArray(value) && value.every((v) => typeof v === "string")) return value.join("\n");
  return JSON.stringify(value, null, 2);
}

export type Said = { role: string; content: string };

export function asked(
  instructions: { role: string; segs: Seg[] } | null,
  prompt: Seg[],
  guidance: Seg[] | null,
  picked: unknown[] | null,
): Said[] {
  const guided = guidance ? filled(guidance, { schema: "‹the answer's schema›" }) : "";
  const placing = (segs: Seg[]) => segs.some((s) => isInsert(s) && s.insert === "output_guidance");
  const fills = {
    output_guidance: guided,
    tool_guidance: "",
    completion: "‹completion›",
    expectation: picked === null ? "‹expectation›" : fillText(picked),
  };
  // Duplication: As src/chatddx/factors/request.py:compile_request places it, guidance goes where it's inserted, or
  // else after the instructions.
  let system = instructions ? filled(instructions.segs, fills) : "";
  if (guided && !placing(prompt) && !(instructions && placing(instructions.segs)))
    system = system ? `${system}\n\n${guided}` : guided;
  const said: Said[] = [];
  if (system) said.push({ role: instructions?.role ?? "system", content: system });
  said.push({ role: "user", content: filled(prompt, fills) });
  return said;
}
