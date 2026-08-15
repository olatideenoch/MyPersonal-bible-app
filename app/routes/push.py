"""Web Push (daily verse reminders) endpoints."""
from flask import Blueprint, jsonify, request

import datetime as dt
import json
from app.services.daily_verse import get_daily_verse
from app.services.storage import _load_push_subs, _save_push_subs
from app.utils import clean_text
from app.config import Config

bp = Blueprint('push', __name__)

@bp.route('/api/push/config', methods=['GET'])
def api_push_config():
    """Public - tells the browser whether push reminders are configured."""
    return jsonify({
        'available': bool(Config.VAPID_PUBLIC_KEY and Config.VAPID_PRIVATE_KEY),
        'public_key': Config.VAPID_PUBLIC_KEY or '',
    })

@bp.route('/api/push/subscribe', methods=['POST'])
def api_push_subscribe():
    """Store or remove a browser push subscription.
    Body: {"subscription": {...}, "enabled": true|false}"""
    body = request.get_json() or {}
    sub = body.get('subscription')
    enabled = bool(body.get('enabled', True))

    if not sub or not sub.get('endpoint'):
        return jsonify({'error': 'Missing subscription'}), 400

    subs = _load_push_subs()
    endpoint = sub.get('endpoint')
    subs = [s for s in subs if s.get('endpoint') != endpoint]
    if enabled:
        sub['subscribed_at'] = dt.datetime.now().isoformat()
        subs.append(sub)
    if not _save_push_subs(subs):
        return jsonify({'error': 'Failed to save subscription'}), 500
    return jsonify({'success': True, 'enabled': enabled, 'total': len(subs)})

@bp.route('/api/push/send', methods=['GET', 'POST'])
def api_push_send():
    """Send today's verse to every subscribed browser.
    Protected by ?token=Config.APP_PUSH_TOKEN. Call daily from a free cron
    (e.g. GitHub Actions workflow or cron-job.org)."""
    token = request.args.get('token', '').strip() or (request.get_json(silent=True) or {}).get('token', '')
    if not Config.APP_PUSH_TOKEN or token != Config.APP_PUSH_TOKEN:
        return jsonify({'error': 'Not authorized'}), 403

    subs = _load_push_subs()
    if not subs:
        return jsonify({'sent': 0, 'failed': 0, 'removed': 0, 'message': 'No subscribers yet'})

    verse = get_daily_verse()
    reference = verse.get('reference', 'Verse of the Day')
    text = clean_text(verse.get('text', ''))[:220]
    payload = {
        'title': 'Verse of the Day 📖',
        'body': f"{reference} — \"{text}\"",
        'url': '/',
    }

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        return jsonify({'error': 'pywebpush not installed (add it to requirements.txt)'}), 500

    sent = 0
    failed = 0
    dead = []
    for sub in subs:
        try:
            webpush(
                subscription_info=sub,
                data=json.dumps(payload),
                vapid_private_key=Config.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": Config.VAPID_SUBJECT},
                timeout=10,
            )
            sent += 1
        except WebPushException as e:
            failed += 1
            # 404 / 410 = subscription no longer valid -> remove it
            if e.response is not None and e.response.status_code in (404, 410):
                dead.append(sub.get('endpoint'))
        except Exception as e:
            failed += 1
            print(f"Push error: {e}")

    if dead:
        remaining = [s for s in subs if s.get('endpoint') not in dead]
        _save_push_subs(remaining)
    return jsonify({'sent': sent, 'failed': failed, 'removed': len(dead)})
