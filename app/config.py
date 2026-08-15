"""Application configuration, driven entirely by environment variables.

Every third-party key and path is centralised here so integrations can be
added or swapped without touching route or service code.
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Allow OAuth over HTTP for local development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

load_dotenv()


class Config:
    """Base configuration. Override per-environment via env vars (see README)."""

    # --- Flask ---
    SECRET_KEY = os.environ.get("APP_SECRET_KEY")
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

    # --- Email (Resend) ---
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
    RESEND_API_URL = "https://api.resend.com/emails"
    MAIL_TO = os.environ.get("MAIL_TO")

    # --- Text-to-speech (Voice RSS) ---
    VOICE_RSS_API_KEY = os.environ.get("VOICE_RSS_API_KEY")
    VOICE_RSS_URL = "https://api.voicerss.org/"

    # --- Bible APIs ---
    BIBLE_API_BASE = "https://bible-api.com"
    API_BIBLE_KEY = os.environ.get("API_BIBLE_KEY")
    API_BIBLE_BASE = "https://rest.api.bible/v1"
    API_BIBLE_SECONDARY_KEY = os.environ.get("API_BIBLE_SECONDARY_KEY")
    API_BIBLE_SECONDARY_BASE = "https://rest.api.bible/v1"

    # --- Web Push (daily verse reminders) ---
    # Generate with: python generate_vapid.py
    VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
    VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
    VAPID_SUBJECT = os.environ.get("VAPID_SUBJECT", "mailto:admin@mypersonal-bible.app")
    # Secret token required to trigger the daily push (e.g. from a free cron)
    APP_PUSH_TOKEN = os.environ.get("APP_PUSH_TOKEN")

    # --- Storage ---
    # Points at a Render Persistent Disk mount in production (set SYNC_DATA_DIR
    # in the Render dashboard, e.g. /var/data/sync_data) so user data survives
    # redeploys. Falls back to a local "sync_data" folder for development.
    SYNC_DATA_DIR = Path(os.environ.get("SYNC_DATA_DIR", "sync_data"))


def ensure_storage_dirs() -> None:
    """Create the sync-data directory if it doesn't exist yet."""
    Config.SYNC_DATA_DIR.mkdir(parents=True, exist_ok=True)
