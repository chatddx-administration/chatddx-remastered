import { mount } from "svelte";
import type { Props } from "$lib/variation/props";
import Variation from "./Variation.svelte";

const target = document.getElementById("variation");
const held = document.getElementById("variation-props");
if (target && held) {
  const props = JSON.parse(held.textContent ?? "null") as Props;
  target.replaceChildren();
  mount(Variation, { target, props: { held: props } });
}
