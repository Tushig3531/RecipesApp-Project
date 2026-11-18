import { api, el } from "./api.js";

const LINKS = [
  ["recipes.html", "Cook"],
  ["fridge.html", "Fridge", "fridge"],
  ["shopping.html", "Shopping list", "shopping"],
  ["saved.html", "Saved"],
];

// api() sends logged-out visitors to the login page
export const session = api("/me").catch(() => null);

export async function refreshCounts() {
  const data = await api("/me").catch(() => null);
  if (data) paintCounts(data.counts);
}

function paintCounts(counts = {}) {
  document.querySelectorAll("[data-count]").forEach((badge) => {
    const n = counts[badge.dataset.count] || 0;
    badge.textContent = n ? String(n) : "";
    badge.hidden = !n;
  });
}

async function logout() {
  try {
    await api("/logout", { method: "POST" });
  } catch {
    /* leaving anyway */
  }
  window.location.href = "index.html";
}

function renderNav() {
  const host = document.getElementById("app-nav");
  if (!host) return;
  const here = location.pathname.split("/").pop() || "recipes.html";
  host.replaceChildren(
    el("div", { class: "container topbar" },
      el("a", { class: "brand", href: "recipes.html" }, "RecipesApp"),
      el("nav", { class: "topnav", "aria-label": "Main" },
        LINKS.map(([href, label, count]) =>
          el("a", { href, class: href === here ? "active" : null, "aria-current": href === here ? "page" : null },
            label,
            count ? el("span", { class: "count", dataset: { count }, hidden: true }) : null))),
      el("div", { class: "account" },
        el("span", { class: "account-name", id: "account-name" }),
        el("button", { class: "link-button", type: "button", onclick: logout }, "Log out")))
  );
}

renderNav();
session.then((data) => {
  if (!data) return;
  document.getElementById("account-name").textContent = data.user.username;
  paintCounts(data.counts);
});