import { api, debounce, el, suggestionKeys, toast } from "./api.js";
import { refreshCounts } from "./auth.js";

const byId = (id) => document.getElementById(id);
const USE_SOON_DAYS = 3;
let items = [];
let suggestSeq = 0;

const searchInput = byId("item-search");
const suggestionBox = byId("item-suggestions");
searchInput.addEventListener("input", debounce(suggestItems, 200));
searchInput.addEventListener("keydown", (e) => suggestionKeys(e, suggestionBox, searchInput));
suggestionBox.addEventListener("keydown", (e) => suggestionKeys(e, suggestionBox, searchInput));
document.addEventListener("click", (e) => { if (!e.target.closest(".search-box")) suggestionBox.hidden = true; });
byId("add-form").addEventListener("submit", addItem);
byId("fridge-list").addEventListener("click", onListClick);
load();

async function load() {
  try {
    items = await api("/fridge");
    render();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function suggestItems() {
  const q = searchInput.value.trim();
  if (q.length < 2) {
    suggestionBox.hidden = true;
    return;
  }
  const seq = ++suggestSeq;
  try {
    const data = await api(`/fridge/search_items_fridge?q=${encodeURIComponent(q)}`);
    if (seq !== suggestSeq) return;
    const labels = Object.entries(data)
      .flatMap(([base, types]) => types.map((t) => (t ? `${base} (${t})` : base)))
      .slice(0, 12);
    if (!labels.length) {
      suggestionBox.hidden = true;
      return;
    }
    suggestionBox.replaceChildren(...labels.map((label) =>
      el("button", {
        type: "button", class: "suggestion",
        onclick: () => { searchInput.value = label; suggestionBox.hidden = true; byId("amount").focus(); },
      }, label)));
    suggestionBox.hidden = false;
  } catch {
    suggestionBox.hidden = true;
  }
}

async function addItem(e) {
  e.preventDefault();
  const errorBox = byId("add-error");
  errorBox.textContent = "";
  const name = searchInput.value.trim();
  const amount = parseFloat(byId("amount").value);
  if (!name) { errorBox.textContent = "Type or pick an item."; return; }
  if (!(amount > 0)) { errorBox.textContent = "Enter how much you have."; return; }

  const unit = byId("unit").value;
  const quantity = `${+amount.toFixed(2)} ${unit === "items" && amount === 1 ? "item" : unit}`;
  try {
    await api("/fridge/add", {
      method: "POST",
      body: { item_name: name, quantity, brand: byId("brand").value.trim(), expires_on: byId("expires").value || null },
    });
    toast(`Added ${name}`);
    byId("add-form").reset();
    searchInput.focus();
    await load();
    refreshCounts();
  } catch (err) {
    errorBox.textContent = err.message;
  }
}

function expiry(isoDate) {
  if (!isoDate) return null;
  const [y, m, d] = isoDate.split("-").map(Number);
  const due = new Date(y, m - 1, d);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((due - today) / 86400000);
  if (days < 0) return { days, text: "Expired", level: "expired" };
  if (days === 0) return { days, text: "Use today", level: "soon" };
  if (days <= USE_SOON_DAYS) return { days, text: `${days} day${days === 1 ? "" : "s"} left`, level: "soon" };
  return { days, text: `Use by ${due.toLocaleDateString(undefined, { month: "short", day: "numeric" })}`, level: "ok" };
}

function render() {
  const list = byId("fridge-list");
  byId("fridge-count").textContent = items.length ? `${items.length} item${items.length === 1 ? "" : "s"}` : "";
  if (!items.length) {
    list.replaceChildren(el("div", { class: "empty-state" },
      el("h2", {}, "Nothing in here yet"),
      el("p", {}, "Add what you have at home and we'll match it against thousands of recipes.")));
    return;
  }
  const soon = items.filter((i) => { const x = expiry(i.expires_on); return x && x.days <= USE_SOON_DAYS; });
  const rest = items.filter((i) => !soon.includes(i));
  const groups = [];
  if (soon.length) groups.push(group("Use soon", soon, "use-soon"));
  if (rest.length) groups.push(group(soon.length ? "Everything else" : "In your fridge", rest));
  list.replaceChildren(...groups);
}

function group(title, list, extra = "") {
  return el("section", { class: `fridge-group ${extra}` },
    el("h3", {}, title),
    el("ul", { class: "fridge-items" }, list.map((item) => itemRow(item))));
}

function itemRow(item) {
  const exp = expiry(item.expires_on);
  return el("li", { class: "fridge-item", dataset: { id: item.id } },
    el("div", {},
      el("span", { class: "fridge-item-name" }, item.item_name),
      item.brand ? el("span", { class: "fridge-item-brand" }, item.brand) : null),
    el("span", { class: "fridge-item-qty" }, item.quantity),
    exp ? el("span", { class: `expiry ${exp.level}` }, exp.text) : el("span"),
    el("div", { class: "fridge-item-actions" },
      el("button", { type: "button", class: "link-button", dataset: { action: "edit" } }, "Edit"),
      el("button", { type: "button", class: "link-button danger", dataset: { action: "remove" } }, "Remove")));
}

function editRow(item) {
  const qty = el("input", { class: "form-control form-control-sm", value: item.quantity, maxlength: "50", "aria-label": `Quantity of ${item.item_name}` });
  const date = el("input", { class: "form-control form-control-sm", type: "date", value: item.expires_on || "", "aria-label": "Use by date" });
  const save = async () => {
    try {
      await api(`/fridge/${item.id}`, { method: "PATCH", body: { quantity: qty.value.trim(), expires_on: date.value || null } });
      toast(`Updated ${item.item_name}`);
      await load();
    } catch (err) {
      toast(err.message, "error");
    }
  };
  qty.addEventListener("keydown", (e) => { if (e.key === "Enter") save(); });
  setTimeout(() => qty.focus(), 0);
  return el("li", { class: "fridge-item editing", dataset: { id: item.id } },
    el("span", { class: "fridge-item-name" }, item.item_name),
    qty, date,
    el("div", { class: "fridge-item-actions" },
      el("button", { type: "button", class: "btn btn-basil btn-sm", onclick: save }, "Save"),
      el("button", { type: "button", class: "link-button", onclick: () => render() }, "Cancel")));
}

function onListClick(e) {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  const row = btn.closest("li");
  const item = items.find((i) => String(i.id) === row.dataset.id);
  if (!item) return;
  if (btn.dataset.action === "edit") row.replaceWith(editRow(item));
  if (btn.dataset.action === "remove") removeItem(item);
}

async function removeItem(item) {
  if (!confirm(`Remove ${item.item_name} from your fridge?`)) return;
  try {
    await api(`/fridge/${item.id}`, { method: "DELETE" });
    toast(`Removed ${item.item_name}`);
    await load();
    refreshCounts();
  } catch (err) {
    toast(err.message, "error");
  }
}