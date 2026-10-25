import { written } from "$lib/editors/writing";
import { worded } from "$lib/kinds";
import { t } from "$lib/locale";
import type { JudgeChoice } from "./judging";

export type Chunk = {
  digest: string;
  body: Record<string, unknown>;
  name: string;
  thread: number | null;
  head?: number;
  mine?: boolean;
  language?: string | null;
};
export type Texts = {
  configuration: { thread: number; head: number; mine: boolean; name: string } | null;
  recipe: Record<string, unknown>;
  parts: Record<"instructions" | "prompt" | "output", Chunk | null>;
};
export type Part = keyof Texts["parts"];
export async function rewritten(
  judge: JudgeChoice & { texts: Texts; body: Record<string, unknown>; head: number },
  bodies: Partial<Record<Part, Record<string, unknown>>>,
  me: string,
): Promise<
  { judge: JudgeChoice & { texts: Texts; body: Record<string, unknown>; head: number } } | { problem: string }
> {
  const parts: Partial<Record<Part, string>> = {};
  const now = JSON.parse(JSON.stringify(judge.texts)) as Texts;
  for (const [part, body] of Object.entries(bodies) as [Part, Record<string, unknown>][]) {
    const chunk = judge.texts.parts[part];
    if (!chunk) continue;
    const language = chunk.language ? { language: chunk.language } : {};
    const got = await written(chunk, { component: body, ...language });
    if ("problem" in got) return { problem: t("%(part)s: %(problem)s", { part: worded(part), problem: got.problem }) };
    parts[part] = got.digest;
    now.parts[part] = { ...chunk, digest: got.digest, body, thread: got.thread, head: got.head, mine: true };
  }
  const configuration = judge.texts.configuration;
  const requested = t("%(judge)s's request", { judge: judge.name });
  const made = configuration
    ? await written(configuration, { parts })
    : await written({ thread: null, name: requested }, { recipe: { ...judge.texts.recipe, ...parts } });
  if ("problem" in made) return { problem: t("its configuration: %(problem)s", { problem: made.problem }) };
  now.configuration = { thread: made.thread, head: made.head, mine: true, name: configuration?.name ?? requested };
  now.recipe = { ...judge.texts.recipe, ...parts };
  const body = { ...judge.body, skeleton: made.digest };
  const asked = await written(
    { thread: judge.thread, head: judge.head, mine: judge.owner === me, name: judge.name },
    { component: body },
  );
  if ("problem" in asked) return { problem: t("the judge: %(problem)s", { problem: asked.problem }) };
  return {
    judge: {
      ...judge,
      digest: asked.digest,
      thread: asked.thread,
      head: asked.head,
      owner: me,
      configuration: now.configuration.name,
      body,
      texts: now,
    },
  };
}
