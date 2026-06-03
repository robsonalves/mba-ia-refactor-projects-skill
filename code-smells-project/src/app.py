import logging

from flask import Flask
from flask_cors import CORS

from src.config.database import close_db, init_schema, seed_if_empty
from src.config.settings import settings
from src.middlewares.error_handler import register_error_handlers
from src.views.routes import register_routes


def create_app():
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app)

    init_schema()
    seed_if_empty()

    register_error_handlers(app)
    register_routes(app)
    app.teardown_appcontext(close_db)

    return app
