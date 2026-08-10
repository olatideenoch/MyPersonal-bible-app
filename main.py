from flask import Flask, render_template, url_for, redirect, request, jsonify, send_file, session, Response
import requests
import datetime as dt
import random
import os
import re
import json
import io
import secrets
import html
from datetime import timedelta
from typing import List
from pathlib import Path
from requests_oauthlib import OAuth2Session

from dotenv import load_dotenv

# Allow OAuth over HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

# Resend API configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_API_URL = "https://api.resend.com/emails"

# Voice RSS API configuration
VOICE_RSS_API_KEY = os.environ.get("VOICE_RSS_API_KEY")
VOICE_RSS_URL = "https://api.voicerss.org/"

# Bible API configurations
BIBLE_API_BASE = "https://bible-api.com"
API_BIBLE_KEY = os.environ.get("API_BIBLE_KEY")
API_BIBLE_BASE = "https://rest.api.bible/v1"
API_BIBLE_SECONDARY_KEY = os.environ.get("API_BIBLE_SECONDARY_KEY")
API_BIBLE_SECONDARY_BASE = "https://rest.api.bible/v1"

# Create sync data directory if it doesn't exist
SYNC_DATA_DIR = Path("sync_data")
SYNC_DATA_DIR.mkdir(exist_ok=True)

# ========== BIBLE DATA STRUCTURE ==========

BIBLE_BOOKS = [
    {"name": "Genesis", "chapters": 50, "slug": "genesis"},
    {"name": "Exodus", "chapters": 40, "slug": "exodus"},
    {"name": "Leviticus", "chapters": 27, "slug": "leviticus"},
    {"name": "Numbers", "chapters": 36, "slug": "numbers"},
    {"name": "Deuteronomy", "chapters": 34, "slug": "deuteronomy"},
    {"name": "Joshua", "chapters": 24, "slug": "joshua"},
    {"name": "Judges", "chapters": 21, "slug": "judges"},
    {"name": "Ruth", "chapters": 4, "slug": "ruth"},
    {"name": "1 Samuel", "chapters": 31, "slug": "1-samuel"},
    {"name": "2 Samuel", "chapters": 24, "slug": "2-samuel"},
    {"name": "1 Kings", "chapters": 22, "slug": "1-kings"},
    {"name": "2 Kings", "chapters": 25, "slug": "2-kings"},
    {"name": "1 Chronicles", "chapters": 29, "slug": "1-chronicles"},
    {"name": "2 Chronicles", "chapters": 36, "slug": "2-chronicles"},
    {"name": "Ezra", "chapters": 10, "slug": "ezra"},
    {"name": "Nehemiah", "chapters": 13, "slug": "nehemiah"},
    {"name": "Esther", "chapters": 10, "slug": "esther"},
    {"name": "Job", "chapters": 42, "slug": "job"},
    {"name": "Psalms", "chapters": 150, "slug": "psalms"},
    {"name": "Proverbs", "chapters": 31, "slug": "proverbs"},
    {"name": "Ecclesiastes", "chapters": 12, "slug": "ecclesiastes"},
    {"name": "Song of Solomon", "chapters": 8, "slug": "song-of-solomon"},
    {"name": "Isaiah", "chapters": 66, "slug": "isaiah"},
    {"name": "Jeremiah", "chapters": 52, "slug": "jeremiah"},
    {"name": "Lamentations", "chapters": 5, "slug": "lamentations"},
    {"name": "Ezekiel", "chapters": 48, "slug": "ezekiel"},
    {"name": "Daniel", "chapters": 12, "slug": "daniel"},
    {"name": "Hosea", "chapters": 14, "slug": "hosea"},
    {"name": "Joel", "chapters": 3, "slug": "joel"},
    {"name": "Amos", "chapters": 9, "slug": "amos"},
    {"name": "Obadiah", "chapters": 1, "slug": "obadiah"},
    {"name": "Jonah", "chapters": 4, "slug": "jonah"},
    {"name": "Micah", "chapters": 7, "slug": "micah"},
    {"name": "Nahum", "chapters": 3, "slug": "nahum"},
    {"name": "Habakkuk", "chapters": 3, "slug": "habakkuk"},
    {"name": "Zephaniah", "chapters": 3, "slug": "zephaniah"},
    {"name": "Haggai", "chapters": 2, "slug": "haggai"},
    {"name": "Zechariah", "chapters": 14, "slug": "zechariah"},
    {"name": "Malachi", "chapters": 4, "slug": "malachi"},
    {"name": "Matthew", "chapters": 28, "slug": "matthew"},
    {"name": "Mark", "chapters": 16, "slug": "mark"},
    {"name": "Luke", "chapters": 24, "slug": "luke"},
    {"name": "John", "chapters": 21, "slug": "john"},
    {"name": "Acts", "chapters": 28, "slug": "acts"},
    {"name": "Romans", "chapters": 16, "slug": "romans"},
    {"name": "1 Corinthians", "chapters": 16, "slug": "1-corinthians"},
    {"name": "2 Corinthians", "chapters": 13, "slug": "2-corinthians"},
    {"name": "Galatians", "chapters": 6, "slug": "galatians"},
    {"name": "Ephesians", "chapters": 6, "slug": "ephesians"},
    {"name": "Philippians", "chapters": 4, "slug": "philippians"},
    {"name": "Colossians", "chapters": 4, "slug": "colossians"},
    {"name": "1 Thessalonians", "chapters": 5, "slug": "1-thessalonians"},
    {"name": "2 Thessalonians", "chapters": 3, "slug": "2-thessalonians"},
    {"name": "1 Timothy", "chapters": 6, "slug": "1-timothy"},
    {"name": "2 Timothy", "chapters": 4, "slug": "2-timothy"},
    {"name": "Titus", "chapters": 3, "slug": "titus"},
    {"name": "Philemon", "chapters": 1, "slug": "philemon"},
    {"name": "Hebrews", "chapters": 13, "slug": "hebrews"},
    {"name": "James", "chapters": 5, "slug": "james"},
    {"name": "1 Peter", "chapters": 5, "slug": "1-peter"},
    {"name": "2 Peter", "chapters": 3, "slug": "2-peter"},
    {"name": "1 John", "chapters": 5, "slug": "1-john"},
    {"name": "2 John", "chapters": 1, "slug": "2-john"},
    {"name": "3 John", "chapters": 1, "slug": "3-john"},
    {"name": "Jude", "chapters": 1, "slug": "jude"},
    {"name": "Revelation", "chapters": 22, "slug": "revelation"},
]

