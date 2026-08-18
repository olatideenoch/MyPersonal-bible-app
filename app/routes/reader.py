"""Bible reader: chapters, verses, versions, compare, commentary, audio, random verse."""
from flask import Blueprint, jsonify, render_template, request, send_file, session

import datetime as dt
import random
import io
import requests
import os
from app.bible.books import (
    API_BIBLE_VERSIONS,
    BIBLE_BOOKS,
    VERSION_LIST,
    get_book_by_name,
    get_book_by_slug,
    get_version_name,
)
from app.bible.verses import RANDOM_FALLBACK_VERSES, fetch_chapter_bibleapi_smart
from app.content import get_commentary, search_kjv
from app.services.audio import text_to_speech_voicerss
from app.services.daily_verse import get_daily_verse
from app.utils import clean_text
from app.services.storage import load_user_sync_data
from app.config import Config

bp = Blueprint('reader', __name__)

@bp.route("/api/download-audio", methods=["POST"])
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

@bp.route("/api/play-audio", methods=["POST"])
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

@bp.route("/books/<book_slug>", methods=["GET", "POST"])
def books(book_slug):
    book = get_book_by_slug(book_slug)
    
    if not book:
        return f"Book '{book_slug}' not found", 404

    selected_chapter = request.form.get("chapter") or request.args.get("chapter")
    selected_version = request.form.get("version") or request.args.get("version")
    verses = []
    chapter_text = ""
    error_message = None
    user = session.get('user')

    # If no version was requested, honour the signed-in user's preferred
    # version (falling back to KJV when none is set).
    if not selected_version:
        selected_version = "en-kjv"
        if user:
            try:
                sync_data = load_user_sync_data(user['id'])
                pref = sync_data.get("preferred_version")
                if pref:
                    selected_version = pref
            except Exception as e:
                print(f"Preferred version lookup error: {e}")

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

@bp.route('/api/chapter/<book_name>/<int:chapter>')
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

@bp.route('/api/books', methods=['GET'])
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

@bp.route('/api/versions', methods=['GET'])
def api_versions():
    return jsonify({
        'total': len(VERSION_LIST),
        'versions': VERSION_LIST
    })

@bp.route('/api/daily-verse', methods=['GET'])
def api_daily_verse():
    daily_verse = get_daily_verse()
    return jsonify({
        'date': dt.date.today().isoformat(),
        'verse': daily_verse
    })

@bp.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Missing search query parameter "q"'}), 400
    
    api_key = Config.API_BIBLE_KEY or os.environ.get("API_KEY")
    headers = {"api-key": api_key} if api_key else {}
    
    try:
        search_bible_id = API_BIBLE_VERSIONS.get("en-niv", "78a9f6124f344018-01")
        search_url = f"{Config.API_BIBLE_BASE}/bibles/{search_bible_id}/search"
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
            
            if results:
                return jsonify({
                    'query': query,
                    'total': len(results),
                    'results': results,
                    'source': 'api_bible'
                })
            # else fall through to the built-in index
        else:
            print(f"Search API error: {response.status_code} - using built-in KJV index")
            
    except Exception as e:
        print(f"Search API error: {e} - using built-in KJV index")

    # Built-in KJV fallback - always available, no API key needed
    results = search_kjv(query, limit=limit)
    return jsonify({
        'query': query,
        'total': len(results),
        'results': results,
        'source': 'kjv'
    })

@bp.route('/api/verse/<book_name>/<int:chapter>/<int:verse>')
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

@bp.route('/compare')
def compare_page():
    user = session.get('user')
    return render_template('compare.html', user=user, current_year=dt.datetime.now().year,
                           books=BIBLE_BOOKS, versions=VERSION_LIST)

@bp.route('/api/compare/<book_name>/<int:chapter>', methods=['GET'])
def api_compare(book_name, chapter):
    """Fetch two translations of the same chapter side by side."""
    v1 = request.args.get('v1', 'en-kjv')
    v2 = request.args.get('v2', 'en-web')

    book = get_book_by_slug(book_name) or get_book_by_name(book_name)
    if not book:
        return jsonify({'error': 'Book "%s" not found' % book_name}), 404
    if chapter < 1 or chapter > book['chapters']:
        return jsonify({'error': 'Chapter %d not valid for %s' % (chapter, book["name"])}), 404

    verses1, _ = fetch_chapter_bibleapi_smart(book['name'], chapter, v1)
    verses2, _ = fetch_chapter_bibleapi_smart(book['name'], chapter, v2)

    if not verses1 and not verses2:
        return jsonify({'error': 'Unable to load either version. Please try again.'}), 502

    return jsonify({
        'book': book['name'],
        'book_slug': book['slug'],
        'chapter': chapter,
        'total_chapters': book['chapters'],
        'versions': [
            {'id': v1, 'name': get_version_name(v1), 'verses': verses1},
            {'id': v2, 'name': get_version_name(v2), 'verses': verses2},
        ]
    })

@bp.route('/api/random-verse', methods=['GET'])
def api_random_verse():
    """Return a random verse from the Bible (fetched live, with curated fallback)."""
    version = request.args.get('version', 'en-kjv')

    # Try fetching a truly random verse from the live API first
    for _ in range(3):
        book = random.choice(BIBLE_BOOKS)
        chapter = random.randint(1, book['chapters'])
        try:
            verses, _ = fetch_chapter_bibleapi_smart(book['name'], chapter, version)
            if verses:
                v = random.choice(verses)
                return jsonify({
                    'reference': v['reference'],
                    'text': v['text'],
                    'book': book['name'],
                    'book_slug': book['slug'],
                    'chapter': chapter,
                    'verse': v['verse'],
                    'version': version,
                })
        except Exception as e:
            print(f"Random verse fetch error: {e}")

    # Fallback to the curated list
    v = random.choice(RANDOM_FALLBACK_VERSES)
    return jsonify({
        'reference': v['reference'],
        'text': v['text'],
        'book': '', 'book_slug': '', 'chapter': 0, 'verse': '',
        'version': 'en-kjv',
        'fallback': True,
    })

@bp.route('/api/commentary/<book_name>/<int:chapter>', methods=['GET'])
def api_commentary(book_name, chapter):
    """Return Matthew Henry's Concise Commentary for a chapter (bundled data, offline-capable)."""
    book = get_book_by_slug(book_name) or get_book_by_name(book_name)
    if not book:
        return jsonify({'error': 'Book "%s" not found' % book_name}), 404
    if chapter < 1 or chapter > book['chapters']:
        return jsonify({'error': 'Chapter %d not valid for %s' % (chapter, book["name"])}), 404

    commentary = get_commentary(book['slug'], chapter)
    if not commentary:
        return jsonify({
            'book': book['name'], 'chapter': chapter, 'available': False,
            'message': 'No commentary available for this chapter.'
        })
    return jsonify({
        'book': book['name'],
        'book_slug': book['slug'],
        'chapter': chapter,
        'available': True,
        'outline': commentary.get('outline', ''),
        'sections': commentary.get('sections', []),
        'source': "Matthew Henry's Concise Commentary (public domain)",
    })
