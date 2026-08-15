"""Account: Google OAuth, data sync, streaks, Bible-in-a-Year, profile, export."""
from flask import Blueprint, jsonify, redirect, render_template, request, send_file, session, url_for

import datetime as dt
import io
import json
from requests_oauthlib import OAuth2Session
from app.bible.plans import BIBLE_YEAR_PLAN, BIBLE_YEAR_TOTAL_DAYS
from app.services.analytics import compute_bible_year_progress, compute_profile_analytics, compute_streak
from app.services.storage import load_user_sync_data, merge_sync_data, save_user_sync_data
from app.config import Config

bp = Blueprint('user', __name__)

@bp.route('/login/google')
def google_login():
    """Initiate Google OAuth"""
    google = OAuth2Session(
        Config.GOOGLE_CLIENT_ID,
        redirect_uri=url_for('user.google_callback', _external=True),
        scope=['openid', 'email', 'profile']
    )
    
    auth_url, state = google.authorization_url(
        Config.GOOGLE_AUTH_URL,
        access_type='offline',
        prompt='select_account'
    )
    
    session['oauth_state'] = state
    return redirect(auth_url)

@bp.route('/login/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        google = OAuth2Session(
            Config.GOOGLE_CLIENT_ID,
            state=session.get('oauth_state'),
            redirect_uri=url_for('user.google_callback', _external=True)
        )
        
        token = google.fetch_token(
            Config.GOOGLE_TOKEN_URL,
            client_secret=Config.GOOGLE_CLIENT_SECRET,
            authorization_response=request.url
        )
        
        session.pop('oauth_state', None)
        
        google = OAuth2Session(Config.GOOGLE_CLIENT_ID, token=token)
        user_info = google.get(Config.GOOGLE_USERINFO_URL).json()
        
        session['user'] = {
            'id': user_info['sub'],
            'name': user_info.get('name', user_info.get('email')),
            'email': user_info['email'],
            'picture': user_info.get('picture', '')
        }
        session.permanent = True
        
        print(f"Login successful: {user_info.get('email')}")
        return redirect(url_for('main.index'))
        
    except Exception as e:
        print(f"Login failed: {e}")
        session.pop('oauth_state', None)
        return redirect(url_for('main.index'))

@bp.route('/logout')
def logout():
    """Logout user"""
    session.pop('user', None)
    return redirect(url_for('main.index'))

@bp.route('/api/sync', methods=['POST'])
def sync_data():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    server_data = load_user_sync_data(user_id)
    merged_data = merge_sync_data(data, server_data)
    
    if save_user_sync_data(user_id, merged_data):
        return jsonify({'success': True, 'message': 'Data synced successfully'})
    else:
        return jsonify({'error': 'Failed to save data'}), 500

@bp.route('/api/sync', methods=['GET'])
def get_sync_data():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    data['streak'] = compute_streak(data.get('readingLog', []))
    data['bibleYearProgress'] = compute_bible_year_progress(data.get('bibleYear', {}))
    
    return jsonify(data)

@bp.route('/api/log-reading', methods=['POST'])
def log_reading():
    """Record that the user read a chapter today, for streak tracking.
    Lightweight and automatic (called on chapter load) — separate from
    the full bookmarks/highlights sync so it doesn't need a manual Sync Now."""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    user_id = session['user']['id']
    today_str = dt.date.today().isoformat()
    
    data = load_user_sync_data(user_id)
    reading_log = set(data.get('readingLog', []))
    reading_log.add(today_str)
    data['readingLog'] = sorted(reading_log)
    
    if not save_user_sync_data(user_id, data):
        return jsonify({'error': 'Failed to save reading log'}), 500
    
    streak = compute_streak(data['readingLog'])
    return jsonify({'success': True, 'streak': streak})

@bp.route('/api/bible-year/plan', methods=['GET'])
def bible_year_plan():
    """Public - the static 365-day reading plan. No auth needed since it's the same for everyone."""
    return jsonify({"days": BIBLE_YEAR_TOTAL_DAYS, "plan": BIBLE_YEAR_PLAN})

@bp.route('/api/bible-year/progress', methods=['GET'])
def bible_year_progress():
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    progress = compute_bible_year_progress(data.get('bibleYear', {}))
    return jsonify({'authenticated': True, 'progress': progress})

