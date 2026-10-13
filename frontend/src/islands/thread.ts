import { mount } from "svelte";
import ExpectationEditor, { type ExpectationEditing } from "$lib/editors/ExpectationEditor.svelte";
import Thread, { type Held } from "./Thread.svelte";

const target = document.getElementById("thread-view");
const props = document.getElementById("thread-props");
if (target && props) {
  const held = JSON.parse(props.textContent ?? "null") as Held;
  target.replaceChildren();
  mount(Thread, { target, props: { held } });
}

for (const at of document.querySelectorAll<HTMLElement>("[data-editor]")) {
  const editor = JSON.parse(at.querySelector("script")?.textContent ?? "null") as ExpectationEditing;
  at.replaceChildren();
  mount(ExpectationEditor, { target: at, props: { editor } });
}
