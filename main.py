from flask import Flask, render_template, url_for, redirect, request, jsonify, send_file
import requests
import datetime as dt
import random
import os
import io
import tempfile
import shutil
import re
import smtplib
import ssl
import socket
import asyncio
from email.message import EmailMessage
from email.utils import formataddr
from typing import List

from dotenv import load_dotenv

load_dotenv()

# Import edge-tts for audio generation
try:
    import edge_tts
    _EDGE_TTS_AVAILABLE = True
except Exception as e:
    print(f"Edge-TTS not available: {e}")
    _EDGE_TTS_AVAILABLE = False

app = Flask(__name__)

def split_text_intelligently(text: str, max_length: int) -> List[str]:
    """
    Split text at sentence boundaries to avoid awkward cuts
    Perfect for long chapters like Psalm 119
    """
    if len(text) <= max_length:
        return [text]
    
    # Replace sentence endings with a marker
    for delimiter in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
        text = text.replace(delimiter, delimiter.strip() + '|||SPLIT|||')
    
    parts = [p.strip() for p in text.split('|||SPLIT|||') if p.strip()]
    
    chunks = []
    current = ""
    
    for part in parts:
        # Add the sentence ending back if missing
        if part and not part[-1] in '.!?':
            part += '.'
        
        if len(current) + len(part) + 1 <= max_length:
            current += (" " + part) if current else part
        else:
            if current:
                chunks.append(current.strip())
            current = part
    
    if current:
        chunks.append(current.strip())
    
    return chunks if chunks else [text]


def generate_audio_edge_tts(text: str, output_path: str, voice: str = "en-US-AriaNeural") -> bool:
    """
    Generate audio using Edge TTS with proper async handling
    Handles both short verses and long chapters (Psalm 119)
    THIS WILL WORK ON RENDER!
    """
    if not _EDGE_TTS_AVAILABLE:
        print("Edge-TTS is not available. Please install it: pip install edge-tts")
        return False
    
    if not text or not text.strip():
        print("Error: Empty text provided")
        return False
    
    try:
        MAX_LENGTH = 5000  # Edge-TTS can handle long texts
        
        if len(text) <= MAX_LENGTH:
            # Single chunk - process directly
            print(f"Generating audio for text ({len(text)} characters)")
            
            async def generate_single():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_path)
            
            # Create new event loop for Flask (critical for proper async handling)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(generate_single())
            finally:
                loop.close()
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"Audio generated successfully: {output_path} ({file_size} bytes)")
                return True
            else:
                print("Error: Audio file was not created")
                return False
        
        else:
            # Multiple chunks - process and combine
            chunks = split_text_intelligently(text, MAX_LENGTH)
            print(f"Split text into {len(chunks)} chunks for audio generation")
            
            temp_dir = tempfile.mkdtemp(prefix='edge_tts_')
            chunk_files = []
            
            try:
                async def generate_chunks():
                    for i, chunk in enumerate(chunks):
                        chunk_path = os.path.join(temp_dir, f"chunk_{i}.mp3")
                        communicate = edge_tts.Communicate(chunk, voice)
                        await communicate.save(chunk_path)
                        chunk_files.append(chunk_path)
                        print(f"Generated chunk {i+1}/{len(chunks)}")
                
                # Run async generation with proper event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(generate_chunks())
                finally:
                    loop.close()
                
                # Concatenate MP3 files (binary concatenation works perfectly for MP3)
                with open(output_path, 'wb') as outfile:
                    for chunk_file in chunk_files:
                        with open(chunk_file, 'rb') as infile:
                            outfile.write(infile.read())
                
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"Successfully combined {len(chunks)} chunks into {output_path} ({file_size} bytes)")
                    return True
                else:
                    print("Error: Combined audio file was not created")
                    return False
                
            finally:
                # Cleanup temporary chunk files
                for f in chunk_files:
                    if os.path.exists(f):
                        try:
                            os.remove(f)
                        except Exception as e:
                            print(f"Could not remove temp file {f}: {e}")
                try:
                    os.rmdir(temp_dir)
                except Exception as e:
                    print(f"Could not remove temp dir {temp_dir}: {e}")
    
    except Exception as e:
        print(f"Edge-TTS error: {e}")
        import traceback
        traceback.print_exc()
        return False

