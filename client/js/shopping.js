import { api, el, prefs, toast } from "./api.js";
import { refreshCounts } from "./auth.js";

const STORES = [
  { id: "walmart", name: "Walmart", url: (q) => `https://www.walmart.com/search?q=${encodeURIComponent(q)}` },
  { id: "target", name: "Target", url: (q) => `https://www.target.com/s?searchTerm=${encodeURIComponent(q)}` },
  { id: "kroger", name: "Kroger", url: (q) => `https://www.kroger.com/search?query=${encodeURIComponent(q)}` },
  { id: "hyvee", name: "Hy-Vee", url: (q) => `https://www.hy-vee.com/aisles-online/search?search=${encodeURIComponent(q)}` },
  { id: "costco", name: "Costco", url: (q) => `https://www.costco.com/CatalogSearch?keyword=${encodeURIComponent(q)}` },
];

const byId = (id) => document.getElementById(id);
let items = [];

const storeSelect = byId("store");
storeSelect.replaceChildren(...STORES.map((s) => el("option", { value: s.id }, s.name)));
storeSelect.value = prefs.get("store", "walmart");
storeSelect.addEventListener("change", () => { prefs.set("store", storeSelect.value); render(); });
byId("add-shopping").addEventListener("submit", addItem);
byId("clear-checked").addEventListener("click", clearChecked);
load();

async function load() {
  try {
    items = await api("/shopping");
    render();
  } catch (err) {
    toast(err.message, "error");
  }
}

function currentStore() {
  return STORES.find((s) => s.id === storeSelect.value) || STORES[0];
}

function render() {
  items.sort((a, b) => Number(a.checked) - Number(b.checked));
  byId("shopping-list").replaceChildren(...items.map(row));
  byId("shopping-empty").hidden = items.length > 0;
  updateClearButton();
}

function updateClearButton() {
  const n = items.filter((i) => i.checked).length;
  const btn = byId("clear-checked");
  btn.hidden = !n;
  btn.textContent = `Clear ${n} checked item${n === 1 ? "" : "s"}`;
}

function row(item) {
  const store = currentStore();
  const li = el("li", { class: item.checked ? "shop-item done" : "shop-item" });
  const box = el("input", { type: "checkbox", checked: item.checked });
  box.addEventListener("change", () => toggle(item, box.checked, li));
  li.append(
    el("label", { class: "shop-label" }, box,
      el("span", { class: "shop-text" }, item.text,
        item.recipe_name ? el("span", { class: "shop-for" }, `for ${item.recipe_name}`) : null)),
    el("a", { class: "shop-find", href: store.url(item.term), target: "_blank", rel: "noopener" }, `Find at ${store.name}`),
    el("button", { type: "button", class: "icon-button", "aria-label": `Remove ${item.text}`, onclick: () => remove(item) }, "×"));
  return li;
}

async function toggle(item, checked, li) {
  item.checked = checked;
  li.classList.toggle("done", checked);
  updateClearButton();
  try {
    await api(`/shopping/${item.id}`, { method: "PATCH", body: { checked } });
    refreshCounts();
  } catch (err) {
    item.checked = !checked;
    render();
    toast(err.message, "error");
  }
}

async function addItem(e) {
  e.preventDefault();
  const input = byId("shopping-input");
  const text = input.value.trim();
  if (!text) return;
  try {
    const item = await api("/shopping", { method: "POST", body: { text } });
    items.unshift(item);
    input.value = "";
    render();
    refreshCounts();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function remove(item) {
  try {
    await api(`/shopping/${item.id}`, { method: "DELETE" });
    items = items.filter((i) => i !== item);
    render();
    refreshCounts();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function clearChecked() {
  try {
    const { removed } = await api("/shopping/checked", { method: "DELETE" });
    items = items.filter((i) => !i.checked);
    render();
    toast(`Cleared ${removed} checked item${removed === 1 ? "" : "s"}`);
  } catch (err) {
    toast(err.message, "error");
  }
}