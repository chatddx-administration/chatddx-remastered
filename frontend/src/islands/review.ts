import { mount } from "svelte";
import Answer from "$lib/review/Answer.svelte";
import { type Review, stepped } from "$lib/review/review";
import Vignette from "$lib/review/Vignette.svelte";

const held = document.getElementById("review-props");
if (held) {
  const review = JSON.parse(held.textContent ?? "null") as Review;

  const vignette = document.getElementById("review-vignette");
  if (vignette) {
    vignette.replaceChildren();
    mount(Vignette, { target: vignette, props: { family: review.family } });
  }

  for (const at of document.querySelectorAll<HTMLDetailsElement>("details[data-answer]")) {
    const answer = review.answers[Number(at.dataset.answer)];
    const body = at.querySelector<HTMLElement>("[data-answer-body]");
    if (!answer || !body) continue;
    const opened = () => {
      if (!at.open) return;
      at.removeEventListener("toggle", opened);
      body.replaceChildren();
      mount(Answer, { target: body, props: { answer, case: review.case, labels: review.labels, units: review.units } });
    };
    at.addEventListener("toggle", opened);
  }

  document.addEventListener("keydown", (pressed) => {
    const to = stepped(pressed, review);
    if (to) location.assign(to);
  });
}