@bp.route('/api/bible-year/start', methods=['POST'])
def bible_year_start():
    """Begin (or restart) the Bible-in-a-Year plan from today, clearing any prior progress."""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    data['bibleYear'] = {"start_date": dt.date.today().isoformat(), "completed_days": []}
    
    if not save_user_sync_data(user_id, data):
        return jsonify({'error': 'Failed to save'}), 500
    
    progress = compute_bible_year_progress(data['bibleYear'])
    return jsonify({'success': True, 'progress': progress})

@bp.route('/api/bible-year/mark', methods=['POST'])
def bible_year_mark():
    """Mark a plan day as read (or unread). Body: {"day": 1, "completed": true}"""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    body = request.get_json() or {}
    day = body.get('day')
    completed = body.get('completed', True)
    
    if not isinstance(day, int) or day < 1 or day > BIBLE_YEAR_TOTAL_DAYS:
        return jsonify({'error': f'day must be an integer between 1 and {BIBLE_YEAR_TOTAL_DAYS}'}), 400
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    bible_year = data.get('bibleYear') or {"start_date": None, "completed_days": []}
    
    if not bible_year.get('start_date'):
        bible_year['start_date'] = dt.date.today().isoformat()
    
    completed_days = set(bible_year.get('completed_days', []))
    if completed:
        completed_days.add(day)
    else:
        completed_days.discard(day)
    bible_year['completed_days'] = sorted(completed_days)
    data['bibleYear'] = bible_year
    
    if not save_user_sync_data(user_id, data):
        return jsonify({'error': 'Failed to save'}), 500
    
    progress = compute_bible_year_progress(bible_year)
    return jsonify({'success': True, 'progress': progress})

@bp.route('/profile')
def user_profile():
    """Renders the user's profile / activity dashboard. Analytics are fetched
    client-side from /api/profile/analytics, matching how sync and Bible-in-a-Year
    data are already fetched client-side elsewhere in the app."""
    user = session.get('user')
    return render_template('user-profile.html', user=user, current_year=dt.datetime.now().year)

@bp.route('/api/profile/analytics', methods=['GET'])
def profile_analytics():
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401

    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    analytics = compute_profile_analytics(data)
    return jsonify({'authenticated': True, 'analytics': analytics})

@bp.route('/api/user', methods=['GET'])
def get_user():
    user = session.get('user')
    if user:
        return jsonify({
            'authenticated': True,
            'name': user['name'],
            'email': user['email'],
            'picture': user.get('picture', '')
        })
    return jsonify({'authenticated': False})

