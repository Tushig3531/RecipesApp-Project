import os
import pathlib
from datetime import timedelta

import dotenv
import sqlalchemy as sa
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = pathlib.Path(__file__).resolve().parent
dotenv.load_dotenv(BASE_DIR / ".env")
dotenv.load_dotenv(BASE_DIR / ".flaskenv")

db = SQLAlchemy()
migrate = Migrate()

IS_DEV = os.getenv("APP_ENV", "production").lower() == "development"

DEFAULT_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://recipesapps.com",
    "https://www.recipesapps.com",
]

# Columns added after tables already existed; create_all() won't add these by itself
NEW_COLUMNS = {
    "fridge_item": {"expires_on": "DATE"},
}


def _secret(name):
    value = os.getenv(name)
    if value:
        return value
    if IS_DEV:
        return f"dev-only-{name.lower()}"
    raise RuntimeError(f"{name} is not set. Add it to the Cloud Run service's environment variables.")


def _database_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        name = os.getenv("FLASK_DATABASE_FILE", "recipe_database")
        return f"sqlite:///{BASE_DIR / f'{name}.sqlite3'}"
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def _env_list(name, default):
    raw = os.getenv(name)
    return [item.strip() for item in raw.split(",") if item.strip()] if raw else default


def _add_missing_columns():
    inspector = sa.inspect(db.engine)
    for table, columns in NEW_COLUMNS.items():
        existing = {c["name"] for c in inspector.get_columns(table)}
        for name, ddl in columns.items():
            if name not in existing:
                with db.engine.begin() as conn:
                    conn.execute(sa.text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=_secret("FLASK_SECRET_KEY"),
        JWT_SECRET_KEY=_secret("FLASK_JWT_SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=_database_url(),
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        JWT_TOKEN_LOCATION=["cookies"],
        JWT_ACCESS_COOKIE_PATH="/",
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=int(os.getenv("JWT_EXPIRES_HOURS", "24"))),
        JWT_COOKIE_SECURE=os.getenv("JWT_COOKIE_SECURE", "true").lower() == "true",
        JWT_COOKIE_SAMESITE=os.getenv("JWT_COOKIE_SAMESITE", "None"),
        JWT_COOKIE_CSRF_PROTECT=False,  # CSRF handled by JSON-only writes in app.py
    )

    CORS(app, origins=_env_list("CORS_ORIGINS", DEFAULT_ORIGINS), supports_credentials=True)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        import model  # noqa: F401  registers tables
        db.create_all()
        _add_missing_columns()

    return app