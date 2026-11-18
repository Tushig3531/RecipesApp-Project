import { api, el, toast, PLACEHOLDER_IMG } from "./api.js";
import { refreshCounts } from "./auth.js";

const byId = (id) => document.getElementById(id);
let current = null; // { recipe, saved, status, have, total }

export function renderRecipes(container, recipes, options = {}) {
  container.replaceChildren(...recipes.map((r) => recipeCard(r, options)));
}

export function showSkeleton(container, n = 8) {
  container.replaceChildren(...Array.from({ length: n }, () =>
    el("div", { class: "recipe-card skeleton", "aria-hidden": "true" },
      el("div", { class: "card-photo" }),
      el("div", { class: "card-body-x" },
        el("div", { class: "skeleton-line" }),
        el("div", { class: "skeleton-line short" })))));
}

export function emptyState(title, text, action = null) {
  return el("div", { class: "empty-state" }, el("h2", {}, title), el("p", {}, text), action);
}

export async function openRecipeModal(recipeId) {
  ensureModal();
  try {
    current = await api(`/recipes/${recipeId}`);
    renderSheet();
    $("#recipe-modal").modal("show");
    loadVideo(recipeId);
  } catch (err) {
    toast(err.message, "error");
  }
}

function setImage(img, url) {
  img.onerror = () => { img.onerror = null; img.src = PLACEHOLDER_IMG; };
  img.src = url || PLACEHOLDER_IMG;
}

function tagPills(tags = []) {
  const pills = [];
  if (tags.includes("vegan")) pills.push(["Vegan", "veg"]);
  else if (tags.includes("vegetarian")) pills.push(["Vegetarian", "veg"]);
  if (tags.includes("drink")) pills.push(["Drink", "drink"]);
  return pills.map(([text, kind]) =>
    el("span", { class: `tag ${kind}`, title: "Best guess from the ingredient list" }, text));
}

function meter(have, total) {
  const label = `${have} of ${total} ingredients in your fridge`;
  const shown = Math.min(total, 12);
  const filled = Math.round((have / total) * shown);
  const pips = el("span", { class: "pips", "aria-hidden": "true" },
    Array.from({ length: shown }, (_, i) => el("span", { class: i < filled ? "pip on" : "pip" })));
  return el("div", { class: "meter", title: label },
    pips, el("span", { class: "meter-text", "aria-hidden": "true" }, `${have}/${total}`),
    el("span", { class: "sr-only" }, label));
}

function recipeCard(recipe, { onRemove } = {}) {
  const photo = el("img", { class: "card-photo", alt: "", loading: "lazy" });
  setImage(photo, recipe.image_url);

  const body = el("div", { class: "card-body-x" },
    el("h3", { class: "card-name" }, recipe.name),
    recipe.total ? meter(recipe.have, recipe.total) : null,
    recipe.missing?.length ? el("p", { class: "card-missing" }, `Need ${recipe.missing.join(", ")}`) : null,
    el("div", { class: "card-foot" },
      el("div", { class: "tag-row compact" }, tagPills(recipe.tags)),
      onRemove
        ? el("button", {
            type: "button", class: "link-button danger",
            onclick: (e) => { e.stopPropagation(); onRemove(recipe); },
          }, "Remove")
        : null));

  const card = el("article", { class: "recipe-card", tabindex: "0", role: "button", "aria-label": recipe.name }, photo, body);
  const open = () => openRecipeModal(recipe.recipe_id);
  card.addEventListener("click", open);
  card.addEventListener("keydown", (e) => {
    if (e.target === card && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      open();
    }
  });
  return card;
}

