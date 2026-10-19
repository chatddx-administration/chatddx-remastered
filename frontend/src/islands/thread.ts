import { mount } from "svelte";
import ChunkEditor, { type ChunkEditing } from "$lib/editors/ChunkEditor.svelte";
import ExpectationEditor, { type ExpectationEditing } from "$lib/editors/ExpectationEditor.svelte";
import JudgeEditor, { type JudgeEditing } from "$lib/scorer/JudgeEditor.svelte";
import ScorerEditor, { type ScorerEditing } from "$lib/scorer/ScorerEditor.svelte";
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

for (const at of document.querySelectorAll<HTMLElement>("[data-chunk-editor]")) {
  const editor = JSON.parse(at.querySelector("script")?.textContent ?? "null") as ChunkEditing;
  at.replaceChildren();
  mount(ChunkEditor, { target: at, props: { editor } });
}

for (const at of document.querySelectorAll<HTMLElement>("[data-judge-editor]")) {
  const editor = JSON.parse(at.querySelector("script")?.textContent ?? "null") as JudgeEditing;
  at.replaceChildren();
  mount(JudgeEditor, { target: at, props: { editor } });
}

for (const at of document.querySelectorAll<HTMLElement>("[data-scorer-editor]")) {
  const editor = JSON.parse(at.querySelector("script")?.textContent ?? "null") as ScorerEditing;
  at.replaceChildren();
  mount(ScorerEditor, { target: at, props: { editor } });
}
