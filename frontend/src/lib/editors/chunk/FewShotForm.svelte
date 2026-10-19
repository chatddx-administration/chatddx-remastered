<script lang="ts">
  import { FIELD } from "$lib/utils";
  import { type Body, moved } from "../chunks";

  type Example = { role: string; content: string };

  let { body, set }: { body: Body; set: (body: Body) => void } = $props();

  const messages = $derived((Array.isArray(body.messages) ? body.messages : []) as Example[]);

  function changed(next: Example[]): void {
    set({ ...body, messages: next });
  }
</script>

<div class="space-y-2 text-sm" role="group" aria-label="Its messages">
  <p class="font-medium">Its messages, in order</p>
  {#each messages as m, at (at)}
    <div class="flex gap-2">
      <select
        class="{FIELD} w-28"
        aria-label="Message {at + 1}, from"
        value={m.role}
        onchange={(e) => changed(messages.map((x, i) => (i === at ? { ...x, role: e.currentTarget.value } : x)))}
      >
        <option value="user">user</option>
        <option value="assistant">assistant</option>
      </select>
      <textarea
        class="min-w-0 flex-1 rounded-md border border-input bg-transparent px-2 py-1 [field-sizing:content]"
        rows="2"
        aria-label="Message {at + 1}"
        value={m.content}
        oninput={(e) => changed(messages.map((x, i) => (i === at ? { ...x, content: e.currentTarget.value } : x)))}
      ></textarea>
      <div class="flex flex-col">
        <button type="button" class="rounded px-1 hover:bg-muted disabled:opacity-40" disabled={at === 0} aria-label="Message {at + 1} up" onclick={() => changed(moved(messages, at, -1))}>▲</button>
        <button
          type="button"
          class="rounded px-1 hover:bg-muted disabled:opacity-40"
          disabled={at === messages.length - 1}
          aria-label="Message {at + 1} down"
          onclick={() => changed(moved(messages, at, 1))}>▼</button
        >
        <button type="button" class="rounded px-1 text-muted-foreground hover:bg-muted" aria-label="Leave out message {at + 1}" onclick={() => changed(messages.filter((_, i) => i !== at))}>×</button>
      </div>
    </div>
  {/each}
  <button
    type="button"
    class="rounded-md border border-dashed border-border px-2 py-0.5 text-muted-foreground hover:bg-muted"
    onclick={() => changed([...messages, { role: messages.at(-1)?.role === "user" ? "assistant" : "user", content: "" }])}>+ a message</button
  >
</div>
