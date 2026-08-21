"""Bundled Bible data: KJV search index, Matthew Henry commentary, Yoruba Bible.

All data is public-domain or openly licensed (see build_data.py) and lives in
static/data/*.json.gz. Loaded lazily into memory on first use.

Works fully offline and costs nothing - no API keys required.
"""
import gzip
import json
import os
import re

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "data")  # app/static/data

_cache = {}


def _load(name: str):
    if name not in _cache:
        path = os.path.join(_DATA_DIR, name)
        try:
            with gzip.open(path, "rb") as f:
                _cache[name] = json.loads(f.read().decode("utf-8"))
        except Exception as e:
            print(f"Bundled data error ({name}): {e}")
            _cache[name] = None
    return _cache[name]


# ---------------------------------------------------------------- KJV search

_kjv_index = None  # list of {"ref": "John 3:16", "low": "lowercased text", "text": ...}
_search_cache = {}  # query -> results (small LRU)


def get_kjv_books():
    data = _load("kjv.json.gz")
    return (data or {}).get("books", [])


def get_yoruba_books():
    data = _load("yoruba.json.gz")
    return (data or {}).get("books", [])


def _ensure_kjv_index():
    global _kjv_index
    if _kjv_index is not None:
        return _kjv_index
    _kjv_index = []
    for book in get_kjv_books():
        for ci, chapter in enumerate(book["chapters"], start=1):
            for vi, text in enumerate(chapter, start=1):
                if text:
                    _kjv_index.append({
                        "ref": f"{book['name']} {ci}:{vi}",
                        "low": text.lower(),
                        "text": text,
                    })
    return _kjv_index


def search_kjv(query: str, limit: int = 20) -> list:
    """Search the bundled KJV. Returns [{"reference", "text"}, ...] ranked by
    phrase match > all words > some words. No network, no API key."""
    q = re.sub(r"\s+", " ", query).strip().lower()
    if not q:
        return []
    cache_key = f"{q}|{limit}"
    if cache_key in _search_cache:
        return _search_cache[cache_key]

    index = _ensure_kjv_index()
    words = q.split()
    scored = []
    for entry in index:
        low = entry["low"]
        if q in low:
            score = 600 + max(0, 300 - len(low))  # phrase match, prefer shorter verses
        elif all(w in low for w in words):
            score = 400 + max(0, 200 - len(low))
        else:
            hits = sum(1 for w in words if w in low)
            if hits == 0:
                continue
            score = hits * 30 + max(0, 100 - len(low))
        scored.append((score, entry["ref"], entry["text"]))

    scored.sort(key=lambda x: -x[0])
    results = [{"reference": r, "text": t} for _, r, t in scored[:limit]]

    if len(_search_cache) > 50:
        _search_cache.pop(next(iter(_search_cache)))
    _search_cache[cache_key] = results
    return results


# ------------------------------------------------------------- Commentary

def get_commentary(book_slug: str, chapter: int):
    """Return {"outline": str, "sections": [{"title", "text"}]} or None."""
    data = _load("commentary.json.gz")
    if not data:
        return None
    books = data.get("books", {})
    chapters = books.get(book_slug)
    if not chapters:
        return None
    return chapters.get(str(chapter))


# ------------------------------------------------------------- Verse headings

def chapter_headings(book_slug: str, chapter: int):
    """Section headings for one chapter as {verse_number: heading_text}.

    Bundled from the Berean Standard Bible (public domain), see
    build_headings.py. Returns {} when the book/chapter has no headings.
    """
    try:
        chapter = int(chapter)
    except (TypeError, ValueError):
        return {}
    data = _load("headings.json.gz")
    if not data:
        return {}
    book = (data.get("books") or {}).get(book_slug) or {}
    raw = book.get(str(chapter)) or {}
    return {int(k): v for k, v in raw.items() if v}
