export type Said = { tag: string; messages: Record<string, string | string[]> };
type Given = Record<string, string | number>;

const PLACEHOLDER = /%(?:\((\w+)\)s|%)/g;
let spoken: Said | undefined;

export function speaking(given: Said): void {
  spoken = given;
}

export function t(message: string, given: Given = {}): string {
  return filled(said(message), given);
}

// Policy: a message holding markup is markup, as a translation is trusted as the server's are;
// what is put into it is escaped, as a {% trans %} block's variables are.
export function th(message: string, given: Given = {}): string {
  return filled(said(message), given, escaped);
}

export function tn(singular: string, plural: string, n: number, given: Given = {}): string {
  return filled(counted(singular, plural, n), given);
}

export function tp(context: string, message: string, given: Given = {}): string {
  return filled(said(message, context), given);
}

export function tnp(context: string, singular: string, plural: string, n: number, given: Given = {}): string {
  return filled(counted(singular, plural, n, context), given);
}

export function whoops(message: string): string {
  return said(message, "whoops");
}

export function listed(items: string[], type: "conjunction" | "disjunction" = "conjunction"): string {
  return new Intl.ListFormat(catalog().tag, { type }).format(items);
}

function said(message: string, context?: string): string {
  const found = catalog().messages[keyed(message, context)];
  return typeof found === "string" ? found : message;
}

function counted(singular: string, plural: string, n: number, context?: string): string {
  const { tag, messages } = catalog();
  const found = messages[keyed(singular, context)];
  const [one, other] = Array.isArray(found) ? found : [singular, plural];
  return (new Intl.PluralRules(tag).select(n) === "one" ? one : other) ?? plural;
}

function keyed(message: string, context: string | undefined): string {
  return context === undefined ? message : `${context}\u0004${message}`;
}

function catalog(): Said {
  spoken ??= inPage() ?? { tag: "en", messages: {} };
  return spoken;
}

function inPage(): Said | undefined {
  const text = typeof document === "undefined" ? null : document.getElementById("locale")?.textContent;
  return text ? (JSON.parse(text) as Said) : undefined;
}

function filled(message: string, given: Given, shown: (value: string) => string = String): string {
  return message.replace(PLACEHOLDER, (_, name: string | undefined) => {
    if (name === undefined) return "%";
    const value = given[name];
    if (value === undefined) throw new Error(`nothing given for %(${name})s in ${JSON.stringify(message)}`);
    return shown(String(value));
  });
}

function escaped(value: string): string {
  return value.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}
