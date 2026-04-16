from flask import Flask, render_template, url_for, redirect, request, jsonify, send_file
import requests
import datetime as dt
import random
import os
import re
import smtplib
import ssl
import socket
import json
import io
from email.message import EmailMessage
from email.utils import formataddr
from typing import List

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Voice RSS API configuration
VOICE_RSS_API_KEY = os.environ.get("VOICE_RSS_API_KEY")
VOICE_RSS_URL = "https://api.voicerss.org/"

# bible-api.com (Tim Morgan) helpers
BIBLE_API_BASE = "https://bible-api.com"

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
    """
    Return a daily verse that stays constant for the whole day.
    """
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

BIBLE_BOOKS = [
    {"name": "Genesis", "chapters": 50},
    {"name": "Exodus", "chapters": 40},
    {"name": "Leviticus", "chapters": 27},
    {"name": "Numbers", "chapters": 36},
    {"name": "Deuteronomy", "chapters": 34},
    {"name": "Joshua", "chapters": 24},
    {"name": "Judges", "chapters": 21},
    {"name": "Ruth", "chapters": 4},
    {"name": "1Samuel", "chapters": 31},
    {"name": "2Samuel", "chapters": 24},
    {"name": "1Kings", "chapters": 22},
    {"name": "2Kings", "chapters": 25},
    {"name": "1Chronicles", "chapters": 29},
    {"name": "2Chronicles", "chapters": 36},
    {"name": "Ezra", "chapters": 10},
    {"name": "Nehemiah", "chapters": 13},
    {"name": "Esther", "chapters": 10},
    {"name": "Job", "chapters": 42},
    {"name": "Psalms", "chapters": 150},
    {"name": "Proverbs", "chapters": 31},
    {"name": "Ecclesiastes", "chapters": 12},
    {"name": "SongofSolomon", "chapters": 8},
    {"name": "Isaiah", "chapters": 66},
    {"name": "Jeremiah", "chapters": 52},
    {"name": "Lamentations", "chapters": 5},
    {"name": "Ezekiel", "chapters": 48},
    {"name": "Daniel", "chapters": 12},
    {"name": "Hosea", "chapters": 14},
    {"name": "Joel", "chapters": 3},
    {"name": "Amos", "chapters": 9},
    {"name": "Obadiah", "chapters": 1},
    {"name": "Jonah", "chapters": 4},
    {"name": "Micah", "chapters": 7},
    {"name": "Nahum", "chapters": 3},
    {"name": "Habakkuk", "chapters": 3},
    {"name": "Zephaniah", "chapters": 3},
    {"name": "Haggai", "chapters": 2},
    {"name": "Zechariah", "chapters": 14},
    {"name": "Malachi", "chapters": 4},
    {"name": "Matthew", "chapters": 28},
    {"name": "Mark", "chapters": 16},
    {"name": "Luke", "chapters": 24},
    {"name": "John", "chapters": 21},
    {"name": "Acts", "chapters": 28},
    {"name": "Romans", "chapters": 16},
    {"name": "1Corinthians", "chapters": 16},
    {"name": "2Corinthians", "chapters": 13},
    {"name": "Galatians", "chapters": 6},
    {"name": "Ephesians", "chapters": 6},
    {"name": "Philippians", "chapters": 4},
    {"name": "Colossians", "chapters": 4},
    {"name": "1Thessalonians", "chapters": 5},
    {"name": "2Thessalonians", "chapters": 3},
    {"name": "1Timothy", "chapters": 6},
    {"name": "2Timothy", "chapters": 4},
    {"name": "Titus", "chapters": 3},
    {"name": "Philemon", "chapters": 1},
    {"name": "Hebrews", "chapters": 13},
    {"name": "James", "chapters": 5},
    {"name": "1Peter", "chapters": 5},
    {"name": "2Peter", "chapters": 3},
    {"name": "1John", "chapters": 5},
    {"name": "2John", "chapters": 1},
    {"name": "3John", "chapters": 1},
    {"name": "Jude", "chapters": 1},
    {"name": "Revelation", "chapters": 22},
]

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

