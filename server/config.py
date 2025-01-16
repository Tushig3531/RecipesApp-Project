# config.py

import pathlib
import os
import dotenv
from flask import Flask
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import urllib.parse

db = SQLAlchemy()
mm = Marshmallow()

def create_app():
    this_app = Flask(__name__)
    this_dir = pathlib.Path(__file__)

    # Load .flaskenv from the same directory or parent directory
    dotenv.load_dotenv(this_dir.parent / ".flaskenv")

    this_app.config.from_prefixed_env()

    password_raw = os.getenv("CLOUD_SQL_PASSWORD", "")
    password_encoded = urllib.parse.quote_plus(password_raw)
    # Read env variables:
    db_user = os.getenv("CLOUD_SQL_USERNAME", "admin")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_name = os.getenv("CLOUD_SQL_DATABASE", "recipesdb")

    uri = f"postgresql+psycopg2://{db_user}:{password_encoded}@{db_host}:5432/{db_name}"
    this_app.config["SQLALCHEMY_DATABASE_URI"] = uri

    this_app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "default_secret")
    this_app.config["JWT_SECRET_KEY"] = os.getenv("FLASK_JWT_SECRET_KEY", "default_jwt_secret")
    this_app.config["SQLALCHEMY_ECHO"] = os.getenv("FLASK_SQLALCHEMY_ECHO", False)
    this_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = os.getenv("FLASK_SQLALCHEMY_TRACK_MODIFICATIONS", False)

    CORS(
        this_app,
        resources={r"/*": {"origins": [
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://[::]:5500"
        ]}},
        supports_credentials=True
    )

    db.init_app(this_app)
    mm.init_app(this_app)

    from model import User, Recipe, SavedRecipe, FridgeItem

    migrate = Migrate(this_app, db)

    # Create tables if they don’t exist
    with this_app.app_context():
        db.create_all()

    return this_app
