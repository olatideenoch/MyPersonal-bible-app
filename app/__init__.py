"""MyPersonal Bible application package.

Provides the application factory used by the production entry point
(``gunicorn main:app`` / ``python main.py``) and by the test suite.
"""
from flask import Flask

from .config import Config, ensure_storage_dirs


def create_app(config_object=None) -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    ensure_storage_dirs()

    from .routes import register_blueprints

    register_blueprints(app)

    return app