# Add testament information
for i, book in enumerate(BIBLE_BOOKS):
    book['testament'] = 'Old' if i < 39 else 'New'


def _build_bible_in_a_year_plan(days: int = 365) -> list:
    all_chapters = []
    for book in BIBLE_BOOKS:
        for ch in range(1, book["chapters"] + 1):
            all_chapters.append({"book": book["name"], "slug": book["slug"], "chapter": ch})

    total = len(all_chapters)
    base = total // days
    remainder = total % days

    # Spread the "extra chapter" days evenly across the year instead of bunching them at the end
    extra_days = set()
    if remainder:
        for j in range(remainder):
            extra_days.add(round(j * days / remainder))

    def label_groups(readings):
        parts = []
        for g in readings:
            if g["start"] == g["end"]:
                parts.append(f"{g['book']} {g['start']}")
            else:
                parts.append(f"{g['book']} {g['start']}-{g['end']}")
        return "; ".join(parts)

    plan = []
    idx = 0
    for day_num in range(1, days + 1):
        count = max(base + (1 if (day_num - 1) in extra_days else 0), 1)
        day_chapters = all_chapters[idx: idx + count]
        idx += count

        groups = []
        for c in day_chapters:
            if groups and groups[-1]["slug"] == c["slug"] and c["chapter"] == groups[-1]["end"] + 1:
                groups[-1]["end"] = c["chapter"]
            else:
                groups.append({"book": c["book"], "slug": c["slug"], "start": c["chapter"], "end": c["chapter"]})

        plan.append({"day": day_num, "readings": groups, "label": label_groups(groups)})

    # Fold any leftover chapters (rounding edge case) into the final day
    if idx < total:
        for c in all_chapters[idx:]:
            last_readings = plan[-1]["readings"]
            if last_readings and last_readings[-1]["slug"] == c["slug"] and c["chapter"] == last_readings[-1]["end"] + 1:
                last_readings[-1]["end"] = c["chapter"]
            else:
                last_readings.append({"book": c["book"], "slug": c["slug"], "start": c["chapter"], "end": c["chapter"]})
        plan[-1]["label"] = label_groups(plan[-1]["readings"])

    return plan


BIBLE_YEAR_PLAN = _build_bible_in_a_year_plan(365)
BIBLE_YEAR_TOTAL_DAYS = len(BIBLE_YEAR_PLAN)


# ========== VERSION LIST & MAPPINGS ==========

VERSION_LIST = [
    {"id": "en-kjv", "version": "King James Version (KJV)", "source": "bible_api", "popularity": 1},
    {"id": "en-niv", "version": "New International Version (NIV)", "source": "api_bible", "popularity": 2},
    {"id": "en-nkjv", "version": "New King James Version (NKJV)", "source": "api_bible", "popularity": 3},
<<<<<<< HEAD
    {"id": "en-amp", "version": "Amplified Bible (AMP)", "source": "api_bible_secondary", "popularity": 4},
    # {"id": "en-esv", "version": "English Standard Version (ESV)", "source": "bible_api", "popularity": 4},
=======
    {"id": "en-esv", "version": "English Standard Version (ESV)", "source": "bible_api", "popularity": 4},
>>>>>>> d21cbf841cbcd21bc64539875dc8cacdafb31f72
    {"id": "en-nasb", "version": "New American Standard Bible (NASB)", "source": "api_bible_secondary", "popularity": 5},
    {"id": "en-csb", "version": "Christian Standard Bible (CSB)", "source": "api_bible_secondary", "popularity": 6},
    {"id": "en-nlt", "version": "New Living Translation (NLT)", "source": "api_bible", "popularity": 7},
    # {"id": "en-bsb", "version": "Berean Standard Bible (BSB)", "source": "bible_api", "popularity": 8},
    {"id": "en-web", "version": "World English Bible (WEB)", "source": "bible_api", "popularity": 9},
    # {"id": "en-nrsv", "version": "New Revised Standard Version (NRSV)", "source": "bible_api", "popularity": 10},
    # {"id": "en-rsv", "version": "Revised Standard Version (RSV)", "source": "bible_api", "popularity": 11},
    {"id": "en-asv", "version": "American Standard Version (ASV)", "source": "bible_api", "popularity": 12},
    {"id": "en-bbe", "version": "Bible in Basic English (BBE)", "source": "bible_api", "popularity": 13},
    {"id": "en-darby", "version": "Darby Bible", "source": "bible_api", "popularity": 14},
    {"id": "en-dra", "version": "Douay-Rheims (DRA)", "source": "bible_api", "popularity": 15},
<<<<<<< HEAD
    # {"id": "en-ylt", "version": "Young's Literal Translation (YLT)", "source": "bible_api", "popularity": 16},
    # {"id": "en-msg", "version": "The Message (MSG)", "source": "bible_api", "popularity": 18},
    # {"id": "en-net", "version": "NET Bible (NET)", "source": "bible_api", "popularity": 19},
    # {"id": "en-erv", "version": "Easy-to-Read Version (ERV)", "source": "bible_api", "popularity": 20},
    # {"id": "pt-almeida", "version": "João Ferreira de Almeida (Português)", "source": "bible_api", "popularity": 21},
=======
    {"id": "en-ylt", "version": "Young's Literal Translation (YLT)", "source": "bible_api", "popularity": 16},
    {"id": "en-amp", "version": "Amplified Bible (AMP)", "source": "api_bible_secondary", "popularity": 17},
    {"id": "en-msg", "version": "The Message (MSG)", "source": "bible_api", "popularity": 18},
    {"id": "en-net", "version": "NET Bible (NET)", "source": "bible_api", "popularity": 19},
    {"id": "en-erv", "version": "Easy-to-Read Version (ERV)", "source": "bible_api", "popularity": 20},
    {"id": "pt-almeida", "version": "João Ferreira de Almeida (Português)", "source": "bible_api", "popularity": 21},
>>>>>>> d21cbf841cbcd21bc64539875dc8cacdafb31f72
    {"id": "ro-rccv", "version": "Cornilescu (Română)", "source": "bible_api", "popularity": 22},
    # {"id": "zh-cuv", "version": "Chinese Union Version (中文)", "source": "bible_api", "popularity": 23},
    # {"id": "cs-bkr", "version": "Bible Kralická (Čeština)", "source": "bible_api", "popularity": 24},
]