DAILY_VERSES = [
    {
        "text": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.",
        "reference": "John 3:16"
    },
    {
        "text": "The Lord is my shepherd; I shall not want.",
        "reference": "Psalm 23:1"
    },
    {
        "text": "I can do all this through him who gives me strength.",
        "reference": "Philippians 4:13"
    },
    {
        "text": "In the beginning God created the heavens and the earth.",
        "reference": "Genesis 1:1"
    },
    {
        "text": "Trust in the Lord with all your heart and lean not on your own understanding.",
        "reference": "Proverbs 3:5"
    },
    {
        "text": "Be still, and know that I am God.",
        "reference": "Psalm 46:10"
    },
    {
        "text": "The joy of the Lord is your strength.",
        "reference": "Nehemiah 8:10"
    },
    {
        "text": "Love your neighbor as yourself.",
        "reference": "Matthew 22:39"
    },
    {
        "text": "Do not be anxious about anything, but in every situation, by prayer and petition, with thanksgiving, present your requests to God.",
        "reference": "Philippians 4:6"
    },
    {
        "text": "I have come that they may have life, and have it to the full.",
        "reference": "John 10:10"
    },
    {
        "text": "This is the day the Lord has made; let us rejoice and be glad in it.",
        "reference": "Psalm 118:24"
    },
    {
        "text": "The Lord is my light and my salvation—whom shall I fear?",
        "reference": "Psalm 27:1"
    },
    {
        "text": "Cast all your anxiety on him because he cares for you.",
        "reference": "1 Peter 5:7"
    },
    {
        "text": "For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future.",
        "reference": "Jeremiah 29:11"
    },
    {
        "text": "Peace I leave with you; my peace I give you.",
        "reference": "John 14:27"
    },
    {
        "text": "And we know that in all things God works for the good of those who love him.",
        "reference": "Romans 8:28"
    },
    {
        "text": "The name of the Lord is a strong tower; the righteous run to it and are safe.",
        "reference": "Proverbs 18:10"
    },
    {
        "text": "Let everything that has breath praise the Lord.",
        "reference": "Psalm 150:6"
    },
    {
        "text": "Blessed are the peacemakers, for they will be called children of God.",
        "reference": "Matthew 5:9"
    },
    {
        "text": "Your word is a lamp for my feet, a light on my path.",
        "reference": "Psalm 119:105"
    },
    {
        "text": "Give thanks to the Lord, for he is good; his love endures forever.",
        "reference": "Psalm 107:1"
    },
    {
        "text": "The Lord bless you and keep you; the Lord make his face shine on you and be gracious to you.",
        "reference": "Numbers 6:24-25"
    },
    {
        "text": "Come to me, all you who are weary and burdened, and I will give you rest.",
        "reference": "Matthew 11:28"
    },
    {
        "text": "Great is his faithfulness; his mercies begin afresh each morning.",
        "reference": "Lamentations 3:23"
    },
    {
        "text": "But those who hope in the Lord will renew their strength. They will soar on wings like eagles.",
        "reference": "Isaiah 40:31"
    }
]

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
    {"name": "Revelation", "chapters": 22}
]

