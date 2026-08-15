"""Public API surface - all content endpoints work without auth or API keys."""
import pytest

from app.bible.plans import READING_PLANS


def test_versions(client):
    data = client.get("/api/versions").get_json()
    assert data["total"] >= 10
    ids = [v["id"] for v in data["versions"]]
    assert "en-kjv" in ids
    assert "fr-ls1910" in ids  # French
    assert "yo-yoruba" in ids   # Yoruba


def test_books_filter(client):
    all_books = client.get("/api/books").get_json()
    assert all_books["total"] == 66
    old = client.get("/api/books?testament=old").get_json()
    assert old["total"] == 39
    new = client.get("/api/books?testament=new").get_json()
    assert new["total"] == 27


def test_reading_plans(client):
    data = client.get("/api/plans").get_json()
    ids = [p["id"] for p in data["plans"]]
    assert "bible-90" in ids and "proverbs-31" in ids
    assert len(ids) == len(READING_PLANS) >= 6
    detail = client.get("/api/plans/psalms-30").get_json()
    assert detail["total_days"] == 30
    assert detail["plan"][0]["day"] == 1


def test_topics(client):
    data = client.get("/api/topics").get_json()
    slugs = [t["slug"] for t in data["topics"]]
    assert len(slugs) >= 25
    assert "love" in slugs and "healing" in slugs
    topic = client.get("/api/topics/love").get_json()
    assert topic["title"] == "God's Love"
    assert topic["verses"][0]["reference"]
    assert client.get("/api/topics/nope").status_code == 404


def test_quiz(client):
    data = client.get("/api/quiz?limit=5").get_json()
    assert len(data["questions"]) == 5
    assert len(data["answer_key"]) == 5
    assert all(len(q["options"]) == 4 for q in data["questions"])
    by_cat = client.get("/api/quiz?limit=3&category=Life of Jesus").get_json()
    assert all(q["category"] == "Life of Jesus" for q in by_cat["questions"])


def test_commentary_is_bundled_and_offline(client):
    data = client.get("/api/commentary/john/3").get_json()
    assert data["available"] is True
    assert data["sections"], "John 3 should have commentary sections"
    assert client.get("/api/commentary/genesis/999").status_code == 404


def test_kjv_search_fallback_always_works(client):
    # No API key configured in tests -> results come from the bundled KJV index
    data = client.get("/api/search?q=shepherd").get_json()
    assert data["total"] > 0
    assert data["results"][0]["text"]
    # phrase search ranks the exact verse first
    phrase = client.get("/api/search?q=valley of the shadow of death").get_json()
    assert phrase["results"][0]["reference"] == "Psalms 23:4"


def test_daily_verse(client):
    data = client.get("/api/daily-verse").get_json()
    assert data["verse"]["reference"] == "John 3:16"  # seeded in conftest


def test_random_verse(client, monkeypatch):
    # Simulate the live fetch failing -> curated fallback kicks in.
    # Patch the name as imported into the reader blueprint.
    import app.routes.reader as reader

    monkeypatch.setattr(reader, "fetch_chapter_bibleapi_smart", lambda *a, **k: ([], ""))
    data = client.get("/api/random-verse").get_json()
    assert data.get("fallback") is True
    assert data["text"] and data["reference"]


def test_push_config_public(client):
    data = client.get("/api/push/config").get_json()
    assert "available" in data


def test_compare_bad_reference(client):
    assert client.get("/api/compare/notabook/1").status_code == 404


def test_auth_required_for_private_endpoints(client):
    assert client.get("/api/sync").status_code == 401
    assert client.post("/api/sync", json={}).status_code == 401
    assert client.get("/api/export").status_code == 401
    assert client.post("/api/clear-progress").status_code == 401
    assert client.get("/api/plans/psalms-30/progress").status_code == 401


def test_custom_plan_validation(client):
    # no books -> 400
    assert client.post("/api/plans/custom/build", json={"books": []}).status_code == 400
    # anonymous users can't manage a custom plan
    assert client.get("/api/plans/custom/whatever").status_code == 401
