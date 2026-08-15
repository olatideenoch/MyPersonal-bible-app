"""Study features: reading plans (incl. custom), topics, quiz, devotional, memorize."""
from flask import Blueprint, jsonify, render_template, request, session

import datetime as dt
import math
import secrets
import random
from app.bible.books import BIBLE_BOOKS
from app.bible.devotionals import DAILY_DEVOTIONALS
from app.bible.plans import READING_PLANS, READING_PLANS_BY_ID, _group_chapters, _label_groups
from app.bible.quiz import QUIZ_CATEGORIES, QUIZ_QUESTIONS
from app.bible.topics import TOPICS_BY_SLUG, TOPIC_VERSES
from app.services.storage import load_user_sync_data, save_user_sync_data

bp = Blueprint('study', __name__)

@bp.route('/bible-in-a-year')
def bible_in_a_year():
    """Renders the Bible in a Year tracker page. The 365-day plan and the
    signed-in user's progress are fetched client-side via
    /api/bible-year/plan and /api/bible-year/progress, matching how sync
    data is already fetched client-side elsewhere in the app."""
    user = session.get('user')
    return render_template('bible_in_a_year.html', user=user, current_year=dt.datetime.now().year)

@bp.route('/plans')
def reading_plans_page():
    user = session.get('user')
    light_plans = [{
        "id": p["id"], "title": p["title"], "icon": p["icon"], "color": p["color"],
        "description": p["description"], "total_days": len(p["plan"])
    } for p in READING_PLANS]
    return render_template('reading-plans.html', user=user, current_year=dt.datetime.now().year,
                           plans=light_plans, books=BIBLE_BOOKS)

@bp.route('/api/plans', methods=['GET'])
def api_plans():
    """Public - list all available reading plans with their metadata."""
    return jsonify({
        "plans": [{
            "id": p["id"], "title": p["title"], "icon": p["icon"], "color": p["color"],
            "description": p["description"], "total_days": len(p["plan"])
        } for p in READING_PLANS]
    })

@bp.route('/api/plans/<plan_id>', methods=['GET'])
def api_plan_detail(plan_id):
    """Public - full day-by-day plan."""
    plan = READING_PLANS_BY_ID.get(plan_id)
    if not plan:
        return jsonify({'error': 'Plan "%s" not found' % plan_id}), 404
    return jsonify({
        "id": plan["id"], "title": plan["title"], "icon": plan["icon"], "color": plan["color"],
        "description": plan["description"], "total_days": len(plan["plan"]), "plan": plan["plan"]
    })

@bp.route('/api/plans/<plan_id>/start', methods=['POST'])
def api_plan_start(plan_id):
    """Begin (or restart) a plan from today."""
    plan = _resolve_plan_meta(plan_id)
    if not plan:
        return jsonify({'error': 'Plan "%s" not found' % plan_id}), 404
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401

    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    plans = data.get('plans', {}) or {}
    plans[plan_id] = {"start_date": dt.date.today().isoformat(), "completed_days": []}
    data['plans'] = plans
    if not save_user_sync_data(user_id, data):
        return jsonify({'error': 'Failed to save'}), 500
    return jsonify({'success': True})

@bp.route('/api/plans/<plan_id>/mark', methods=['POST'])
def api_plan_mark(plan_id):
    """Mark a plan day as read (or unread). Body: {"day": 1, "completed": true}"""
    plan = _resolve_plan_meta(plan_id)
    if not plan:
        return jsonify({'error': 'Plan "%s" not found' % plan_id}), 404
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401

    body = request.get_json() or {}
    day = body.get('day')
    completed = body.get('completed', True)
    total = len(plan["plan"])
    if not isinstance(day, int) or day < 1 or day > total:
        return jsonify({'error': 'day must be an integer between 1 and %d' % total}), 400

    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    plans = data.get('plans', {}) or {}
    entry = plans.get(plan_id) or {"start_date": dt.date.today().isoformat(), "completed_days": []}
    if not entry.get('start_date'):
        entry['start_date'] = dt.date.today().isoformat()
    completed_days = set(entry.get('completed_days', []) or [])
    if completed:
        completed_days.add(day)
    else:
        completed_days.discard(day)
    entry['completed_days'] = sorted(completed_days)
    plans[plan_id] = entry
    data['plans'] = plans
    if not save_user_sync_data(user_id, data):
        return jsonify({'error': 'Failed to save'}), 500

    completed_count = len(entry['completed_days'])
    return jsonify({
        'success': True,
        'completed_count': completed_count,
        'total_days': total,
        'percent_complete': round((completed_count / total) * 100, 1) if total else 0
    })

