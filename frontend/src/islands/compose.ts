import { mount } from "svelte";
import type { Props } from "$lib/compose/props";
import Compose from "./Compose.svelte";

const target = document.getElementById("compose");
const held = document.getElementById("compose-props");
if (target && held) {
  const props = JSON.parse(held.textContent ?? "null") as Props;
  target.replaceChildren();
  mount(Compose, { target, props: { held: props } });
}
