"""Chapter fetching across all translation sources.

Sources: API.Bible (premium), bible-api.com (public domain),
getbible.net v2 (French) and the bundled local data (Yoruba).
"""
import html
import re

import requests

import app.content as bundled
from app.bible.books import (
    API_BIBLE_BOOKS,
    API_BIBLE_VERSIONS,
    API_BIBLE_VERSIONS_SECONDARY,
    BIBLEAPI_TRANSLATIONS,
    BIBLE_BOOKS,
    GETBIBLE_TRANSLATIONS,
    get_version_source,
)
from app.config import Config
from app.utils import clean_text, dedupe_verses


def fetch_chapter_bibleapi(book_name: str, chapter: int, version_id: str = "en-kjv") -> tuple:
    """
    Fetch from bible-api.com (free, public domain)
    Most reliable fallback
    """
    translation = BIBLEAPI_TRANSLATIONS.get(version_id, "kjv")
    ref = f"{book_name}+{chapter}"
    url = f"{Config.BIBLE_API_BASE}/{ref}?translation={translation}"

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
    if not Config.API_BIBLE_KEY:
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
            Config.API_BIBLE_KEY,
            Config.API_BIBLE_BASE
        )

    if version_id in API_BIBLE_VERSIONS_SECONDARY:
        return (
            API_BIBLE_VERSIONS_SECONDARY[version_id],
            Config.API_BIBLE_SECONDARY_KEY,
            Config.API_BIBLE_SECONDARY_BASE
        )

    return None, None, None

def fetch_chapter_getbible(book_name: str, chapter: int, version_id: str) -> tuple:
    """Fetch from getbible.net v2 (free, no key). Used for French (Louis Segond 1910)."""
    translation = GETBIBLE_TRANSLATIONS.get(version_id)
    if not translation:
        return [], ""
    book_nr = next((i + 1 for i, b in enumerate(BIBLE_BOOKS) if b["name"] == book_name), None)
    if not book_nr:
        return [], ""

    url = f"https://api.getbible.net/v2/{translation}/{book_nr}/{chapter}.json"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"getbible error for {book_name} {chapter}: {resp.status_code}")
            return [], ""
        data = resp.json()
        raw_verses = data.get("verses", [])
        verses = []
        for v in raw_verses:
            text = clean_text(v.get("text", "").strip())
            verse_num = str(v.get("verse", ""))
            verses.append({
                "verse": verse_num,
                "reference": f"{book_name} {chapter}:{verse_num}",
                "text": text,
            })
        verses = dedupe_verses(verses)
        chapter_text = " ".join(v["text"] for v in verses)
        print(f"✅ Fetched from getbible.net: {book_name} {chapter} ({len(verses)} verses)")
        return verses, chapter_text
    except Exception as e:
        print(f"getbible error: {e}")
        return [], ""

def fetch_chapter_local(book_name: str, chapter: int, data_source: str = "yoruba") -> tuple:
    """Fetch from the bundled data files (works offline, no API). Used for Yoruba."""
    books = bundled.get_yoruba_books() if data_source == "yoruba" else []
    book = next((b for b in books if b["name"] == book_name), None)
    if not book or chapter < 1 or chapter > len(book["chapters"]):
        return [], ""
    raw = book["chapters"][chapter - 1]
    verses = []
    for vi, text in enumerate(raw, start=1):
        if text:
            verses.append({
                "verse": str(vi),
                "reference": f"{book_name} {chapter}:{vi}",
                "text": clean_text(text),
            })
    chapter_text = " ".join(v["text"] for v in verses)
    return verses, chapter_text

def fetch_chapter_bibleapi_smart(book_name: str, chapter: int, version_id: str) -> tuple:
    """
    Smart fetcher with fallback logic.
    API.Bible is tried first for versions mapped to it; getbible.net and the
    bundled local data are used for their versions; everything else falls
    back to Bible-API.com.
    """
    source = get_version_source(version_id)

    if source in ("api_bible", "api_bible_secondary"):
        verses, text = fetch_chapter_apibible(book_name, chapter, version_id)
        if verses:
            return verses, text
        print("API.Bible failed, falling back to Bible API")
        return fetch_chapter_bibleapi(book_name, chapter, version_id)

    if source == "getbible":
        return fetch_chapter_getbible(book_name, chapter, version_id)

    if source == "local":
        return fetch_chapter_local(book_name, chapter)

    return fetch_chapter_bibleapi(book_name, chapter, version_id)

RANDOM_FALLBACK_VERSES = [
    {"reference": "Jeremiah 29:11", "text": "For I know the thoughts that I think toward you, saith the LORD, thoughts of peace, and not of evil, to give you an expected end."},
    {"reference": "Psalm 46:10", "text": "Be still, and know that I am God: I will be exalted among the heathen, I will be exalted in the earth."},
    {"reference": "Romans 8:28", "text": "And we know that all things work together for good to them that love God, to them who are the called according to his purpose."},
    {"reference": "Joshua 1:9", "text": "Have not I commanded thee? Be strong and of a good courage; be not afraid, neither be thou dismayed: for the LORD thy God is with thee whithersoever thou goest."},
    {"reference": "Psalm 118:24", "text": "This is the day which the LORD hath made; we will rejoice and be glad in it."},
    {"reference": "Proverbs 16:3", "text": "Commit thy works unto the LORD, and thy thoughts shall be established."},
    {"reference": "Isaiah 40:31", "text": "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint."},
    {"reference": "Matthew 5:16", "text": "Let your light so shine before men, that they may see your good works, and glorify your Father which is in heaven."},
    {"reference": "Galatians 5:22-23", "text": "But the fruit of the Spirit is love, joy, peace, longsuffering, gentleness, goodness, faith, Meekness, temperance: against such there is no law."},
    {"reference": "Psalm 34:8", "text": "O taste and see that the LORD is good: blessed is the man that trusteth in him."},
    {"reference": "Numbers 6:24", "text": "The LORD bless thee, and keep thee:"},
    {"reference": "Zephaniah 3:17", "text": "The LORD thy God in the midst of thee is mighty; he will save, he will rejoice over thee with joy; he will rest in his love, he will joy over thee with singing."},
    {"reference": "Psalm 37:4", "text": "Delight thyself also in the LORD; and he shall give thee the desires of thine heart."},
    {"reference": "Isaiah 26:3", "text": "Thou wilt keep him in perfect peace, whose mind is stayed on thee: because he trusteth in thee."},
    {"reference": "Micah 6:8", "text": "He hath shewed thee, O man, what is good; and what doth the LORD require of thee, but to do justly, and to love mercy, and to walk humbly with thy God?"},
    {"reference": "Psalm 121:1-2", "text": "I will lift up mine eyes unto the hills, from whence cometh my help. My help cometh from the LORD, which made heaven and earth."},
    {"reference": "Colossians 3:23", "text": "And whatsoever ye do, do it heartily, as to the Lord, and not unto men;"},
    {"reference": "Psalm 19:14", "text": "Let the words of my mouth, and the meditation of my heart, be acceptable in thy sight, O LORD, my strength, and my redeemer."},
    {"reference": "1 Peter 5:7", "text": "Casting all your care upon him; for he careth for you."},
    {"reference": "Psalm 27:1", "text": "The LORD is my light and my salvation; whom shall I fear? the LORD is the strength of my life; of whom shall I be afraid?"},
]
