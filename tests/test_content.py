"""Bundled content integrity + KJV search ranking."""
from app.content import get_commentary, get_kjv_books, get_yoruba_books, search_kjv


def test_kjv_bundle_complete():
    books = get_kjv_books()
    assert len(books) == 66
    assert sum(len(b["chapters"]) for b in books) == 1189
    john = next(b for b in books if b["slug"] == "john")
    assert "For God so loved the world" in john["chapters"][2][15]


def test_yoruba_bundle_complete():
    books = get_yoruba_books()
    assert len(books) == 66
    john = next(b for b in books if b["slug"] == "john")
    assert "Nítorí" in john["chapters"][2][15]


def test_commentary_coverage():
    assert get_commentary("john", 3) is not None
    assert get_commentary("genesis", 1)["sections"]
    # 2 John exists but has a single chapter with commentary
    assert get_commentary("2-john", 1) is not None
    # invalid book returns None gracefully
    assert get_commentary("notabook", 1) is None


def test_search_ranking_phrase_first():
    results = search_kjv("valley of the shadow of death")
    assert results[0]["reference"] == "Psalms 23:4"


def test_search_ranking_phrase_beats_keywords():
    phrase = search_kjv("the LORD is my shepherd")
    keywords = search_kjv("LORD shepherd")
    assert phrase[0]["reference"] == "Psalms 23:1"
    # phrase matches should rank the exact verse first
    assert any(r["reference"] == "Psalms 23:1" for r in keywords)


def test_search_limit_and_empty():
    assert len(search_kjv("love", limit=5)) == 5
    assert search_kjv("") == []
    assert search_kjv("zzzqqqnotaword") == []


def test_verse_headings_bundled():
    """Section headings (public-domain BSB) load per book/chapter."""
    from app.content import chapter_headings

    heb10 = chapter_headings("hebrews", 10)
    assert heb10.get(1) == "Christ’s Perfect Sacrifice", heb10
    assert heb10.get(19) == "A Call to Persevere", heb10

    gen1 = chapter_headings("genesis", 1)
    assert gen1.get(1) == "The Creation"
    assert gen1.get(3) == "The First Day"

    ps23 = chapter_headings("psalms", 23)
    assert ps23.get(1) == "The LORD Is My Shepherd"

    # chapters without headings / unknown books return empty
    assert chapter_headings("obadiah", 99) == {}
    assert chapter_headings("nope", 1) == {}


def test_reader_renders_headings_for_any_version(client):
    """The reader shows section headings regardless of the selected version."""
    # KJV (a version with no headings of its own)
    r = client.post("/books/hebrews", data={"chapter": "10", "version": "en-kjv"})
    body = r.get_data(as_text=True)
    assert r.status_code == 200
    assert 'class="col-12 verse-heading"' in body
    assert "A Call to Persevere" in body
    assert "Christ’s Perfect Sacrifice" in body
    # the heading precedes verse 19 and never sits inside a verse item
    assert body.find("A Call to Persevere") < body.find('id="verse-19"')
    # a chapter without headings renders normally
    r2 = client.post("/books/obadiah", data={"chapter": "1", "version": "en-kjv"})
    assert r2.status_code == 200


def test_bundled_kjv_fallback_complete(client):
    """The bundled KJV serves full chapters (used when the API returns partial data)."""
    from app.bible.verses import fetch_chapter_local

    verses, text = fetch_chapter_local("Obadiah", 1, "kjv")
    assert len(verses) == 21, len(verses)
    assert "The vision of Obadiah" in text
    verses2, _ = fetch_chapter_local("Obadiah", 1, "yoruba")
    assert len(verses2) == 21


def test_headings_english_only(client):
    """Headings render for English versions and stay hidden for other languages."""
    from app.routes.reader import version_uses_headings

    assert version_uses_headings("en-kjv") is True
    assert version_uses_headings("en-web") is True
    assert version_uses_headings("fr-ls1910") is False
    assert version_uses_headings("ro-rccv") is False
    assert version_uses_headings("yo-yoruba") is False
    assert version_uses_headings(None) is False

    # Yoruba uses the bundled local data, so this render is fully offline-safe:
    # the page must NOT contain English heading blocks or the credit line.
    r = client.post("/books/hebrews", data={"chapter": "10", "version": "yo-yoruba"})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert 'class="col-12 verse-heading"' not in body
    assert "Berean Standard Bible" not in body
    assert "A Call to Persevere" not in body

    # Français and Română are fetched from remote APIs; even if the fetch
    # fails, the page must never inject English headings for them.
    for v in ("fr-ls1910", "ro-rccv"):
        r2 = client.post("/books/hebrews", data={"chapter": "10", "version": v})
        assert r2.status_code == 200
        assert 'class="col-12 verse-heading"' not in r2.get_data(as_text=True)

    # the English page keeps them
    r3 = client.post("/books/hebrews", data={"chapter": "10", "version": "en-kjv"})
    body3 = r3.get_data(as_text=True)
    assert "A Call to Persevere" in body3