@bp.route('/api/plans/<plan_id>/progress', methods=['GET'])
def api_plan_progress(plan_id):
    plan = _resolve_plan_meta(plan_id)
    if not plan:
        return jsonify({'error': 'Plan "%s" not found' % plan_id}), 404
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401

    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    entry = (data.get('plans', {}) or {}).get(plan_id) or {}
    completed = sorted(set(entry.get('completed_days', []) or []))
    total = len(plan["plan"])
    return jsonify({
        'authenticated': True,
        'start_date': entry.get('start_date'),
        'completed_days': completed,
        'completed_count': len(completed),
        'total_days': total,
        'percent_complete': round((len(completed) / total) * 100, 1) if total else 0
    })

@bp.route('/topics')
def topics_page():
    user = session.get('user')
    return render_template('topics.html', user=user, current_year=dt.datetime.now().year)

@bp.route('/api/topics', methods=['GET'])
def api_topics():
    """Public - list all topic collections (without verses)."""
    return jsonify({
        "topics": [{
            "slug": t["slug"], "title": t["title"], "icon": t["icon"], "description": t["description"],
            "verse_count": len(t["verses"])
        } for t in TOPIC_VERSES]
    })

@bp.route('/api/topics/<slug>', methods=['GET'])
def api_topic_detail(slug):
    """Public - one topic with its verses."""
    topic = TOPICS_BY_SLUG.get(slug.lower())
    if not topic:
        return jsonify({'error': 'Topic "%s" not found' % slug}), 404
    return jsonify(topic)

@bp.route('/quiz')
def quiz_page():
    user = session.get('user')
    return render_template('quiz.html', user=user, current_year=dt.datetime.now().year,
                           categories=QUIZ_CATEGORIES)

@bp.route('/api/quiz', methods=['GET'])
def api_quiz():
    """Public - return a quiz (all questions shuffled, or by category)."""
    category = request.args.get('category', '').strip()
    limit = min(request.args.get('limit', 10, type=int) or 10, 25)
    pool = [q for q in QUIZ_QUESTIONS if not category or q['category'] == category]
    if not pool:
        return jsonify({'error': 'Category "%s" not found' % category}), 404
    questions = random.sample(pool, min(limit, len(pool)))
    # Don't leak the answer index to the client
    return jsonify({
        "categories": QUIZ_CATEGORIES,
        "questions": [{
            "question": q["question"], "options": q["options"], "category": q["category"],
            "difficulty": q["difficulty"]
        } for q in questions],
        "answer_key": [q["answer"] for q in questions],
        "references": [q.get("reference", "") for q in questions],
    })

@bp.route('/api/quiz/submit', methods=['POST'])
def api_quiz_submit():
    """Record a quiz result for signed-in users. Body: {"score": 8, "total": 10}"""
    body = request.get_json() or {}
    score = body.get('score')
    total = body.get('total')
    category = body.get('category', 'Mixed')
    if not isinstance(score, int) or not isinstance(total, int) or total <= 0 or score < 0 or score > total:
        return jsonify({'error': 'Invalid score/total'}), 400

    percentage = round((score / total) * 100, 1)

    if 'user' in session:
        user_id = session['user']['id']
        data = load_user_sync_data(user_id)
        stats = data.get('quizStats') or {"attempts": 0, "total_correct": 0, "total_answered": 0, "best_percentage": 0.0, "history": []}
        stats['attempts'] = (stats.get('attempts', 0) or 0) + 1
        stats['total_correct'] = (stats.get('total_correct', 0) or 0) + score
        stats['total_answered'] = (stats.get('total_answered', 0) or 0) + total
        stats['best_percentage'] = max(stats.get('best_percentage', 0) or 0, percentage)
        history = stats.get('history', []) or []
        history.append({"date": dt.date.today().isoformat(), "score": score, "total": total, "percentage": percentage, "category": category})
        stats['history'] = history[-100:]
        data['quizStats'] = stats
        save_user_sync_data(user_id, data)

    return jsonify({'success': True, 'percentage': percentage})

@bp.route('/api/quiz/stats', methods=['GET'])
def api_quiz_stats():
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    return jsonify({'authenticated': True, 'stats': data.get('quizStats') or {}})

@bp.route('/devotional')
def devotional_page():
    """Daily devotional - rotates on a 31-day monthly cycle."""
    user = session.get('user')
    today = dt.date.today()
    # Day-of-month -> devotional (31-day cycle)
    day_num = ((today.day - 1) % 31) + 1
    selected_day = request.args.get('day', type=int) or day_num
    if selected_day < 1 or selected_day > 31:
        selected_day = day_num
    devotional = DAILY_DEVOTIONALS[selected_day - 1]
    return render_template('devotional.html', user=user, current_year=today.year,
                           devotionals=DAILY_DEVOTIONALS, devotional=devotional,
                           selected_day=selected_day, today_day=day_num)