function ensureModal() {
  if (byId("recipe-modal")) return;
  document.body.append(
    el("div", { class: "modal fade", id: "recipe-modal", tabindex: "-1", role: "dialog", "aria-labelledby": "modal-title", "aria-hidden": "true" },
      el("div", { class: "modal-dialog modal-xl modal-dialog-scrollable", role: "document" },
        el("div", { class: "modal-content recipe-sheet" },
          el("div", { class: "modal-header" },
            el("h2", { class: "modal-title", id: "modal-title" }),
            el("button", { type: "button", class: "close", "data-dismiss": "modal", "aria-label": "Close" },
              el("span", { "aria-hidden": "true" }, "×"))),
          el("div", { class: "modal-body" },
            el("div", { class: "row" },
              el("div", { class: "col-lg-5 mb-4" },
                el("img", { id: "modal-image", class: "sheet-image", alt: "" }),
                el("div", { id: "modal-tags", class: "tag-row" }),
                el("div", { id: "modal-video", class: "sheet-video" })),
              el("div", { class: "col-lg-7" },
                el("div", { class: "sheet-heading" },
                  el("h3", {}, "Ingredients"),
                  el("span", { id: "modal-have", class: "have-summary" })),
                el("p", { class: "legend", "aria-hidden": "true" },
                  el("span", { class: "ing-dot have" }), "In your fridge",
                  el("span", { class: "ing-dot missing" }), "Missing",
                  el("span", { class: "ing-dot staple" }), "Pantry staple"),
                el("ul", { id: "modal-ingredients", class: "ingredient-list" }),
                el("button", { id: "modal-add-missing", class: "btn btn-outline-basil btn-sm mb-4", type: "button", onclick: addMissing }),
                el("h3", {}, "Method"),
                el("ol", { id: "modal-steps", class: "step-list" })))),
          el("div", { class: "modal-footer" },
            el("button", { id: "save-recipe", class: "btn btn-basil", type: "button", onclick: toggleSaved }, "Save recipe"),
            el("button", { class: "btn btn-quiet", type: "button", "data-dismiss": "modal" }, "Close")))))
  );
  $("#recipe-modal").on("hidden.bs.modal", () => {
    current = null;
    byId("modal-video").replaceChildren(); // stops playback
  });
}

function renderSheet() {
  const { recipe, status, have, total } = current;
  byId("modal-title").textContent = recipe.name;
  const img = byId("modal-image");
  img.alt = recipe.name;
  setImage(img, recipe.image_url);
  byId("modal-tags").replaceChildren(...tagPills(recipe.tags));

  byId("modal-have").textContent = total
    ? (have ? `You have ${have} of ${total}` : "None of these are in your fridge yet")
    : "";

  const prefix = { have: "In your fridge: ", missing: "Missing: ", staple: "Pantry staple: " };
  byId("modal-ingredients").replaceChildren(...recipe.ingredients.map((line, i) =>
    el("li", { class: `ing ${status[i]}` }, el("span", { class: "sr-only" }, prefix[status[i]]), line)));

  const missing = status.filter((s) => s === "missing").length;
  const addButton = byId("modal-add-missing");
  addButton.hidden = !missing;
  addButton.disabled = false;
  addButton.textContent = `Add ${missing} missing item${missing === 1 ? "" : "s"} to shopping list`;

  byId("modal-steps").replaceChildren(...recipe.steps.map((step) => el("li", {}, step)));
  renderSaveButton();
}

function renderSaveButton() {
  const btn = byId("save-recipe");
  btn.textContent = current.saved ? "Remove from saved" : "Save recipe";
  btn.className = current.saved ? "btn btn-quiet" : "btn btn-basil";
}

async function toggleSaved() {
  if (!current) return;
  const btn = byId("save-recipe");
  const { recipe_id, name } = current.recipe;
  btn.disabled = true;
  try {
    if (current.saved) {
      await api(`/unsave_recipe/${recipe_id}`, { method: "DELETE" });
      current.saved = false;
      toast(`Removed ${name} from saved`);
    } else {
      await api("/save_recipe", { method: "POST", body: { recipe_id } });
      current.saved = true;
      toast(`Saved ${name}`);
    }
    renderSaveButton();
    document.dispatchEvent(new CustomEvent("saved-changed"));
  } catch (err) {
    toast(err.message, "error");
  } finally {
    btn.disabled = false;
  }
}

async function addMissing() {
  if (!current) return;
  const btn = byId("modal-add-missing");
  btn.disabled = true;
  try {
    const { added } = await api(`/recipes/${current.recipe.recipe_id}/shopping`, { method: "POST", body: {} });
    toast(added ? `Added ${added} item${added === 1 ? "" : "s"} to your shopping list` : "Those are already on your shopping list");
    btn.textContent = "Added to shopping list";
    refreshCounts();
  } catch (err) {
    toast(err.message, "error");
    btn.disabled = false;
  }
}

async function loadVideo(recipeId) {
  const box = byId("modal-video");
  box.textContent = "Finding a video…";
  try {
    const { youtube_url } = await api(`/recipes/${recipeId}/video`);
    if (current?.recipe.recipe_id !== recipeId) return; // closed or switched recipes
    if (!youtube_url) {
      box.textContent = "No video for this one.";
      return;
    }
    box.replaceChildren(
      el("div", { class: "embed-responsive embed-responsive-16by9" },
        el("iframe", {
          class: "embed-responsive-item", src: youtube_url, title: `${current.recipe.name} video`,
          allow: "accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
          allowfullscreen: true,
        })));
  } catch {
    box.textContent = "Video unavailable right now.";
  }
}