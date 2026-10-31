import { mount } from "svelte";
import { t } from "$lib/locale";
import About from "$lib/review/About.svelte";
import Appendices from "$lib/review/Appendices.svelte";
import { Edited } from "$lib/review/edited.svelte";
import { flipped, kept, type Picked, pickedIn, shown } from "$lib/review/filtering";
import Expected from "$lib/review/Expected.svelte";
import Faring from "$lib/review/Faring.svelte";
import { Measure, measuredAt } from "$lib/review/measure.svelte";
import Measuring from "$lib/review/Measuring.svelte";
import type { Review } from "$lib/review/review";
import Save from "$lib/review/Save.svelte";
import Vignette from "$lib/review/Vignette.svelte";

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

  const list = document.querySelector<HTMLElement>("[data-cases]");
  const current = list?.querySelector<HTMLElement>('li a[aria-current="page"]');
  if (list && current) list.scrollTop = current.offsetTop - (list.clientHeight - current.offsetHeight) / 2;
  const filters = list?.querySelector<HTMLElement>("nav[data-filters]");
  if (list && filters) filtering(list, filters);

  const edited = new Edited(review.case, (to) => location.assign(to));
  const about = document.getElementById("review-about");
  if (about) {
    about.replaceChildren();
    mount(About, { target: about, props: { about: review.about, edited } });
  }

  const vignette = document.getElementById("review-vignette");
  if (vignette) {
    vignette.replaceChildren();
    mount(Vignette, { target: vignette, props: { family: review.family } });
  }

  const grid = document.querySelector<HTMLElement>("[data-review]");
  const measuring = document.getElementById("review-measure");
  const moved = (field: string | null, pushed = true): void => {
    if (!grid || !measuring) return;
    measure.field = field;
    grid.toggleAttribute("data-measuring", field !== null);
    measuring.inert = field === null;
    if (pushed) history.pushState(history.state, "", measuredAt(location.href, field));
    if (field !== null && !matchMedia("(width >= 80rem)").matches) {
      measuring.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };
  const measure = new Measure(review.measure, moved);
  addEventListener("popstate", () => {
    const field = new URL(location.href).searchParams.get("measure");
    moved(field !== null && measure.fields.includes(field) ? field : null, false);
  });

  const expected = document.getElementById("review-expected");
  const editor = review.expected.editor;
  if (expected && editor) {
    expected.replaceChildren();
    const shown = mount(Expected, {
      target: expected,
      props: { expected: review.expected, editor, edited, measure },
    });
    if (measuring && measure.fields.length) {
      mount(Measuring, {
        target: measuring,
        props: { measure, case: review.case, schema: editor.schema, current: () => shown.current() },
      });
    }
  }

  const appendices = document.getElementById("review-appendices");
  if (appendices) {
    appendices.replaceChildren();
    mount(Appendices, {
      target: appendices,
      props: { appendices: review.appendices, family: review.family, case: review.case, edited },
    });
  }

  const faring = document.querySelector("#review-faring > .pane");
  if (faring && review.schema) {
    faring.replaceChildren();
    mount(Faring, { target: faring, props: { family: review.family, case: review.case, schema: review.schema } });
  }

  const save = document.getElementById("review-save");
  if (save) mount(Save, { target: save, props: { edited } });
  const running = document.querySelector<HTMLFormElement>("form[data-running]");
  let leaving = false;
  running?.addEventListener("submit", (sent) => {
    if (edited.pending && !confirm(t("What you changed isn't saved: run the case as it was last saved?"))) {
      sent.preventDefault();
    } else leaving = true;
  });
  addEventListener("beforeunload", (left) => {
    if (edited.pending && !leaving) left.preventDefault();
  });
  for (const at of document.querySelectorAll<HTMLFormElement>("form[data-confirm]")) {
    at.addEventListener("submit", (sent) => {
      if (!confirm(at.dataset.confirm ?? "")) sent.preventDefault();
    });
  }
}
