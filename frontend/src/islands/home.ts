import { mount } from "svelte";
import Home from "./Home.svelte";

const target = document.getElementById("home");
const held = document.getElementById("home-props");
if (target && held) {
  const { limit, models } = JSON.parse(held.textContent ?? "null") as {
    limit: number;
    models: { name: string; weights: string }[];
  };
  target.replaceChildren();
  mount(Home, { target, props: { limit, models } });
}