# API.Bible mapping (book name -> API.Bible book ID)
# Full reference: https://api.scripture.api.bible/
API_BIBLE_BOOKS = {
    "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV", "Numbers": "NUM",
    "Deuteronomy": "DEU", "Joshua": "JOS", "Judges": "JDG", "Ruth": "RUT",
    "1 Samuel": "1SA", "2 Samuel": "2SA", "1 Kings": "1KI", "2 Kings": "2KI",
    "1 Chronicles": "1CH", "2 Chronicles": "2CH", "Ezra": "EZR", "Nehemiah": "NEH",
    "Esther": "EST", "Job": "JOB", "Psalms": "PSA", "Proverbs": "PRO",
    "Ecclesiastes": "ECC", "Song of Solomon": "SNG", "Isaiah": "ISA", "Jeremiah": "JER",
    "Lamentations": "LAM", "Ezekiel": "EZK", "Daniel": "DAN", "Hosea": "HOS",
    "Joel": "JOL", "Amos": "AMO", "Obadiah": "OBA", "Jonah": "JON",
    "Micah": "MIC", "Nahum": "NAM", "Habakkuk": "HAB", "Zephaniah": "ZEP",
    "Haggai": "HAG", "Zechariah": "ZEC", "Malachi": "MAL", "Matthew": "MAT",
    "Mark": "MRK", "Luke": "LUK", "John": "JHN", "Acts": "ACT",
    "Romans": "ROM", "1 Corinthians": "1CO", "2 Corinthians": "2CO", "Galatians": "GAL",
    "Ephesians": "EPH", "Philippians": "PHP", "Colossians": "COL", "1 Thessalonians": "1TH",
    "2 Thessalonians": "2TH", "1 Timothy": "1TI", "2 Timothy": "2TI", "Titus": "TIT",
    "Philemon": "PHM", "Hebrews": "HEB", "James": "JAS", "1 Peter": "1PE",
    "2 Peter": "2PE", "1 John": "1JN", "2 John": "2JN", "3 John": "3JN",
    "Jude": "JUD", "Revelation": "REV"
}

# API.Bible version IDs (verified against the live API catalog)
API_BIBLE_VERSIONS = {
    "en-nkjv": "63097d2a0a2f7db3-01",
    "en-niv": "78a9f6124f344018-01",
    "en-nlt": "d6e14a625393b4da-01",
}

API_BIBLE_VERSIONS_SECONDARY = {
    "en-csb": "a556c5305ee15c3f-01",
    "en-amp": "a81b73293d3080c9-01",
    "en-nasb": "a761ca71e0b3ddcf-01",
}

# Bible-API.com translation mappings
BIBLEAPI_TRANSLATIONS = {
    "en-kjv": "kjv",
    "en-bsb": "bsb",
    "en-web": "web",
    "en-asv": "asv",
    "en-bbe": "bbe",
    "en-darby": "darby",
    "en-dra": "dra",
    "en-ylt": "ylt",
    "en-esv": "esv",
    "en-nasb": "nasb",
    "en-csb": "csb",
    "en-nlt": "nlt",
    "en-niv": "niv",
    "en-nkjv": "nkjv",
    "en-nrsv": "nrsv",
    "en-rsv": "rsv",
    "en-amp": "amp",
    "en-msg": "msg",
    "en-net": "net",
    "en-erv": "erv",
    "pt-almeida": "almeida",
    "ro-rccv": "rccv",
    "zh-cuv": "cuv",
    "cs-bkr": "bkr",
}


# ========== HELPER FUNCTIONS ==========

def get_book_by_slug(slug: str):
    """Get book by slug"""
    slug_lower = slug.lower()
    for book in BIBLE_BOOKS:
        if book['slug'] == slug_lower:
            return book
    return None


def get_book_by_name(name: str):
    """Get book by name"""
    name_lower = name.lower()
    for book in BIBLE_BOOKS:
        if book['name'].lower() == name_lower:
            return book
    return None


def get_version_name(version_id: str) -> str:
    """Get human-friendly version name"""
    return next((v['version'] for v in VERSION_LIST if v['id'] == version_id), version_id)


def get_version_source(version_id: str) -> str:
    """Get API source for a version"""
    return next((v.get('source', 'bible_api') for v in VERSION_LIST if v['id'] == version_id), 'bible_api')


