"""Site-wide routes: robots.txt, sitemap, health check, offline page, service worker."""
import datetime as dt

from flask import Blueprint, Response, current_app, jsonify, send_from_directory, url_for

from app.bible.books import BIBLE_BOOKS

bp = Blueprint("meta", __name__)


@bp.route("/robots.txt")
def robots_txt():
    sitemap_url = url_for("meta.sitemap_xml", _external=True)
    content = f"User-agent: *\nAllow: /\nSitemap: {sitemap_url}\n"
    return Response(content, mimetype="text/plain")


@bp.route("/sitemap.xml")
def sitemap_xml():
    pages = [
        url_for("main.index", _external=True),
        url_for("main.contact", _external=True),
        url_for("main.install_guide", _external=True),
        url_for("main.search", _external=True),
        url_for("study.reading_plans_page", _external=True),
        url_for("study.topics_page", _external=True),
        url_for("study.quiz_page", _external=True),
        url_for("reader.compare_page", _external=True),
        url_for("study.devotional_page", _external=True),
        url_for("study.prayer_journal_page", _external=True),
        url_for("study.bible_in_a_year", _external=True),
        url_for("user.continue_reading_page", _external=True),
        url_for("study.memorize_page", _external=True),
    ]
    pages.extend(url_for("reader.books", book_slug=book["slug"], _external=True) for book in BIBLE_BOOKS)
    lastmod = dt.date.today().isoformat()
    xml_urls = "\n".join(
        f"    <url>\n      <loc>{page}</loc>\n      <lastmod>{lastmod}</lastmod>\n"
        f"      <changefreq>weekly</changefreq>\n      <priority>0.7</priority>\n    </url>"
        for page in pages
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{xml_urls}\n"
        "</urlset>"
    )
    return Response(xml, mimetype="application/xml")


@bp.route("/health")
def health():
    return jsonify(status="ok"), 200


@bp.route("/sw.js")
def service_worker():
    """Serve the service worker from the site root so it can control the whole
    origin (a worker served from /static/ would be limited to /static/ scope)."""
    response = send_from_directory(current_app.static_folder, "sw.js", mimetype="application/javascript")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@bp.route("/offline")
def offline():
    """Shown by the service worker when the user is offline and the page isn't cached."""
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Offline - MyPersonal Bible</title></head>"
        "<body style='margin:0;font-family:Georgia,serif;background:#1a0f00;color:#f2e8d0;display:flex;align-items:center;"
        "justify-content:center;min-height:100vh;text-align:center;'>"
        "<div style='padding:24px;'><div style='font-size:64px;margin-bottom:16px;'>&#128218;</div>"
        "<h1 style='font-size:1.8rem;margin:0 0 12px;'>You're offline</h1>"
        "<p style='max-width:420px;line-height:1.7;opacity:0.85;margin:0 auto 20px;'>"
        "Chapters you have already read are saved on this device, so you can open them from your history or bookmarks. "
        "Reconnect to the internet to explore the full Bible.</p>"
        "<p style='opacity:0.6;font-size:0.9rem;'>MyPersonal Bible</p></div></body></html>"
    ), 503