@bp.route('/prayer-journal')
def prayer_journal_page():
    user = session.get('user')
    return render_template('prayer-journal.html', user=user, current_year=dt.datetime.now().year)

def _resolve_plan_meta(plan_id):
    """Resolve a plan (built-in or user's custom plan) to its metadata dict."""
    meta = READING_PLANS_BY_ID.get(plan_id)
    if meta:
        return meta
    if 'user' in session:
        data = load_user_sync_data(session['user']['id'])
        custom = (data.get('customPlans') or {}).get(plan_id)
        if custom:
            return custom
    return None

@bp.route('/api/plans/custom/build', methods=['POST'])
def api_custom_plan_build():
    """Build a custom plan from a selection of books.
    Body: {"title": "...", "books": ["Genesis", "John", ...],
           "pace": "chapters_per_day"|"days", "pace_value": 5, "start_now": true}"""
    body = request.get_json() or {}
    title = (body.get('title') or 'My Custom Plan').strip()[:60] or 'My Custom Plan'
    book_names = body.get('books') or []
    valid_books = [b['name'] for b in BIBLE_BOOKS if b['name'] in book_names]
    if not valid_books:
        return jsonify({'error': 'Select at least one book'}), 400

    pace = body.get('pace', 'chapters_per_day')
    try:
        pace_value = int(body.get('pace_value') or 0)
    except (TypeError, ValueError):
        pace_value = 0

    plan = _build_custom_plan(valid_books, pace, pace_value)
    if not plan:
        return jsonify({'error': 'Could not build the plan'}), 400

    plan_id = 'custom-' + secrets.token_hex(4)
    plan_def = {
        'id': plan_id,
        'title': title,
        'icon': 'fa-wand-magic-sparkles',
        'color': '#3f6d4e',
        'description': '%d chapters from %d books - a plan made just for you.' % (
            sum(len(d['readings']) for d in plan), len(valid_books)),
        'total_days': len(plan),
        'books': valid_books,
        'pace': pace,
        'pace_value': pace_value,
        'plan': plan,
    }

    if 'user' in session:
        user_id = session['user']['id']
        data = load_user_sync_data(user_id)
        custom_plans = data.get('customPlans') or {}
        custom_plans[plan_id] = plan_def
        data['customPlans'] = custom_plans
        if body.get('start_now'):
            plans = data.get('plans') or {}
            plans[plan_id] = {'start_date': dt.date.today().isoformat(), 'completed_days': []}
            data['plans'] = plans
        if not save_user_sync_data(user_id, data):
            return jsonify({'error': 'Failed to save'}), 500

    return jsonify(plan_def)

def _build_custom_plan(book_names: list, pace: str, pace_value: int) -> list:
    all_chapters = []
    for b in BIBLE_BOOKS:
        if b['name'] in book_names:
            for ch in range(1, b['chapters'] + 1):
                all_chapters.append({'book': b['name'], 'slug': b['slug'], 'chapter': ch})
    if not all_chapters:
        return []

    if pace == 'days':
        days = max(1, min(int(pace_value), len(all_chapters)))
        base = len(all_chapters) // days
        rem = len(all_chapters) % days
        per_day = [base + (1 if i < rem else 0) for i in range(days)]
    else:
        cpd = max(1, min(int(pace_value), 20))
        per_day = [cpd] * math.ceil(len(all_chapters) / cpd)

    plan = []
    idx = 0
    for day_num, count in enumerate(per_day, 1):
        if count <= 0:
            continue
        day_chapters = all_chapters[idx: idx + count]
        idx += count
        groups = _group_chapters(day_chapters)
        plan.append({'day': day_num, 'readings': groups, 'label': _label_groups(groups)})
    return plan

@bp.route('/api/plans/custom/<plan_id>', methods=['GET'])
def api_custom_plan_detail(plan_id):
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    plan = (data.get('customPlans') or {}).get(plan_id)
    if not plan:
        return jsonify({'error': 'Custom plan "%s" not found' % plan_id}), 404
    return jsonify(plan)

@bp.route('/api/plans/custom/<plan_id>', methods=['DELETE'])
def api_custom_plan_delete(plan_id):
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    custom_plans = data.get('customPlans') or {}
    if plan_id not in custom_plans:
        return jsonify({'error': 'Custom plan not found'}), 404
    custom_plans.pop(plan_id, None)
    plans = data.get('plans') or {}
    plans.pop(plan_id, None)
    data['customPlans'] = custom_plans
    data['plans'] = plans
    if not save_user_sync_data(user_id, data):
        return jsonify({'error': 'Failed to save'}), 500
    return jsonify({'success': True})

@bp.route('/memorize')
def memorize_page():
    user = session.get('user')
    return render_template('memorize.html', user=user, current_year=dt.datetime.now().year)