def clean_text(text: str) -> str:
    """Clean verse text"""
    if not text:
        return text
    text = text.replace('…', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def dedupe_verses(raw_verses: list) -> list:
    """Remove duplicate verses"""
    seen = set()
    out = []
    for v in raw_verses:
        key = v.get('verse') or v.get('reference') or v.get('text')
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


# ========== FETCH FUNCTIONS ==========

def fetch_chapter_bibleapi(book_name: str, chapter: int, version_id: str = "en-kjv") -> tuple:
    """
    Fetch from bible-api.com (free, public domain)
    Most reliable fallback
    """
    translation = BIBLEAPI_TRANSLATIONS.get(version_id, "kjv")
    ref = f"{book_name}+{chapter}"
    url = f"{BIBLE_API_BASE}/{ref}?translation={translation}"

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            if translation != "kjv":
                print(f"Translation {translation} unavailable for {ref}; falling back to KJV")
                return fetch_chapter_bibleapi(book_name, chapter, "en-kjv")
            print(f"Bible API error for {ref}: {resp.status_code}")
            return [], ""

        data = resp.json()
        raw_verses = data.get("verses", [])

        verses = []
        for v in raw_verses:
            text = clean_text(v.get("text", "").strip())
            verses.append({
                "verse": str(v.get("verse", "")),
                "reference": f"{book_name} {chapter}:{v.get('verse', '')}",
                "text": text,
            })

        verses = dedupe_verses(verses)
        chapter_text = " ".join(v["text"] for v in verses)
        print(f"✅ Fetched from Bible API: {book_name} {chapter} ({len(verses)} verses)")
        return verses, chapter_text

    except Exception as e:
        print(f"Bible API error: {e}")
        return [], ""


def parse_api_bible_verses(content: str, book_name: str, chapter: int) -> list:
    """Extract verse-level text from API.Bible's HTML chapter content."""
    if not content:
        return []

    pattern = re.compile(
        r'<span[^>]*data-number="(\d+)"[^>]*>(.*?)</span>(.*?)(?=<span[^>]*data-number=|$)',
        re.S,
    )

    verses = []
    for match in pattern.finditer(content):
        verse_num = match.group(1)
        verse_text = re.sub(r'<[^>]+>', ' ', match.group(3))
        verse_text = html.unescape(verse_text)
        verse_text = clean_text(verse_text)
        if verse_text:
            verses.append({
                "verse": verse_num,
                "reference": f"{book_name} {chapter}:{verse_num}",
                "text": verse_text,
            })

    if not verses:
        fallback_text = clean_text(re.sub(r'<[^>]+>', ' ', content))
        if fallback_text:
            verses.append({
                "verse": "1",
                "reference": f"{book_name} {chapter}:1",
                "text": fallback_text,
            })

    return dedupe_verses(verses)


def fetch_chapter_apibible(book_name: str, chapter: int, version_id: str) -> tuple:
    """
    Fetch chapter text from API.Bible using the current REST API format.
    """
    if not API_BIBLE_KEY:
        print("API.Bible key not configured")
        return [], ""

    book_code = API_BIBLE_BOOKS.get(book_name)
    if not book_code:
        print(f"Book '{book_name}' not found in API.Bible mapping")
        return [], ""

    version_code, api_key, api_base = get_api_bible_credentials(version_id)
    if not version_code:
        print(f"Version '{version_id}' not found in API.Bible mapping")
        return [], ""

    try:
        headers = {
            "api-key": api_key,
            "Accept": "application/json",
        }

        chapter_ref = f"{book_code}.{chapter}"
        url = f"{api_base}/bibles/{version_code}/chapters/{chapter_ref}"

        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code != 200:
            print(f"API.Bible error: {resp.status_code} - {resp.text[:200]}")
            return [], ""

        data = resp.json()
        chapter_data = data.get("data", {})
        content = chapter_data.get("content", "")

        if not content:
            print(f"No chapter content found for {book_name} {chapter}")
            return [], ""

        verses = parse_api_bible_verses(content, book_name, chapter)
        chapter_text = " ".join(v["text"] for v in verses)
        print(f"Fetched from API.Bible: {book_name} {chapter} ({len(verses)} verses)")
        return verses, chapter_text

    except Exception as e:
        print(f"API.Bible fetch error: {e}")
        return [], ""

def get_api_bible_credentials(version_id):
    """
    Returns:
    version_code,
    api_key,
    api_base
    """

    if version_id in API_BIBLE_VERSIONS:
        return (
            API_BIBLE_VERSIONS[version_id],
            API_BIBLE_KEY,
            API_BIBLE_BASE
        )

    if version_id in API_BIBLE_VERSIONS_SECONDARY:
        return (
            API_BIBLE_VERSIONS_SECONDARY[version_id],
            API_BIBLE_SECONDARY_KEY,
            API_BIBLE_SECONDARY_BASE
        )

    return None, None, None


def fetch_chapter_bibleapi_smart(book_name: str, chapter: int, version_id: str) -> tuple:
    """
    Smart fetcher with fallback logic.
    API.Bible is tried first for versions mapped to it; every version falls back to Bible-API.com.
    """
    source = get_version_source(version_id)

    if source in ("api_bible", "api_bible_secondary"):
        verses, text = fetch_chapter_apibible(book_name, chapter, version_id)
        if verses:
            return verses, text
        print(f"API.Bible failed, falling back to Bible API")

    return fetch_chapter_bibleapi(book_name, chapter, version_id)


# ========== DAILY VERSE ==========

_daily_verse_cache = {"date": None, "verse": None}

def get_daily_verse() -> dict:
    """Get daily verse with caching"""
    today_str = dt.date.today().isoformat()

    if _daily_verse_cache["date"] == today_str and _daily_verse_cache["verse"]:
        return _daily_verse_cache["verse"]

    verse = None
    try:
        resp = requests.get(f"{BIBLE_API_BASE}/?random=verse", timeout=8)
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


# ========== SYNC DATA ==========

def get_user_sync_file(user_id: str) -> Path:
    safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    return SYNC_DATA_DIR / f"{safe_id}.json"


def load_user_sync_data(user_id: str) -> dict:
    sync_file = get_user_sync_file(user_id)
    if sync_file.exists():
        try:
            with open(sync_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sync data: {e}")
    return {
        "bookmarks": [],
        "highlights": {},
        "progress": {},
        "readingLog": [],
        "bibleYear": {"start_date": None, "completed_days": []},
        "font_size": None,
        "theme": None,
        "last_sync": None
    }


def save_user_sync_data(user_id: str, data: dict) -> bool:
    sync_file = get_user_sync_file(user_id)
    try:
        data["last_sync"] = dt.datetime.now().isoformat()
        with open(sync_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving sync data: {e}")
        return False


def merge_sync_data(local_data: dict, server_data: dict) -> dict:
    """Merge local and server sync data"""
    merged = {}
    
    # Merge bookmarks
    local_bookmarks = local_data.get("bookmarks", [])
    server_bookmarks = server_data.get("bookmarks", [])
    bookmark_map = {}
    for b in server_bookmarks + local_bookmarks:
        ref = b.get("reference", "")
        if ref not in bookmark_map or b.get("timestamp", "") > bookmark_map[ref].get("timestamp", ""):
            bookmark_map[ref] = b
    merged["bookmarks"] = list(bookmark_map.values())
    
    # Merge highlights
    merged["highlights"] = {}
    server_highlights = server_data.get("highlights", {})
    local_highlights = local_data.get("highlights", {})
    all_chapters = set(server_highlights.keys()) | set(local_highlights.keys())
    for chapter in all_chapters:
        server_verses = set(server_highlights.get(chapter, []))
        local_verses = set(local_highlights.get(chapter, []))
        merged["highlights"][chapter] = list(server_verses | local_verses)
    
    # Merge reading log (union of dates read, deduped and sorted)
    server_log = set(server_data.get("readingLog", []))
    local_log = set(local_data.get("readingLog", []))
    merged["readingLog"] = sorted(server_log | local_log)
    
    # Merge Bible-in-a-Year progress (union completed days, keep the earliest start date)
    server_by = server_data.get("bibleYear") or {}
    local_by = local_data.get("bibleYear") or {}
    merged_completed = set(server_by.get("completed_days", [])) | set(local_by.get("completed_days", []))
    server_start = server_by.get("start_date")
    local_start = local_by.get("start_date")
    if server_start and local_start:
        merged_start = min(server_start, local_start)
    else:
        merged_start = server_start or local_start
    merged["bibleYear"] = {"start_date": merged_start, "completed_days": sorted(merged_completed)}
    
    # Merge progress
    merged["progress"] = {}
    server_progress = server_data.get("progress", {})
    local_progress = local_data.get("progress", {})
    all_progress = set(server_progress.keys()) | set(local_progress.keys())
    for key in all_progress:
        server_val = server_progress.get(key, {})
        local_val = local_progress.get(key, {})
        server_ts = server_val.get("timestamp", "")
        local_ts = local_val.get("timestamp", "")
        merged["progress"][key] = server_val if server_ts > local_ts else local_val
    
    merged["font_size"] = local_data.get("font_size") or server_data.get("font_size")
    merged["theme"] = local_data.get("theme") or server_data.get("theme")
    
    return merged


def compute_streak(reading_log: list) -> dict:
    """Given a list of ISO date strings ('YYYY-MM-DD') the user read on,
    compute their current streak, longest streak, and last-read date."""
    if not reading_log:
        return {"current_streak": 0, "longest_streak": 0, "last_read": None, "total_days_read": 0}
    
    try:
        dates = sorted({dt.date.fromisoformat(d) for d in reading_log})
    except ValueError:
        return {"current_streak": 0, "longest_streak": 0, "last_read": None, "total_days_read": 0}
    
    today = dt.date.today()
    longest_streak = 1
    run = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            run += 1
        else:
            run = 1
        longest_streak = max(longest_streak, run)
    
    last_read = dates[-1]
    gap_from_today = (today - last_read).days
    
    if gap_from_today > 1:
        # Streak is broken (missed at least one full day)
        current_streak = 0
    else:
        # Walk backwards from the most recent read day counting consecutive days
        current_streak = 1
        for i in range(len(dates) - 1, 0, -1):
            if (dates[i] - dates[i - 1]).days == 1:
                current_streak += 1
            else:
                break
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "last_read": last_read.isoformat(),
        "total_days_read": len(dates)
    }


def compute_bible_year_progress(bible_year: dict) -> dict:
    """Given a user's {start_date, completed_days} for the Bible-in-a-Year plan,
    compute completion stats and whether they're on track, ahead, or behind."""
    bible_year = bible_year or {}
    completed_days = sorted(set(bible_year.get("completed_days", [])))
    start_date_str = bible_year.get("start_date")
    total_days = BIBLE_YEAR_TOTAL_DAYS
    completed_count = len(completed_days)

    result = {
        "start_date": start_date_str,
        "completed_days": completed_days,
        "completed_count": completed_count,
        "total_days": total_days,
        "percent_complete": round((completed_count / total_days) * 100, 1) if total_days else 0,
        "expected_day": None,
        "days_ahead_behind": None,
        "status": "not_started"
    }

    if not start_date_str:
        return result

    try:
        start_date = dt.date.fromisoformat(start_date_str)
    except ValueError:
        return result

    today = dt.date.today()
    elapsed = (today - start_date).days + 1
    expected_day = min(max(elapsed, 1), total_days)
    result["expected_day"] = expected_day

    diff = completed_count - expected_day
    result["days_ahead_behind"] = diff
    if completed_count >= total_days:
        result["status"] = "completed"
    elif diff >= 0:
        result["status"] = "on_track"
    else:
        result["status"] = "behind"

    return result


# ========== AUDIO/TTS ==========

def _fetch_voice_rss_chunk(text: str, voice: str = "en-us") -> bytes:
    """Fetch a single chunk from Voice RSS API"""
    data = {
        "key": VOICE_RSS_API_KEY,
        "src": text,
        "hl": voice,
        "r": "0",
        "c": "mp3",
        "f": "44khz_16bit_stereo",
        "ssml": "false",
        "b64": "false"
    }
    
    try:
        response = requests.post(VOICE_RSS_URL, data=data, timeout=30)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'audio' in content_type or response.content[:3] in [b'ID3', b'\xff\xfb']:
                return response.content
        return None
    except Exception as e:
        print(f"Voice RSS error: {e}")
        return None


def text_to_speech_voicerss(text: str, voice: str = "en-us") -> bytes:
    """Convert text to speech with chunking"""
    MAX_CHARS = 4500
    
    def chunk_text(text: str, max_length: int = 4500) -> list:
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += (" " if current_chunk else "") + sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:max_length]]

    chunks = chunk_text(text, MAX_CHARS)
    
    if len(chunks) == 1:
        return _fetch_voice_rss_chunk(chunks[0], voice)
    
    audio_chunks = []
    for chunk in chunks:
        chunk_audio = _fetch_voice_rss_chunk(chunk, voice)
        if chunk_audio is None:
            return None
        audio_chunks.append(chunk_audio)
    
    return b''.join(audio_chunks)


