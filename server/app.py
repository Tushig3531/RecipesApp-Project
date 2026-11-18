"""RecipesApp API."""
import logging
import os
import re
import time
from collections import defaultdict, deque
from datetime import date, timedelta

import requests
from flask import jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token, get_jwt_identity,
    jwt_required, set_access_cookies, unset_jwt_cookies,
)
from sqlalchemy.exc import IntegrityError

import catalog
from config import create_app, db
from model import FridgeItem, Recipe, SavedRecipe, ShoppingItem, User

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("recipesapp")

app = create_app()
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

catalog.load()
catalog.load_items()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_PER_PAGE = 48
DIETS = {"vegetarian", "vegan"}
KINDS = {"food", "drinks", "all"}
USE_SOON_DAYS = 3
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_FAILURES = 8
_failed_logins = defaultdict(deque)


# ---------- helpers ----------

def error(message, status):
    return jsonify({"error": message}), status


def body():
    return request.get_json(silent=True) or {}


def clean_str(value, max_len):
    return value.strip()[:max_len] if isinstance(value, str) else ""


def current_user_id():
    return int(get_jwt_identity())


def parse_date(value):
    if value in (None, ""):
        return None
    return date.fromisoformat(str(value))


def paginate(items, serialize):
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 24, type=int), 1), MAX_PER_PAGE)
    start = (page - 1) * per_page
    return {
        "recipes": [serialize(x) for x in items[start:start + per_page]],
        "count": len(items),
        "page": page,
        "per_page": per_page,
    }


def recipe_pool():
    diets = [d for d in request.args.get("diet", "").split(",") if d in DIETS]
    kind = request.args.get("kind", "food")
    return catalog.filtered(diets, kind if kind in KINDS else "food")


def fridge_matchers(user_id):
    """Regex for everything in the user's fridge, and one for items to use soon."""
    items = FridgeItem.query.filter_by(user_id=user_id).all()
    soon = date.today() + timedelta(days=USE_SOON_DAYS)
    everything = catalog.matcher(i.item_name for i in items)
    expiring = catalog.matcher(i.item_name for i in items if i.expires_on and i.expires_on <= soon)
    return everything, expiring


def recipe_row(recipe):
    row = Recipe.query.filter_by(recipe_id=recipe["recipe_id"]).first()
    if row is None:
        row = Recipe(
            recipe_id=recipe["recipe_id"],
            name=recipe["name"][:255],
            ingredients="\n".join(recipe["ingredients"]),
            instructions="\n".join(recipe["steps"]),
            image_url=recipe["image_url"],
        )
        db.session.add(row)
        db.session.flush()
    return row


def saved_entry(user_id, recipe_id):
    return (SavedRecipe.query
            .join(Recipe, SavedRecipe.recipe_id == Recipe.id)
            .filter(SavedRecipe.user_id == user_id, Recipe.recipe_id == recipe_id)
            .first())


def fridge_dict(item):
    return {
        "id": item.id,
        "item_name": item.item_name,
        "brand": "" if item.brand in (None, "No Brand") else item.brand,
        "quantity": item.quantity,
        "expires_on": item.expires_on.isoformat() if item.expires_on else None,
    }


def shopping_dict(item):
    return {
        "id": item.id,
        "text": item.text,
        "term": item.term,
        "recipe_name": item.recipe_name or "",
        "checked": item.checked,
    }


def find_youtube_video(title):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return ""
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part": "snippet", "type": "video", "videoEmbeddable": "true",
                    "maxResults": 1, "q": f"{title} recipe", "key": api_key},
            timeout=5,
        )
    except requests.RequestException as exc:
        log.warning("YouTube search failed for %r: %s", title, type(exc).__name__)
        return ""
    if resp.status_code != 200:  # don't log the URL, it contains the key
        log.warning("YouTube search returned %s for %r", resp.status_code, title)
        return ""
    items = resp.json().get("items", [])
    return items[0].get("id", {}).get("videoId", "") if items else ""


def _recent_failures(key):
    attempts = _failed_logins[key]
    cutoff = time.monotonic() - LOGIN_WINDOW_SECONDS
    while attempts and attempts[0] < cutoff:
        attempts.popleft()
    return attempts


# ---------- guards & errors ----------

