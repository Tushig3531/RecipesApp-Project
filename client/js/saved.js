import { api, el, toast } from "./api.js";
import { emptyState, renderRecipes, showSkeleton } from "./recipes-ui.js";

const grid = document.getElementById("saved-grid");
const summary = document.getElementById("saved-summary");

document.addEventListener("saved-changed", load);
load();

async function load() {
  if (!grid.children.length) showSkeleton(grid, 4);
  try {
    const recipes = await api("/saved_recipes");
    summary.textContent = recipes.length ? `${recipes.length} saved recipe${recipes.length === 1 ? "" : "s"}` : "";
    if (!recipes.length) {
      grid.replaceChildren(emptyState(
        "No saved recipes yet",
        "Open any recipe and choose “Save recipe” to keep it here.",
        el("a", { class: "btn btn-basil", href: "recipes.html" }, "Find recipes")));
      return;
    }
    renderRecipes(grid, recipes, { onRemove: remove });
  } catch (err) {
    toast(err.message, "error");
  }
}

async function remove(recipe) {
  try {
    await api(`/unsave_recipe/${recipe.recipe_id}`, { method: "DELETE" });
    toast(`Removed ${recipe.name} from saved`);
    load();
  } catch (err) {
    toast(err.message, "error");
  }
}