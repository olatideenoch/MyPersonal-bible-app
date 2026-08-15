"""Every public page renders successfully."""
import pytest

PAGES = [
    "/",
    "/search",
    "/contact",
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
