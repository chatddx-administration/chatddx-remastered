import { mount } from "svelte";
import { remembered } from "$lib/drawers";
import type { Props } from "$lib/variation/props";
import Variation from "./Variation.svelte";

for (const drawer of document.querySelectorAll<HTMLDetailsElement>("details[data-drawer]")) {
  remembered(drawer, "lab");
}

const target = document.getElementById("variation");
const held = document.getElementById("variation-props");
if (target && held) {
  const props = JSON.parse(held.textContent ?? "null") as Props;
  target.replaceChildren();
  mount(Variation, { target, props: { held: props } });
}
