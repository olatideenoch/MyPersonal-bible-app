"""User sync-data persistence (JSON files) and push-subscription storage.

One JSON document per signed-in user plus a single file for browser push
subscriptions. These functions are the single choke point every route uses,
so swapping this module for a PostgreSQL-backed store later is a drop-in
change (see DATA_STORAGE.md).
"""
import datetime as dt
import json
import re
from pathlib import Path

from app.config import Config


def get_user_sync_file(user_id: str) -> Path:
    safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    return Config.SYNC_DATA_DIR / f"{safe_id}.json"

def load_user_sync_data(user_id: str) -> dict:
    sync_file = get_user_sync_file(user_id)
    if sync_file.exists():
        try:
            with open(sync_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading sync data: {e}")
    return {
        "bookmarks": [],
        "highlights": {},
        "highlightColors": {},
        "highlightLabels": {},
        "memoryState": {},
        "notes": [],
        "progress": {},
        "readingLog": [],
        "bibleYear": {"start_date": None, "completed_days": []},
        "plans": {},
        "customPlans": {},
        "prayers": [],
        "quizStats": {"attempts": 0, "total_correct": 0, "total_answered": 0, "best_percentage": 0.0, "history": []},
        "font_size": None,
        "preferred_version": None,
        "dailyActivity": {},
        "theme": None,
        "last_sync": None
    }

def save_user_sync_data(user_id: str, data: dict) -> bool:
    sync_file = get_user_sync_file(user_id)
    try:
        data["last_sync"] = dt.datetime.now().isoformat()
        with open(sync_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving sync data: {e}")
        return False

def merge_sync_data(local_data: dict, server_data: dict) -> dict:
    """Merge local and server sync data"""
    merged = {}
    
    # Merge bookmarks
    local_bookmarks = local_data.get("bookmarks", [])
    server_bookmarks = server_data.get("bookmarks", [])
    bookmark_map = {}
    for b in server_bookmarks + local_bookmarks:
        ref = b.get("reference", "")
        if ref not in bookmark_map or b.get("timestamp", "") > bookmark_map[ref].get("timestamp", ""):
            bookmark_map[ref] = b
    merged["bookmarks"] = list(bookmark_map.values())
    
    # Merge highlights
    merged["highlights"] = {}
    server_highlights = server_data.get("highlights", {})
    local_highlights = local_data.get("highlights", {})
    all_chapters = set(server_highlights.keys()) | set(local_highlights.keys())
    for chapter in all_chapters:
        server_verses = set(server_highlights.get(chapter, []))
        local_verses = set(local_highlights.get(chapter, []))
        merged["highlights"][chapter] = list(server_verses | local_verses)
    
    # Merge reading log (union of dates read, deduped and sorted)
    server_log = set(server_data.get("readingLog", []))
    local_log = set(local_data.get("readingLog", []))
    merged["readingLog"] = sorted(server_log | local_log)
    
    # Merge Bible-in-a-Year progress (union completed days, keep the earliest start date)
    server_by = server_data.get("bibleYear") or {}
    local_by = local_data.get("bibleYear") or {}
    merged_completed = set(server_by.get("completed_days", [])) | set(local_by.get("completed_days", []))
    server_start = server_by.get("start_date")
    local_start = local_by.get("start_date")
    if server_start and local_start:
        merged_start = min(server_start, local_start)
    else:
        merged_start = server_start or local_start
    merged["bibleYear"] = {"start_date": merged_start, "completed_days": sorted(merged_completed)}
    
    # Merge progress
    merged["progress"] = {}
    server_progress = server_data.get("progress", {})
    local_progress = local_data.get("progress", {})
    all_progress = set(server_progress.keys()) | set(local_progress.keys())
    for key in all_progress:
        server_val = server_progress.get(key, {})
        local_val = local_progress.get(key, {})
        server_ts = server_val.get("timestamp", "")
        local_ts = local_val.get("timestamp", "")
        merged["progress"][key] = server_val if server_ts > local_ts else local_val
    
    # Merge highlight colors (chapter -> {verse: color}; local wins on conflicts)
    merged["highlightColors"] = {}
    server_colors = server_data.get("highlightColors", {}) or {}
    local_colors = local_data.get("highlightColors", {}) or {}
    for chapter in set(server_colors.keys()) | set(local_colors.keys()):
        colors = dict(server_colors.get(chapter, {}) or {})
        colors.update(local_colors.get(chapter, {}) or {})
        merged["highlightColors"][chapter] = colors

    # Merge highlight labels (chapter -> {verse: {label, text, updated_at}})
    merged["highlightLabels"] = {}
    server_labels = server_data.get("highlightLabels", {}) or {}
    local_labels = local_data.get("highlightLabels", {}) or {}
    for chapter in set(server_labels.keys()) | set(local_labels.keys()):
        s_ch = server_labels.get(chapter, {}) or {}
        l_ch = local_labels.get(chapter, {}) or {}
        labels = {}
        for verse in set(s_ch.keys()) | set(l_ch.keys()):
            s_v = s_ch.get(verse) or {}
            l_v = l_ch.get(verse) or {}
            s_stamp = s_v.get("updated_at") or ""
            l_stamp = l_v.get("updated_at") or ""
            labels[verse] = l_v if l_stamp >= s_stamp else s_v
        merged["highlightLabels"][chapter] = labels

    # Merge memory (memorize) state (reference -> {box, due, last})
    merged["memoryState"] = {}
    server_mem = server_data.get("memoryState", {}) or {}
    local_mem = local_data.get("memoryState", {}) or {}
    for ref in set(server_mem.keys()) | set(local_mem.keys()):
        s_v = server_mem.get(ref) or {}
        l_v = local_mem.get(ref) or {}
        s_stamp = l_v.get("last") or ""
        l_stamp = l_v.get("last") or ""
        merged["memoryState"][ref] = l_v if l_stamp >= s_stamp else s_v

    # Merge custom reading plans (local definitions win; union of both)
    merged["customPlans"] = {}
    server_custom = server_data.get("customPlans", {}) or {}
    local_custom = local_data.get("customPlans", {}) or {}
    for plan_id in set(server_custom.keys()) | set(local_custom.keys()):
        merged["customPlans"][plan_id] = local_custom.get(plan_id) or server_custom.get(plan_id)

    # Merge notes (dedupe by id; newest updated_at wins)
    note_map = {}
    for n in (server_data.get("notes", []) or []) + (local_data.get("notes", []) or []):
        nid = n.get("id") or n.get("created_at")
        if not nid:
            continue
        n_stamp = n.get("updated_at") or n.get("created_at") or ""
        if nid not in note_map or n_stamp > (note_map[nid].get("updated_at") or note_map[nid].get("created_at") or ""):
            note_map[nid] = n
    merged["notes"] = sorted(note_map.values(), key=lambda n: n.get("created_at") or "")

    # Merge reading-plan progress (union completed days, earliest start date)
    merged["plans"] = {}
    server_plans = server_data.get("plans", {}) or {}
    local_plans = local_data.get("plans", {}) or {}
    for plan_id in set(server_plans.keys()) | set(local_plans.keys()):
        sp = server_plans.get(plan_id, {}) or {}
        lp = local_plans.get(plan_id, {}) or {}
        s_start = sp.get("start_date")
        l_start = lp.get("start_date")
        merged_start = (min(s_start, l_start) if (s_start and l_start) else (s_start or l_start))
        merged["plans"][plan_id] = {
            "start_date": merged_start,
            "completed_days": sorted(set(sp.get("completed_days", []) or []) | set(lp.get("completed_days", []) or []))
        }

    # Merge prayer journal (dedupe by id; newest updated_at wins)
    prayer_map = {}
    for p in (server_data.get("prayers", []) or []) + (local_data.get("prayers", []) or []):
        pid = p.get("id") or p.get("created_at")
        if not pid:
            continue
        p_stamp = p.get("updated_at") or p.get("created_at") or ""
        if pid not in prayer_map or p_stamp > (prayer_map[pid].get("updated_at") or prayer_map[pid].get("created_at") or ""):
            prayer_map[pid] = p
    merged["prayers"] = sorted(prayer_map.values(), key=lambda p: p.get("created_at") or "")

    # Merge quiz stats (keep the best of both copies; dedupe history by date+score)
    def _merge_quiz_stats(s, l):
        s = s or {}
        l = l or {}
        history = {}
        for h in (s.get("history") or []) + (l.get("history") or []):
            key = f"{h.get('date', '')}_{h.get('score', '')}_{h.get('total', '')}_{h.get('category', '')}"
            history[key] = h
        hist = sorted(history.values(), key=lambda h: h.get("date") or "")[-100:]
        return {
            "attempts": max(s.get("attempts", 0) or 0, l.get("attempts", 0) or 0),
            "total_correct": max(s.get("total_correct", 0) or 0, l.get("total_correct", 0) or 0),
            "total_answered": max(s.get("total_answered", 0) or 0, l.get("total_answered", 0) or 0),
            "best_percentage": max(s.get("best_percentage", 0) or 0, l.get("best_percentage", 0) or 0),
            "history": hist,
        }

    merged["quizStats"] = _merge_quiz_stats(server_data.get("quizStats"), local_data.get("quizStats"))

    # Merge preferred version (local wins if set)
    merged["preferred_version"] = local_data.get("preferred_version") or server_data.get("preferred_version")

    # Merge daily activity (date -> {chapters, minutes}). Devices track
    # independently, so take the max per field to avoid double counting.
    merged["dailyActivity"] = {}
    server_da = server_data.get("dailyActivity", {}) or {}
    local_da = local_data.get("dailyActivity", {}) or {}
    for date_key in set(server_da.keys()) | set(local_da.keys()):
        s_entry = server_da.get(date_key, {}) or {}
        l_entry = local_da.get(date_key, {}) or {}
        merged["dailyActivity"][date_key] = {
            "chapters": max(int(s_entry.get("chapters", 0) or 0), int(l_entry.get("chapters", 0) or 0)),
            "minutes": round(max(float(s_entry.get("minutes", 0) or 0), float(l_entry.get("minutes", 0) or 0)), 1),
        }

    merged["font_size"] = local_data.get("font_size") or server_data.get("font_size")
    merged["theme"] = local_data.get("theme") or server_data.get("theme")
    
    return merged

def _push_subs_file() -> Path:
    return Config.SYNC_DATA_DIR / "push_subscriptions.json"

def _load_push_subs() -> list:
    f = _push_subs_file()
    if f.exists():
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except Exception as e:
            print(f"Error loading push subscriptions: {e}")
    return []

def _save_push_subs(subs: list) -> bool:
    try:
        with open(_push_subs_file(), 'w', encoding='utf-8') as fh:
            json.dump(subs, fh)
        return True
    except Exception as e:
        print(f"Error saving push subscriptions: {e}")
        return False
