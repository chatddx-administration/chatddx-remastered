import { mount } from "svelte";
import Recipe, { type RecipeProps } from "./Recipe.svelte";

const target = document.getElementById("recipe-view");
const props = document.getElementById("recipe-props");
if (target && props) {
  target.replaceChildren();
  mount(Recipe, { target, props: { props: JSON.parse(props.textContent ?? "null") as RecipeProps } });
}
