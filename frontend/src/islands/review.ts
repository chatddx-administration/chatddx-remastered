import { mount, unmount } from "svelte";
import { remembered } from "$lib/drawers";
import AppendixEditor from "$lib/editors/AppendixEditor.svelte";
import About from "$lib/review/About.svelte";
import { flipped, kept, type Picked, pickedIn, shown } from "$lib/review/filtering";
import Answer from "$lib/review/Answer.svelte";
import Expected from "$lib/review/Expected.svelte";
import Pending from "$lib/review/Pending.svelte";
import { replaced, type Review } from "$lib/review/review";
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

function changed(at: HTMLButtonElement, body: HTMLElement, show: () => ReturnType<typeof mount>): void {
  const read = [...body.childNodes];
  let shown: ReturnType<typeof mount> | null = null;
  at.hidden = false;
  at.addEventListener("click", () => {
    if (shown) {
      void unmount(shown);
      shown = null;
      body.replaceChildren(...read);
    } else {
      body.replaceChildren();
      shown = show();
    }
    at.setAttribute("aria-pressed", String(shown !== null));
  });
}

function filtering(list: HTMLElement, filters: HTMLElement): void {
  let picked: Picked = pickedIn(location.search);
  const items = [...list.querySelectorAll<HTMLLIElement>("li[data-tags]")];
  const none = list.querySelector<HTMLElement>("li[data-none]");
  const choices = [...filters.querySelectorAll<HTMLAnchorElement>("a[data-tag], a[data-language], a[data-all]")];

  const applied = () => {
    for (const item of items) {
      const tags = JSON.parse(item.dataset.tags ?? "[]") as string[];
      item.hidden = !shown(tags, item.dataset.language ?? "", picked);
    }
    if (none) none.hidden = items.some((item) => !item.hidden);
    for (const at of choices) {
      const { tag, language } = at.dataset;
      const on =
        tag !== undefined
          ? picked.tags.includes(tag)
          : language !== undefined
            ? picked.languages.includes(language)
            : !picked.tags.length && !picked.languages.length;
      if (on) at.setAttribute("aria-current", "true");
      else at.removeAttribute("aria-current");
    }
    history.replaceState(history.state, "", kept(location.pathname + location.search + location.hash, picked));
    for (const at of document.querySelectorAll<HTMLAnchorElement>('a[href^="/review/"]')) {
      if (!choices.includes(at)) at.setAttribute("href", kept(at.getAttribute("href") ?? "", picked));
    }
    for (const at of document.querySelectorAll<HTMLInputElement>('input[name="back"], input[name="next"]')) {
      if (at.value.startsWith("/review/")) at.value = kept(at.value, picked);
    }
  };

  filters.addEventListener("click", (clicked) => {
    const at = (clicked.target as Element).closest<HTMLAnchorElement>("a[data-tag], a[data-language], a[data-all]");
    if (!at || clicked.button || clicked.metaKey || clicked.ctrlKey || clicked.shiftKey || clicked.altKey) return;
    clicked.preventDefault();
    const { tag, language } = at.dataset;
    if (tag !== undefined) picked = { ...picked, tags: flipped(picked.tags, tag) };
    else if (language !== undefined) picked = { ...picked, languages: flipped(picked.languages, language) };
    else picked = { tags: [], languages: [] };
    applied();
  });
}

const held = document.getElementById("review-props");
if (held) {
  const review = JSON.parse(held.textContent ?? "null") as Review;

  for (const drawer of document.querySelectorAll<HTMLDetailsElement>("details[data-drawer]")) {
    remembered(drawer, "review");
  }
  const list = document.querySelector<HTMLElement>("[data-cases]");
  const current = list?.querySelector<HTMLElement>('li a[aria-current="page"]');
  if (list && current) list.scrollTop = current.offsetTop - (list.clientHeight - current.offsetHeight) / 2;
  const filters = list?.querySelector<HTMLElement>("nav[data-filters]");
  if (list && filters) filtering(list, filters);

  const about = document.getElementById("review-about");
  if (about) {
    about.replaceChildren();
    mount(About, { target: about, props: { about: review.about } });
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

  for (const at of document.querySelectorAll<HTMLElement>("[data-appendix]")) {
    const given = review.appendices[Number(at.dataset.appendix)];
    const change = at.querySelector<HTMLButtonElement>("button[data-change]");
    const body = at.querySelector<HTMLElement>("[data-appendix-body]");
    if (!given || !change || !body) continue;
    changed(change, body, () =>
      mount(AppendixEditor, {
        target: body,
        props: { ...given, quiet: true, to: (saved) => replaced(review.back, review.case, saved.cases) },
      }),
    );
  }

  const appending = document.querySelector<HTMLFormElement>("form[data-appending]");
  const save = appending?.querySelector("button");
  if (appending && save) {
    const typed = [...appending.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>("[required]")];
    const check = () => {
      save.disabled = typed.some((at) => !at.value.trim());
    };
    check();
    appending.addEventListener("input", check);
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
}