@app.before_request
def require_json_on_writes():
    # Other sites can post plain HTML forms with the user's cookie, but they can't send
    # Content-Type: application/json without a CORS preflight, which CORS rejects.
    if request.method in ("POST", "PUT", "PATCH") and request.endpoint != "logout" and not request.is_json:
        return error("Requests must be JSON.", 415)


@jwt.unauthorized_loader
@jwt.invalid_token_loader
def not_logged_in(_reason):
    return error("Please log in.", 401)


@jwt.expired_token_loader
def session_expired(_header, _payload):
    return error("Your session expired. Please log in again.", 401)


@app.errorhandler(404)
def not_found(_):
    return error("Not found.", 404)


@app.errorhandler(405)
def method_not_allowed(_):
    return error("Method not allowed.", 405)


@app.errorhandler(500)
def server_error(_):
    db.session.rollback()
    return error("Something went wrong on our end. Please try again.", 500)


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "recipes": catalog.count()})


# ---------- auth ----------

@app.post("/register")
def register():
    data = body()
    username = clean_str(data.get("username"), 200)
    email = clean_str(data.get("email"), 200).lower()
    password = data.get("password") if isinstance(data.get("password"), str) else ""

    if not username or not email or not password:
        return error("Username, email and password are required.", 400)
    if len(username) > 80:
        return error("Username must be 80 characters or fewer.", 400)
    if len(email) > 120 or not EMAIL_RE.match(email):
        return error("Enter a valid email address.", 400)
    if len(password) < 8 or len(password.encode()) > 72:
        return error("Password must be 8 to 72 characters.", 400)
    if User.query.filter(db.func.lower(User.email) == email).first():
        return error("That email already has an account. Log in instead.", 409)
    if User.query.filter_by(username=username).first():
        return error("That username is taken. Try another.", 409)

    db.session.add(User(username=username, email=email,
                        password=bcrypt.generate_password_hash(password).decode()))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("That username or email is already registered.", 409)
    return jsonify({"message": "Account created."}), 201


@app.post("/login")
def login():
    data = body()
    email = clean_str(data.get("email"), 200).lower()
    password = data.get("password") if isinstance(data.get("password"), str) else ""
    if not email or not password:
        return error("Email and password are required.", 400)

    failures = _recent_failures(email)
    if len(failures) >= LOGIN_MAX_FAILURES:
        return error("Too many failed attempts. Wait 15 minutes and try again.", 429)

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        failures.append(time.monotonic())
        return error("Email or password is incorrect.", 401)

    _failed_logins.pop(email, None)
    resp = jsonify({"user": {"id": user.id, "username": user.username}})
    set_access_cookies(resp, create_access_token(identity=str(user.id)))
    return resp, 200


@app.post("/logout")
def logout():
    resp = jsonify({"message": "Logged out."})
    unset_jwt_cookies(resp)
    return resp, 200


@app.get("/me")
@jwt_required()
def me():
    user_id = current_user_id()
    user = db.session.get(User, user_id)
    if not user:
        return error("Please log in.", 401)
    return jsonify({
        "user": {"id": user.id, "username": user.username},
        "counts": {
            "fridge": FridgeItem.query.filter_by(user_id=user_id).count(),
            "shopping": ShoppingItem.query.filter_by(user_id=user_id, checked=False).count(),
        },
    })


# ---------- recipes ----------

@app.get("/search_recipes_by_ingredients")
@jwt_required()
def search_by_ingredients():
    terms = [t.strip().lower() for t in request.args.get("ingredients", "").split(",") if t.strip()]
    if not terms:
        return error("Enter at least one ingredient.", 400)
    have, _ = fridge_matchers(current_user_id())
    results = catalog.search_by_ingredients(terms, recipe_pool())
    return jsonify(paginate(results, lambda r: catalog.summary(r, have)))


@app.get("/search_recipes_by_name")
@jwt_required()
def search_by_name():
    name = request.args.get("name", "").strip()
    if not name:
        return error("Enter a recipe name.", 400)
    have, _ = fridge_matchers(current_user_id())
    results = catalog.search_by_name(name, recipe_pool())
    return jsonify(paginate(results, lambda r: catalog.summary(r, have)))


