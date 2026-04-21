from flask import Flask, render_template, url_for, redirect, request, jsonify, send_file, session
import requests
import datetime as dt
import random
import os
import re
import json
import io
import secrets
from typing import List
from pathlib import Path

from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")

# Google OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'
    }
)

# Resend API configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_API_URL = "https://api.resend.com/emails"

# Voice RSS API configuration
VOICE_RSS_API_KEY = os.environ.get("VOICE_RSS_API_KEY")
VOICE_RSS_URL = "https://api.voicerss.org/"

# bible-api.com (Tim Morgan) helpers
BIBLE_API_BASE = "https://bible-api.com"

# Create sync data directory if it doesn't exist
SYNC_DATA_DIR = Path("sync_data")
SYNC_DATA_DIR.mkdir(exist_ok=True)

BIBLEAPI_VERSION_MAP = {
    "en-kjv":  "kjv",
    "en-web":  "web",
    "en-oeb":  "oeb-us",
    "en-clementine": "clementine",
    "pt-almeida":    "almeida",
    "ro-rccv":       "rccv",
}

def _bibleapi_translation(version_id: str) -> str:
    """Return bible-api.com translation slug for a given version ID, defaulting to KJV."""
    return BIBLEAPI_VERSION_MAP.get(version_id, "kjv")

_daily_verse_cache = {"date": None, "verse": None}

def get_daily_verse() -> dict:
    """Return a daily verse that stays constant for the whole day."""
    today_str = dt.date.today().isoformat()        

    if _daily_verse_cache["date"] == today_str and _daily_verse_cache["verse"]:
        return _daily_verse_cache["verse"]

    random.seed(today_str)

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
        print(f"Daily verse fetch failed: {e}")

    if not verse:
        fallback_list = [
            {"text": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.", "reference": "John 3:16"},
            {"text": "The Lord is my shepherd; I shall not want.", "reference": "Psalm 23:1"},
            {"text": "I can do all this through him who gives me strength.", "reference": "Philippians 4:13"},
            {"text": "Trust in the Lord with all your heart and lean not on your own understanding.", "reference": "Proverbs 3:5"},
            {"text": "Be still, and know that I am God.", "reference": "Psalm 46:10"},
            {"text": "Do not be anxious about anything, but in every situation, by prayer and petition, with thanksgiving, present your requests to God.", "reference": "Philippians 4:6"},
            {"text": "For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future.", "reference": "Jeremiah 29:11"},
            {"text": "Your word is a lamp for my feet, a light on my path.", "reference": "Psalm 119:105"},
            {"text": "Come to me, all you who are weary and burdened, and I will give you rest.", "reference": "Matthew 11:28"},
            {"text": "But those who hope in the Lord will renew their strength. They will soar on wings like eagles.", "reference": "Isaiah 40:31"},
        ]
        verse = random.choice(fallback_list)

    random.seed()
    _daily_verse_cache["date"] = today_str
    _daily_verse_cache["verse"] = verse
    return verse

# Updated BIBLE_BOOKS with proper display names and slugs
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

def get_book_by_slug(slug: str):
    """Find a book by its URL slug."""
    slug_lower = slug.lower()
    for book in BIBLE_BOOKS:
        if book['slug'] == slug_lower:
            return book
    return None

def get_book_by_name(name: str):
    """Find a book by its display name (case-insensitive)."""
    name_lower = name.lower()
    for book in BIBLE_BOOKS:
        if book['name'].lower() == name_lower:
            return book
    return None

VERSION_LIST = [
    {"id": "en-kjv",        "version": "King James Version (KJV)"},
    {"id": "en-web",        "version": "World English Bible (WEB)"},
    {"id": "en-oeb",        "version": "Open English Bible (OEB-US)"},
    {"id": "en-clementine", "version": "Clementine Latin Vulgate"},
    {"id": "pt-almeida",    "version": "João Ferreira de Almeida (Portuguese)"},
    {"id": "ro-rccv",       "version": "Romanian Cornilescu Version (RCCV)"},
]

def clean_text(text: str) -> str:
    """Clean verse text from API using regex."""
    if not text:
        return text
    text = text.replace('…', '')
    return text

def dedupe_verses(raw_verses: list) -> list:
    """Remove duplicate verse entries while preserving order."""
    seen = set()
    out = []
    for v in raw_verses:
        key = v.get('verse') or v.get('reference') or v.get('text')
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out

def fetch_chapter_bibleapi(book_name: str, chapter: int, version_id: str = "en-kjv"):
    translation = _bibleapi_translation(version_id)
    ref = f"{book_name}+{chapter}"
    url = f"{BIBLE_API_BASE}/{ref}?translation={translation}"

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"bible-api.com error {resp.status_code} for {url}")
            return [], ""

        data = resp.json()
        raw_verses = data.get("verses", [])

        verses = []
        for v in raw_verses:
            text = clean_text(v.get("text", "").strip())
            verses.append({
                "verse":     str(v.get("verse", "")),
                "reference": v.get("book_name", book_name) + " " + str(chapter) + ":" + str(v.get("verse", "")),
                "text":      text,
            })

        verses = dedupe_verses(verses)
        chapter_text = " ".join(v["text"] for v in verses)
        return verses, chapter_text

    except Exception as e:
        print(f"fetch_chapter_bibleapi failed: {e}")
        return [], ""


