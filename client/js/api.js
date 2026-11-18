export const API_BASE = window.API_BASE;

export const PLACEHOLDER_IMG =
  "data:image/svg+xml;charset=utf-8," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">' +
    '<rect width="100%" height="100%" fill="#E4EEE8"/>' +
    '<text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" ' +
    'font-family="sans-serif" font-size="20" fill="#5C6D69">No photo</text></svg>'
  );

export async function api(path, { method = "GET", body, redirectOn401 = true } = {}) {
  const options = { method, credentials: "include", headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(API_BASE + path, options);
  } catch {
    throw new Error("Can't reach the server. Check your connection and try again.");
  }
  const data = await res.json().catch(() => ({}));
  if (res.status === 401 && redirectOn401) {
    window.location.href = "index.html";
    throw new Error(data.error || "Please log in.");
  }
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

// el("a", { class: "x", href: "/", onclick: fn }, "text", childNode)
export function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  node.append(...children.flat(Infinity).filter((c) => c !== null && c !== undefined && c !== false));
  return node;
}

export function toast(message, kind = "ok") {
  let region = document.getElementById("toasts");
  if (!region) {
    region = el("div", { id: "toasts", class: "toasts", role: "status", "aria-live": "polite" });
    document.body.append(region);
  }
  const note = el("div", { class: `toast-note ${kind}` }, message);
  region.append(note);
  setTimeout(() => note.remove(), kind === "error" ? 6000 : 3500);
}

export function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

// Arrow-key movement between an input and its suggestion buttons
export function suggestionKeys(event, box, input) {
  const buttons = [...box.querySelectorAll("button")];
  const i = buttons.indexOf(document.activeElement);
  if (event.key === "ArrowDown" && buttons.length) {
    event.preventDefault();
    buttons[Math.min(i + 1, buttons.length - 1)].focus();
  } else if (event.key === "ArrowUp" && i >= 0) {
    event.preventDefault();
    (i === 0 ? input : buttons[i - 1]).focus();
  } else if (event.key === "Escape") {
    box.hidden = true;
    input.focus();
  }
}

export const prefs = {
  get(key, fallback) {
    try {
      const value = localStorage.getItem(`recipesapp:${key}`);
      return value === null ? fallback : JSON.parse(value);
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(`recipesapp:${key}`, JSON.stringify(value));
    } catch {
      /* storage unavailable; preferences just won't persist */
    }
  },
};