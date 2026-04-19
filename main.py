from flask import Flask, render_template, url_for, redirect, request, jsonify, send_file
import requests
import datetime as dt
import random
import os
import re
import json
import io
from typing import List

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Resend API configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_API_URL = "https://api.resend.com/emails"

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

# Bible books with proper display names and slugs
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


# ========== AUDIO GENERATION (VOICE RSS) ==========

def text_to_speech_voicerss(text: str, voice: str = "en-us") -> bytes:
    """Convert text to speech using Voice RSS API. Returns MP3 audio data as bytes."""
    if not text or not text.strip():
        print("ERROR: No text provided for audio generation")
        return None
    
    text = text.strip()
    print(f"🎵 Generating audio: {len(text)} chars")
    
    params = {
        "key": VOICE_RSS_API_KEY,
        "src": text,
        "hl": voice,
        "r": "0",
        "c": "MP3",
        "f": "16khz_16bit_mono"
    }
    
    try:
        response = requests.post(VOICE_RSS_URL, data=params, timeout=30)
        
        if response.status_code == 200:
            print(f"  ✓ Audio generated: {len(response.content)} bytes")
            return response.content
        else:
            print(f"  ✗ Voice RSS error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  ✗ Voice RSS failed: {e}")
        return None


@app.route("/api/download-audio", methods=["POST"])
def download_audio():
    """Generate and download MP3 audio for given text."""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing text parameter"}), 400
        
        text = data['text'].strip()
        filename = data.get('filename', 'bible-audio.mp3')
        
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        if not filename.endswith('.mp3'):
            filename += '.mp3'
        
        audio_data = text_to_speech_voicerss(text)
        
        if audio_data is None:
            return jsonify({"error": "Failed to generate audio. Please try again."}), 500
        
        return send_file(
            io.BytesIO(audio_data),
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Download audio error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/api/play-audio", methods=["POST"])
def play_audio():
    """Stream MP3 audio for playback."""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing text parameter"}), 400
        
        text = data['text'].strip()
        
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        audio_data = text_to_speech_voicerss(text)
        
        if audio_data is None:
            return jsonify({"error": "Failed to generate audio."}), 500
        
        return send_file(
            io.BytesIO(audio_data),
            mimetype="audio/mpeg"
        )
        
    except Exception as e:
        print(f"Play audio error: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500


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
                print(f"API Error: {response.status_code}")
        except Exception as e:
            print(f"Search request failed: {e}")
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
    )


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


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    app.run(debug=True)