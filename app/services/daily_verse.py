"""Daily verse with per-day caching and curated fallback."""
import datetime as dt
import random

import requests

from app.config import Config


_daily_verse_cache = {"date": None, "verse": None}

def get_daily_verse() -> dict:
    """Get daily verse with caching"""
    today_str = dt.date.today().isoformat()

    if _daily_verse_cache["date"] == today_str and _daily_verse_cache["verse"]:
        return _daily_verse_cache["verse"]

    verse = None
    try:
        resp = requests.get(f"{Config.BIBLE_API_BASE}/?random=verse", timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("text", "").strip()
            reference = data.get("reference", "").strip()
            if text and reference:
                verse = {"text": text, "reference": reference}
    except Exception as e:
        print(f"Daily verse error: {e}")

    if not verse:
        fallback_list = [
            {"text": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.", "reference": "John 3:16"},
            {"text": "The Lord is my shepherd; I shall not want.", "reference": "Psalm 23:1"},
            {"text": "I can do all this through him who gives me strength.", "reference": "Philippians 4:13"},
            {"text": "Trust in the Lord with all your heart and lean not on your own understanding.", "reference": "Proverbs 3:5"},
        ]
        verse = random.choice(fallback_list)

    _daily_verse_cache["date"] = today_str
    _daily_verse_cache["verse"] = verse
    return verse
