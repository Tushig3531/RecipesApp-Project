import { api, debounce, el, prefs, suggestionKeys, toast } from "./api.js";
import { emptyState, openRecipeModal, renderRecipes, showSkeleton } from "./recipes-ui.js";

const PER_PAGE = 24;
const PLACEHOLDERS = { ingredients: "chicken, garlic, lemon", name: "mac and cheese" };
const byId = (id) => document.getElementById(id);
const state = { mode: "fridge", query: "", page: 1 };
let requestSeq = 0;
let suggestSeq = 0;

restorePrefs();
bindEvents();
applyMode();

function currentMode() {
  return document.querySelector('input[name="mode"]:checked')?.value || "fridge";
}

function selectedDiets() {
  return [...document.querySelectorAll('input[name="diet"]:checked')].map((b) => b.value);
}

function filterParams() {
  const params = new URLSearchParams({ kind: byId("include-drinks").checked ? "all" : "food" });
  const diets = selectedDiets();
  if (diets.length) params.set("diet", diets.join(","));
  return params;
}

function restorePrefs() {
  const saved = prefs.get("cook", {});
  const mode = document.querySelector(`input[name="mode"][value="${saved.mode}"]`);
  if (mode) mode.checked = true;
  for (const diet of saved.diets || []) {
    const box = document.querySelector(`input[name="diet"][value="${diet}"]`);
    if (box) box.checked = true;
  }
  byId("include-drinks").checked = Boolean(saved.drinks);
}

function savePrefs() {
  prefs.set("cook", { mode: currentMode(), diets: selectedDiets(), drinks: byId("include-drinks").checked });
}

function bindEvents() {
  document.querySelectorAll('input[name="mode"]').forEach((radio) =>
    radio.addEventListener("change", () => { savePrefs(); applyMode(); }));

  document.querySelectorAll('input[name="diet"], #include-drinks').forEach((box) =>
    box.addEventListener("change", () => {
      savePrefs();
      if (state.mode === "fridge" || state.query) load(1);
    }));

  byId("search-form").addEventListener("submit", (e) => { e.preventDefault(); newSearch(); });

  const input = byId("search-input");
  const box = byId("suggestions");
  input.addEventListener("input", debounce(showSuggestions, 200));
  input.addEventListener("keydown", (e) => suggestionKeys(e, box, input));
  box.addEventListener("keydown", (e) => suggestionKeys(e, box, input));
  document.addEventListener("click", (e) => { if (!e.target.closest(".search-box")) box.hidden = true; });

  byId("prev").addEventListener("click", () => load(state.page - 1, true));
  byId("next").addEventListener("click", () => load(state.page + 1, true));
  byId("surprise").addEventListener("click", surprise);
}

function applyMode() {
  state.mode = currentMode();
  state.query = "";
  const searching = state.mode !== "fridge";
  byId("search-form").hidden = !searching;
  byId("suggestions").hidden = true;
  if (searching) {
    const input = byId("search-input");
    input.value = "";
    input.placeholder = PLACEHOLDERS[state.mode];
    byId("results").replaceChildren();
    byId("result-summary").textContent = "";
    updatePager(0, 1, PER_PAGE);
    input.focus();
  } else {
    load(1);
  }
}

function newSearch() {
  const query = byId("search-input").value.trim().replace(/,\s*$/, "");
  if (!query) {
    toast("Type an ingredient or a recipe name first.", "warn");
    return;
  }
  byId("suggestions").hidden = true;
  state.query = query;
  load(1);
}

async function load(page, scroll = false) {
  const params = filterParams();
  params.set("page", page);
  params.set("per_page", PER_PAGE);
  let path = "/recipes/from_fridge?";
  if (state.mode === "ingredients") {
    params.set("ingredients", state.query);
    path = "/search_recipes_by_ingredients?";
  } else if (state.mode === "name") {
    params.set("name", state.query);
    path = "/search_recipes_by_name?";
  }

  const seq = ++requestSeq;
  showSkeleton(byId("results"), 8);
  try {
    const data = await api(path + params);
    if (seq !== requestSeq) return; // a newer request replaced this one
    state.page = data.page;
    render(data);
    if (scroll) {
      const smooth = !matchMedia("(prefers-reduced-motion: reduce)").matches;
      byId("result-summary").scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
    }
  } catch (err) {
    if (seq !== requestSeq) return;
    byId("results").replaceChildren();
    toast(err.message, "error");
  }
}

function render(data) {
  const results = byId("results");
  const summary = byId("result-summary");

  if (data.empty_fridge) {
    summary.textContent = "";
    results.replaceChildren(emptyState(
      "Your fridge is empty",
      "Add a few things you have at home and recipes that use them will show up here.",
      el("a", { class: "btn btn-basil", href: "fridge.html" }, "Add fridge items")));
    updatePager(0, 1, PER_PAGE);
    return;
  }

  const n = data.count.toLocaleString();
  if (state.mode === "fridge") {
    summary.textContent = data.count ? `${n} recipes use something from your fridge. Closest matches first.` : "";
  } else {
    summary.textContent = data.count ? `${n} recipe${data.count === 1 ? "" : "s"} for “${state.query}”` : "";
  }

  if (!data.recipes.length) {
    const empty = state.mode === "fridge"
      ? emptyState("No matches with these filters", "Turn a filter off, or add more items to your fridge.")
      : emptyState(`Nothing found for “${state.query}”`,
          state.mode === "ingredients"
            ? "Try fewer ingredients, or a simpler word like “chicken” instead of “chicken breast”."
            : "Try a shorter name, or search by ingredient instead.");
    results.replaceChildren(empty);
  } else {
    renderRecipes(results, data.recipes);
  }
  updatePager(data.count, data.page, data.per_page || PER_PAGE);
}

function updatePager(count, page, perPage) {
  const pages = Math.max(1, Math.ceil(count / perPage));
  byId("pager").hidden = count <= perPage;
  byId("page-label").textContent = `Page ${page} of ${pages}`;
  byId("prev").disabled = page <= 1;
  byId("next").disabled = page >= pages;
}

async function surprise() {
  try {
    const { recipe_id } = await api(`/recipes/random?${filterParams()}`);
    openRecipeModal(recipe_id);
  } catch (err) {
    toast(err.message, "error");
  }
}

async function showSuggestions() {
  if (state.mode === "fridge") return;
  const input = byId("search-input");
  const box = byId("suggestions");
  const term = state.mode === "ingredients" ? input.value.split(",").pop().trim() : input.value.trim();
  if (term.length < 2) {
    box.hidden = true;
    return;
  }
  const seq = ++suggestSeq;
  try {
    const params = new URLSearchParams({ type: state.mode, q: input.value });
    const { suggestions } = await api(`/autocomplete_recipes?${params}`);
    if (seq !== suggestSeq) return;
    if (!suggestions.length) {
      box.hidden = true;
      return;
    }
    box.replaceChildren(...suggestions.map((s) =>
      el("button", { type: "button", class: "suggestion", role: "option", onclick: () => pickSuggestion(s) }, s)));
    box.hidden = false;
  } catch {
    box.hidden = true;
  }
}

function pickSuggestion(s) {
  const input = byId("search-input");
  byId("suggestions").hidden = true;
  if (state.mode === "ingredients") {
    const parts = input.value.split(",");
    parts[parts.length - 1] = s; // replace only the word being typed
    input.value = parts.map((p) => p.trim()).filter(Boolean).join(", ") + ", ";
    input.focus();
  } else {
    input.value = s;
    newSearch();
  }
}