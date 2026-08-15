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
