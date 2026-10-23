import { mount } from "svelte";
import Home from "./Home.svelte";

const target = document.getElementById("home");
const held = document.getElementById("home-props");
if (target && held) {
  const { limit } = JSON.parse(held.textContent ?? "null") as { limit: number };
  target.replaceChildren();
  mount(Home, { target, props: { limit } });
}
