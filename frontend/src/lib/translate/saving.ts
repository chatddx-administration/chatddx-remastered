import { written } from "$lib/scorer/rewriting";
import type { Configuration, Held, Unchanged } from "./translate";

export type Saved = { to: string } | { problem: string };

export async function saved(
  held: Held | null,
  configuration: Configuration,
  body: Held["body"],
  into: string,
  unchanged: Unchanged,
): Promise<Saved> {
  let digest = held?.digest ?? null;
  if (!unchanged.translations) {
    const at =
      held?.thread != null
        ? { thread: held.thread, head: held.head ?? undefined, mine: held.mine, name: held.title }
        : { thread: null, name: configuration.name };
    const got = await written(at, { component: body });
    if ("problem" in got) return { problem: `The translations: ${got.problem}` };
    digest = got.digest;
  }
  let thread = configuration.thread;
  if (digest !== configuration.translations) {
    const mine = configuration.mine && configuration.latest;
    const at = { thread, head: configuration.head, mine, name: configuration.name };
    const got = await written(at, { parts: { translations: digest }, ...(mine ? {} : { head: configuration.head }) });
    if ("problem" in got) return { problem: `The configuration: ${got.problem}` };
    thread = got.thread;
  }
  return { to: `/translate/${thread}?into=${encodeURIComponent(into)}` };
}
