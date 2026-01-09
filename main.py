from flask import Flask, render_template, url_for, redirect, request, Response
from gtts import gTTS
from pydub import AudioSegment
from elevenlabs import generate, stream
import requests
import datetime as dt
import random
import time
import io
import os

app = Flask(__name__)

# List of inspirational verses for "Verse of the Day" (randomly picked)
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

# Correct list of Bible books with chapter counts
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
    {"id": "grc-grctr", "version": "Tischendorf Greek New Testament"},
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
    {"id": "cmn-Hans-CN-feb", "version": "Chinese Free Evangelical Bible"},
    {"id": "arb-kehm", "version": "Arabic Van Dyck (Modern)"},
    {"id": "ckb-okss", "version": "Central Kurdish Sorani Standard"},
    {"id": "ur-Deva-IN-irvurd", "version": "Indian Revised Version Urdu"},
    {"id": "urw-sobp15", "version": "Sobri Urdu Bible"},
    {"id": "hi-IN-irvhin", "version": "Indian Revised Version Hindi"},
    {"id": "hi-ohss", "version": "Open Hindi Standard Scripture"},
    {"id": "bn-irvben", "version": "Indian Revised Version Bengali"},
    {"id": "bn-obss", "version": "Open Bengali Standard Scripture"},
    {"id": "ta-irvtam", "version": "Indian Revised Version Tamil"},
    {"id": "ta-IN-otcv", "version": "Old Tamil Catholic Version"},
    {"id": "kn-irvkan", "version": "Indian Revised Version Kannada"},
    {"id": "kn-okcv", "version": "Old Kannada Catholic Version"},
    {"id": "ml-IN-irvmal", "version": "Indian Revised Version Malayalam"},
    {"id": "te-IN-irvtel", "version": "Indian Revised Version Telugu"},
    {"id": "gu-irvguj", "version": "Indian Revised Version Gujarati"},
    {"id": "pa-IN-irvpun", "version": "Indian Revised Version Punjabi"},
    {"id": "mr-irvmar", "version": "Indian Revised Version Marathi"},
    {"id": "as-irvasm", "version": "Indian Revised Version Assamese"},
    {"id": "ory-irvory", "version": "Indian Revised Version Oriya"},
    {"id": "th-kjv", "version": "Thai King James Version"},
    {"id": "id-tsi", "version": "Terjemahan Sederhana Indonesia"},
    {"id": "yo-oycb", "version": "Open Yoruba Contemporary Bible"},
    {"id": "ig-biuo", "version": "Bible in Igbo Union Version"},
    {"id": "ha-bsrk", "version": "Hausa Bible (BSRK)"},
    {"id": "sw-onen", "version": "Open Swahili New Testament"},
    {"id": "ln-smnb", "version": "Lingala Standard Modern New Bible"},
    {"id": "hu-neiv", "version": "New Hungarian Translation"},
    {"id": "fi-aeuut", "version": "Finnish Modern Translation"},
    {"id": "nb-oelb", "version": "Norwegian Bible"},
    {"id": "lg-olcb", "version": "Luganda Open Bible"},
    {"id": "ny-tccl", "version": "Chichewa Contemporary Language"},
    {"id": "ki-kgnk", "version": "Kikuyu Bible"},
    {"id": "luo-onlt", "version": "Luo Open New Living Translation"},
    {"id": "hr-okok", "version": "Croatian Bible"},
    {"id": "be-ббб", "version": "Belarusian Bible"},
    {"id": "sr-Latn-srp1865", "version": "Serbian Latin 1865"},
    {"id": "to-rwv", "version": "Tongan Revised Version"},
    {"id": "pes-opcb", "version": "Persian Old Persian Catholic Bible"}
]

@app.route("/")
def index():
    daily_verse = random.choice(DAILY_VERSES)
    return render_template("index.html",
                           current_year=dt.datetime.now().year,
                           daily_verse=daily_verse,
                           books=BIBLE_BOOKS)

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
        query = request.form.get("query").strip()
    elif request.method == "GET":
        query = request.args.get("query", "").strip()
    
    if query:
        try:
            # Search using the REST API Bible endpoint (KJV version)
            search_url = f"https://rest.api.bible/v1/bibles/9879dbb7cfe39e4d-01/search?query={query}"
            response = requests.get(search_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                search_results = []
                
                # Extract verses from search results
                if "data" in data and "verses" in data["data"]:
                    for verse in data["data"]["verses"]:
                        search_results.append({
                            "text": verse.get("text", ""),
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
                           search_results=search_results,
                           search_performed=search_performed,
                           query=query)

audio_cache = {}
@app.route("/books/<book_name>", methods=["GET", "POST"])
def books(book_name):
    book = next((b for b in BIBLE_BOOKS if b['name'].lower().replace(' ', '-') == book_name.lower()), None)
    if not book:
        return "Book not found", 404

    selected_chapter = request.form.get("chapter")
    selected_version = request.form.get("version", "en-kjv")  # Default
    verses = []
    chapter_text = ""

    if selected_chapter:
        selected_chapter = int(selected_chapter)
        url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/{selected_version}/books/{book_name.lower()}/chapters/{selected_chapter}.json"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                verses = data.get("data", [])
                chapter_text = " ".join([verse.get("text", "").strip() for verse in verses])
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



# @app.route("/audio/<book_name>/<int:chapter>")
# def chapter_audio(book_name, chapter):
#     selected_version = request.args.get("version", "en-kjv")
#     cache_key = f"{book_name}_{chapter}_{selected_version}"
#     if cache_key not in audio_cache:
#         url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/{selected_version}/books/{book_name.lower()}/chapters/{chapter}.json"
#         try:
#             response = requests.get(url)
#             if response.status_code != 200:
#                 return "Chapter not found", 404
#             data = response.json()
#             verses = data.get("data", [])
#             chapter_text = " ".join([verse.get("text", "").strip() for verse in verses])
#             if not chapter_text:
#                 return "Chapter not found", 404 
#             audio_bytes = generate(
#                 text=chapter_text,
#                 voice="Rachel",
#                 model="eleven_monolingual_v1",
#                 api_key=os.environ.get("ELEVENLABS_API_KEY")
#             )
#             audio_cache[cache_key] = audio_bytes
#             return Response(audio_bytes, mimetype="audio/mpeg")  
#         except Exception as e:
#             print(f"Error fetching chapter for audio: {e}")
#             return "Chapter not found", 404
#     return Response()

if __name__ == "__main__":
    app.run(debug=True)