def text_to_speech_voicerss(text: str, voice: str = "en-us") -> bytes:
    """
    Convert text to speech using Voice RSS API.
    Returns MP3 audio data as bytes.
    """
    # Voice RSS has a 5000 character limit per request
    max_chars = 5000
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
    
    params = {
        "key": VOICE_RSS_API_KEY,
        "src": text,
        "hl": voice,
        "r": "0",  # Reading speed: -10 to 10, 0 is normal
        "c": "mp3",
        "f": "44khz_16bit_stereo",
        "ssml": "false",
        "b64": "false"
    }
    
    try:
        response = requests.get(VOICE_RSS_URL, params=params, timeout=30)
        if response.status_code == 200:
            # Check if response is audio data (starts with ID3 or FF FB for MP3)
            content_type = response.headers.get('Content-Type', '')
            if 'audio' in content_type or response.content[:3] in [b'ID3', b'\xff\xfb']:
                return response.content
            else:
                # Voice RSS returns error messages as plain text
                error_msg = response.text[:200]
                print(f"Voice RSS API error: {error_msg}")
                return None
        else:
            print(f"Voice RSS API returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"Voice RSS request failed: {e}")
        return None

@app.route("/api/download-audio", methods=["POST"])
def download_audio():
    """
    Generate and download MP3 audio for given text.
    Expects JSON with 'text' and optional 'filename' fields.
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing text parameter"}), 400
    
    text = data['text'].strip()
    filename = data.get('filename', 'bible-audio.mp3')
    
    # Ensure .mp3 extension
    if not filename.endswith('.mp3'):
        filename += '.mp3'
    
    audio_data = text_to_speech_voicerss(text)
    
    if audio_data is None:
        return jsonify({"error": "Failed to generate audio. Voice RSS API may be unavailable or text too long."}), 500
    
    return send_file(
        io.BytesIO(audio_data),
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=filename
    )

@app.route("/api/play-audio", methods=["POST"])
def play_audio():
    """
    Stream MP3 audio for playback.
    Expects JSON with 'text' field.
    """
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
    return render_template(
        "index.html",
        current_year=dt.datetime.now().year,
        daily_verse=daily_verse,
        books=BIBLE_BOOKS,
        versions=VERSION_LIST,
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
    return render_template(
        "index.html",
        current_year=dt.datetime.now().year,
        daily_verse=daily_verse,
        books=BIBLE_BOOKS,
        versions=VERSION_LIST,
        search_results=search_results,
        search_performed=search_performed,
        query=query,
    )

def _sanitize_header_value(value: str) -> str:
    if not value:
        return ''
    return value.replace('\r', '').replace('\n', '').strip()

def _send_contact_email(sender_name: str, sender_email: str, subject: str, message: str):
    mail_host = os.environ.get('MAIL_HOST')
    mail_port = int(os.environ.get('MAIL_PORT', 587))
    mail_user = os.environ.get('MAIL_USERNAME')
    mail_pass = os.environ.get('MAIL_PASSWORD')
    mail_to   = os.environ.get('MAIL_TO')
    use_tls   = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
    use_ssl   = os.environ.get('MAIL_USE_SSL', 'false').lower() in ('1', 'true', 'yes')

    if not mail_user or not mail_pass:
        return False, 'Email sending is not configured. Set MAIL_USERNAME and MAIL_PASSWORD in the environment.'

    safe_name    = _sanitize_header_value(sender_name)
    safe_email   = _sanitize_header_value(sender_email)
    safe_subject = _sanitize_header_value(subject) or 'New contact message'

    msg = EmailMessage()
    msg['Subject'] = f"[MyPersonalBibleApp] {safe_subject}"
    msg['From']    = formataddr((safe_name or 'Contact Form', mail_user))
    msg['To']      = mail_to
    if safe_email:
        msg['Reply-To'] = safe_email

    body = (
        f"Name: {safe_name or '(not provided)'}\n"
        f"Email: {safe_email or '(not provided)'}\n"
        f"Subject: {safe_subject}\n\nMessage:\n{message}\n"
    )
    msg.set_content(body)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(mail_host, mail_port, timeout=10) as smtp:
                smtp.login(mail_user, mail_pass)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(mail_host, mail_port, timeout=10) as smtp:
                if use_tls:
                    smtp.starttls()
                smtp.login(mail_user, mail_pass)
                smtp.send_message(msg)
        return True, 'Your message was sent successfully. Thank you!'
    except Exception as e:
        hint = ''
        msg_err = str(e).lower()

        if hasattr(e, 'errno') and e.errno in (101, 110, 113):
            hint = ' (network unreachable or connection refused; check firewall/Internet access)'
        elif isinstance(e, socket.timeout) or 'timed out' in msg_err:
            hint = ' (timeout; check that your server can reach the SMTP host and port)'
        elif isinstance(e, ssl.SSLError) or 'handshake' in msg_err:
            hint = ' (SSL/TLS handshake failed; verify port/SSL settings)'
        elif isinstance(e, smtplib.SMTPAuthenticationError):
            hint = ' (authentication failed; check username/password)'

        return False, f'Failed to send email{hint}'

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form_data = {'name': '', 'email': '', 'subject': '', 'message': ''}
    status_message = None
    status_type = 'info'

    if request.method == 'POST':
        form_data['name']    = request.form.get('name', '').strip()
        form_data['email']   = request.form.get('email', '').strip()
        form_data['subject'] = request.form.get('subject', '').strip()
        form_data['message'] = request.form.get('message', '').strip()

        if not form_data['email'] or not form_data['message']:
            status_type    = 'warning'
            status_message = 'Please provide both your email address and a message.'
        else:
            success, msg = _send_contact_email(
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
    )

@app.route("/books/<book_name>", methods=["GET", "POST"])
def books(book_name):
    book = next(
        (b for b in BIBLE_BOOKS if b['name'].lower().replace(' ', '-') == book_name.lower()),
        None,
    )
    if not book:
        return "Book not found", 404

    selected_chapter = request.form.get("chapter")
    selected_version = request.form.get("version", "en-kjv")
    verses       = []
    chapter_text = ""

    if selected_chapter:
        selected_chapter = int(selected_chapter)
        verses, chapter_text = fetch_chapter_bibleapi(
            book['name'], selected_chapter, selected_version
        )

    return render_template(
        "books.html",
        current_year=dt.datetime.now().year,
        book=book,
        selected_chapter=selected_chapter,
        selected_version=selected_version,
        chapter_text=chapter_text,
        verses=verses,
        versions=VERSION_LIST,
    )

@app.route('/api/chapter/<book_name>/<int:chapter>')
def api_chapter(book_name, chapter):
    """
    Get chapter data with optional verse range filtering.
    Query params:
    - version: Bible version ID (default: en-kjv)
    - verse_start: Starting verse number (optional)
    - verse_end: Ending verse number (optional)
    - format: 'full' or 'simple' (default: full)
    """
    selected_version = request.args.get('version', 'en-kjv')
    verse_start = request.args.get('verse_start', type=int)
    verse_end = request.args.get('verse_end', type=int)
    format_type = request.args.get('format', 'full')
    
    # Validate book exists
    book = next((b for b in BIBLE_BOOKS if b['name'].lower() == book_name.lower()), None)
    if not book:
        return jsonify({'error': f'Book "{book_name}" not found'}), 404
    
    # Validate chapter number
    if chapter < 1 or chapter > book['chapters']:
        return jsonify({'error': f'Chapter {chapter} not found in {book_name}. Valid chapters: 1-{book["chapters"]}'}), 404
    
    verses, chapter_text = fetch_chapter_bibleapi(book_name, chapter, selected_version)

    if not verses:
        return jsonify({'error': 'Chapter not found or request failed'}), 404

    # Filter by verse range if specified
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
        
        # Update chapter_text for filtered verses
        if filtered_verses:
            chapter_text = " ".join(v["text"] for v in filtered_verses)
        else:
            chapter_text = ""

    # Build response based on format
    response_data = {
        'book': book_name,
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
    """
    Get list of all Bible books with metadata.
    Query params:
    - testament: 'old', 'new', or 'all' (default: all)
    """
    testament = request.args.get('testament', 'all').lower()
    
    books = BIBLE_BOOKS.copy()
    
    if testament == 'old':
        books = books[:39]  # First 39 books are Old Testament
    elif testament == 'new':
        books = books[39:]  # Books 40-66 are New Testament
    
    # Add full book names and slugs
    enriched_books = []
    for book in books:
        enriched_books.append({
            'name': book['name'],
            'slug': book['name'].lower().replace(' ', '-'),
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
    """Get list of available Bible versions."""
    return jsonify({
        'total': len(VERSION_LIST),
        'versions': VERSION_LIST
    })


@app.route('/api/daily-verse', methods=['GET'])
def api_daily_verse():
    """Get the verse of the day."""
    daily_verse = get_daily_verse()
    return jsonify({
        'date': dt.date.today().isoformat(),
        'verse': daily_verse
    })


@app.route('/api/search', methods=['GET'])
def api_search():
    """
    Search Bible verses by keyword.
    Query params:
    - q: Search query (required)
    - version: Bible version ID (default: en-kjv)
    - limit: Max results (default: 20)
    """
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
    """
    Get a single verse.
    Query params:
    - version: Bible version ID (default: en-kjv)
    """
    selected_version = request.args.get('version', 'en-kjv')
    
    verses, _ = fetch_chapter_bibleapi(book_name, chapter, selected_version)
    
    if not verses:
        return jsonify({'error': 'Chapter not found or request failed'}), 404
    
    # Find the specific verse
    target_verse = None
    for v in verses:
        if v.get('verse') == str(verse):
            target_verse = v
            break
    
    if not target_verse:
        return jsonify({'error': f'Verse {verse} not found in {book_name} {chapter}'}), 404
    
    return jsonify({
        'book': book_name,
        'chapter': chapter,
        'verse': verse,
        'reference': target_verse['reference'],
        'text': target_verse['text'],
        'version': selected_version
    })
    
@app.route("/health")
def health():
    return jsonify(status="ok"), 200

if __name__ == "__main__":
    app.run(debug=True)