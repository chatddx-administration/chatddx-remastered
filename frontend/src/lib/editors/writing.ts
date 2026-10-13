import { api, type Schemas, why } from "$lib/api/client";

export type Mode = "new" | "edit" | "fork";
export type Editing = { mode: Mode; thread?: number; head?: number; name: string };
export type Component = Schemas["ComponentBody"];

export function said(editing: Editing, name: string, unchanged: boolean): string {
  if (editing.mode === "edit") return unchanged ? "Nothing to save: it holds this already." : "Saves a new version of it.";
  if (!name.trim()) return "Give it a name to save it.";
  return editing.mode === "new"
    ? `Writes “${name.trim()}”, a new thread of your own.`
    : `Saves it as “${name.trim()}”, a fork of your own.`;
}

export type Checked = { digest: string; findings: Schemas["Finding"][] } | { problem: string };

export async function checked(component: Component): Promise<Checked> {
  const got = await api.POST("/api/components/check", { body: component });
  return got.data ? got.data : { problem: why(got.error) };
}

export type Saved =
  | { to: string; cases: number }
  | { problem: string; moved: number | null };

export async function saved(editing: Editing, name: string, component: Component): Promise<Saved> {
  const thread = editing.thread ?? 0;
  if (editing.mode === "edit") {
    const got = await api.POST("/api/threads/{thread}/edits", {
      params: { path: { thread } },
      body: { head: editing.head ?? 0, component },
    });
    if (got.data) return { to: `/threads/${thread}`, cases: Object.keys(got.data.cases ?? {}).length };
    if (got.response.status === 409) {
      const now = await api.GET("/api/threads/{thread}", { params: { path: { thread } } });
      return { problem: why(got.error), moved: now.data?.head.id ?? null };
    }
    return { problem: why(got.error), moved: null };
  }
  const got =
    editing.mode === "new"
      ? await api.POST("/api/threads", { body: { component, name: name.trim() } })
      : await api.POST("/api/threads/{thread}/forks", {
          params: { path: { thread } },
          body: { name: name.trim(), component },
        });
  return got.data ? { to: `/threads/${got.data.id}`, cases: 0 } : { problem: why(got.error), moved: null };
}