@bp.route('/api/export', methods=['GET'])
def api_export():
    """Export the signed-in user's data (bookmarks, highlights, notes, prayers) as JSON, Markdown or plain text."""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401

    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    fmt = request.args.get('format', 'json').lower()

    bookmarks = data.get('bookmarks', []) or []
    highlights = data.get('highlights', {}) or {}
    highlight_colors = data.get('highlightColors', {}) or {}
    highlight_labels = data.get('highlightLabels', {}) or {}
    notes = data.get('notes', []) or []
    prayers = data.get('prayers', []) or []
    reading_log = data.get('readingLog', []) or []

    # Flatten highlights into references (union of highlighted + labeled verses)
    highlight_refs = []
    all_chapters = set(highlights.keys()) | set(highlight_labels.keys())
    for chapter_key in sorted(all_chapters):
        # chapter_key looks like "John_3"
        parts = chapter_key.rsplit('_', 1)
        book_part = parts[0].replace('_', ' ') if parts else chapter_key
        chapter_part = parts[1] if len(parts) > 1 else ''
        verse_list = set(highlights.get(chapter_key, []) or []) | set((highlight_labels.get(chapter_key) or {}).keys())
        for verse in sorted(verse_list, key=lambda v: int(v) if str(v).isdigit() else 0):
            color = (highlight_colors.get(chapter_key) or {}).get(str(verse), '')
            label = ((highlight_labels.get(chapter_key) or {}).get(str(verse)) or {}).get('label', '')
            ref = f"{book_part} {chapter_part}:{verse}"
            highlight_refs.append({'reference': ref, 'color': color or 'default', 'label': label or ''})

    export_data = {
        'exported_at': dt.datetime.now().isoformat(),
        'exported_by': session['user'].get('email', user_id),
        'bookmarks': bookmarks,
        'highlights': highlight_refs,
        'notes': notes,
        'prayers': prayers,
        'reading_days': sorted(reading_log),
    }

    if fmt == 'json':
        content = json.dumps(export_data, indent=2)
        filename = 'mypersonal-bible-data.json'
        mimetype = 'application/json'
    elif fmt == 'md':
        lines = ["# MyPersonal Bible - Exported Data", "",
                 "_Exported on %s_" % dt.datetime.now().strftime('%B %d, %Y at %H:%M'), "", "## Bookmarks", ""]
        if bookmarks:
            for b in bookmarks:
                lines.append("- **%s** — \"%s\"" % (b.get('reference', ''), b.get('text', '')))
        else:
            lines.append("_No bookmarks saved._")
        lines += ["", "## Highlights", ""]
        if highlight_refs:
            for h in highlight_refs:
                extra = []
                if h.get('color') and h['color'] != 'default':
                    extra.append("color: %s" % h['color'])
                if h.get('label'):
                    extra.append("label: %s" % h['label'])
                suffix = " _(%s)_" % ", ".join(extra) if extra else ""
                lines.append("- %s%s" % (h['reference'], suffix))
        else:
            lines.append("_No highlights saved._")
        lines += ["", "## Notes", ""]
        if notes:
            for n in notes:
                lines.append("### %s (%s)" % (n.get('reference', 'Note'), (n.get('created_at', '') or '')[:10]))
                lines.append("")
                lines.append(n.get('text', ''))
                lines.append("")
        else:
            lines.append("_No notes saved._")
        lines += ["", "## Prayer Journal", ""]
        if prayers:
            for p in prayers:
                status = "✅ Answered" if p.get('answered') else "🙏 Praying"
                lines.append("- %s: %s" % (status, p.get('text', '')))
        else:
            lines.append("_No prayers saved._")
        content = "\n".join(lines)
        filename = 'mypersonal-bible-data.md'
        mimetype = 'text/markdown'
    elif fmt == 'txt':
        lines = ["MYPERSONAL BIBLE - EXPORTED DATA",
                 "Exported on %s" % dt.datetime.now().strftime('%B %d, %Y at %H:%M'), "=" * 50, "", "BOOKMARKS", "-" * 20]
        if bookmarks:
            lines += ["%s: %s" % (b.get('reference', ''), b.get('text', '')) for b in bookmarks]
        else:
            lines.append("(none)")
        lines += ["", "HIGHLIGHTS", "-" * 20]
        if highlight_refs:
            for h in highlight_refs:
                extra = []
                if h.get('color') and h['color'] != 'default':
                    extra.append(h['color'])
                if h.get('label'):
                    extra.append(h['label'])
                suffix = " (%s)" % ", ".join(extra) if extra else ""
                lines.append(h['reference'] + suffix)
        else:
            lines.append("(none)")
        lines += ["", "NOTES", "-" * 20]
        if notes:
            for n in notes:
                lines.append("[%s - %s]" % (n.get('reference', 'Note'), (n.get('created_at', '') or '')[:10]))
                lines.append(n.get('text', ''))
                lines.append("")
        else:
            lines.append("(none)")
        lines += ["", "PRAYERS", "-" * 20]
        if prayers:
            for p in prayers:
                status = "[ANSWERED]" if p.get('answered') else "[PRAYING]"
                lines.append("%s %s" % (status, p.get('text', '')))
        else:
            lines.append("(none)")
        content = "\n".join(lines)
        filename = 'mypersonal-bible-data.txt'
        mimetype = 'text/plain'
    else:
        return jsonify({'error': 'format must be one of: json, md, txt'}), 400

    return send_file(
        io.BytesIO(content.encode('utf-8')),
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )

@bp.route('/continue-reading')
def continue_reading_page():
    user = session.get('user')
    return render_template('continue-reading.html', user=user, current_year=dt.datetime.now().year)

@bp.route('/api/clear-progress', methods=['POST'])
def api_clear_progress():
    """Clear reading history. Local copy is cleared client-side; this wipes the server copy."""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    data['progress'] = {}
    if not save_user_sync_data(user_id, data):
        return jsonify({'error': 'Failed to save'}), 500
    return jsonify({'success': True})
