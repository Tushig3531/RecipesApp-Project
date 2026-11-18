from datetime import datetime, timezone

from config import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    fridge_items = db.relationship("FridgeItem", backref="owner", lazy=True, cascade="all, delete-orphan")
    saved_recipes = db.relationship("SavedRecipe", backref="owner", lazy=True, cascade="all, delete-orphan")
    shopping_items = db.relationship("ShoppingItem", backref="owner", lazy=True, cascade="all, delete-orphan")


class FridgeItem(db.Model):
    __tablename__ = "fridge_item"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    item_name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100))
    quantity = db.Column(db.String(50), nullable=False)
    date_added = db.Column(db.DateTime, default=utcnow)
    expires_on = db.Column(db.Date)


class Recipe(db.Model):
    """DB copy of catalog recipes that were saved or had a video looked up."""
    __tablename__ = "recipe"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    ingredients = db.Column(db.Text, nullable=False, default="")
    instructions = db.Column(db.Text, nullable=False, default="")
    image_url = db.Column(db.String(300))
    youtube_url = db.Column(db.String(300))
    saved_recipes = db.relationship("SavedRecipe", backref="recipe", lazy=True, cascade="all, delete-orphan")


class SavedRecipe(db.Model):
    __tablename__ = "saved_recipe"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "recipe_id", name="_user_recipe_uc"),)


class ShoppingItem(db.Model):
    __tablename__ = "shopping_item"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    text = db.Column(db.String(200), nullable=False)
    term = db.Column(db.String(100), nullable=False)
    recipe_name = db.Column(db.String(255))
    checked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)