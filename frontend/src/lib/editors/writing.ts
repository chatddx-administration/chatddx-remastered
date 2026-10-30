import { api, type Schemas, why } from "$lib/api/client";
import { t } from "$lib/locale";

type Mode = "new" | "edit" | "fork";
export type Editing = { mode: Mode; thread?: number; head?: number; name: string };
export type Component = Schemas["ComponentBody"];

export function said(editing: Editing, name: string, unchanged: boolean): string {
  if (editing.mode === "edit") {
    return unchanged ? "" : t("Saves a new version of it.");
  }
  if (!name.trim()) return t("Give it a name to save it.");
  return editing.mode === "new"
    ? t("Writes “%(name)s”, a new thread of your own.", { name: name.trim() })
    : t("Saves it as “%(name)s”, a fork of your own.", { name: name.trim() });
}

export type Checked = { digest: string; findings: Schemas["Finding"][] } | { problem: string };

export async function checked(component: Component): Promise<Checked> {
  const got = await api.POST("/api/components/check", { body: component });
  return got.data ? got.data : { problem: why(got.error) };
}

export type Saved = (Extract<Written, { digest: string }> & { to: string }) | Extract<Written, { problem: string }>;

export type Labelled = (string | null)[];

// Policy: an empty name goes unnamed, which only an expectation may.
type Target = { thread: number | null; head?: number; mine?: boolean; name: string };
export type Written =
  | { digest: string; thread: number; head: number; cases: Record<string, string> }
  | { problem: string; moved: number | null };

export async function written(at: Target, body: Record<string, unknown>): Promise<Written> {
  if (at.thread !== null && at.mine && at.head !== undefined) {
    const thread = at.thread;
    const got = await api.POST("/api/threads/{thread}/edits", {
      params: { path: { thread } },
      body: { head: at.head, ...body },
    });
    if (got.data) return { digest: got.data.digest, thread, head: got.data.id, cases: got.data.cases ?? {} };
    if (got.response.status === 409) {
      const now = await api.GET("/api/threads/{thread}", { params: { path: { thread } } });
      return { problem: why(got.error), moved: now.data?.head.id ?? null };
    }
    return { problem: why(got.error), moved: null };
  }
  const got =
    at.thread === null
      ? await api.POST("/api/threads", { body: { name: at.name || null, ...body } })
      : await api.POST("/api/threads/{thread}/forks", {
          params: { path: { thread: at.thread } },
          body: { name: at.name, ...body },
        });
  return got.data
    ? { digest: got.data.head.digest, thread: got.data.id, head: got.data.head.id, cases: {} }
    : { problem: why(got.error), moved: null };
}

export async function saved(editing: Editing, name: string, component: Component, views?: Labelled): Promise<Saved> {
  const at = {
    thread: editing.mode === "new" ? null : (editing.thread ?? 0),
    head: editing.head ?? 0,
    mine: editing.mode === "edit",
    name: name.trim(),
  };
  const got = await written(at, {
    component,
    ...(views ? { labels: { views } } : {}),
  });
  return "problem" in got ? got : { ...got, to: `/threads/${got.thread}` };
}
