import { mount } from "svelte";
import Home from "./Home.svelte";

const target = document.getElementById("home");
if (target) {
  target.replaceChildren();
  mount(Home, { target });
}