@app.get("/autocomplete_recipes")
@jwt_required()
def autocomplete_recipes():
    query = request.args.get("q", "")
    if request.args.get("type", "ingredients") in ("ingredient", "ingredients"):
        suggestions = catalog.suggest_ingredients(query.split(",")[-1])
    else:
        suggestions = catalog.suggest_names(query)
    return jsonify({"suggestions": suggestions})


@app.get("/recipes/from_fridge")
@jwt_required()
def recipes_from_fridge():
    have, expiring = fridge_matchers(current_user_id())
    if have is None:
        return jsonify({"recipes": [], "count": 0, "page": 1, "per_page": 24, "empty_fridge": True})
    ranked = catalog.rank_by_fridge(recipe_pool(), have, expiring)
    return jsonify(paginate(ranked, lambda r: {
        **catalog.summary(r, have),
        "missing": catalog.missing_terms(r, have)[:4],
    }))


@app.get("/recipes/random")
@jwt_required()
def random_recipe():
    recipe = catalog.random_from(recipe_pool())
    if not recipe:
        return error("No recipes match those filters.", 404)
    return jsonify({"recipe_id": recipe["recipe_id"]})


@app.get("/recipes/<int:recipe_id>")
@jwt_required()
def recipe_detail(recipe_id):
    recipe = catalog.get(recipe_id)
    if not recipe:
        return error("Recipe not found.", 404)
    user_id = current_user_id()
    have, _ = fridge_matchers(user_id)
    status = catalog.ingredient_status(recipe, have)
    return jsonify({
        "recipe": catalog.public(recipe),
        "saved": saved_entry(user_id, recipe_id) is not None,
        "status": status,
        "have": status.count("have"),
        "total": status.count("have") + status.count("missing"),
    })


@app.get("/recipes/<int:recipe_id>/video")
@jwt_required()
def recipe_video(recipe_id):
    recipe = catalog.get(recipe_id)
    if not recipe:
        return error("Recipe not found.", 404)
    row = recipe_row(recipe)
    if not row.youtube_url:
        video_id = find_youtube_video(recipe["name"])
        if video_id:
            row.youtube_url = f"https://www.youtube.com/embed/{video_id}"
    db.session.commit()
    return jsonify({"youtube_url": row.youtube_url or ""})


@app.post("/recipes/<int:recipe_id>/shopping")
@jwt_required()
def add_missing_to_shopping(recipe_id):
    recipe = catalog.get(recipe_id)
    if not recipe:
        return error("Recipe not found.", 404)
    user_id = current_user_id()
    have, _ = fridge_matchers(user_id)
    on_list = {s.term for s in ShoppingItem.query.filter_by(user_id=user_id, checked=False).all()}
    added = 0
    rows = zip(recipe["ingredients"], catalog.terms(recipe), catalog.ingredient_status(recipe, have))
    for line, term, status in rows:
        term = term[:100]
        if status == "missing" and term not in on_list:
            db.session.add(ShoppingItem(user_id=user_id, text=line[:200], term=term,
                                        recipe_name=recipe["name"][:255]))
            on_list.add(term)
            added += 1
    db.session.commit()
    return jsonify({"added": added}), 201


@app.post("/save_recipe")
@jwt_required()
def save_recipe():
    try:
        recipe_id = int(body().get("recipe_id"))
    except (TypeError, ValueError):
        return error("recipe_id is required.", 400)
    recipe = catalog.get(recipe_id)
    if not recipe:
        return error("Recipe not found.", 404)

    user_id = current_user_id()
    row = recipe_row(recipe)
    if SavedRecipe.query.filter_by(user_id=user_id, recipe_id=row.id).first():
        db.session.commit()
        return jsonify({"message": "Already saved."}), 200

    db.session.add(SavedRecipe(user_id=user_id, recipe_id=row.id))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Already saved."}), 200
    return jsonify({"message": "Saved."}), 201


@app.delete("/unsave_recipe/<int:recipe_id>")
@jwt_required()
def unsave_recipe(recipe_id):
    entry = saved_entry(current_user_id(), recipe_id)
    if not entry:
        return error("That recipe isn't in your saved list.", 404)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Removed."})


@app.get("/saved_recipes")
@jwt_required()
def saved_recipes():
    user_id = current_user_id()
    rows = (db.session.query(Recipe.recipe_id)
            .join(SavedRecipe, SavedRecipe.recipe_id == Recipe.id)
            .filter(SavedRecipe.user_id == user_id)
            .order_by(SavedRecipe.id.desc())
            .all())
    have, _ = fridge_matchers(user_id)
    recipes = [catalog.get(rid) for (rid,) in rows]
    return jsonify([catalog.summary(r, have) for r in recipes if r])


