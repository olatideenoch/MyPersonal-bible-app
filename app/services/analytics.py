"""Reading analytics: streaks, plan progress and achievements."""
import calendar
import datetime as dt

import pandas as pd

from app.bible.plans import BIBLE_YEAR_TOTAL_DAYS, READING_PLANS_BY_ID


def compute_streak(reading_log: list) -> dict:
    """Given a list of ISO date strings ('YYYY-MM-DD') the user read on,
    compute their current streak, longest streak, and last-read date."""
    if not reading_log:
        return {"current_streak": 0, "longest_streak": 0, "last_read": None, "total_days_read": 0}
    
    try:
        dates = sorted({dt.date.fromisoformat(d) for d in reading_log})
    except ValueError:
        return {"current_streak": 0, "longest_streak": 0, "last_read": None, "total_days_read": 0}
    
    today = dt.date.today()
    longest_streak = 1
    run = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            run += 1
        else:
            run = 1
        longest_streak = max(longest_streak, run)
    
    last_read = dates[-1]
    gap_from_today = (today - last_read).days
    
    if gap_from_today > 1:
        # Streak is broken (missed at least one full day)
        current_streak = 0
    else:
        # Walk backwards from the most recent read day counting consecutive days
        current_streak = 1
        for i in range(len(dates) - 1, 0, -1):
            if (dates[i] - dates[i - 1]).days == 1:
                current_streak += 1
            else:
                break
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "last_read": last_read.isoformat(),
        "total_days_read": len(dates)
    }

def compute_bible_year_progress(bible_year: dict) -> dict:
    """Given a user's {start_date, completed_days} for the Bible-in-a-Year plan,
    compute completion stats and whether they're on track, ahead, or behind."""
    bible_year = bible_year or {}
    completed_days = sorted(set(bible_year.get("completed_days", [])))
    start_date_str = bible_year.get("start_date")
    total_days = BIBLE_YEAR_TOTAL_DAYS
    completed_count = len(completed_days)

    result = {
        "start_date": start_date_str,
        "completed_days": completed_days,
        "completed_count": completed_count,
        "total_days": total_days,
        "percent_complete": round((completed_count / total_days) * 100, 1) if total_days else 0,
        "expected_day": None,
        "days_ahead_behind": None,
        "status": "not_started"
    }

    if not start_date_str:
        return result

    try:
        start_date = dt.date.fromisoformat(start_date_str)
    except ValueError:
        return result

    today = dt.date.today()
    elapsed = (today - start_date).days + 1
    expected_day = min(max(elapsed, 1), total_days)
    result["expected_day"] = expected_day

    diff = completed_count - expected_day
    result["days_ahead_behind"] = diff
    if completed_count >= total_days:
        result["status"] = "completed"
    elif diff >= 0:
        result["status"] = "on_track"
    else:
        result["status"] = "behind"

    return result