# ========== FLASK ROUTES ==========

@app.route("/api/download-audio", methods=["POST"])
def download_audio():
    """Download audio file"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing text parameter"}), 400
    
    text = data['text'].strip()
    filename = data.get('filename', 'bible-audio.mp3')
    
    if not filename.endswith('.mp3'):
        filename += '.mp3'
    
    audio_data = text_to_speech_voicerss(text)
    
    if audio_data is None:
        return jsonify({"error": "Failed to generate audio"}), 500
    
    return send_file(
        io.BytesIO(audio_data),
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=filename
    )


@app.route("/api/play-audio", methods=["POST"])
def play_audio():
    """Stream audio"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing text parameter"}), 400
    
    text = data['text'].strip()
    audio_data = text_to_speech_voicerss(text)
    
    if audio_data is None:
        return jsonify({"error": "Failed to generate audio"}), 500
    
    return send_file(io.BytesIO(audio_data), mimetype="audio/mpeg")


@app.route("/")
def index():
    daily_verse = get_daily_verse()
    user = session.get('user')
    return render_template(
        "index.html",
        current_year=dt.datetime.now().year,
        daily_verse=daily_verse,
        books=BIBLE_BOOKS,
        versions=VERSION_LIST,
        user=user
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    api_key = API_BIBLE_KEY or os.environ.get("API_KEY")
    headers = {"api-key": api_key} if api_key else {}
    
    search_results = None
    search_performed = False
    query = ""
    
    if request.method == "POST":
        query = request.form.get("query", "").strip()
    elif request.method == "GET":
        query = request.args.get("query", "").strip()
    
    if query:
        try:
            search_bible_id = API_BIBLE_VERSIONS.get("en-niv", "78a9f6124f344018-01")
            search_url = f"{API_BIBLE_BASE}/bibles/{search_bible_id}/search"
            response = requests.get(search_url, headers=headers, params={"query": query}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                search_results = []
                
                if "data" in data and "verses" in data["data"]:
                    for verse in data["data"]["verses"]:
                        cleaned = clean_text(verse.get("text", ""))
                        search_results.append({
                            "text": cleaned,
                            "reference": verse.get("reference", "")
                        })
            else:
                search_results = []
                print(f"Search API error: {response.status_code}")
        except Exception as e:
            print(f"Search error: {e}")
            search_results = []       
        search_performed = True

    daily_verse = get_daily_verse()
    user = session.get('user')
    return render_template(
        "index.html",
        current_year=dt.datetime.now().year,
        daily_verse=daily_verse,
        books=BIBLE_BOOKS,
        versions=VERSION_LIST,
        search_results=search_results,
        search_performed=search_performed,
        query=query,
        user=user
    )


def _send_contact_email_resend(sender_name: str, sender_email: str, subject: str, message: str):
    """Send email via Resend"""
    if not RESEND_API_KEY:
        return False, 'Resend API key is not configured.'
    
    from_email = "MyPersonal Bible App <noreply@resend.dev>"
    to_email = os.environ.get("MAIL_TO")
    
    email_body = f"""
    <h2>New Contact Form Submission</h2>
    <p><strong>Name:</strong> {sender_name or '(not provided)'}</p>
    <p><strong>Email:</strong> {sender_email or '(not provided)'}</p>
    <p><strong>Category:</strong> {subject or '(not specified)'}</p>
    <p><strong>Message:</strong></p>
    <p style="white-space: pre-wrap;">{message}</p>
    <hr>
    <p><small>Sent from MyPersonal Bible App Contact Form</small></p>
    """
    
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": f"[MyPersonalBibleApp] {subject or 'New contact message'}",
        "html": email_body,
    }
    
    if sender_email:
        payload["reply_to"] = sender_email
    
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(RESEND_API_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code in (200, 201, 202):
            return True, 'Your message was sent successfully. Thank you!'
        else:
            print(f"Resend error: {response.status_code}")
            return False, 'Failed to send email. Please try again later.'
            
    except Exception as e:
        print(f"Email send error: {e}")
        return False, 'Failed to send email. Please try again later.'


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form_data = {'name': '', 'email': '', 'subject': '', 'message': ''}
    status_message = None
    status_type = 'info'
    user = session.get('user')

    if request.method == 'POST':
        form_data['name'] = request.form.get('name', '').strip()
        form_data['email'] = request.form.get('email', '').strip()
        form_data['subject'] = request.form.get('subject', '').strip()
        form_data['message'] = request.form.get('message', '').strip()

        if not form_data['email'] or not form_data['message']:
            status_type = 'warning'
            status_message = 'Please provide both your email address and a message.'
        else:
            success, msg = _send_contact_email_resend(
                sender_name=form_data['name'],
                sender_email=form_data['email'],
                subject=form_data['subject'],
                message=form_data['message'],
            )
            status_type = 'success' if success else 'danger'
            status_message = msg
            if success:
                form_data = {'name': '', 'email': '', 'subject': '', 'message': ''}

    return render_template(
        'contact.html',
        current_year=dt.datetime.now().year,
        status_message=status_message,
        status_type=status_type,
        form_data=form_data,
        user=user
    )


@app.route("/books/<book_slug>", methods=["GET", "POST"])
def books(book_slug):
    book = get_book_by_slug(book_slug)
    
    if not book:
        return f"Book '{book_slug}' not found", 404

    # Chapter/version can arrive either via the in-page POST form (existing
    # dropdown/prev-next nav) or as GET query params, so a URL like
    # /books/genesis?chapter=1 is directly deep-linkable (used by the
    # Bible in a Year day list).
    selected_chapter = request.form.get("chapter") or request.args.get("chapter")
    selected_version = request.form.get("version") or request.args.get("version", "en-kjv")
    verses = []
    chapter_text = ""
    error_message = None
    user = session.get('user')

    if selected_chapter:
        try:
            selected_chapter = int(selected_chapter)
            verses, chapter_text = fetch_chapter_bibleapi_smart(
                book['name'], selected_chapter, selected_version
            )

            if not verses:
                version_name = get_version_name(selected_version)
                error_message = (
                    f"Unable to load {version_name} for {book['name']} {selected_chapter}. "
                    f"Please try another version or check your internet connection."
                )
        except Exception as e:
            print(f"Chapter fetch error: {e}")
            error_message = f"Error loading chapter: {str(e)}"

    return render_template(
        "books.html",
        current_year=dt.datetime.now().year,
        book=book,
        books=BIBLE_BOOKS,
        selected_chapter=selected_chapter if selected_chapter else None,
        selected_version=selected_version,
        chapter_text=chapter_text,
        verses=verses,
        versions=VERSION_LIST,
        error_message=error_message,
        user=user
    )


@app.route('/api/chapter/<book_name>/<int:chapter>')
def api_chapter(book_name, chapter):
    selected_version = request.args.get('version', 'en-kjv')
    
    book = get_book_by_slug(book_name) or get_book_by_name(book_name)
    if not book:
        return jsonify({'error': f'Book "{book_name}" not found'}), 404
    
    if chapter < 1 or chapter > book['chapters']:
        return jsonify({'error': f'Chapter {chapter} not valid for {book["name"]}'}), 404
    
    verses, chapter_text = fetch_chapter_bibleapi_smart(book['name'], chapter, selected_version)

    if not verses:
        return jsonify({'error': 'Chapter not found or request failed'}), 404

    return jsonify({
        'book': book['name'],
        'book_slug': book['slug'],
        'chapter': chapter,
        'total_chapters': book['chapters'],
        'version': selected_version,
        'version_name': get_version_name(selected_version),
        'verse_count': len(verses),
        'chapter_text': chapter_text,
        'verses': verses,
    })


@app.route('/api/books', methods=['GET'])
def api_books():
    testament = request.args.get('testament', 'all').lower()
    
    books = BIBLE_BOOKS.copy()
    
    if testament == 'old':
        books = books[:39]
    elif testament == 'new':
        books = books[39:]
    
    return jsonify({
        'total': len(books),
        'testament': testament,
        'books': books
    })


@app.route('/api/versions', methods=['GET'])
def api_versions():
    return jsonify({
        'total': len(VERSION_LIST),
        'versions': VERSION_LIST
    })


@app.route('/api/daily-verse', methods=['GET'])
def api_daily_verse():
    daily_verse = get_daily_verse()
    return jsonify({
        'date': dt.date.today().isoformat(),
        'verse': daily_verse
    })


@app.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Missing search query parameter "q"'}), 400
    
    api_key = API_BIBLE_KEY or os.environ.get("API_KEY")
    headers = {"api-key": api_key} if api_key else {}
    
    try:
        search_bible_id = API_BIBLE_VERSIONS.get("en-niv", "78a9f6124f344018-01")
        search_url = f"{API_BIBLE_BASE}/bibles/{search_bible_id}/search"
        response = requests.get(search_url, headers=headers, params={"query": query, "limit": limit}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            if "data" in data and "verses" in data["data"]:
                for verse in data["data"]["verses"]:
                    cleaned = clean_text(verse.get("text", ""))
                    results.append({
                        "text": cleaned,
                        "reference": verse.get("reference", "")
                    })
            
            return jsonify({
                'query': query,
                'total': len(results),
                'results': results
            })
        else:
            return jsonify({'error': f'Search failed: {response.status_code}'}), response.status_code
            
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': 'Search request failed'}), 500


@app.route('/api/verse/<book_name>/<int:chapter>/<int:verse>')
def api_verse(book_name, chapter, verse):
    selected_version = request.args.get('version', 'en-kjv')
    
    book = get_book_by_slug(book_name) or get_book_by_name(book_name)
    if not book:
        return jsonify({'error': f'Book "{book_name}" not found'}), 404
    
    verses, _ = fetch_chapter_bibleapi_smart(book['name'], chapter, selected_version)
    
    if not verses:
        return jsonify({'error': 'Chapter not found'}), 404
    
    target_verse = None
    for v in verses:
        if v.get('verse') == str(verse):
            target_verse = v
            break
    
    if not target_verse:
        return jsonify({'error': f'Verse {verse} not found'}), 404
    
    return jsonify({
        'book': book['name'],
        'book_slug': book['slug'],
        'chapter': chapter,
        'verse': verse,
        'reference': target_verse['reference'],
        'text': target_verse['text'],
        'version': selected_version
    })


# ========== GOOGLE OAUTH ==========

@app.route('/login/google')
def google_login():
    """Initiate Google OAuth"""
    google = OAuth2Session(
        GOOGLE_CLIENT_ID,
        redirect_uri=url_for('google_callback', _external=True),
        scope=['openid', 'email', 'profile']
    )
    
    auth_url, state = google.authorization_url(
        GOOGLE_AUTH_URL,
        access_type='offline',
        prompt='select_account'
    )
    
    session['oauth_state'] = state
    return redirect(auth_url)


@app.route('/login/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        google = OAuth2Session(
            GOOGLE_CLIENT_ID,
            state=session.get('oauth_state'),
            redirect_uri=url_for('google_callback', _external=True)
        )
        
        token = google.fetch_token(
            GOOGLE_TOKEN_URL,
            client_secret=GOOGLE_CLIENT_SECRET,
            authorization_response=request.url
        )
        
        session.pop('oauth_state', None)
        
        google = OAuth2Session(GOOGLE_CLIENT_ID, token=token)
        user_info = google.get(GOOGLE_USERINFO_URL).json()
        
        session['user'] = {
            'id': user_info['sub'],
            'name': user_info.get('name', user_info.get('email')),
            'email': user_info['email'],
            'picture': user_info.get('picture', '')
        }
        session.permanent = True
        
        print(f"Login successful: {user_info.get('email')}")
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"Login failed: {e}")
        session.pop('oauth_state', None)
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('user', None)
    return redirect(url_for('index'))


# ========== SYNC API ==========

@app.route('/api/sync', methods=['POST'])
def sync_data():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    server_data = load_user_sync_data(user_id)
    merged_data = merge_sync_data(data, server_data)
    
    if save_user_sync_data(user_id, merged_data):
        return jsonify({'success': True, 'message': 'Data synced successfully'})
    else:
        return jsonify({'error': 'Failed to save data'}), 500


@app.route('/api/sync', methods=['GET'])
def get_sync_data():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    data['streak'] = compute_streak(data.get('readingLog', []))
    data['bibleYearProgress'] = compute_bible_year_progress(data.get('bibleYear', {}))
    
    return jsonify(data)


@app.route('/api/log-reading', methods=['POST'])
def log_reading():
    """Record that the user read a chapter today, for streak tracking.
    Lightweight and automatic (called on chapter load) — separate from
    the full bookmarks/highlights sync so it doesn't need a manual Sync Now."""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    user_id = session['user']['id']
    today_str = dt.date.today().isoformat()
    
    data = load_user_sync_data(user_id)
    reading_log = set(data.get('readingLog', []))
    reading_log.add(today_str)
    data['readingLog'] = sorted(reading_log)
    
    if not save_user_sync_data(user_id, data):
        return jsonify({'error': 'Failed to save reading log'}), 500
    
    streak = compute_streak(data['readingLog'])
    return jsonify({'success': True, 'streak': streak})


@app.route('/api/bible-year/plan', methods=['GET'])
def bible_year_plan():
    """Public - the static 365-day reading plan. No auth needed since it's the same for everyone."""
    return jsonify({"days": BIBLE_YEAR_TOTAL_DAYS, "plan": BIBLE_YEAR_PLAN})


@app.route('/api/bible-year/progress', methods=['GET'])
def bible_year_progress():
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    progress = compute_bible_year_progress(data.get('bibleYear', {}))
    return jsonify({'authenticated': True, 'progress': progress})


@app.route('/api/bible-year/start', methods=['POST'])
def bible_year_start():
    """Begin (or restart) the Bible-in-a-Year plan from today, clearing any prior progress."""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    data['bibleYear'] = {"start_date": dt.date.today().isoformat(), "completed_days": []}
    
    if not save_user_sync_data(user_id, data):
        return jsonify({'error': 'Failed to save'}), 500
    
    progress = compute_bible_year_progress(data['bibleYear'])
    return jsonify({'success': True, 'progress': progress})


@app.route('/api/bible-year/mark', methods=['POST'])
def bible_year_mark():
    """Mark a plan day as read (or unread). Body: {"day": 1, "completed": true}"""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    body = request.get_json() or {}
    day = body.get('day')
    completed = body.get('completed', True)
    
    if not isinstance(day, int) or day < 1 or day > BIBLE_YEAR_TOTAL_DAYS:
        return jsonify({'error': f'day must be an integer between 1 and {BIBLE_YEAR_TOTAL_DAYS}'}), 400
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    bible_year = data.get('bibleYear') or {"start_date": None, "completed_days": []}
    
    if not bible_year.get('start_date'):
        bible_year['start_date'] = dt.date.today().isoformat()
    
    completed_days = set(bible_year.get('completed_days', []))
    if completed:
        completed_days.add(day)
    else:
        completed_days.discard(day)
    bible_year['completed_days'] = sorted(completed_days)
    data['bibleYear'] = bible_year
    
    if not save_user_sync_data(user_id, data):
        return jsonify({'error': 'Failed to save'}), 500
    
    progress = compute_bible_year_progress(bible_year)
    return jsonify({'success': True, 'progress': progress})


@app.route('/api/user', methods=['GET'])
def get_user():
    user = session.get('user')
    if user:
        return jsonify({
            'authenticated': True,
            'name': user['name'],
            'email': user['email'],
            'picture': user.get('picture', '')
        })
    return jsonify({'authenticated': False})


@app.route('/install')
def install_guide():
    user = session.get('user')
    return render_template('install.html', user=user, current_year=dt.datetime.now().year)


@app.route('/bible-in-a-year')
def bible_in_a_year():
    """Renders the Bible in a Year tracker page. The 365-day plan and the
    signed-in user's progress are fetched client-side via
    /api/bible-year/plan and /api/bible-year/progress, matching how sync
    data is already fetched client-side elsewhere in the app."""
    user = session.get('user')
    return render_template('bible_in_a_year.html', user=user, current_year=dt.datetime.now().year)


@app.route('/robots.txt')
def robots_txt():
    sitemap_url = url_for('sitemap_xml', _external=True)
    content = f"User-agent: *\nAllow: /\nSitemap: {sitemap_url}\n"
    return Response(content, mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    pages = [
        url_for('index', _external=True),
        url_for('contact', _external=True),
        url_for('install_guide', _external=True),
        url_for('search', _external=True)
    ]
    pages.extend(url_for('books', book_slug=book['slug'], _external=True) for book in BIBLE_BOOKS)
    lastmod = dt.date.today().isoformat()
    xml_urls = "\n".join(
        f"    <url>\n      <loc>{page}</loc>\n      <lastmod>{lastmod}</lastmod>\n      <changefreq>weekly</changefreq>\n      <priority>0.7</priority>\n    </url>"
        for page in pages
    )
    xml = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n{xml_urls}\n</urlset>"
    return Response(xml, mimetype='application/xml')


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    app.run(debug=True)