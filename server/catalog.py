"""Recipe and grocery-item catalog, loaded from CSV once at startup."""
import ast
import csv
import logging
import pathlib
import random
import re

log = logging.getLogger(__name__)
BASE_DIR = pathlib.Path(__file__).resolve().parent
IMAGE_BASE = os.getenv("RECIPE_IMAGE_BASE", "")

_recipes, _by_id, _names = [], {}, []
_items, _ingredient_words = [], []

_WORD = re.compile(r"[a-zà-öø-ÿ]+(?:['’-][a-zà-öø-ÿ]+)*")
_UNITS = set("""
cup cups c tablespoon tablespoons tbsp tbs teaspoon teaspoons tsp ounce ounces oz fl pound pounds lb lbs
gram grams g kilogram kilograms kg ml milliliter milliliters liter liters litre litres quart quarts qt
pint pints pt gallon gallons clove cloves can cans jar jars package packages pkg stick sticks slice slices
pinch pinches dash dashes handful handfuls bunch bunches sprig sprigs stalk stalks head heads piece pieces
loaf loaves large medium small whole inch inches
""".split())
_PREP = set("""
chopped finely coarsely roughly thinly thickly minced sliced diced grated shredded crushed peeled seeded
halved quartered divided fresh freshly ground packed lightly softened melted room temperature plus more
optional about trimmed rinsed drained cut into torn to taste for serving good-quality toasted cooked
uncooked beaten juiced zested such as of a an the garnish
""".split())
_STAPLE_WORDS = set("""
salt kosher sea flaky fine black white pepper peppercorns cracked water ice cubes cold hot warm boiling
tap filtered and or
""".split())

_MEAT = re.compile(
    r"\b(?:chicken|beef|steaks?|pork|bacon|ham|prosciutto|pancetta|guanciale|salami|pepperoni|chorizo|"
    r"sausages?|lamb|veal|venison|turkey|duck|goose|quail|anchov(?:y|ies)|fish|salmon|tuna|cod|halibut|"
    r"trout|sardines?|mackerel|tilapia|snapper|shrimp|prawns?|crab|lobster|clams?|mussels?|oysters?|"
    r"scallops?|squid|calamari|octopus|gelatin|lard|worcestershire|brisket|pastrami|bologna|hot dogs?|meatballs?)\b"
)
_ANIMAL = re.compile(
    r"\b(?:milk|butter|buttermilk|cream|cheeses?|cheddar|parmesan|parmigiano|pecorino|mozzarella|ricotta|"
    r"feta|mascarpone|gruy[eè]re|brie|yogh?urt|ghee|whey|cr[eè]me|eggs?|yolks?|honey|mayonnaise|mayo)\b"
)
_PLANT_SWAPS = re.compile(
    r"\b(?:coconut|almond|oat|soy|rice|cashew|hemp|vegan|plant-based|non-?dairy)\s+(?:milk|cream|butter|yogh?urt|cheese)\b"
    r"|\b(?:peanut|almond|cashew|nut|sunflower|cocoa|cacao|apple|seed)\s+butter\b|\bcream of tartar\b"
)
_SPIRITS = re.compile(
    r"\b(?:bourbon|whiske?y|scotch|tequila|mezcal|rum|vodka|gin|brandy|cognac|vermouth|liqueur|amaro|aperol|"
    r"campari|bitters|grand marnier|triple sec|cointreau|chartreuse|absinthe|prosecco|champagne|sake|pisco|"
    r"aquavit|sherry|port)\b"
)
_BAR = re.compile(
    r"cocktail|shaker|strain into|rocks glass|coupe|highball|collins|martini|mug|thermos|pint glass|"
    r"wine glass|old-fashioned glass|over ice|ice-filled"
)


def _parse_list(raw):
    raw = (raw or "").strip()
    if not raw:
        return []
    try:
        value = ast.literal_eval(raw)
        if isinstance(value, (list, tuple)):
            return [str(v).strip() for v in value if str(v).strip()]
    except (ValueError, SyntaxError):
        pass
    return [raw]


def _image_url(name):
    name = (name or "").strip()
    if not IMAGE_BASE or not name or name.startswith("#"):
        return ""
    return f"{IMAGE_BASE}/{name}.png"


def clean_term(line):
    """'2 Tbsp. finely chopped sage, divided' -> 'sage'. Used for shopping searches."""
    text = re.sub(r"\([^)]*\)", " ", (line or "").lower())
    text = re.split(r"[,;]", text, maxsplit=1)[0]
    words = [w for w in _WORD.findall(text) if w not in _UNITS and w not in _PREP]
    return " ".join(words)[:100] or (line or "").strip()[:100]


def _is_staple(term):
    words = term.split()
    return bool(words) and all(w in _STAPLE_WORDS for w in words)


def _tags(lines, instructions):
    text = " ".join(lines)
    tags = []
    if not _MEAT.search(text):
        tags.append("vegetarian")
        if not _ANIMAL.search(_PLANT_SWAPS.sub(" ", text)):
            tags.append("vegan")
    if len(lines) <= 10 and _SPIRITS.search(text) and _BAR.search(instructions):
        tags.append("drink")
    return tags