# ---------- fridge ----------

@app.get("/fridge/search_items_fridge")
@jwt_required()
def search_items_fridge():
    return jsonify(catalog.search_items(request.args.get("q", "")))


@app.get("/fridge")
@jwt_required()
def get_fridge():
    items = (FridgeItem.query.filter_by(user_id=current_user_id())
             .order_by(FridgeItem.expires_on.is_(None), FridgeItem.expires_on, FridgeItem.date_added.desc())
             .all())
    return jsonify([fridge_dict(i) for i in items])


@app.post("/fridge/add")
@jwt_required()
def add_fridge_item():
    data = body()
    name = clean_str(data.get("item_name"), 100)
    quantity = clean_str(data.get("quantity"), 50)
    if not name:
        return error("Type or pick an item.", 400)
    if not quantity:
        return error("Enter how much you have.", 400)
    try:
        expires_on = parse_date(data.get("expires_on"))
    except ValueError:
        return error("Use-by date must look like 2026-11-30.", 400)
    item = FridgeItem(user_id=current_user_id(), item_name=name, quantity=quantity,
                      brand=clean_str(data.get("brand"), 100) or None, expires_on=expires_on)
    db.session.add(item)
    db.session.commit()
    return jsonify(fridge_dict(item)), 201


@app.patch("/fridge/<int:item_id>")
@jwt_required()
def update_fridge_item(item_id):
    item = FridgeItem.query.filter_by(id=item_id, user_id=current_user_id()).first()
    if not item:
        return error("Item not found.", 404)
    data = body()
    for field, max_len, label in (("item_name", 100, "Item name"), ("quantity", 50, "Quantity")):
        if field in data:
            value = clean_str(data[field], max_len)
            if not value:
                return error(f"{label} can't be empty.", 400)
            setattr(item, field, value)
    if "brand" in data:
        item.brand = clean_str(data["brand"], 100) or None
    if "expires_on" in data:
        try:
            item.expires_on = parse_date(data["expires_on"])
        except ValueError:
            return error("Use-by date must look like 2026-11-30.", 400)
    db.session.commit()
    return jsonify(fridge_dict(item))


@app.delete("/fridge/<int:item_id>")
@jwt_required()
def delete_fridge_item(item_id):
    item = FridgeItem.query.filter_by(id=item_id, user_id=current_user_id()).first()
    if not item:
        return error("Item not found.", 404)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Removed."})


# ---------- shopping list ----------

@app.get("/shopping")
@jwt_required()
def get_shopping():
    items = (ShoppingItem.query.filter_by(user_id=current_user_id())
             .order_by(ShoppingItem.checked, ShoppingItem.created_at.desc())
             .all())
    return jsonify([shopping_dict(i) for i in items])


@app.post("/shopping")
@jwt_required()
def add_shopping():
    text = clean_str(body().get("text"), 200)
    if not text:
        return error("Type something to add.", 400)
    item = ShoppingItem(user_id=current_user_id(), text=text, term=catalog.clean_term(text)[:100])
    db.session.add(item)
    db.session.commit()
    return jsonify(shopping_dict(item)), 201


@app.patch("/shopping/<int:item_id>")
@jwt_required()
def update_shopping(item_id):
    item = ShoppingItem.query.filter_by(id=item_id, user_id=current_user_id()).first()
    if not item:
        return error("Item not found.", 404)
    checked = body().get("checked")
    if isinstance(checked, bool):
        item.checked = checked
    db.session.commit()
    return jsonify(shopping_dict(item))


@app.delete("/shopping/checked")
@jwt_required()
def clear_checked_shopping():
    removed = ShoppingItem.query.filter_by(user_id=current_user_id(), checked=True).delete()
    db.session.commit()
    return jsonify({"removed": removed})


@app.delete("/shopping/<int:item_id>")
@jwt_required()
def delete_shopping(item_id):
    item = ShoppingItem.query.filter_by(id=item_id, user_id=current_user_id()).first()
    if not item:
        return error("Item not found.", 404)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Removed."})


if __name__ == "__main__":
    app.run(debug=True, port=8080)