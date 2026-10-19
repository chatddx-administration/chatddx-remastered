import { mount } from "svelte";
import { remembered } from "$lib/drawers";
import Request from "$lib/translate/Request.svelte";
import Texts from "$lib/translate/Texts.svelte";
import type { Translating } from "$lib/translate/translate";

const held = document.getElementById("translate-props");
if (held) {
  const translating = JSON.parse(held.textContent ?? "null") as Translating;
  for (const drawer of document.querySelectorAll<HTMLDetailsElement>("details[data-drawer]")) {
    remembered(drawer, "translate");
  }
  for (const [id, component] of [
    ["translate-texts", Texts],
    ["translate-request", Request],
  ] as const) {
    const target = document.getElementById(id);
    if (!target) continue;
    target.replaceChildren();
    mount(component, { target, props: { translating } });
  }
}
