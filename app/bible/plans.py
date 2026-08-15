"""Built-in reading plans and the Bible-in-a-Year plan builder."""
import math

from app.bible.books import BIBLE_BOOKS


def _build_bible_in_a_year_plan(days: int = 365) -> list:
    all_chapters = []
    for book in BIBLE_BOOKS:
        for ch in range(1, book["chapters"] + 1):
            all_chapters.append({"book": book["name"], "slug": book["slug"], "chapter": ch})

    total = len(all_chapters)
    base = total // days
    remainder = total % days

    # Spread the "extra chapter" days evenly across the year instead of bunching them at the end
    extra_days = set()
    if remainder:
        for j in range(remainder):
            extra_days.add(round(j * days / remainder))

    def label_groups(readings):
        parts = []
        for g in readings:
            if g["start"] == g["end"]:
                parts.append(f"{g['book']} {g['start']}")
            else:
                parts.append(f"{g['book']} {g['start']}-{g['end']}")
        return "; ".join(parts)

    plan = []
    idx = 0
    for day_num in range(1, days + 1):
        count = max(base + (1 if (day_num - 1) in extra_days else 0), 1)
        day_chapters = all_chapters[idx: idx + count]
        idx += count

        groups = []
        for c in day_chapters:
            if groups and groups[-1]["slug"] == c["slug"] and c["chapter"] == groups[-1]["end"] + 1:
                groups[-1]["end"] = c["chapter"]
            else:
                groups.append({"book": c["book"], "slug": c["slug"], "start": c["chapter"], "end": c["chapter"]})

        plan.append({"day": day_num, "readings": groups, "label": label_groups(groups)})

    # Fold any leftover chapters (rounding edge case) into the final day
    if idx < total:
        for c in all_chapters[idx:]:
            last_readings = plan[-1]["readings"]
            if last_readings and last_readings[-1]["slug"] == c["slug"] and c["chapter"] == last_readings[-1]["end"] + 1:
                last_readings[-1]["end"] = c["chapter"]
            else:
                last_readings.append({"book": c["book"], "slug": c["slug"], "start": c["chapter"], "end": c["chapter"]})
        plan[-1]["label"] = label_groups(plan[-1]["readings"])

    return plan

BIBLE_YEAR_PLAN = _build_bible_in_a_year_plan(365)

BIBLE_YEAR_TOTAL_DAYS = len(BIBLE_YEAR_PLAN)

def _label_groups(groups: list) -> str:
    """Turn a list of contiguous reading groups into a human label."""
    parts = []
    for g in groups:
        if g["start"] == g["end"]:
            parts.append(f"{g['book']} {g['start']}")
        else:
            parts.append(f"{g['book']} {g['start']}-{g['end']}")
    return "; ".join(parts)

def _group_chapters(day_chapters: list) -> list:
    """Group consecutive chapter objects of the same book into ranges."""
    groups = []
    for c in day_chapters:
        if groups and groups[-1]["slug"] == c["slug"] and c["chapter"] == groups[-1]["end"] + 1:
            groups[-1]["end"] = c["chapter"]
        else:
            groups.append({"book": c["book"], "slug": c["slug"], "start": c["chapter"], "end": c["chapter"]})
    return groups

def _build_plan(book_names: list, chapters_per_day: int) -> list:
    """Build a reading plan from a subset of books, grouped by chapters-per-day."""
    all_chapters = []
    for name in book_names:
        book = next((b for b in BIBLE_BOOKS if b["name"] == name), None)
        if not book:
            continue
        for ch in range(1, book["chapters"] + 1):
            all_chapters.append({"book": book["name"], "slug": book["slug"], "chapter": ch})

    total = len(all_chapters)
    if not total:
        return []
    days = math.ceil(total / chapters_per_day)
    plan = []
    idx = 0
    for day_num in range(1, days + 1):
        day_chapters = all_chapters[idx: idx + chapters_per_day]
        idx += chapters_per_day
        groups = _group_chapters(day_chapters)
        plan.append({"day": day_num, "readings": groups, "label": _label_groups(groups)})
    return plan

NT_BOOKS = [b["name"] for b in BIBLE_BOOKS if b["testament"] == "New"]

OT_BOOKS = [b["name"] for b in BIBLE_BOOKS if b["testament"] == "Old"]

GOSPELS = ["Matthew", "Mark", "Luke", "John"]

EPISTLES = [
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
    "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude",
]

READING_PLANS = [
    {
        "id": "bible-90",
        "title": "Bible in 90 Days",
        "icon": "fa-book-bible",
        "color": "#9a6a1e",
        "description": "Read the entire Bible from Genesis to Revelation in three months. A steady, achievable pace for a complete overview of Scripture.",
        "plan": _build_plan(OT_BOOKS + NT_BOOKS, 14),
    },
    {
        "id": "bible-180",
        "title": "Bible in 180 Days",
        "icon": "fa-road",
        "color": "#8a6d1e",
        "description": "Read the whole Bible in six months at a comfortable, unhurried pace — perfect for building a lifelong daily habit.",
        "plan": _build_bible_in_a_year_plan(180),
    },
    {
        "id": "nt-30",
        "title": "New Testament in 30 Days",
        "icon": "fa-cross",
        "color": "#3f6d4e",
        "description": "Immerse yourself in the life of Jesus and the birth of the early church — all 27 New Testament books in one month.",
        "plan": _build_plan(NT_BOOKS, 9),
    },
    {
        "id": "ot-60",
        "title": "Old Testament in 60 Days",
        "icon": "fa-scroll",
        "color": "#7a4b2a",
        "description": "Journey through the Law, the Prophets and the Writings of the Old Testament in two months.",
        "plan": _build_plan(OT_BOOKS, 16),
    },
    {
        "id": "psalms-30",
        "title": "Psalms in 30 Days",
        "icon": "fa-music",
        "color": "#5b3a7a",
        "description": "Five Psalms a day for thirty days — the ancient prayer book of Israel, one song at a time.",
        "plan": _build_plan(["Psalms"], 5),
    },
    {
        "id": "proverbs-31",
        "title": "Proverbs in 31 Days",
        "icon": "fa-lightbulb",
        "color": "#8a6d1e",
        "description": "One chapter of Proverbs every day of the month. Timeless wisdom for daily decisions.",
        "plan": _build_plan(["Proverbs"], 1),
    },
    {
        "id": "gospels-14",
        "title": "The Gospels in 14 Days",
        "icon": "fa-dove",
        "color": "#4a6d7a",
        "description": "Walk with Jesus through Matthew, Mark, Luke and John in two weeks — four portraits, one Saviour.",
        "plan": _build_plan(GOSPELS, 7),
    },
    {
        "id": "epistles-14",
        "title": "The Epistles in 14 Days",
        "icon": "fa-envelope-open-text",
        "color": "#6d4a7a",
        "description": "Every New Testament letter — Romans through Jude — in two weeks. The church's instruction manual, cover to cover.",
        "plan": _build_plan(EPISTLES, 9),
    },
]

READING_PLANS_BY_ID = {p["id"]: p for p in READING_PLANS}
