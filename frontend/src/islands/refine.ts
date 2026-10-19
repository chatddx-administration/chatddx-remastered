import { remembered } from "$lib/drawers";

for (const drawer of document.querySelectorAll<HTMLDetailsElement>("details[data-drawer]")) {
  remembered(drawer, "refine");
}
