import { mount } from "svelte";
import { remembered } from "$lib/drawers";
import AppendixEditor from "$lib/editors/AppendixEditor.svelte";
import Answer from "$lib/review/Answer.svelte";
import Expected from "$lib/review/Expected.svelte";
import Pending from "$lib/review/Pending.svelte";
import { replaced, type Review, stepped } from "$lib/review/review";
import Vignette from "$lib/review/Vignette.svelte";

function unfolded(at: HTMLDetailsElement, body: HTMLElement, show: () => void): void {
  const opened = () => {
    if (!at.open) return;
    at.removeEventListener("toggle", opened);
    body.replaceChildren();
    show();
  };
  at.addEventListener("toggle", opened);
}

const held = document.getElementById("review-props");
if (held) {
  const review = JSON.parse(held.textContent ?? "null") as Review;

  for (const drawer of document.querySelectorAll<HTMLDetailsElement>("details[data-drawer]")) {
    remembered(drawer, "review");
  }
  const cases = document.querySelector<HTMLDetailsElement>('details[data-drawer="cases"]');
  const list = cases?.querySelector<HTMLElement>(":scope > div");
  const current = list?.querySelector<HTMLElement>('a[aria-current="page"]');
  if (cases && list && current) {
    const centred = () => {
      if (cases.open) list.scrollTop = current.offsetTop - (list.clientHeight - current.offsetHeight) / 2;
    };
    centred();
    cases.addEventListener("toggle", centred);
  }
  const record = document.querySelector<HTMLDetailsElement>('details[data-drawer="record"]');
  if (record && location.hash === "#record") {
    record.open = true;
    history.replaceState(history.state, "", location.pathname + location.search);
  }

  const vignette = document.getElementById("review-vignette");
  if (vignette) {
    vignette.replaceChildren();
    mount(Vignette, { target: vignette, props: { family: review.family } });
  }

  const expected = document.getElementById("review-expected");
  const editor = review.expected.editor;
  if (expected && editor) {
    expected.replaceChildren();
    mount(Expected, { target: expected, props: { expected: review.expected, editor, back: review.back } });
  }

  for (const at of document.querySelectorAll<HTMLDetailsElement>("details[data-appendix]")) {
    const given = review.appendices[Number(at.dataset.appendix)];
    const body = at.querySelector<HTMLElement>("[data-appendix-body]");
    if (!given || !body) continue;
    unfolded(at, body, () =>
      mount(AppendixEditor, {
        target: body,
        props: { ...given, to: (saved) => replaced(review.back, review.case, saved.cases) },
      }),
    );
  }

  for (const at of document.querySelectorAll<HTMLDetailsElement>("details[data-answer]")) {
    const answer = review.answers[Number(at.dataset.answer)];
    const body = at.querySelector<HTMLElement>("[data-answer-body]");
    if (!answer || !body) continue;
    unfolded(at, body, () =>
      mount(Answer, {
        target: body,
        props: { answer, case: review.case, labels: review.labels, units: review.units },
      }),
    );
  }

  // Compromise: what someone has typed or picked outweighs showing a finished run at once; it then waits for "Show it".
  let touched = false;
  for (const name of ["input", "change"]) document.addEventListener(name, () => (touched = true), true);
  let waiting = review.pending.length;
  for (const at of document.querySelectorAll<HTMLElement>("[data-pending]")) {
    const given = review.pending[Number(at.dataset.pending)];
    if (!given) continue;
    at.replaceChildren();
    mount(Pending, {
      target: at,
      props: {
        ...given,
        done: () => {
          waiting -= 1;
          if (waiting === 0 && !touched) setTimeout(() => location.reload(), 800);
        },
      },
    });
  }

  document.addEventListener("keydown", (pressed) => {
    const to = stepped(pressed, review);
    if (to) location.assign(to);
  });
}
