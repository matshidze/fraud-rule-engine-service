# app/__init__.py
import os
from flask import Flask

from .extensions import db


def _env(key: str, default: str) -> str:
    """Small helper to read env vars with defaults."""
    val = os.getenv(key)
    return val if val is not None and val != "" else default


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.setdefault("FRAUD_SCORE_THRESHOLD", int(_env("FRAUD_SCORE_THRESHOLD", "70")))
    app.config.setdefault("BLACKLISTED_COUNTRIES", _env("BLACKLISTED_COUNTRIES", "NG,IR,KP"))
    app.config.setdefault("BLACKLISTED_MERCHANTS", _env("BLACKLISTED_MERCHANTS", ""))

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    testing = _env("TESTING", "0") == "1"
    app.config["TESTING"] = testing

    if testing:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = _env(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@db:5432/fraud",
        )


    db.init_app(app)


    from .routes_api import api  # noqa: WPS433

    app.register_blueprint(api, url_prefix="/api/v1")

    try:
        from .routes_ui import ui_bp  # type: ignore  # noqa: WPS433
        app.register_blueprint(ui_bp)
    except Exception:
        pass

    with app.app_context():
        db.create_all()

    return app
