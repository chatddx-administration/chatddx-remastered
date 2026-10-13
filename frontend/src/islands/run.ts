import { mount } from "svelte";
import ManagementPlan from "$lib/plan/ManagementPlan.svelte";
import { isPlan } from "$lib/plan/types";
import RunLive, { type Live } from "./RunLive.svelte";

for (const held of document.querySelectorAll<HTMLScriptElement>('script[type="application/json"][data-plan]')) {
  const target = held.previousElementSibling;
  const plan: unknown = JSON.parse(held.textContent ?? "null");
  if (target instanceof HTMLElement && target.hasAttribute("data-plan") && isPlan(plan)) {
    mount(ManagementPlan, { target, props: { plan } });
  }
}

const target = document.getElementById("run-live");
const held = document.getElementById("run-live-props");
if (target && held) {
  const live = JSON.parse(held.textContent ?? "null") as Live;
  target.replaceChildren();
  mount(RunLive, { target, props: { live } });
}