def _fetch_voice_rss_chunk(text: str, voice: str = "en-us") -> bytes:
    """Fetch a single chunk from Voice RSS API."""
    params = {
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
        response = requests.get(VOICE_RSS_URL, params=params, timeout=30)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'audio' in content_type or response.content[:3] in [b'ID3', b'\xff\xfb']:
                return response.content
            else:
                error_msg = response.text[:200]
                print(f"Voice RSS API error: {error_msg}")
                return None
        else:
            print(f"Voice RSS API returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"Voice RSS request failed: {e}")
        return None


def text_to_speech_voicerss(text: str, voice: str = "en-us") -> bytes:
    """
    Convert text to speech using Voice RSS API with chunking for long texts.
    Returns MP3 audio data as bytes.
    """
    MAX_CHARS = 4500  # Leave room for API overhead
    
    def chunk_text(text: str, max_length: int = 4500) -> list:
        """Split text into chunks at sentence boundaries."""
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

    # Split text into chunks
    chunks = chunk_text(text, MAX_CHARS)
    
    if len(chunks) == 1:
        # Single chunk - process normally
        return _fetch_voice_rss_chunk(chunks[0], voice)
    
    # Multiple chunks - fetch and combine
    print(f"Processing {len(chunks)} chunks for audio generation...")
    
    audio_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"  Fetching chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
        chunk_audio = _fetch_voice_rss_chunk(chunk, voice)
        if chunk_audio is None:
            print(f"  Failed to fetch chunk {i+1}")
            return None
        audio_chunks.append(chunk_audio)
    
    # Combine all audio chunks
    combined = b''.join(audio_chunks)
    print(f"Successfully combined {len(chunks)} chunks ({len(combined)} bytes)")
    return combined


# ========== USER DATA SYNC FUNCTIONS (JSON File Storage) ==========

def get_user_sync_file(user_id: str) -> Path:
    """Get the sync file path for a user."""
    # Sanitize user_id for filename
    safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    return SYNC_DATA_DIR / f"{safe_id}.json"

def load_user_sync_data(user_id: str) -> dict:
    """Load synced data for a user from JSON file."""
    sync_file = get_user_sync_file(user_id)
    if sync_file.exists():
        try:
            with open(sync_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sync data for {user_id}: {e}")
    return {
        "bookmarks": [],
        "highlights": {},
        "progress": {},
        "font_size": None,
        "theme": None,
        "last_sync": None
    }

def save_user_sync_data(user_id: str, data: dict) -> bool:
    """Save synced data for a user to JSON file."""
    sync_file = get_user_sync_file(user_id)
    try:
        data["last_sync"] = dt.datetime.now().isoformat()
        with open(sync_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving sync data for {user_id}: {e}")
        return False

def merge_sync_data(local_data: dict, server_data: dict) -> dict:
    """Merge local and server data, keeping most recent or combining."""
    merged = {}
    
    # Merge bookmarks (combine and dedupe by reference)
    local_bookmarks = local_data.get("bookmarks", [])
    server_bookmarks = server_data.get("bookmarks", [])
    bookmark_map = {}
    for b in server_bookmarks + local_bookmarks:
        ref = b.get("reference", "")
        if ref not in bookmark_map or b.get("timestamp", "") > bookmark_map[ref].get("timestamp", ""):
            bookmark_map[ref] = b
    merged["bookmarks"] = list(bookmark_map.values())
    
    # Merge highlights (combine by chapter)
    merged["highlights"] = {}
    server_highlights = server_data.get("highlights", {})
    local_highlights = local_data.get("highlights", {})
    all_chapters = set(server_highlights.keys()) | set(local_highlights.keys())
    for chapter in all_chapters:
        server_verses = set(server_highlights.get(chapter, []))
        local_verses = set(local_highlights.get(chapter, []))
        merged["highlights"][chapter] = list(server_verses | local_verses)
    
    # Merge progress (keep most recent per chapter)
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
    
    # Use most recent font size
    merged["font_size"] = local_data.get("font_size") or server_data.get("font_size")
    
    # Use most recent theme
    merged["theme"] = local_data.get("theme") or server_data.get("theme")
    
    return merged


# ========== ROUTES ==========

@app.route("/api/download-audio", methods=["POST"])
def download_audio():
    """Generate and download MP3 audio for given text."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing text parameter"}), 400
    
    text = data['text'].strip()
    filename = data.get('filename', 'bible-audio.mp3')
    
    if not filename.endswith('.mp3'):
        filename += '.mp3'
    
    print(f"Generating audio for text length: {len(text)} characters")
    audio_data = text_to_speech_voicerss(text)
    
    if audio_data is None:
        return jsonify({"error": "Failed to generate audio. Voice RSS API may be unavailable."}), 500
    
    return send_file(
        io.BytesIO(audio_data),
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=filename
    )


@app.route("/api/play-audio", methods=["POST"])
def play_audio():
    """Stream MP3 audio for playback."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing text parameter"}), 400
    
    text = data['text'].strip()
    
    audio_data = text_to_speech_voicerss(text)
    
    if audio_data is None:
        return jsonify({"error": "Failed to generate audio"}), 500
    
    return send_file(
        io.BytesIO(audio_data),
        mimetype="audio/mpeg"
    )


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
    api_key = os.environ.get("API_KEY")
    headers = {"api-key": api_key}
    
    search_results = None
    search_performed = False
    query = ""
    
    if request.method == "POST":
        query = request.form.get("query", "").strip()
    elif request.method == "GET":
        query = request.args.get("query", "").strip()
    
    if query:
        try:
            search_url = f"https://rest.api.bible/v1/bibles/9879dbb7cfe39e4d-01/search?query={query}"
            response = requests.get(search_url, headers=headers)
            
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
                print(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")
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
    """Send contact form email using Resend API."""
    if not RESEND_API_KEY:
        return False, 'Resend API key is not configured.'
    
    from_email = "MyPersonal Bible App <noreply@resend.dev>"
    to_email = os.environ.get("MAIL_TO", "mypersonalbibleapp@gmail.com")
    
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
    
    plain_text = f"""
New Contact Form Submission

Name: {sender_name or '(not provided)'}
Email: {sender_email or '(not provided)'}
Category: {subject or '(not specified)'}

Message:
{message}

---
Sent from MyPersonal Bible App Contact Form
    """
    
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": f"[MyPersonalBibleApp] {subject or 'New contact message'}",
        "html": email_body,
        "text": plain_text,
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
            error_data = response.json() if response.text else {}
            error_msg = error_data.get('message', f'API error: {response.status_code}')
            print(f"Resend API error: {error_msg}")
            return False, f'Failed to send email: {error_msg}'
            
    except requests.exceptions.Timeout:
        return False, 'Email service timeout. Please try again later.'
    except Exception as e:
        print(f"Resend request failed: {e}")
        return False, f'Failed to send email: {str(e)}'


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form_data = {'name': '', 'email': '', 'subject': '', 'message': ''}
    status_message = None
    status_type = 'info'
    user = session.get('user')

    if request.method == 'POST':
        form_data['name']    = request.form.get('name', '').strip()
        form_data['email']   = request.form.get('email', '').strip()
        form_data['subject'] = request.form.get('subject', '').strip()
        form_data['message'] = request.form.get('message', '').strip()

        if not form_data['email'] or not form_data['message']:
            status_type    = 'warning'
            status_message = 'Please provide both your email address and a message.'
        else:
            success, msg = _send_contact_email_resend(
                sender_name=form_data['name'],
                sender_email=form_data['email'],
                subject=form_data['subject'],
                message=form_data['message'],
            )
            status_type    = 'success' if success else 'danger'
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
    """Display a book's chapters using clean URL slug."""
    book = get_book_by_slug(book_slug)
    
    if not book:
        return f"Book '{book_slug}' not found", 404

    selected_chapter = request.form.get("chapter")
    selected_version = request.form.get("version", "en-kjv")
    verses       = []
    chapter_text = ""
    user = session.get('user')

    if selected_chapter:
        selected_chapter = int(selected_chapter)
        verses, chapter_text = fetch_chapter_bibleapi(
            book['name'], selected_chapter, selected_version
        )

    return render_template(
        "books.html",
        current_year=dt.datetime.now().year,
        book=book,
        books=BIBLE_BOOKS,
        selected_chapter=selected_chapter,
        selected_version=selected_version,
        chapter_text=chapter_text,
        verses=verses,
        versions=VERSION_LIST,
        user=user
    )


# Legacy route for backward compatibility
@app.route("/books/<book_name>", methods=["GET", "POST"])
def books_legacy(book_name):
    """Legacy route - redirects to the new slug-based route."""
    book = get_book_by_slug(book_name)
    if book:
        return redirect(url_for('books', book_slug=book['slug']), code=301)
    
    book = get_book_by_name(book_name)
    if book:
        return redirect(url_for('books', book_slug=book['slug']), code=301)
    
    clean_name = book_name.lower().replace('-', '').replace(' ', '')
    for b in BIBLE_BOOKS:
        if b['name'].lower().replace(' ', '') == clean_name:
            return redirect(url_for('books', book_slug=b['slug']), code=301)
    
    return f"Book '{book_name}' not found", 404


@app.route('/api/chapter/<book_name>/<int:chapter>')
def api_chapter(book_name, chapter):
    selected_version = request.args.get('version', 'en-kjv')
    verse_start = request.args.get('verse_start', type=int)
    verse_end = request.args.get('verse_end', type=int)
    format_type = request.args.get('format', 'full')
    
    book = get_book_by_slug(book_name) or get_book_by_name(book_name)
    if not book:
        return jsonify({'error': f'Book "{book_name}" not found'}), 404
    
    if chapter < 1 or chapter > book['chapters']:
        return jsonify({'error': f'Chapter {chapter} not found in {book["name"]}. Valid chapters: 1-{book["chapters"]}'}), 404
    
    verses, chapter_text = fetch_chapter_bibleapi(book['name'], chapter, selected_version)

    if not verses:
        return jsonify({'error': 'Chapter not found or request failed'}), 404

    filtered_verses = verses
    if verse_start is not None or verse_end is not None:
        filtered_verses = []
        for verse in verses:
            verse_num = int(verse.get('verse', 0))
            if verse_num:
                if verse_start and verse_num < verse_start:
                    continue
                if verse_end and verse_num > verse_end:
                    continue
                filtered_verses.append(verse)
        
        if filtered_verses:
            chapter_text = " ".join(v["text"] for v in filtered_verses)
        else:
            chapter_text = ""

    response_data = {
        'book': book['name'],
        'book_slug': book['slug'],
        'book_full': book['name'],
        'chapter': chapter,
        'total_chapters': book['chapters'],
        'version': selected_version,
        'version_name': next((v['version'] for v in VERSION_LIST if v['id'] == selected_version), selected_version),
        'verse_count': len(verses),
        'filtered_count': len(filtered_verses) if (verse_start or verse_end) else len(verses)
    }
    
    if format_type == 'simple':
        response_data['verses'] = filtered_verses if (verse_start or verse_end) else verses
    else:
        response_data.update({
            'chapter_text': chapter_text,
            'verses': filtered_verses if (verse_start or verse_end) else verses,
            'has_filter': verse_start is not None or verse_end is not None,
            'verse_range': {
                'start': verse_start if verse_start else 1,
                'end': verse_end if verse_end else len(verses)
            } if (verse_start or verse_end) else None
        })

    return jsonify(response_data)


@app.route('/api/books', methods=['GET'])
def api_books():
    testament = request.args.get('testament', 'all').lower()
    
    books = BIBLE_BOOKS.copy()
    
    if testament == 'old':
        books = books[:39]
    elif testament == 'new':
        books = books[39:]
    
    enriched_books = []
    for book in books:
        enriched_books.append({
            'name': book['name'],
            'slug': book['slug'],
            'chapters': book['chapters'],
            'testament': 'Old' if BIBLE_BOOKS.index(book) < 39 else 'New'
        })
    
    return jsonify({
        'total': len(enriched_books),
        'testament': testament,
        'books': enriched_books
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
    version = request.args.get('version', 'en-kjv')
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Missing search query parameter "q"'}), 400
    
    api_key = os.environ.get("API_KEY")
    headers = {"api-key": api_key}
    
    try:
        search_url = f"https://rest.api.bible/v1/bibles/9879dbb7cfe39e4d-01/search?query={query}&limit={limit}"
        response = requests.get(search_url, headers=headers, timeout=10)
        
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
                'version': version,
                'total': len(results),
                'results': results
            })
        else:
            return jsonify({'error': f'Search API error: {response.status_code}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': f'Search request failed: {str(e)}'}), 500


@app.route('/api/verse/<book_name>/<int:chapter>/<int:verse>')
def api_verse(book_name, chapter, verse):
    selected_version = request.args.get('version', 'en-kjv')
    
    book = get_book_by_slug(book_name) or get_book_by_name(book_name)
    if not book:
        return jsonify({'error': f'Book "{book_name}" not found'}), 404
    
    verses, _ = fetch_chapter_bibleapi(book['name'], chapter, selected_version)
    
    if not verses:
        return jsonify({'error': 'Chapter not found or request failed'}), 404
    
    target_verse = None
    for v in verses:
        if v.get('verse') == str(verse):
            target_verse = v
            break
    
    if not target_verse:
        return jsonify({'error': f'Verse {verse} not found in {book["name"]} {chapter}'}), 404
    
    return jsonify({
        'book': book['name'],
        'book_slug': book['slug'],
        'chapter': chapter,
        'verse': verse,
        'reference': target_verse['reference'],
        'text': target_verse['text'],
        'version': selected_version
    })


# ========== GOOGLE OAUTH ROUTES ==========

@app.route('/login/google')
def google_login():
    """Initiate Google OAuth login."""
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/login/google/callback')
def google_callback():
    """Handle Google OAuth callback."""
    try:
        token = google.authorize_access_token()
        user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
        
        # Store user info in session (no database!)
        session['user'] = {
            'id': user_info['sub'],  # Google's unique ID
            'name': user_info['name'],
            'email': user_info['email'],
            'picture': user_info.get('picture', '')
        }
        
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Google OAuth error: {e}")
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Log out the current user."""
    session.pop('user', None)
    return redirect(url_for('index'))


# ========== SYNC API ROUTES ==========

@app.route('/api/sync', methods=['POST'])
def sync_data():
    """Save user data to JSON file storage."""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Load existing server data
    server_data = load_user_sync_data(user_id)
    
    # Merge with new data
    merged_data = merge_sync_data(data, server_data)
    
    # Save merged data
    if save_user_sync_data(user_id, merged_data):
        return jsonify({'success': True, 'message': 'Data synced successfully'})
    else:
        return jsonify({'error': 'Failed to save data'}), 500


@app.route('/api/sync', methods=['GET'])
def get_sync_data():
    """Retrieve synced data for current user."""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    
    return jsonify(data)


@app.route('/api/user', methods=['GET'])
def get_user():
    """Get current user info."""
    user = session.get('user')
    if user:
        return jsonify({
            'authenticated': True,
            'name': user['name'],
            'email': user['email'],
            'picture': user.get('picture', '')
        })
    return jsonify({'authenticated': False})


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    app.run(debug=True)