def load(path=None):
    path = pathlib.Path(path or BASE_DIR / "Food.csv")
    _recipes.clear()
    _by_id.clear()
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            raw_id = (row.get("recipe_id") or "").strip()
            title = (row.get("Title") or "").strip()
            if not raw_id.isdigit() or not title:
                continue
            ingredients = _parse_list(row.get("Ingredients"))
            lines = [i.lower() for i in ingredients]
            terms = [clean_term(i) for i in ingredients]
            staple = [_is_staple(t) for t in terms]
            instructions = row.get("Instructions") or ""
            recipe = {
                "recipe_id": int(raw_id),
                "name": title,
                "ingredients": ingredients,
                "steps": [s.strip() for s in instructions.splitlines() if s.strip()],
                "image_url": _image_url(row.get("Image_Name")),
                "tags": _tags(lines, instructions.lower()),
                "_lines": lines,
                "_terms": terms,
                "_staple": staple,
                "_core": [i for i, s in enumerate(staple) if not s],
                "_search": " ".join(lines),
            }
            _recipes.append(recipe)
            _by_id[recipe["recipe_id"]] = recipe
    _names[:] = list(dict.fromkeys(r["name"] for r in _recipes))
    drinks = sum("drink" in r["tags"] for r in _recipes)
    log.info("Loaded %d recipes (%d drinks)", len(_recipes), drinks)


def load_items(path=None):
    path = pathlib.Path(path or BASE_DIR / "Item.csv")
    with path.open(encoding="utf-8-sig", newline="") as f:
        _items[:] = [r["ItemName"].strip() for r in csv.DictReader(f) if (r.get("ItemName") or "").strip()]
    words = {base_name(item) for item in _items}
    _ingredient_words[:] = sorted(w for w in words if w)


# ---------- lookups ----------

def count():
    return len(_recipes)


def get(recipe_id):
    return _by_id.get(recipe_id)


def terms(recipe):
    return recipe["_terms"]


def public(recipe):
    return {k: v for k, v in recipe.items() if not k.startswith("_")}


def summary(recipe, have_matcher=None):
    data = {
        "recipe_id": recipe["recipe_id"],
        "name": recipe["name"],
        "image_url": recipe["image_url"],
        "tags": recipe["tags"],
    }
    if have_matcher is not None:
        lines = recipe["_lines"]
        data["have"] = sum(1 for i in recipe["_core"] if have_matcher.search(lines[i]))
        data["total"] = len(recipe["_core"])
    return data


def filtered(diets=(), kind="all"):
    pool = _recipes
    if kind == "food":
        pool = [r for r in pool if "drink" not in r["tags"]]
    elif kind == "drinks":
        pool = [r for r in pool if "drink" in r["tags"]]
    for diet in diets:
        pool = [r for r in pool if diet in r["tags"]]
    return pool


def random_from(pool):
    return random.choice(pool) if pool else None


# ---------- matching ----------

def base_name(name):
    """'Chicken (Breast, Boneless)' -> 'chicken'"""
    return re.sub(r"\s*\([^)]*\)", "", name or "").strip().lower()


def _forms(term):
    forms = {term}
    if term.endswith("es") and len(term) > 4:
        forms.add(term[:-2])
    if term.endswith("s") and len(term) > 3:
        forms.add(term[:-1])
    return forms


def _compile(forms):
    # whole words with simple plurals: egg/eggs, tomato/tomatoes, but never "eggplant"
    alts = "|".join(sorted((re.escape(f) for f in forms), key=len, reverse=True))
    return re.compile(rf"\b(?:{alts})(?:e?s)?\b")


def matcher(names):
    """One regex that matches any of the given fridge item names."""
    forms = set()
    for name in names:
        base = base_name(name)
        if len(base) >= 2:
            forms |= _forms(base)
    return _compile(forms) if forms else None


def ingredient_status(recipe, have_matcher):
    out = []
    for line, staple in zip(recipe["_lines"], recipe["_staple"]):
        if staple:
            out.append("staple")
        elif have_matcher is not None and have_matcher.search(line):
            out.append("have")
        else:
            out.append("missing")
    return out


def missing_terms(recipe, have_matcher):
    lines, names = recipe["_lines"], recipe["_terms"]
    return [names[i] for i in recipe["_core"] if not (have_matcher and have_matcher.search(lines[i]))]


def rank_by_fridge(pool, have_matcher, expiring_matcher=None):
    """Recipes sorted by how much of them is already in the fridge."""
    scored = []
    for r in pool:
        core = r["_core"]
        if not core:
            continue
        lines = r["_lines"]
        have = sum(1 for i in core if have_matcher.search(lines[i]))
        if have:
            # +1 keeps 1-of-1 recipes from outranking 8-of-9
            scored.append([have / (len(core) + 1), have, r])
    scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
    if expiring_matcher is not None:
        head = scored[:200]
        for s in head:
            r = s[2]
            if any(expiring_matcher.search(r["_lines"][i]) for i in r["_core"]):
                s[0] += 0.15
        head.sort(key=lambda s: (s[0], s[1]), reverse=True)
        scored[:200] = head
    return [s[2] for s in scored]


def search_by_ingredients(search_terms, pool):
    patterns = [_compile(_forms(t)) for t in search_terms]
    return [r for r in pool if all(p.search(r["_search"]) for p in patterns)]


def search_by_name(query, pool):
    q = query.strip().lower()
    return [r for r in pool if q in r["name"].lower()]


def _starts_then_contains(values, q, limit):
    starts = [v for v in values if v.lower().startswith(q)]
    contains = [v for v in values if q in v.lower() and not v.lower().startswith(q)]
    return (starts + contains)[:limit]


def suggest_ingredients(query, limit=10):
    q = query.strip().lower()
    return _starts_then_contains(_ingredient_words, q, limit) if len(q) >= 2 else []


def suggest_names(query, limit=10):
    q = query.strip().lower()
    return _starts_then_contains(_names, q, limit) if len(q) >= 2 else []


def search_items(query):
    q = query.strip().lower()
    results = {}
    if not q:
        return results
    for item in _items:
        if q not in item.lower():
            continue
        match = re.match(r"^(.*?)\s*\((.*?)\)", item)
        if match:
            results.setdefault(match.group(1).strip(), []).append(match.group(2).strip())
        else:
            results.setdefault(item, []).append("")
    return results