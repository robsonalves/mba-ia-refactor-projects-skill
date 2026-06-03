from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS

from src.config.database import db
from src.config.settings import settings
from src.middlewares.error_handler import register_error_handlers
from src.middlewares.logging_setup import setup_logging
from src.views.report_routes import report_bp
from src.views.task_routes import task_bp
from src.views.user_routes import user_bp


def create_app():
    setup_logging(settings.LOG_LEVEL)

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG

    CORS(app)
    db.init_app(app)

    register_error_handlers(app)
    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "timestamp": str(datetime.utcnow())})

    @app.route("/")
    def index():
        return jsonify({"message": "Task Manager API", "version": "1.0"})

    with app.app_context():
        from src.models import category, task, user  # noqa: F401 import to register models

        db.create_all()

    return app