def compute_profile_analytics(data: dict) -> dict:
    """Build a per-year activity dashboard from a user's sync data using pandas.
    Looks at readingLog (dates the user opened a chapter) plus bookmarks/highlights
    to produce: an overall summary, and for every calendar year that has activity,
    a monthly breakdown, a day-of-week breakdown, the longest streak within that
    year, and the count of bookmarks added that year."""
    reading_log = data.get('readingLog', []) or []
    bookmarks = data.get('bookmarks', []) or []
    highlights = data.get('highlights', {}) or {}
    bible_year = data.get('bibleYear', {}) or {}

    result = {
        'years': [],
        'per_year': {},
        'overall': {
            'total_days_read': 0,
            'current_streak': 0,
            'longest_streak': 0,
            'first_read': None,
            'last_read': None,
            'total_bookmarks': len(bookmarks),
            'total_highlighted_verses': sum(len(v) for v in highlights.values()),
            'years_active': 0,
        },
        'bible_year': compute_bible_year_progress(bible_year),
    }

    try:
        unique_dates = sorted({dt.date.fromisoformat(d) for d in reading_log})
    except ValueError:
        unique_dates = []

    # ---- Reading plans progress + achievements (computed even with no reading history) ----
    streak = compute_streak(reading_log)

    # ---- Reading plans progress ----
    plans_data = data.get('plans', {}) or {}
    custom_plans = data.get('customPlans', {}) or {}
    plans_progress = {}
    for pid, p in plans_data.items():
        meta = READING_PLANS_BY_ID.get(pid) or custom_plans.get(pid)
        if not meta:
            continue
        completed = sorted(set(p.get("completed_days", []) or []))
        total = len(meta["plan"])
        plans_progress[pid] = {
            "id": pid,
            "title": meta["title"],
            "icon": meta["icon"],
            "color": meta["color"],
            "start_date": p.get("start_date"),
            "completed_count": len(completed),
            "total_days": total,
            "percent_complete": round((len(completed) / total) * 100, 1) if total else 0,
            "status": "completed" if (total and len(completed) >= total) else ("in_progress" if p.get("start_date") else "not_started"),
        }
    result['plans'] = plans_progress

    # ---- Achievements ----
    prayers = data.get('prayers', []) or []
    notes = data.get('notes', []) or []
    quiz_stats = data.get('quizStats', {}) or {}
    memory_state = data.get('memoryState', {}) or {}
    answered_prayers = [p for p in prayers if p.get('answered')]
    any_plan_completed = any(v.get('status') == 'completed' for v in plans_progress.values())
    bible_year_status = result['bible_year'].get('status')

    def earned(condition):
        return bool(condition)

    result['achievements'] = [
        {"id": "first_read", "title": "First Steps", "description": "Read your first chapter", "icon": "fa-book-open",
         "earned": earned(streak['total_days_read'] >= 1)},
        {"id": "streak_3", "title": "Faithful Three", "description": "Read 3 days in a row", "icon": "fa-fire",
         "earned": earned(streak['longest_streak'] >= 3)},
        {"id": "streak_7", "title": "Week Warrior", "description": "Read 7 days in a row", "icon": "fa-calendar-week",
         "earned": earned(streak['longest_streak'] >= 7)},
        {"id": "streak_30", "title": "Deeply Rooted", "description": "Read 30 days in a row", "icon": "fa-seedling",
         "earned": earned(streak['longest_streak'] >= 30)},
        {"id": "streak_100", "title": "Unshakeable", "description": "Read 100 days in a row", "icon": "fa-mountain",
         "earned": earned(streak['longest_streak'] >= 100)},
        {"id": "days_50", "title": "Dedicated Reader", "description": "Read on 50 different days", "icon": "fa-book-reader",
         "earned": earned(streak['total_days_read'] >= 50)},
        {"id": "days_365", "title": "Man of the Word", "description": "Read on 365 different days", "icon": "fa-crown",
         "earned": earned(streak['total_days_read'] >= 365)},
        {"id": "bookmarks_10", "title": "Collector", "description": "Save 10 bookmarks", "icon": "fa-bookmark",
         "earned": earned(len(bookmarks) >= 10)},
        {"id": "highlights_20", "title": "Highlighter", "description": "Highlight 20 verses", "icon": "fa-highlighter",
         "earned": earned(sum(len(v) for v in highlights.values()) >= 20)},
        {"id": "notes_10", "title": "Scribe", "description": "Write 10 personal notes", "icon": "fa-pen-nib",
         "earned": earned(len(notes) >= 10)},
        {"id": "prayers_10", "title": "Prayer Warrior", "description": "Add 10 prayers to your journal", "icon": "fa-hands-praying",
         "earned": earned(len(prayers) >= 10)},
        {"id": "prayer_answered", "title": "Answered!", "description": "Mark a prayer as answered", "icon": "fa-circle-check",
         "earned": earned(len(answered_prayers) >= 1)},
        {"id": "bible_year_complete", "title": "Finisher", "description": "Complete the Bible in a Year plan", "icon": "fa-flag-checkered",
         "earned": earned(bible_year_status == 'completed')},
        {"id": "plan_complete", "title": "Plan Completer", "description": "Complete any reading plan", "icon": "fa-list-check",
         "earned": earned(any_plan_completed)},
        {"id": "quiz_perfect", "title": "Quiz Champion", "description": "Score 100% on a Bible quiz", "icon": "fa-trophy",
         "earned": earned((quiz_stats.get('best_percentage') or 0) >= 100)},
        {"id": "quiz_50", "title": "Quiz Enthusiast", "description": "Answer 50 quiz questions", "icon": "fa-brain",
         "earned": earned((quiz_stats.get('total_answered') or 0) >= 50)},
        {"id": "memorize_5", "title": "Word Keeper", "description": "Save 5 verses to Memorize", "icon": "fa-bookmark",
         "earned": earned(len(memory_state) >= 5)},
        {"id": "memorize_mastered", "title": "Hidden in My Heart", "description": "Master a memorized verse", "icon": "fa-heart",
         "earned": earned(any((v.get('box') or 0) >= 5 for v in memory_state.values()))},
    ]


    if not unique_dates:
        return result

    # Reading-log activity, indexed with pandas for year/month/weekday grouping
    df = pd.DataFrame({'date': pd.to_datetime(unique_dates)})
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['weekday'] = df['date'].dt.weekday  # Monday = 0

    # Bookmarks-per-year, when timestamps are available
    bm_year_counts = {}
    if bookmarks:
        bm_df = pd.DataFrame(bookmarks)
        if 'timestamp' in bm_df.columns:
            bm_df['ts'] = pd.to_datetime(bm_df['timestamp'], errors='coerce')
            bm_df = bm_df.dropna(subset=['ts'])
            bm_year_counts = bm_df['ts'].dt.year.value_counts().to_dict()

    years = sorted(df['year'].unique().tolist(), reverse=True)
    result['years'] = [int(y) for y in years]

    for y in years:
        y_int = int(y)
        y_df = df[df['year'] == y]

        monthly_counts = y_df.groupby('month').size()
        monthly = [int(monthly_counts.get(m, 0)) for m in range(1, 13)]

        weekday_counts = y_df.groupby('weekday').size()
        weekday = [int(weekday_counts.get(d, 0)) for d in range(0, 7)]

        y_dates = sorted(y_df['date'].dt.date.tolist())
        longest_in_year = 0
        if y_dates:
            longest_in_year = 1
            run = 1
            for i in range(1, len(y_dates)):
                if (y_dates[i] - y_dates[i - 1]).days == 1:
                    run += 1
                else:
                    run = 1
                longest_in_year = max(longest_in_year, run)

        days_in_year = 366 if calendar.isleap(y_int) else 365
        days_read = int(len(y_df))
        best_month = None
        if any(monthly):
            best_month = monthly.index(max(monthly)) + 1

        result['per_year'][str(y_int)] = {
            'days_read': days_read,
            'monthly': monthly,
            'weekday': weekday,
            'longest_streak_in_year': longest_in_year,
            'bookmarks_added': int(bm_year_counts.get(y_int, 0)),
            'best_month': best_month,
            'active_percent': round((days_read / days_in_year) * 100, 1),
        }

    streak = compute_streak(reading_log)
    result['overall'] = {
        'total_days_read': streak['total_days_read'],
        'current_streak': streak['current_streak'],
        'longest_streak': streak['longest_streak'],
        'first_read': unique_dates[0].isoformat(),
        'last_read': streak['last_read'],
        'total_bookmarks': len(bookmarks),
        'total_highlighted_verses': sum(len(v) for v in highlights.values()),
        'years_active': len(years),
    }

    return result
