"""MyPersonal Bible - application entry point.

Kept at the repo root for zero-config compatibility with the existing
Render deployment (start command: ``gunicorn main:app``) and for local
development (``python main.py``).

The application itself lives in the ``app`` package: see ``app/__init__.py``
for the factory and ``app/routes/`` for the URL map.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
