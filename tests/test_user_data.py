"""Authenticated flows: sync, custom plans, bible-in-a-year, quiz stats, export."""
import datetime as dt


def _today():
    return dt.date.today().isoformat()


def test_sync_round_trip(auth_client):
    payload = {
        "bookmarks": [{"id": 1, "reference": "John 3:16", "text": "For God so loved...",
                       "timestamp": f"{_today()}T10:00:00"}],
        "highlights": {"John_3": ["16"]},
        "highlightColors": {"John_3": {"16": "yellow"}},
        "highlightLabels": {"John_3": {"16": {"label": "memorize", "text": "For God so loved...",
                                             "updated_at": f"{_today()}T10:00:00"}}},
        "memoryState": {"John 3:16": {"box": 1, "due": _today(), "last": f"{_today()}T10:00:00"}},
        "notes": [{"id": "n1", "reference": "John 3:16", "text": "The gospel in a nutshell",
                   "created_at": f"{_today()}T10:00:00", "updated_at": f"{_today()}T10:00:00"}],
        "readingLog": [_today()],
        "font_size": 1.4,
        "theme": "dark",
    }
    assert auth_client.post("/api/sync", json=payload).status_code == 200

    data = auth_client.get("/api/sync").get_json()
    assert data["bookmarks"][0]["reference"] == "John 3:16"
    assert data["highlightLabels"]["John_3"]["16"]["label"] == "memorize"
    assert data["memoryState"]["John 3:16"]["box"] == 1
    assert data["notes"][0]["text"] == "The gospel in a nutshell"
    assert data["streak"]["total_days_read"] == 1


