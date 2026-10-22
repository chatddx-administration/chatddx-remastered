import { mount, unmount } from "svelte";
import JudgeTexts, { type Rewriting } from "$lib/scorer/JudgeTexts.svelte";

type Props = {
  judge: Omit<Rewriting, "texts"> & { texts: Rewriting["texts"] | null };
  expectation: string;
  data: unknown;
  me: string;
};

const target = document.getElementById("judge-texts");
const held = document.getElementById("scoring-props");
if (target && held) {
  const props = JSON.parse(held.textContent ?? "null") as Props;
  const { texts } = props.judge;
  const opening = document.createElement("button");
  opening.type = "button";
  opening.className = "rounded-md border border-border px-2.5 py-0.5 text-sm hover:bg-muted";
  opening.textContent = "Change what it is asked";
  const closed = (): void => target.replaceChildren(opening);
  opening.addEventListener("click", () => {
    if (!texts) return;
    target.replaceChildren();
    const shown = mount(JudgeTexts, {
      target,
      props: {
        judge: { ...props.judge, texts },
        expectation: props.expectation,
        data: props.data,
        me: props.me,
        made: (judge) => location.assign(`/scoring/${judge.thread}`),
        left: () => {
          void unmount(shown);
          closed();
        },
      },
    });
  });
  if (texts) closed();
  else {
    const said = document.createElement("p");
    said.className = "text-xs text-muted-foreground";
    said.textContent = "Its request was written by hand, not from a recipe: it is changed in the Library.";
    target.replaceChildren(said);
  }
}