VERSION_LIST = [
    {"id": "en-kjv", "version": "King James Version (KJV)"},
    {"id": "en-web", "version": "World English Bible (WEB)"},
    {"id": "en-asv", "version": "American Standard Version (ASV)"},
    {"id": "en-t4t", "version": "Thoughts for Today (Modern English)"},
    {"id": "en-bsb", "version": "Berean Standard Bible (BSB)"},
    {"id": "en-lsv", "version": "Literal Standard Version (LSV)"},
    {"id": "en-dra", "version": "Douay-Rheims American Edition (DRA)"},
    {"id": "en-rv", "version": "Revised Version (RV)"},
    {"id": "en-fbv", "version": "Free Bible Version (FBV)"},
    {"id": "es-rv09", "version": "Reina-Valera 1909 (Spanish)"},
    {"id": "es-bes", "version": "Biblia del Siglo de Oro (Spanish)"},
    {"id": "es-pddpt", "version": "Palabra de Dios para Ti (Spanish)"},
    {"id": "es-vbl", "version": "Versión Biblia Libre (Spanish)"},
    {"id": "de-luther1912", "version": "Luther Bible 1912 (German)"},
    {"id": "de-elo", "version": "Elberfelder Bible (German)"},
    {"id": "pt-BR-blt", "version": "Bíblia Livre Tradução (Portuguese)"},
    {"id": "pt-tftp", "version": "Tradução Fiel do Texto Original Português (Portuguese)"},
    {"id": "nl-nld1939", "version": "Dutch Statenvertaling 1939"},
    {"id": "pl-ubg", "version": "Updated Gdańsk Bible (Polish)"},
    {"id": "pl-opsz", "version": "Ogólnopolska Biblia Szwedzka (Polish)"},
    {"id": "cs-bkr", "version": "Bible Kralická (Czech)"},
    {"id": "cs-osnc", "version": "Czech Ecumenical Translation"},
    {"id": "it-db1885", "version": "Diodati Bible 1885 (Italian)"},
    {"id": "vi-ovcb", "version": "Old Vietnamese Catholic Bible"},
    {"id": "vi-vie", "version": "Vietnamese Bible"},
    {"id": "he-wlc", "version": "Westminster Leningrad Codex (Hebrew Old Testament)"},
    {"id": "hbo-wlc", "version": "Ancient Hebrew (WLC)"},
    {"id": "he-hdzp", "version": "Hebrew Modern Translation"},
    {"id": "grc-grcbrent", "version": "Brenton Septuagint (Greek Old Testament)"},
    {"id": "grc-srgnt", "version": "SBL Greek New Testament"},
    {"id": "grc-byz1904", "version": "Byzantine Greek New Testament 1904"},
    {"id": "grc-tcgnt", "version": "Textus Receptus Greek New Testament"},
    {"id": "grc-tischendorf", "version": "Tischendorf Greek New Testament"},
    {"id": "grc-f35", "version": "Family 35 Greek New Testament"},
    {"id": "en-engbrent", "version": "Brenton English Septuagint"},
    {"id": "en-US-lxxup", "version": "Lexham English Septuagint"},
    {"id": "en-ojps", "version": "1917 JPS Tanakh (English)"},
    {"id": "en-gnv", "version": "Geneva Bible (GNV)"},
    {"id": "en-oke", "version": "Orthodox KJV Edition"},
    {"id": "en-wmb", "version": "World Messianic Bible"},
    {"id": "en-wmbbe", "version": "World Messianic Bible British Edition"},
    {"id": "en-tcent", "version": "Tree of Life Version (TLV)"},
    {"id": "en-US-asvbt", "version": "American Standard Version (Brenton)"},
    {"id": "en-US-emtv", "version": "English Majority Text Version"},
    {"id": "en-US-f35", "version": "Family 35 English New Testament"},
    {"id": "en-US-kjvcpb", "version": "KJV Cambridge Paragraph Bible"},
]

