from flask import Flask
from .config import Config
from .extensions import db, metrics
from .routes_api import api
from .routes_ui import ui
from .services import ensure_seed_rules

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    metrics.init_app(app)

    app.register_blueprint(api)
    app.register_blueprint(ui)

    with app.app_context():
        db.create_all()
        ensure_seed_rules()

    return app
