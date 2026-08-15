"""Home, search, contact and install pages."""
from flask import Blueprint, render_template, request, session

import datetime as dt
import requests
import os
from app.bible.books import API_BIBLE_VERSIONS, BIBLE_BOOKS, VERSION_LIST
from app.content import search_kjv
from app.services.daily_verse import get_daily_verse
from app.services.emailer import _send_contact_email_resend
from app.utils import clean_text
from app.config import Config

bp = Blueprint('main', __name__)

@bp.route("/")
def index():
    daily_verse = get_daily_verse()
    user = session.get('user')
    return render_template(
        "index.html",
        current_year=dt.datetime.now().year,
        daily_verse=daily_verse,
        books=BIBLE_BOOKS,
        versions=VERSION_LIST,
        user=user
    )

@bp.route("/search", methods=["GET", "POST"])
def search():
    api_key = Config.API_BIBLE_KEY or os.environ.get("API_KEY")
    headers = {"api-key": api_key} if api_key else {}
    
    search_results = None
    search_performed = False
    search_source = None
    query = ""
    
    if request.method == "POST":
        query = request.form.get("query", "").strip()
    elif request.method == "GET":
        query = request.args.get("query", "").strip()
    
    if query:
        try:
            search_bible_id = API_BIBLE_VERSIONS.get("en-niv", "78a9f6124f344018-01")
            search_url = f"{Config.API_BIBLE_BASE}/bibles/{search_bible_id}/search"
            response = requests.get(search_url, headers=headers, params={"query": query}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                search_results = []
                
                if "data" in data and "verses" in data["data"]:
                    for verse in data["data"]["verses"]:
                        cleaned = clean_text(verse.get("text", ""))
                        search_results.append({
                            "text": cleaned,
                            "reference": verse.get("reference", "")
                        })
                if search_results:
                    search_source = "api_bible"
            else:
                search_results = []
                print(f"Search API error: {response.status_code}")
        except Exception as e:
            print(f"Search error: {e}")
            search_results = []

        # Built-in KJV fallback - always available, no API key needed
        if not search_results:
            search_results = search_kjv(query, limit=30)
            search_source = "kjv"
        search_performed = True

    daily_verse = get_daily_verse()
    user = session.get('user')
    return render_template(
        "index.html",
        current_year=dt.datetime.now().year,
        daily_verse=daily_verse,
        books=BIBLE_BOOKS,
        versions=VERSION_LIST,
        search_results=search_results,
        search_performed=search_performed,
        query=query,
        search_source=search_source,
        user=user
    )

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form_data = {'name': '', 'email': '', 'subject': '', 'message': ''}
    status_message = None
    status_type = 'info'
    user = session.get('user')

    if request.method == 'POST':
        form_data['name'] = request.form.get('name', '').strip()
        form_data['email'] = request.form.get('email', '').strip()
        form_data['subject'] = request.form.get('subject', '').strip()
        form_data['message'] = request.form.get('message', '').strip()

        if not form_data['email'] or not form_data['message']:
            status_type = 'warning'
            status_message = 'Please provide both your email address and a message.'
        else:
            success, msg = _send_contact_email_resend(
                sender_name=form_data['name'],
                sender_email=form_data['email'],
                subject=form_data['subject'],
                message=form_data['message'],
            )
            status_type = 'success' if success else 'danger'
            status_message = msg
            if success:
                form_data = {'name': '', 'email': '', 'subject': '', 'message': ''}

    return render_template(
        'contact.html',
        current_year=dt.datetime.now().year,
        status_message=status_message,
        status_type=status_type,
        form_data=form_data,
        user=user
    )

@bp.route('/install')
def install_guide():
    user = session.get('user')
    return render_template('install.html', user=user, current_year=dt.datetime.now().year)