def clean_text(text: str) -> str:
    """Clean verse text from API using regex"""
    if not text:
        return text

    text = re.sub(r'\b\d+\.\d+\b', '', text)
    text = re.sub(r'\b(Heb|Gr|Lat)\.\s*[^.;]*', '', text)
    text = re.sub(r'\bor,\s*[^.;]*', '', text)
    text = re.sub(r'\(.*?\)|\[.*?\]', '', text)
    text = text.replace('…', '')
    text = re.sub(r'\s+([.,;:])', r'\1', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+[.;:]', '', text)
    text = re.sub(r'[\u200B-\u200F\uFEFF]', '', text)
    text = re.sub(r'&[#A-Za-z0-9]+;', ' ', text)
    text = re.sub(r"\[.*?\]|\{.*?\}|<.*?>", ' ', text)
    text = re.sub(r'(?<=\w)[^\w\s]+(?=\w)', ' ', text)
    text = re.sub(r"[^\w\s\.\,\?\!\;\:\'\-]", ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    dot_pos = text.find('.')
    if dot_pos != -1:
        text = text[: dot_pos + 1 ].strip()
    else:
        colon_pos = text.find(':')
        semi_pos = text.find(';')
        candidates = [p for p in (colon_pos, semi_pos) if p != -1]
        if candidates:
            pos = min(candidates)
            text = text[: pos + 1 ].strip()

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


def _sanitize_header_value(value: str) -> str:
    if not value:
        return ''
    return value.replace('\r', '').replace('\n', '').strip()


def _send_contact_email(sender_name: str, sender_email: str, subject: str, message: str):
    mail_host = os.environ.get('MAIL_HOST')
    mail_port = int(os.environ.get('MAIL_PORT', 587))
    mail_user = os.environ.get('MAIL_USERNAME') 
    mail_pass = os.environ.get('MAIL_PASSWORD')
    mail_to = os.environ.get('MAIL_TO') 
    use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('1', 'true', 'yes')
    use_ssl = os.environ.get('MAIL_USE_SSL', 'false').lower() in ('1', 'true', 'yes')

    if not mail_user or not mail_pass:
        return False, 'Email sending is not configured. Set MAIL_USERNAME and MAIL_PASSWORD in the environment.'

    safe_name = _sanitize_header_value(sender_name)
    safe_email = _sanitize_header_value(sender_email)
    safe_subject = _sanitize_header_value(subject) or 'New contact message'

    msg = EmailMessage()
    msg['Subject'] = f"[MyPersonalBibleApp] {safe_subject}"
    msg['From'] = formataddr((safe_name or 'Contact Form', mail_user))
    msg['To'] = mail_to
    if safe_email:
        msg['Reply-To'] = safe_email

    body = f"""Name: {safe_name or '(not provided)'}
Email: {safe_email or '(not provided)'}
Subject: {safe_subject}

Message:
{message}
"""
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
            hint = ' (timeout; check that your server can reach the SMTP host and port, and that outbound SMTP is allowed)' 
        elif isinstance(e, ssl.SSLError) or 'handshake' in msg_err:
            hint = ' (SSL/TLS handshake failed; verify port/SSL settings and that the SMTP host supports the chosen SSL/TLS mode)' 
        elif isinstance(e, smtplib.SMTPAuthenticationError):
            hint = ' (authentication failed; check username/password or use an app password if using Gmail with 2FA)' 

        return False, f'Failed to send email{hint}'

@app.route("/")
def index():
    daily_verse = random.choice(DAILY_VERSES)
    return render_template("index.html",
                           current_year=dt.datetime.now().year,
                           daily_verse=daily_verse,
                           books=BIBLE_BOOKS,
                           versions=VERSION_LIST)


@app.route("/search", methods=["GET", "POST"])
def search():
    api_key = os.environ.get("API_KEY")
    headers = {
        "api-key": api_key
    }
    
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
    
    daily_verse = random.choice(DAILY_VERSES)

    return render_template("index.html",
                           current_year=dt.datetime.now().year,
                           daily_verse=daily_verse,
                           books=BIBLE_BOOKS,
                           versions=VERSION_LIST,
                           search_results=search_results,
                           search_performed=search_performed,
                           query=query)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form_data = {
        'name': '',
        'email': '',
        'subject': '',
        'message': ''
    }
    status_message = None
    status_type = 'info'

    if request.method == 'POST':
        form_data['name'] = request.form.get('name', '').strip()
        form_data['email'] = request.form.get('email', '').strip()
        form_data['subject'] = request.form.get('subject', '').strip()
        form_data['message'] = request.form.get('message', '').strip()

        if not form_data['email'] or not form_data['message']:
            status_type = 'warning'
            status_message = 'Please provide both your email address and a message.'
        else:
            success, msg = _send_contact_email(
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
        form_data=form_data
    )


@app.route("/books/<book_name>", methods=["GET", "POST"])
def books(book_name):
    book = next((b for b in BIBLE_BOOKS if b['name'].lower().replace(' ', '-') == book_name.lower()), None)
    if not book:
        return "Book not found", 404

    selected_chapter = request.form.get("chapter")
    selected_version = request.form.get("version", "en-kjv")
    verses = []
    chapter_text = ""

    if selected_chapter:
        selected_chapter = int(selected_chapter)
        url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/{selected_version}/books/{book_name.lower()}/chapters/{selected_chapter}.json"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                raw_verses = data.get("data", [])
                raw_verses = dedupe_verses(raw_verses)
                verses = [{**v, 'text': clean_text(v.get('text', ''))} for v in raw_verses]
                chapter_text = " ".join([v.get("text", "").strip() for v in verses])
            else:
                verses = []
                chapter_text = ""
        except Exception as e:
            print(f"Error fetching chapter: {e}")
            verses = []
            chapter_text = ""

    return render_template("books.html",
                           current_year=dt.datetime.now().year,
                           book=book,
                           selected_chapter=selected_chapter,
                           selected_version=selected_version,
                           chapter_text=chapter_text,
                           verses=verses,
                           versions=VERSION_LIST) 


@app.route('/api/chapter/<book_name>/<int:chapter>')
def api_chapter(book_name, chapter):
    selected_version = request.args.get('version', 'en-kjv')
    url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/{selected_version}/books/{book_name.lower()}/chapters/{chapter}.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return jsonify({'error': 'Chapter not found'}), 404
        data = response.json()
        raw_verses = data.get('data', [])
        raw_verses = dedupe_verses(raw_verses)
        verses = [{**v, 'text': clean_text(v.get('text', ''))} for v in raw_verses]
        chapter_text = ' '.join([v.get('text', '').strip() for v in verses])
        return jsonify({
            'book': book_name,
            'chapter': chapter,
            'version': selected_version,
            'chapter_text': chapter_text,
            'verses': verses
        })
    except Exception as e:
        print(f"API chapter fetch failed: {e}")
        return jsonify({'error': 'Request failed'}), 500

@app.route('/download/chapter/<book_name>/<int:chapter>')
def download_chapter(book_name, chapter):
    """
    Download complete chapter audio using Edge-TTS
    Works perfectly on Render - handles long chapters like Psalm 119!
    """
    if not _EDGE_TTS_AVAILABLE:
        return jsonify({
            'error': 'Audio generation not available',
            'details': 'edge-tts is not installed. Please install it: pip install edge-tts'
        }), 501
    
    selected_version = request.args.get('version', 'en-kjv')
    voice = request.args.get('voice', 'en-US-AriaNeural')
    
    url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/{selected_version}/books/{book_name.lower()}/chapters/{chapter}.json"
    
    try:
        # Fetch chapter data
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return jsonify({'error': 'Chapter not found'}), 404
        
        data = response.json()
        raw_verses = data.get('data', [])
        raw_verses = dedupe_verses(raw_verses)
        verses = [{**v, 'text': clean_text(v.get('text', ''))} for v in raw_verses]
        chapter_text = ' '.join([v.get('text', '').strip() for v in verses])
        
        if not chapter_text:
            return jsonify({'error': 'No text available for this chapter'}), 404
        
        print(f"Generating audio for {book_name} {chapter} ({len(chapter_text)} characters)")
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix='bible_audio_')
        
        try:
            filename_base = f"{book_name.title().replace('-', '').replace(' ', '')}{chapter}"
            output_path = os.path.join(temp_dir, f"{filename_base}.mp3")
            
            # Generate audio using Edge-TTS
            success = generate_audio_edge_tts(chapter_text, output_path, voice)
            
            if success and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"Audio file generated successfully: {output_path} ({file_size} bytes)")
                
                return send_file(
                    output_path,
                    download_name=f"{filename_base}.mp3",
                    mimetype='audio/mpeg',
                    as_attachment=True
                )
            else:
                error_msg = f"Failed to generate audio. Success: {success}, File exists: {os.path.exists(output_path)}"
                print(error_msg)
                return jsonify({'error': error_msg}), 500
                
        finally:
            # Cleanup temp directory after a delay
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Cleanup failed: {e}")
                
    except Exception as e:
        print(f"Chapter download failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500


@app.route('/download/verse/<book_name>/<int:chapter>')
def download_verse_range(book_name, chapter):
    """
    Download verse range audio using Edge-TTS
    Works on Render with no system dependencies!
    """
    if not _EDGE_TTS_AVAILABLE:
        return jsonify({
            'error': 'Audio generation not available',
            'details': 'edge-tts is not installed. Please install it: pip install edge-tts'
        }), 501
    
    start = request.args.get('start')
    end = request.args.get('end', start)
    selected_version = request.args.get('version', 'en-kjv')
    voice = request.args.get('voice', 'en-US-AriaNeural')

    try:
        start_n = int(start)
        end_n = int(end or start)
    except Exception:
        return jsonify({'error': 'Invalid verse range parameters.'}), 400

    if start_n < 1 or end_n < start_n:
        return jsonify({'error': 'Invalid verse range values.'}), 400

    url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/{selected_version}/books/{book_name.lower()}/chapters/{chapter}.json"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return jsonify({'error': 'Chapter not found'}), 404
        
        data = response.json()
        raw_verses = data.get('data', [])
        raw_verses = dedupe_verses(raw_verses)
        verses = [{**v, 'text': clean_text(v.get('text', ''))} for v in raw_verses]

        # Filter verses in the requested range
        filtered = []
        for v in verses:
            try:
                num = int(v.get('verse') or 0)
            except Exception:
                num = 0
            if num >= start_n and num <= end_n:
                filtered.append(v)

        if not filtered:
            return jsonify({'error': 'No verses found for that range.'}), 404

        text = ' '.join([v.get('text', '').strip() for v in filtered])
        
        print(f"Generating audio for {book_name} {chapter}:{start_n}-{end_n} ({len(text)} characters)")
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix='bible_audio_')
        
        try:
            filename_base = f"{book_name.title().replace('-', '').replace(' ', '')}{chapter}_{start_n}-{end_n}"
            output_path = os.path.join(temp_dir, f"{filename_base}.mp3")
            
            # Generate audio using Edge-TTS
            success = generate_audio_edge_tts(text, output_path, voice)
            
            if success and os.path.exists(output_path):
                print(f"Audio file generated successfully: {output_path}")
                
                return send_file(
                    output_path,
                    download_name=f"{filename_base}.mp3",
                    mimetype='audio/mpeg',
                    as_attachment=True
                )
            else:
                return jsonify({'error': 'Failed to generate audio'}), 500
                
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Cleanup failed: {e}")
                
    except Exception as e:
        print(f"Verse range download failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500


if __name__ == "__main__":
    app.run(debug=True)