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

    dotenv.load_dotenv(this_dir.parent / ".flaskenv")

    this_app.config.from_prefixed_env()


    db_user = os.getenv("CLOUD_SQL_USERNAME")
    db_password = os.getenv("CLOUD_SQL_PASSWORD")
    db_name = os.getenv("CLOUD_SQL_DATABASE")
    connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")

    db_uri = (
        f"postgresql+psycopg2://{db_user}:{db_password}@/"
        f"{db_name}?host=/cloudsql/{connection_name}"
    )
    this_app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    this_app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "default_secret")
    this_app.config["JWT_SECRET_KEY"] = os.getenv("FLASK_JWT_SECRET_KEY", "default_jwt_secret")
    this_app.config["SQLALCHEMY_ECHO"] = bool(int(os.getenv("FLASK_SQLALCHEMY_ECHO", 0)))
    this_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = bool(int(os.getenv("FLASK_SQLALCHEMY_TRACK_MODIFICATIONS", 0)))

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

    with this_app.app_context():
        db.create_all()

    return this_app