def test_merge_keeps_newest_and_unions(auth_client):
    from app.services.storage import load_user_sync_data, merge_sync_data

    server = {
        "notes": [{"id": "n1", "reference": "John 3:16", "text": "server version",
                   "created_at": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"}],
        "plans": {"psalms-30": {"start_date": "2026-01-01", "completed_days": [1, 2]}},
    }
    local = {
        "notes": [{"id": "n1", "reference": "John 3:16", "text": "local edit wins",
                   "created_at": "2026-01-01T00:00:00", "updated_at": "2026-02-01T00:00:00"},
                  {"id": "n2", "reference": "Psalm 23:1", "text": "local only",
                   "created_at": "2026-02-01T00:00:00", "updated_at": "2026-02-01T00:00:00"}],
        "plans": {"psalms-30": {"start_date": "2026-01-01", "completed_days": [1, 2, 3]}},
    }
    merged = merge_sync_data(local, server)
    notes = {n["id"]: n for n in merged["notes"]}
    assert notes["n1"]["text"] == "local edit wins"  # newest timestamp wins
    assert "n2" in notes                                # union of both copies
    assert merged["plans"]["psalms-30"]["completed_days"] == [1, 2, 3]  # union


def test_custom_plan_lifecycle(auth_client):
    # build
    response = auth_client.post("/api/plans/custom/build", json={
        "title": "Genesis + John Journey",
        "books": ["Genesis", "John"],
        "pace": "chapters_per_day",
        "pace_value": 3,
        "start_now": True,
    })
    assert response.status_code == 200
    plan = response.get_json()
    assert plan["id"].startswith("custom-")
    assert plan["total_days"] == 24  # 71 chapters / 3 per day = 24 days

    pid = plan["id"]
    # progress + mark
    progress = auth_client.get(f"/api/plans/{pid}/progress").get_json()
    assert progress["start_date"] == _today()
    marked = auth_client.post(f"/api/plans/{pid}/mark", json={"day": 1, "completed": True}).get_json()
    assert marked["completed_count"] == 1
    # detail
    assert auth_client.get(f"/api/plans/custom/{pid}").get_json()["title"] == "Genesis + John Journey"
    # appears in analytics
    analytics = auth_client.get("/api/profile/analytics").get_json()["analytics"]
    assert pid in analytics["plans"]
    # delete
    assert auth_client.delete(f"/api/plans/custom/{pid}").status_code == 200
    assert auth_client.get(f"/api/plans/custom/{pid}").status_code == 404


def test_bible_year_flow(auth_client):
    assert auth_client.post("/api/bible-year/start").status_code == 200
    marked = auth_client.post("/api/bible-year/mark", json={"day": 1, "completed": True}).get_json()
    assert marked["progress"]["completed_count"] == 1
    data = auth_client.get("/api/bible-year/progress").get_json()
    assert data["authenticated"] is True
    assert data["progress"]["start_date"] == _today()


def test_quiz_stats_flow(auth_client):
    submit = auth_client.post("/api/quiz/submit", json={"score": 9, "total": 10, "category": "Mixed"})
    assert submit.get_json()["percentage"] == 90.0
    stats = auth_client.get("/api/quiz/stats").get_json()
    assert stats["authenticated"] is True
    assert stats["stats"]["attempts"] == 1
    assert stats["stats"]["best_percentage"] == 90.0


def test_export_formats(auth_client):
    auth_client.post("/api/sync", json={
        "bookmarks": [{"id": 1, "reference": "Psalm 23:1", "text": "The LORD is my shepherd",
                       "timestamp": f"{_today()}T09:00:00"}],
        "highlightLabels": {"Psalms_23": {"1": {"label": "promise", "text": "The LORD is my shepherd",
                                               "updated_at": f"{_today()}T09:00:00"}}},
    })
    for fmt in ("json", "md", "txt"):
        response = auth_client.get(f"/api/export?format={fmt}")
        assert response.status_code == 200
        assert "attachment" in response.headers.get("Content-Disposition", "")
    md = auth_client.get("/api/export?format=md").get_data(as_text=True)
    assert "Psalms 23:1" in md
    assert "promise" in md


def test_clear_progress(auth_client):
    auth_client.post("/api/sync", json={
        "progress": {"reading_progress_john_3": {"book": "John", "slug": "john", "chapter": 3,
                                                "timestamp": f"{_today()}T09:00:00"}},
    })
    assert auth_client.get("/api/sync").get_json()["progress"]
    assert auth_client.post("/api/clear-progress").status_code == 200
    assert auth_client.get("/api/sync").get_json()["progress"] == {}


def test_achievements_present(auth_client):
    analytics = auth_client.get("/api/profile/analytics").get_json()["analytics"]
    ids = [a["id"] for a in analytics["achievements"]]
    assert "first_read" in ids
    assert "memorize_5" in ids  # memorization achievements
    assert "quiz_perfect" in ids


def test_daily_activity_roundtrip(auth_client):
    """dailyActivity syncs, merges (max per field) and feeds analytics."""
    auth_client.post("/api/sync", json={
        "dailyActivity": {
            _today(): {"chapters": 4, "minutes": 22.0},
            "2020-01-01": {"chapters": 1, "minutes": 5.0},
        }
    })
    # a second copy with smaller values must not overwrite the larger ones
    auth_client.post("/api/sync", json={
        "dailyActivity": {_today(): {"chapters": 1, "minutes": 1.0}}
    })
    data = auth_client.get("/api/sync").get_json()
    today_entry = data["dailyActivity"].get(_today())
    assert today_entry == {"chapters": 4, "minutes": 22.0}, today_entry

    analytics = auth_client.get("/api/profile/analytics").get_json()["analytics"]
    da = analytics["daily_activity"]
    assert len(da) == 14
    assert da[-1]["date"] == _today()
    assert da[-1]["chapters"] == 4
    assert da[-1]["minutes"] == 22.0
    assert da[-1]["label"]


def test_preferred_version_roundtrip(auth_client):
    auth_client.post("/api/sync", json={"preferred_version": "en-web"})
    assert auth_client.get("/api/sync").get_json()["preferred_version"] == "en-web"

    # books route falls back to the preferred version when none is requested
    html = auth_client.get("/books/john?chapter=1").get_data(as_text=True)
    assert "World English Bible (WEB)" in html

    # explicit version still wins
    html = auth_client.get("/books/john?chapter=1&version=en-kjv").get_data(as_text=True)
    assert "King James Version (KJV)" in html
