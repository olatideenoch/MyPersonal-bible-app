"""Shared pytest fixtures.

Environment must be configured BEFORE the app package is imported (the
Config object reads env vars at import time), so setup happens here first.
"""
import datetime as dt
import os
import sys
import tempfile

# --- environment (before importing the app) ---
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key")
# Isolate test data in a temp dir so real user data is never touched
os.environ.setdefault("SYNC_DATA_DIR", os.path.join(tempfile.mkdtemp(prefix="mpb-test-"), "sync_data"))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from app import create_app  # noqa: E402


@pytest.fixture()
def app():
    application = create_app()
    application.config.update(TESTING=True)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(app):
    """Test client with a signed-in Google user in the session."""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["user"] = {
            "id": "test-user",
            "name": "Test User",
            "email": "test@example.com",
            "picture": "",
        }
    return client


@pytest.fixture(autouse=True)
def seed_daily_verse():
    """Seed the daily-verse cache so tests never hit the network for it."""
    from app.services import daily_verse

    daily_verse._daily_verse_cache["date"] = dt.date.today().isoformat()
    daily_verse._daily_verse_cache["verse"] = {
        "text": "For God so loved the world, that he gave his only begotten Son.",
        "reference": "John 3:16",
    }
