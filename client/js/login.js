import { api } from "./api.js";

// Already logged in? Skip the form.
api("/me", { redirectOn401: false }).then(() => location.replace("recipes.html")).catch(() => {});

function bind(form, handler) {
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorBox = form.querySelector(".form-error");
    const button = form.querySelector('button[type="submit"]');
    errorBox.textContent = "";
    button.disabled = true;
    try {
      await handler(new FormData(form));
    } catch (err) {
      errorBox.textContent = err.message;
      button.disabled = false;
    }
  });
}

const login = (email, password) =>
  api("/login", { method: "POST", body: { email, password }, redirectOn401: false });

bind(document.getElementById("login-form"), async (data) => {
  await login(data.get("email"), data.get("password"));
  location.href = "recipes.html";
});

bind(document.getElementById("register-form"), async (data) => {
  const body = { username: data.get("username"), email: data.get("email"), password: data.get("password") };
  await api("/register", { method: "POST", body, redirectOn401: false });
  await login(body.email, body.password); // straight in, no second form
  location.href = "recipes.html";
});