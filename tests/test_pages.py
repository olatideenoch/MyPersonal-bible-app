"""Every public page renders successfully."""
import pytest

PAGES = [
    "/",
    "/search",
    "/contact",
    "/about",
    "/install",
    "/bible-in-a-year",
    "/plans",
    "/topics",
    "/quiz",
    "/compare",
    "/devotional",
    "/prayer-journal",
    "/memorize",
    "/continue-reading",
    "/profile",
    "/books/john",  # book page without a chapter (no network fetch)
    "/offline",     # 503 by design, but should still render
]


@pytest.mark.parametrize("path", PAGES)
def test_page_renders(client, path):
    response = client.get(path)
    if path == "/offline":
        assert response.status_code == 503
    else:
        assert response.status_code == 200, f"{path} returned {response.status_code}"


def test_devotional_future_days_clamped(client):
    """Users can only read today's devotional and past days, never future ones."""
    import datetime as dt
    today_day = dt.date.today().day
    # requesting the last day of the cycle must clamp to today (unless today IS day 31)
    resp = client.get("/devotional?day=31")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    expected = "Day %d of 31" % min(31, today_day)
    assert expected in body
    # day chips for future days must not be rendered (ignore the canonical
    # link, which echoes the requested URL)
    import re
    chip_days = [int(m.group(1)) for m in re.finditer(r'/devotional\?day=(\d+)', body)
                 if m.start() > 0 and body[m.start() - 1] == '"']
    assert chip_days, "expected day chips in the picker"
    assert max(chip_days) <= today_day
    assert len(chip_days) == today_day
    # day 0 is invalid and falls back to today's devotional
    resp0 = client.get("/devotional?day=0")
    assert resp0.status_code == 200
    assert ("Day %d of 31" % today_day) in resp0.get_data(as_text=True)


def test_meta_routes(client):
    assert client.get("/health").status_code == 200
    robots = client.get("/robots.txt")
    assert robots.status_code == 200
    assert b"Sitemap:" in robots.data
    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert b"<urlset" in sitemap.data
    assert b"/memorize" in sitemap.data


def test_service_worker_served_from_root(client):
    response = client.get("/sw.js")
    assert response.status_code == 200
    assert "javascript" in response.content_type
    assert response.headers.get("Service-Worker-Allowed") == "/"


def test_static_assets(client):
    assert client.get("/static/css/app.css").status_code == 200
    assert client.get("/static/js/app-common.js").status_code == 200
    assert client.get("/static/data/kjv.json.gz").status_code == 200
