from flask import Flask, render_template, url_for, redirect, request, jsonify, send_file, session, Response
import requests
import datetime as dt
import calendar
import random
import os
import re
import json
import io
import secrets
import html
import math
from datetime import timedelta
from typing import List
from pathlib import Path
from requests_oauthlib import OAuth2Session
import pandas as pd

from dotenv import load_dotenv

# Allow OAuth over HTTP for local development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

# Resend API configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_API_URL = "https://api.resend.com/emails"

# Voice RSS API configuration
VOICE_RSS_API_KEY = os.environ.get("VOICE_RSS_API_KEY")
VOICE_RSS_URL = "https://api.voicerss.org/"

# Bible API configurations
BIBLE_API_BASE = "https://bible-api.com"
API_BIBLE_KEY = os.environ.get("API_BIBLE_KEY")
API_BIBLE_BASE = "https://rest.api.bible/v1"
API_BIBLE_SECONDARY_KEY = os.environ.get("API_BIBLE_SECONDARY_KEY")
API_BIBLE_SECONDARY_BASE = "https://rest.api.bible/v1"

# Create sync data directory if it doesn't exist
# Create sync data directory if it doesn't exist. Points at a Render Persistent
# Disk mount path in production (set SYNC_DATA_DIR in the Render dashboard, e.g.
# /var/data/sync_data) so this survives redeploys/restarts. Falls back to a local
# "sync_data" folder for local dev, which is fine since local dev doesn't redeploy.
SYNC_DATA_DIR = Path(os.environ.get("SYNC_DATA_DIR", "sync_data"))
SYNC_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ========== BIBLE DATA STRUCTURE ==========

BIBLE_BOOKS = [
    {"name": "Genesis", "chapters": 50, "slug": "genesis"},
    {"name": "Exodus", "chapters": 40, "slug": "exodus"},
    {"name": "Leviticus", "chapters": 27, "slug": "leviticus"},
    {"name": "Numbers", "chapters": 36, "slug": "numbers"},
    {"name": "Deuteronomy", "chapters": 34, "slug": "deuteronomy"},
    {"name": "Joshua", "chapters": 24, "slug": "joshua"},
    {"name": "Judges", "chapters": 21, "slug": "judges"},
    {"name": "Ruth", "chapters": 4, "slug": "ruth"},
    {"name": "1 Samuel", "chapters": 31, "slug": "1-samuel"},
    {"name": "2 Samuel", "chapters": 24, "slug": "2-samuel"},
    {"name": "1 Kings", "chapters": 22, "slug": "1-kings"},
    {"name": "2 Kings", "chapters": 25, "slug": "2-kings"},
    {"name": "1 Chronicles", "chapters": 29, "slug": "1-chronicles"},
    {"name": "2 Chronicles", "chapters": 36, "slug": "2-chronicles"},
    {"name": "Ezra", "chapters": 10, "slug": "ezra"},
    {"name": "Nehemiah", "chapters": 13, "slug": "nehemiah"},
    {"name": "Esther", "chapters": 10, "slug": "esther"},
    {"name": "Job", "chapters": 42, "slug": "job"},
    {"name": "Psalms", "chapters": 150, "slug": "psalms"},
    {"name": "Proverbs", "chapters": 31, "slug": "proverbs"},
    {"name": "Ecclesiastes", "chapters": 12, "slug": "ecclesiastes"},
    {"name": "Song of Solomon", "chapters": 8, "slug": "song-of-solomon"},
    {"name": "Isaiah", "chapters": 66, "slug": "isaiah"},
    {"name": "Jeremiah", "chapters": 52, "slug": "jeremiah"},
    {"name": "Lamentations", "chapters": 5, "slug": "lamentations"},
    {"name": "Ezekiel", "chapters": 48, "slug": "ezekiel"},
    {"name": "Daniel", "chapters": 12, "slug": "daniel"},
    {"name": "Hosea", "chapters": 14, "slug": "hosea"},
    {"name": "Joel", "chapters": 3, "slug": "joel"},
    {"name": "Amos", "chapters": 9, "slug": "amos"},
    {"name": "Obadiah", "chapters": 1, "slug": "obadiah"},
    {"name": "Jonah", "chapters": 4, "slug": "jonah"},
    {"name": "Micah", "chapters": 7, "slug": "micah"},
    {"name": "Nahum", "chapters": 3, "slug": "nahum"},
    {"name": "Habakkuk", "chapters": 3, "slug": "habakkuk"},
    {"name": "Zephaniah", "chapters": 3, "slug": "zephaniah"},
    {"name": "Haggai", "chapters": 2, "slug": "haggai"},
    {"name": "Zechariah", "chapters": 14, "slug": "zechariah"},
    {"name": "Malachi", "chapters": 4, "slug": "malachi"},
    {"name": "Matthew", "chapters": 28, "slug": "matthew"},
    {"name": "Mark", "chapters": 16, "slug": "mark"},
    {"name": "Luke", "chapters": 24, "slug": "luke"},
    {"name": "John", "chapters": 21, "slug": "john"},
    {"name": "Acts", "chapters": 28, "slug": "acts"},
    {"name": "Romans", "chapters": 16, "slug": "romans"},
    {"name": "1 Corinthians", "chapters": 16, "slug": "1-corinthians"},
    {"name": "2 Corinthians", "chapters": 13, "slug": "2-corinthians"},
    {"name": "Galatians", "chapters": 6, "slug": "galatians"},
    {"name": "Ephesians", "chapters": 6, "slug": "ephesians"},
    {"name": "Philippians", "chapters": 4, "slug": "philippians"},
    {"name": "Colossians", "chapters": 4, "slug": "colossians"},
    {"name": "1 Thessalonians", "chapters": 5, "slug": "1-thessalonians"},
    {"name": "2 Thessalonians", "chapters": 3, "slug": "2-thessalonians"},
    {"name": "1 Timothy", "chapters": 6, "slug": "1-timothy"},
    {"name": "2 Timothy", "chapters": 4, "slug": "2-timothy"},
    {"name": "Titus", "chapters": 3, "slug": "titus"},
    {"name": "Philemon", "chapters": 1, "slug": "philemon"},
    {"name": "Hebrews", "chapters": 13, "slug": "hebrews"},
    {"name": "James", "chapters": 5, "slug": "james"},
    {"name": "1 Peter", "chapters": 5, "slug": "1-peter"},
    {"name": "2 Peter", "chapters": 3, "slug": "2-peter"},
    {"name": "1 John", "chapters": 5, "slug": "1-john"},
    {"name": "2 John", "chapters": 1, "slug": "2-john"},
    {"name": "3 John", "chapters": 1, "slug": "3-john"},
    {"name": "Jude", "chapters": 1, "slug": "jude"},
    {"name": "Revelation", "chapters": 22, "slug": "revelation"},
]

# Add testament information
for i, book in enumerate(BIBLE_BOOKS):
    book['testament'] = 'Old' if i < 39 else 'New'


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


# ========== MULTIPLE READING PLANS ==========

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
]

READING_PLANS_BY_ID = {p["id"]: p for p in READING_PLANS}


# ========== TOPIC VERSE COLLECTIONS (KJV - public domain) ==========

TOPIC_VERSES = [
    {
        "slug": "love", "title": "God's Love", "icon": "fa-heart",
        "description": "The love of God is the heartbeat of the whole Bible. Meditate on these verses whenever you need to be reminded of how deeply you are loved.",
        "verses": [
            {"reference": "John 3:16", "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."},
            {"reference": "1 John 4:8", "text": "He that loveth not knoweth not God; for God is love."},
            {"reference": "1 John 4:19", "text": "We love him, because he first loved us."},
            {"reference": "Romans 5:8", "text": "But God commendeth his love toward us, in that, while we were yet sinners, Christ died for us."},
            {"reference": "1 Corinthians 13:4", "text": "Charity suffereth long, and is kind; charity envieth not; charity vaunteth not itself, is not puffed up,"},
            {"reference": "1 Corinthians 13:13", "text": "And now abideth faith, hope, charity, these three; but the greatest of these is charity."},
            {"reference": "John 13:34", "text": "A new commandment I give unto you, That ye love one another; as I have loved you, that ye also love one another."},
            {"reference": "John 15:13", "text": "Greater love hath no man than this, that a man lay down his life for his friends."},
        ],
    },
    {
        "slug": "faith", "title": "Faith", "icon": "fa-mountain",
        "description": "Faith is the foundation of the Christian life. These verses will strengthen your trust in the God who keeps every promise.",
        "verses": [
            {"reference": "Hebrews 11:1", "text": "Now faith is the substance of things hoped for, the evidence of things not seen."},
            {"reference": "Hebrews 11:6", "text": "But without faith it is impossible to please him: for he that cometh to God must believe that he is, and that he is a rewarder of them that diligently seek him."},
            {"reference": "2 Corinthians 5:7", "text": "(For we walk by faith, not by sight:)"},
            {"reference": "Romans 10:17", "text": "So then faith cometh by hearing, and hearing by the word of God."},
            {"reference": "Mark 11:24", "text": "Therefore I say unto you, What things soever ye desire, when ye pray, believe that ye receive them, and ye shall have them."},
            {"reference": "Matthew 17:20", "text": "And Jesus said unto them, Because of your unbelief: for verily I say unto you, If ye have faith as a grain of mustard seed, ye shall say unto this mountain, Remove hence to yonder place; and it shall remove; and nothing shall be impossible unto you."},
            {"reference": "1 John 5:4", "text": "For whatsoever is born of God overcometh the world: and this is the victory that overcometh the world, even our faith."},
            {"reference": "James 1:6", "text": "But let him ask in faith, nothing wavering. For he that wavereth is like a wave of the sea driven with the wind and tossed."},
        ],
    },
    {
        "slug": "hope", "title": "Hope", "icon": "fa-sun",
        "description": "Biblical hope is not wishful thinking — it is confident expectation in a faithful God. Let these promises lift your heart.",
        "verses": [
            {"reference": "Jeremiah 29:11", "text": "For I know the thoughts that I think toward you, saith the LORD, thoughts of peace, and not of evil, to give you an expected end."},
            {"reference": "Romans 15:13", "text": "Now the God of hope fill you with all joy and peace in believing, that ye may abound in hope, through the power of the Holy Ghost."},
            {"reference": "Isaiah 40:31", "text": "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint."},
            {"reference": "Psalm 42:11", "text": "Why art thou cast down, O my soul? and why art thou disquieted within me? hope thou in God: for I shall yet praise him, who is the health of my countenance, and my God."},
            {"reference": "Romans 12:12", "text": "Rejoicing in hope; patient in tribulation; continuing instant in prayer;"},
            {"reference": "Lamentations 3:22-23", "text": "It is of the LORD's mercies that we are not consumed, because his compassions fail not. They are new every morning: great is thy faithfulness."},
            {"reference": "Psalm 71:14", "text": "But I will hope continually, and will yet praise thee more and more."},
            {"reference": "1 Peter 1:3", "text": "Blessed be the God and Father of our Lord Jesus Christ, which according to his abundant mercy hath begotten us again unto a lively hope by the resurrection of Jesus Christ from the dead,"},
        ],
    },
    {
        "slug": "peace", "title": "Peace", "icon": "fa-dove",
        "description": "In a troubled world, God offers a peace that passes understanding. Rest in these promises of calm for your soul.",
        "verses": [
            {"reference": "John 14:27", "text": "Peace I leave with you, my peace I give unto you: not as the world giveth, give I unto you. Let not your heart be troubled, neither let it be afraid."},
            {"reference": "Philippians 4:6-7", "text": "Be careful for nothing; but in every thing by prayer and supplication with thanksgiving let your requests be made known unto God. And the peace of God, which passeth all understanding, shall keep your hearts and minds through Christ Jesus."},
            {"reference": "Isaiah 26:3", "text": "Thou wilt keep him in perfect peace, whose mind is stayed on thee: because he trusteth in thee."},
            {"reference": "Colossians 3:15", "text": "And let the peace of God rule in your hearts, to the which also ye are called in one body; and be ye thankful."},
            {"reference": "Psalm 29:11", "text": "The LORD will give strength unto his people; the LORD will bless his people with peace."},
            {"reference": "Romans 5:1", "text": "Therefore being justified by faith, we have peace with God through our Lord Jesus Christ:"},
            {"reference": "Matthew 5:9", "text": "Blessed are the peacemakers: for they shall be called the children of God."},
            {"reference": "Psalm 4:8", "text": "I will both lay me down in peace, and sleep: for thou, LORD, only makest me dwell in safety."},
        ],
    },
    {
        "slug": "strength", "title": "Strength", "icon": "fa-dumbbell",
        "description": "When you feel weak, God's strength is made perfect. Draw power from these verses for every battle you face.",
        "verses": [
            {"reference": "Philippians 4:13", "text": "I can do all things through Christ which strengtheneth me."},
            {"reference": "Isaiah 41:10", "text": "Fear thou not; for I am with thee: be not dismayed; for I am thy God: I will strengthen thee; yea, I will help thee; yea, I will uphold thee with the right hand of my righteousness."},
            {"reference": "Psalm 46:1", "text": "God is our refuge and strength, a very present help in trouble."},
            {"reference": "Nehemiah 8:10", "text": "Then he said unto them, Go your way, eat the fat, and drink the sweet, and send portions unto them for whom nothing is prepared: for this day is holy unto our Lord: neither be ye sorry; for the joy of the LORD is your strength."},
            {"reference": "Isaiah 40:29", "text": "He giveth power to the faint; and to them that have no might he increaseth strength."},
            {"reference": "Ephesians 6:10", "text": "Finally, my brethren, be strong in the Lord, and in the power of his might."},
            {"reference": "Psalm 28:7", "text": "The LORD is my strength and my shield; my heart trusted in him, and I am helped: therefore my heart greatly rejoiceth; and with my song will I praise him."},
            {"reference": "2 Corinthians 12:9", "text": "And he said unto me, My grace is sufficient for thee: for my strength is made perfect in weakness. Most gladly therefore will I rather glory in my infirmities, that the power of Christ may rest upon me."},
        ],
    },
    {
        "slug": "comfort", "title": "Comfort & Anxiety", "icon": "fa-hand-holding-heart",
        "description": "Cast your cares on the Lord — He cares for you. These verses are medicine for anxious hearts.",
        "verses": [
            {"reference": "Psalm 23:4", "text": "Yea, though I walk through the valley of the shadow of death, I will fear no evil: for thou art with me; thy rod and thy staff they comfort me."},
            {"reference": "1 Peter 5:7", "text": "Casting all your care upon him; for he careth for you."},
            {"reference": "2 Timothy 1:7", "text": "For God hath not given us the spirit of fear; but of power, and of love, and of a sound mind."},
            {"reference": "Joshua 1:9", "text": "Have not I commanded thee? Be strong and of a good courage; be not afraid, neither be thou dismayed: for the LORD thy God is with thee whithersoever thou goest."},
            {"reference": "Psalm 34:4", "text": "I sought the LORD, and he heard me, and delivered me from all my fears."},
            {"reference": "Matthew 11:28", "text": "Come unto me, all ye that labour and are heavy laden, and I will give you rest."},
            {"reference": "John 14:1", "text": "Let not your heart be troubled: ye believe in God, believe also in me."},
            {"reference": "Psalm 56:3", "text": "What time I am afraid, I will trust in thee."},
            {"reference": "Matthew 6:34", "text": "Take therefore no thought for the morrow: for the morrow shall take thought for the things of itself. Sufficient unto the day is the evil thereof."},
        ],
    },
    {
        "slug": "forgiveness", "title": "Forgiveness", "icon": "fa-hands-praying",
        "description": "Forgiven people forgive. Discover the freedom that comes from receiving and giving forgiveness.",
        "verses": [
            {"reference": "1 John 1:9", "text": "If we confess our sins, he is faithful and just to forgive us our sins, and to cleanse us from all unrighteousness."},
            {"reference": "Ephesians 4:32", "text": "And be ye kind one to another, tenderhearted, forgiving one another, even as God for Christ's sake hath forgiven you."},
            {"reference": "Matthew 6:14", "text": "For if ye forgive men their trespasses, your heavenly Father will also forgive you:"},
            {"reference": "Colossians 3:13", "text": "Forbearing one another, and forgiving one another, if any man have a quarrel against any: even as Christ forgave you, so also do ye."},
            {"reference": "Psalm 103:12", "text": "As far as the east is from the west, so far hath he removed our transgressions from us."},
            {"reference": "Isaiah 1:18", "text": "Come now, and let us reason together, saith the LORD: though your sins be as scarlet, they shall be as white as snow; though they be red like crimson, they shall be as wool."},
            {"reference": "Luke 6:37", "text": "Judge not, and ye shall not be judged: condemn not, and ye shall not be condemned: forgive, and ye shall be forgiven:"},
            {"reference": "Acts 3:19", "text": "Repent ye therefore, and be converted, that your sins may be blotted out, when the times of refreshing shall come from the presence of the Lord;"},
        ],
    },
    {
        "slug": "healing", "title": "Healing", "icon": "fa-heart-pulse",
        "description": "Jehovah Rapha — the God who heals. Pray these scriptures over your body, mind and broken places.",
        "verses": [
            {"reference": "Jeremiah 17:14", "text": "Heal me, O LORD, and I shall be healed; save me, and I shall be saved: for thou art my praise."},
            {"reference": "Psalm 147:3", "text": "He healeth the broken in heart, and bindeth up their wounds."},
            {"reference": "Isaiah 53:5", "text": "But he was wounded for our transgressions, he was bruised for our iniquities: the chastisement of our peace was upon him; and with his stripes we are healed."},
            {"reference": "James 5:15", "text": "And the prayer of faith shall save the sick, and the Lord shall raise him up; and if he have committed sins, they shall be forgiven him."},
            {"reference": "Exodus 15:26", "text": "And said, If thou wilt diligently hearken to the voice of the LORD thy God, and wilt do that which is right in his sight, and wilt give ear to his commandments, and keep all his statutes, I will put none of these diseases upon thee, which I have brought upon the Egyptians: for I am the LORD that healeth thee."},
            {"reference": "Psalm 103:2-3", "text": "Bless the LORD, O my soul, and forget not all his benefits: Who forgiveth all thine iniquities; who healeth all thy diseases;"},
            {"reference": "3 John 1:2", "text": "Beloved, I wish above all things that thou mayest prosper and be in health, even as thy soul prospereth."},
            {"reference": "Psalm 30:2", "text": "O LORD my God, I cried unto thee, and thou hast healed me."},
        ],
    },
    {
        "slug": "wisdom", "title": "Wisdom", "icon": "fa-lightbulb",
        "description": "Wisdom is more precious than gold. Learn to walk skilfully through life with these verses as your guide.",
        "verses": [
            {"reference": "Proverbs 3:5-6", "text": "Trust in the LORD with all thine heart; and lean not unto thine own understanding. In all thy ways acknowledge him, and he shall direct thy paths."},
            {"reference": "James 1:5", "text": "If any of you lack wisdom, let him ask of God, that giveth to all men liberally, and upbraideth not; and it shall be given him."},
            {"reference": "Proverbs 9:10", "text": "The fear of the LORD is the beginning of wisdom: and the knowledge of the holy is understanding."},
            {"reference": "Proverbs 4:7", "text": "Wisdom is the principal thing; therefore get wisdom: and with all thy getting get understanding."},
            {"reference": "Proverbs 1:7", "text": "The fear of the LORD is the beginning of knowledge: but fools despise wisdom and instruction."},
            {"reference": "Psalm 111:10", "text": "The fear of the LORD is the beginning of wisdom: a good understanding have all they that do his commandments: his praise endureth for ever."},
            {"reference": "Proverbs 16:16", "text": "How much better is it to get wisdom than gold! and to get understanding rather to be chosen than silver!"},
            {"reference": "Colossians 3:16", "text": "Let the word of Christ dwell in you richly in all wisdom; teaching and admonishing one another in psalms and hymns and spiritual songs, singing with grace in your hearts to the Lord."},
        ],
    },
    {
        "slug": "prayer", "title": "Prayer", "icon": "fa-hands-praying",
        "description": "Prayer is simply talking with your Father. Let these verses fuel your prayer life with boldness and faith.",
        "verses": [
            {"reference": "Matthew 7:7", "text": "Ask, and it shall be given you; seek, and ye shall find; knock, and it shall be opened unto you:"},
            {"reference": "Jeremiah 33:3", "text": "Call unto me, and I will answer thee, and shew thee great and mighty things, which thou knowest not."},
            {"reference": "1 Thessalonians 5:16-18", "text": "Rejoice evermore. Pray without ceasing. In every thing give thanks: for this is the will of God in Christ Jesus concerning you."},
            {"reference": "James 5:16", "text": "Confess your faults one to another, and pray one for another, that ye may be healed. The effectual fervent prayer of a righteous man availeth much."},
            {"reference": "Psalm 145:18", "text": "The LORD is nigh unto all them that call upon him, to all that call upon him in truth."},
            {"reference": "Matthew 6:6", "text": "But thou, when thou prayest, enter into thy closet, and when thou hast shut thy door, pray to thy Father which is in secret; and thy Father which seeth in secret shall reward thee openly."},
            {"reference": "1 John 5:14", "text": "And this is the confidence that we have in him, that, if we ask any thing according to his will, he heareth us:"},
            {"reference": "Philippians 4:6", "text": "Be careful for nothing; but in every thing by prayer and supplication with thanksgiving let your requests be made known unto God."},
        ],
    },
    {
        "slug": "gratitude", "title": "Gratitude", "icon": "fa-face-smile",
        "description": "A thankful heart changes everything. Count your blessings with these verses on thanksgiving and praise.",
        "verses": [
            {"reference": "1 Thessalonians 5:18", "text": "In every thing give thanks: for this is the will of God in Christ Jesus concerning you."},
            {"reference": "Psalm 100:4", "text": "Enter into his gates with thanksgiving, and into his courts with praise: be thankful unto him, and bless his name."},
            {"reference": "Psalm 107:1", "text": "O give thanks unto the LORD, for he is good: for his mercy endureth for ever."},
            {"reference": "Psalm 118:24", "text": "This is the day which the LORD hath made; we will rejoice and be glad in it."},
            {"reference": "Colossians 3:17", "text": "And whatsoever ye do in word or deed, do all in the name of the Lord Jesus, giving thanks to God and the Father by him."},
            {"reference": "Ephesians 5:20", "text": "Giving thanks always for all things unto God and the Father in the name of our Lord Jesus Christ;"},
            {"reference": "Psalm 9:1", "text": "I will praise thee, O LORD, with my whole heart; I will shew forth all thy marvellous works."},
            {"reference": "Psalm 136:1", "text": "O give thanks unto the LORD; for he is good: for his mercy endureth for ever."},
        ],
    },
    {
        "slug": "courage", "title": "Courage", "icon": "fa-shield-halved",
        "description": "Be strong and courageous — God goes before you. These verses will put steel in your spine for hard days.",
        "verses": [
            {"reference": "Deuteronomy 31:6", "text": "Be strong and of a good courage, fear not, nor be afraid of them: for the LORD thy God, he it is that doth go with thee; he will not fail thee, nor forsake thee."},
            {"reference": "Joshua 1:9", "text": "Have not I commanded thee? Be strong and of a good courage; be not afraid, neither be thou dismayed: for the LORD thy God is with thee whithersoever thou goest."},
            {"reference": "1 Corinthians 16:13", "text": "Watch ye, stand fast in the faith, quit you like men, be strong."},
            {"reference": "Psalm 27:1", "text": "The LORD is my light and my salvation; whom shall I fear? the LORD is the strength of my life; of whom shall I be afraid?"},
            {"reference": "Psalm 31:24", "text": "Be of good courage, and he shall strengthen your heart, all ye that hope in the LORD."},
            {"reference": "Matthew 14:27", "text": "But straightway Jesus spake unto them, saying, Be of good cheer; it is I; be not afraid."},
            {"reference": "Hebrews 13:6", "text": "So that we may boldly say, The Lord is my helper, and I will not fear what man shall do unto me."},
            {"reference": "Isaiah 41:10", "text": "Fear thou not; for I am with thee: be not dismayed; for I am thy God: I will strengthen thee; yea, I will help thee; yea, I will uphold thee with the right hand of my righteousness."},
        ],
    },
    {
        "slug": "guidance", "title": "Guidance", "icon": "fa-compass",
        "description": "God promises to direct your steps. Seek His guidance for every decision with these scriptures.",
        "verses": [
            {"reference": "Psalm 32:8", "text": "I will instruct thee and teach thee in the way which thou shalt go: I will guide thee with mine eye."},
            {"reference": "Psalm 119:105", "text": "Thy word is a lamp unto my feet, and a light unto my path."},
            {"reference": "Isaiah 30:21", "text": "And thine ears shall hear a word behind thee, saying, This is the way, walk ye in it, when ye turn to the right hand, and when ye turn to the left."},
            {"reference": "Psalm 37:23", "text": "The steps of a good man are ordered by the LORD: and he delighteth in his way."},
            {"reference": "Proverbs 16:9", "text": "A man's heart deviseth his way: but the LORD directeth his steps."},
            {"reference": "Psalm 25:4", "text": "Shew me thy ways, O LORD; teach me thy paths."},
            {"reference": "Psalm 23:2-3", "text": "He maketh me to lie down in green pastures: he leadeth me beside the still waters. He restoreth my soul: he leadeth me in the paths of righteousness for his name's sake."},
            {"reference": "Proverbs 3:5-6", "text": "Trust in the LORD with all thine heart; and lean not unto thine own understanding. In all thy ways acknowledge him, and he shall direct thy paths."},
        ],
    },
    {
        "slug": "provision", "title": "Provision", "icon": "fa-hand-holding-dollar",
        "description": "Jehovah Jireh — the LORD will provide. Trust Him for your daily bread with these promises.",
        "verses": [
            {"reference": "Philippians 4:19", "text": "But my God shall supply all your need according to his riches in glory by Christ Jesus."},
            {"reference": "Matthew 6:33", "text": "But seek ye first the kingdom of God, and his righteousness; and all these things shall be added unto you."},
            {"reference": "Psalm 23:1", "text": "The LORD is my shepherd; I shall not want."},
            {"reference": "Psalm 37:25", "text": "I have been young, and now am old; yet have I not seen the righteous forsaken, nor his seed begging bread."},
            {"reference": "Malachi 3:10", "text": "Bring ye all the tithes into the storehouse, that there may be meat in mine house, and prove me now herewith, saith the LORD of hosts, if I will not open you the windows of heaven, and pour you out a blessing, that there shall not be room enough to receive it."},
            {"reference": "Psalm 34:10", "text": "The young lions do lack, and suffer hunger: but they that seek the LORD shall not want any good thing."},
            {"reference": "Genesis 22:14", "text": "And Abraham called the name of that place Jehovahjireh: as it is said to this day, In the mount of the LORD it shall be seen."},
            {"reference": "Luke 12:24", "text": "Consider the ravens: for they neither sow nor reap; which neither have storehouse nor barn; and God feedeth them: how much more are ye better than the fowls?"},
        ],
    },
    {
        "slug": "joy", "title": "Joy", "icon": "fa-champagne-glasses",
        "description": "The joy of the LORD is your strength. Rejoice today with these verses that overflow with gladness.",
        "verses": [
            {"reference": "Psalm 16:11", "text": "Thou wilt shew me the path of life: in thy presence is fulness of joy; at thy right hand there are pleasures for evermore."},
            {"reference": "John 15:11", "text": "These things have I spoken unto you, that my joy might remain in you, and that your joy might be full."},
            {"reference": "Psalm 30:5", "text": "For his anger endureth but a moment; in his favour is life: weeping may endure for a night, but joy cometh in the morning."},
            {"reference": "Philippians 4:4", "text": "Rejoice in the Lord alway: and again I say, Rejoice."},
            {"reference": "Galatians 5:22", "text": "But the fruit of the Spirit is love, joy, peace, longsuffering, gentleness, goodness, faith,"},
            {"reference": "Psalm 5:11", "text": "But let all those that put their trust in thee rejoice: let them ever shout for joy, because thou defendest them: let them also that love thy name be joyful in thee."},
            {"reference": "Psalm 118:24", "text": "This is the day which the LORD hath made; we will rejoice and be glad in it."},
            {"reference": "Nehemiah 8:10", "text": "Then he said unto them, Go your way, eat the fat, and drink the sweet, and send portions unto them for whom nothing is prepared: for this day is holy unto our Lord: neither be ye sorry; for the joy of the LORD is your strength."},
        ],
    },
    {
        "slug": "protection", "title": "Protection", "icon": "fa-shield-heart",
        "description": "God is your refuge and fortress. Pray these verses of protection over yourself and your loved ones.",
        "verses": [
            {"reference": "Psalm 91:1-2", "text": "He that dwelleth in the secret place of the most High shall abide under the shadow of the Almighty. I will say of the LORD, He is my refuge and my fortress: my God; in him will I trust."},
            {"reference": "Psalm 121:7-8", "text": "The LORD shall preserve thee from all evil: he shall preserve thy soul. The LORD shall preserve thy going out and thy coming in from this time forth, and even for evermore."},
            {"reference": "2 Thessalonians 3:3", "text": "But the Lord is faithful, who shall stablish you, and keep you from evil."},
            {"reference": "Proverbs 18:10", "text": "The name of the LORD is a strong tower: the righteous runneth into it, and is safe."},
            {"reference": "Psalm 34:7", "text": "The angel of the LORD encampeth round about them that fear him, and delivereth them."},
            {"reference": "Nahum 1:7", "text": "The LORD is good, a strong hold in the day of trouble; and he knoweth them that trust in him."},
            {"reference": "Psalm 121:1-2", "text": "I will lift up mine eyes unto the hills, from whence cometh my help. My help cometh from the LORD, which made heaven and earth."},
            {"reference": "John 10:28", "text": "And I give unto them eternal life; and they shall never perish, neither shall any man pluck them out of my hand."},
        ],
    },
    {
        "slug": "patience", "title": "Patience", "icon": "fa-hourglass-half",
        "description": "God's timing is perfect, even when it feels slow. Learn to wait well with these scriptures.",
        "verses": [
            {"reference": "Galatians 6:9", "text": "And let us not be weary in well doing: for in due season we shall reap, if we faint not."},
            {"reference": "James 1:3-4", "text": "Knowing this, that the trying of your faith worketh patience. But let patience have her perfect work, that ye may be perfect and entire, wanting nothing."},
            {"reference": "Psalm 27:14", "text": "Wait on the LORD: be of good courage, and he shall strengthen thine heart: wait, I say, on the LORD."},
            {"reference": "Romans 8:25", "text": "But if we hope for that we see not, then do we with patience wait for it."},
            {"reference": "Ecclesiastes 7:8", "text": "Better is the end of a thing than the beginning thereof: and the patient in spirit is better than the proud in spirit."},
            {"reference": "Hebrews 12:1", "text": "Wherefore seeing we also are compassed about with so great a cloud of witnesses, let us lay aside every weight, and the sin which doth so easily beset us, and let us run with patience the race that is set before us,"},
            {"reference": "Romans 12:12", "text": "Rejoicing in hope; patient in tribulation; continuing instant in prayer;"},
            {"reference": "Isaiah 40:31", "text": "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint."},
        ],
    },
    {
        "slug": "salvation", "title": "Salvation", "icon": "fa-cross",
        "description": "The greatest gift ever given. Meditate on the wonder of salvation through these core verses of the gospel.",
        "verses": [
            {"reference": "Romans 10:9", "text": "That if thou shalt confess with thy mouth the Lord Jesus, and shalt believe in thine heart that God hath raised him from the dead, thou shalt be saved."},
            {"reference": "Acts 4:12", "text": "Neither is there salvation in any other: for there is none other name under heaven given among men, whereby we must be saved."},
            {"reference": "Ephesians 2:8-9", "text": "For by grace are ye saved through faith; and that not of yourselves: it is the gift of God: Not of works, lest any man should boast."},
            {"reference": "John 14:6", "text": "Jesus saith unto him, I am the way, the truth, and the life: no man cometh unto the Father, but by me."},
            {"reference": "Romans 6:23", "text": "For the wages of sin is death; but the gift of God is eternal life through Jesus Christ our Lord."},
            {"reference": "Acts 16:31", "text": "And they said, Believe on the Lord Jesus Christ, and thou shalt be saved, and thy house."},
            {"reference": "Titus 3:5", "text": "Not by works of righteousness which we have done, but according to his mercy he saved us, by the washing of regeneration, and renewing of the Holy Ghost;"},
            {"reference": "John 3:16", "text": "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."},
        ],
    },
    {
        "slug": "humility", "title": "Humility", "icon": "fa-person-praying",
        "description": "God gives grace to the humble. Grow in Christ-like humility with these verses.",
        "verses": [
            {"reference": "James 4:10", "text": "Humble yourselves in the sight of the Lord, and he shall lift you up."},
            {"reference": "James 4:6", "text": "But he giveth more grace. Wherefore he saith, God resisteth the proud, but giveth grace unto the humble."},
            {"reference": "Philippians 2:3", "text": "Let nothing be done through strife or vainglory; but in lowliness of mind let each esteem other better than themselves."},
            {"reference": "Micah 6:8", "text": "He hath shewed thee, O man, what is good; and what doth the LORD require of thee, but to do justly, and to love mercy, and to walk humbly with thy God?"},
            {"reference": "Proverbs 22:4", "text": "By humility and the fear of the LORD are riches, and honour, and life."},
            {"reference": "Matthew 23:12", "text": "And whosoever shall exalt himself shall be abased; and he that shall humble himself shall be exalted."},
            {"reference": "1 Peter 5:6", "text": "Humble yourselves therefore under the mighty hand of God, that he may exalt you in due time:"},
            {"reference": "Proverbs 11:2", "text": "When pride cometh, then cometh shame: but with the lowly is wisdom."},
        ],
    },
    {
        "slug": "new-beginnings", "title": "New Beginnings", "icon": "fa-seedling",
        "description": "God specialises in fresh starts. Step into your new season with these verses of renewal.",
        "verses": [
            {"reference": "2 Corinthians 5:17", "text": "Therefore if any man be in Christ, he is a new creature: old things are passed away; behold, all things are become new."},
            {"reference": "Isaiah 43:19", "text": "Behold, I will do a new thing; now it shall spring forth; shall ye not know it? I will even make a way in the wilderness, and rivers in the desert."},
            {"reference": "Lamentations 3:22-23", "text": "It is of the LORD's mercies that we are not consumed, because his compassions fail not. They are new every morning: great is thy faithfulness."},
            {"reference": "Isaiah 43:18", "text": "Remember ye not the former things, neither consider the things of old."},
            {"reference": "Philippians 3:13-14", "text": "Brethren, I count not myself to have apprehended: but this one thing I do, forgetting those things which are behind, and reaching forth unto those things which are before, I press toward the mark for the prize of the high calling of God in Christ Jesus."},
            {"reference": "Ezekiel 36:26", "text": "A new heart also will I give you, and a new spirit will I put within you: and I will take away the stony heart out of your flesh, and I will give you an heart of flesh."},
            {"reference": "Psalm 40:3", "text": "And he hath put a new song in my mouth, even praise unto our God: many shall see it, and fear, and shall trust in the LORD."},
            {"reference": "Revelation 21:5", "text": "And he that sat upon the throne said, Behold, I make all things new. And he said unto me, Write: for these words are true and faithful."},
        ],
    },
]

TOPICS_BY_SLUG = {t["slug"]: t for t in TOPIC_VERSES}


# ========== BIBLE QUIZ ==========

QUIZ_QUESTIONS = [
    # --- General / Structure ---
    {"question": "How many books are in the Bible?", "options": ["39", "66", "73", "27"], "answer": 1, "category": "Structure", "difficulty": "easy", "reference": "The 66-book Protestant canon: 39 Old Testament + 27 New Testament"},
    {"question": "How many books are in the Old Testament?", "options": ["27", "66", "39", "12"], "answer": 2, "category": "Structure", "difficulty": "easy", "reference": ""},
    {"question": "How many books are in the New Testament?", "options": ["39", "12", "66", "27"], "answer": 3, "category": "Structure", "difficulty": "easy", "reference": ""},
    {"question": "What is the first book of the Bible?", "options": ["Exodus", "Genesis", "Psalms", "Matthew"], "answer": 1, "category": "Structure", "difficulty": "easy", "reference": "Genesis 1:1"},
    {"question": "What is the last book of the Bible?", "options": ["Jude", "Revelation", "Malachi", "Acts"], "answer": 1, "category": "Structure", "difficulty": "easy", "reference": ""},
    {"question": "Which is the longest book in the Bible?", "options": ["Isaiah", "Genesis", "Psalms", "Jeremiah"], "answer": 2, "category": "Structure", "difficulty": "medium", "reference": "Psalms has 150 chapters"},
    {"question": "What is the shortest verse in the Bible?", "options": ["\"God is love.\"", "\"Jesus wept.\"", "\"Pray without ceasing.\"", "\"Rejoice evermore.\""], "answer": 1, "category": "Structure", "difficulty": "medium", "reference": "John 11:35"},
    {"question": "What is the longest chapter in the Bible?", "options": ["Psalm 23", "Isaiah 53", "Psalm 119", "Genesis 1"], "answer": 2, "category": "Structure", "difficulty": "medium", "reference": "Psalm 119 has 176 verses"},
    {"question": "What is the final word of the Bible?", "options": ["Hallelujah", "Amen", "Peace", "Forever"], "answer": 1, "category": "Structure", "difficulty": "medium", "reference": "Revelation 22:21"},
    # --- Old Testament ---
    {"question": "Who built the ark to survive the great flood?", "options": ["Abraham", "Moses", "Noah", "Elijah"], "answer": 2, "category": "Old Testament", "difficulty": "easy", "reference": "Genesis 6"},
    {"question": "How many days and nights did rain fall during the flood?", "options": ["7", "12", "40", "100"], "answer": 2, "category": "Old Testament", "difficulty": "easy", "reference": "Genesis 7:12"},
    {"question": "Who led the Israelites out of slavery in Egypt?", "options": ["Joshua", "Aaron", "Moses", "Joseph"], "answer": 2, "category": "Old Testament", "difficulty": "easy", "reference": "Exodus 3"},
    {"question": "How many plagues did God send upon Egypt?", "options": ["7", "10", "12", "40"], "answer": 1, "category": "Old Testament", "difficulty": "easy", "reference": "Exodus 7-12"},
    {"question": "On which mountain did Moses receive the Ten Commandments?", "options": ["Mount Carmel", "Mount Zion", "Mount Sinai", "Mount Ararat"], "answer": 2, "category": "Old Testament", "difficulty": "easy", "reference": "Exodus 19-20"},
    {"question": "What food did God provide from heaven in the wilderness?", "options": ["Bread and fish", "Manna", "Honey and locusts", "Olives"], "answer": 1, "category": "Old Testament", "difficulty": "easy", "reference": "Exodus 16"},
    {"question": "Who was the first king of Israel?", "options": ["David", "Solomon", "Saul", "Samuel"], "answer": 2, "category": "Old Testament", "difficulty": "medium", "reference": "1 Samuel 10"},
    {"question": "Who killed the giant Goliath?", "options": ["Samson", "David", "Jonathan", "Joshua"], "answer": 1, "category": "Old Testament", "difficulty": "easy", "reference": "1 Samuel 17"},
    {"question": "Which king was famous for his God-given wisdom?", "options": ["Saul", "David", "Solomon", "Hezekiah"], "answer": 2, "category": "Old Testament", "difficulty": "easy", "reference": "1 Kings 3"},
    {"question": "Who was thrown into the lions' den for praying to God?", "options": ["Joseph", "Daniel", "Jeremiah", "Jonah"], "answer": 1, "category": "Old Testament", "difficulty": "easy", "reference": "Daniel 6"},
    {"question": "What were the names of Daniel's three faithful friends?", "options": ["Peter, James and John", "Shadrach, Meshach and Abednego", "Ananias, Sapphira and Silas", "Abraham, Isaac and Jacob"], "answer": 1, "category": "Old Testament", "difficulty": "medium", "reference": "Daniel 3"},
    {"question": "Who was swallowed by a great fish?", "options": ["Jonah", "Job", "Moses", "Noah"], "answer": 0, "category": "Old Testament", "difficulty": "easy", "reference": "Jonah 1:17"},
    {"question": "Who was sold into slavery by his own brothers?", "options": ["Moses", "Joseph", "Benjamin", "Jacob"], "answer": 1, "category": "Old Testament", "difficulty": "easy", "reference": "Genesis 37"},
    {"question": "Who interpreted Pharaoh's dreams of seven fat and seven thin cows?", "options": ["Daniel", "Moses", "Joseph", "Aaron"], "answer": 2, "category": "Old Testament", "difficulty": "medium", "reference": "Genesis 41"},
    {"question": "Who was the oldest man recorded in the Bible?", "options": ["Adam", "Noah", "Methuselah", "Abraham"], "answer": 2, "category": "Old Testament", "difficulty": "medium", "reference": "Genesis 5:27 — he lived 969 years"},
    {"question": "How many years did Methuselah live?", "options": ["777", "930", "969", "120"], "answer": 2, "category": "Old Testament", "difficulty": "hard", "reference": "Genesis 5:27"},
    {"question": "Which city's walls fell down after the Israelites marched around it?", "options": ["Babylon", "Jericho", "Nineveh", "Jerusalem"], "answer": 1, "category": "Old Testament", "difficulty": "easy", "reference": "Joshua 6"},
    {"question": "Who succeeded Moses and led Israel into the Promised Land?", "options": ["Aaron", "Caleb", "Joshua", "Samuel"], "answer": 2, "category": "Old Testament", "difficulty": "medium", "reference": "Joshua 1"},
    {"question": "Who was the strongest man in the Bible?", "options": ["David", "Goliath", "Samson", "Hercules"], "answer": 2, "category": "Old Testament", "difficulty": "easy", "reference": "Judges 13-16"},
    {"question": "Who was Ruth's mother-in-law?", "options": ["Esther", "Hannah", "Naomi", "Sarah"], "answer": 2, "category": "Old Testament", "difficulty": "medium", "reference": "Ruth 1"},
    {"question": "Which book is mostly a collection of 150 songs and prayers?", "options": ["Proverbs", "Psalms", "Lamentations", "Ecclesiastes"], "answer": 1, "category": "Old Testament", "difficulty": "easy", "reference": ""},
    {"question": "Who is traditionally credited with writing most of the Psalms?", "options": ["Solomon", "Asaph", "David", "Moses"], "answer": 2, "category": "Old Testament", "difficulty": "medium", "reference": ""},
    {"question": "Which prophet was taken up to heaven in a whirlwind with a chariot of fire?", "options": ["Isaiah", "Elijah", "Elisha", "Ezekiel"], "answer": 1, "category": "Old Testament", "difficulty": "medium", "reference": "2 Kings 2:11"},
    {"question": "Who received the promise of a son in his old age and became the father of many nations?", "options": ["Isaac", "Jacob", "Abraham", "Joseph"], "answer": 2, "category": "Old Testament", "difficulty": "easy", "reference": "Genesis 17"},
    # --- New Testament / Life of Jesus ---
    {"question": "Where was Jesus born?", "options": ["Nazareth", "Jerusalem", "Bethlehem", "Capernaum"], "answer": 2, "category": "Life of Jesus", "difficulty": "easy", "reference": "Matthew 2:1"},
    {"question": "Where did Jesus grow up as a boy?", "options": ["Bethlehem", "Nazareth", "Egypt", "Jericho"], "answer": 1, "category": "Life of Jesus", "difficulty": "easy", "reference": "Matthew 2:23"},
    {"question": "Who baptised Jesus in the River Jordan?", "options": ["Peter", "Andrew", "John the Baptist", "James"], "answer": 2, "category": "Life of Jesus", "difficulty": "easy", "reference": "Matthew 3"},
    {"question": "How long did Jesus fast in the wilderness?", "options": ["7 days", "30 days", "40 days", "1 year"], "answer": 2, "category": "Life of Jesus", "difficulty": "easy", "reference": "Matthew 4:2"},
    {"question": "What was Jesus' first recorded miracle?", "options": ["Healing a blind man", "Turning water into wine", "Feeding the 5,000", "Walking on water"], "answer": 1, "category": "Life of Jesus", "difficulty": "easy", "reference": "John 2 — at the wedding in Cana"},
    {"question": "How many disciples did Jesus choose?", "options": ["7", "10", "12", "70"], "answer": 2, "category": "Life of Jesus", "difficulty": "easy", "reference": "Luke 6:13"},
    {"question": "Who betrayed Jesus for thirty pieces of silver?", "options": ["Peter", "Judas Iscariot", "Thomas", "Matthew"], "answer": 1, "category": "Life of Jesus", "difficulty": "easy", "reference": "Matthew 26:14-15"},
    {"question": "How many times did Peter deny knowing Jesus?", "options": ["Once", "Twice", "Three times", "Seven times"], "answer": 2, "category": "Life of Jesus", "difficulty": "easy", "reference": "Luke 22:34"},
    {"question": "Who was raised from the dead after four days in the tomb?", "options": ["Jairus' daughter", "Lazarus", "Stephen", "Dorcas"], "answer": 1, "category": "Life of Jesus", "difficulty": "medium", "reference": "John 11"},
    {"question": "Who climbed a sycamore tree to see Jesus?", "options": ["Nicodemus", "Bartimaeus", "Zacchaeus", "Matthew"], "answer": 2, "category": "Life of Jesus", "difficulty": "medium", "reference": "Luke 19:1-10"},
    {"question": "What did Jesus say is the greatest commandment?", "options": ["Keep the Sabbath", "Love God and love your neighbour", "Give to the poor", "Honour your parents"], "answer": 1, "category": "Life of Jesus", "difficulty": "medium", "reference": "Matthew 22:36-40"},
    {"question": "With what did Jesus feed the 5,000?", "options": ["Seven loaves and a few fish", "Five loaves and two fish", "Manna from heaven", "Two loaves and five fish"], "answer": 1, "category": "Life of Jesus", "difficulty": "easy", "reference": "Matthew 14:13-21"},
    {"question": "What does the name \"Emmanuel\" mean?", "options": ["Saviour of all", "God with us", "Prince of Peace", "Lamb of God"], "answer": 1, "category": "Life of Jesus", "difficulty": "medium", "reference": "Matthew 1:23"},
    {"question": "On the road to which city did Jesus appear to two disciples after His resurrection?", "options": ["Jerusalem", "Emmaus", "Jericho", "Damascus"], "answer": 1, "category": "Life of Jesus", "difficulty": "hard", "reference": "Luke 24:13-35"},
    # --- The Early Church ---
    {"question": "Who was the first Christian martyr?", "options": ["Peter", "James", "Stephen", "Paul"], "answer": 2, "category": "Early Church", "difficulty": "medium", "reference": "Acts 7"},
    {"question": "Who is called the \"Apostle to the Gentiles\"?", "options": ["Peter", "Paul", "Barnabas", "Silas"], "answer": 1, "category": "Early Church", "difficulty": "medium", "reference": "Romans 11:13"},
    {"question": "How many New Testament books are traditionally attributed to Paul?", "options": ["4", "13", "21", "27"], "answer": 1, "category": "Early Church", "difficulty": "hard", "reference": ""},
    {"question": "What happened on the Day of Pentecost?", "options": ["The temple was rebuilt", "The Holy Spirit descended on the believers", "Jesus ascended", "Paul was converted"], "answer": 1, "category": "Early Church", "difficulty": "medium", "reference": "Acts 2"},
    {"question": "On the road to which city was Saul (Paul) converted?", "options": ["Rome", "Jerusalem", "Damascus", "Antioch"], "answer": 2, "category": "Early Church", "difficulty": "medium", "reference": "Acts 9"},
    {"question": "Where was Paul shipwrecked on his way to Rome?", "options": ["Crete", "Malta", "Cyprus", "Sicily"], "answer": 1, "category": "Early Church", "difficulty": "hard", "reference": "Acts 28:1"},
    {"question": "Who wrote the book of Revelation?", "options": ["Peter", "Paul", "John", "Jude"], "answer": 2, "category": "Early Church", "difficulty": "easy", "reference": "Revelation 1:1"},
    {"question": "How many spiritual gifts (fruit of the Spirit) are listed in Galatians?", "options": ["7", "9", "12", "10"], "answer": 1, "category": "Early Church", "difficulty": "medium", "reference": "Galatians 5:22-23"},
    {"question": "Who wrote the Gospel that begins with \"In the beginning was the Word\"?", "options": ["Matthew", "Mark", "Luke", "John"], "answer": 3, "category": "Early Church", "difficulty": "medium", "reference": "John 1:1"},
    {"question": "Which of these was a tax collector before following Jesus?", "options": ["Matthew", "Luke", "Simon", "Bartholomew"], "answer": 0, "category": "Life of Jesus", "difficulty": "medium", "reference": "Matthew 9:9"},
]

QUIZ_CATEGORIES = sorted({q["category"] for q in QUIZ_QUESTIONS})


# ========== DAILY DEVOTIONALS (31-day monthly cycle) ==========

DAILY_DEVOTIONALS = [
    {"day": 1, "title": "A Fresh Start", "verse_ref": "2 Corinthians 5:17", "verse": "Therefore if any man be in Christ, he is a new creature: old things are passed away; behold, all things are become new.", "theme": "New Beginnings",
     "reflection": "Every morning God offers you what He offered the world at the cross: a brand new start. The failures of yesterday do not have to write the story of today. When you came to Christ, you became a new creation — and that renewal is not a one-time event but a daily reality. You are not the sum of your mistakes; you are the workmanship of a Redeemer who makes all things new. Stop dragging yesterday's guilt into today's grace. Step into the new thing God is doing.", 
     "prayer": "Father, thank You for fresh mercies every morning. Help me to leave the past at the cross and to walk today as the new creation You have made me. Amen.",
     "action": "Write down one thing you will release to God today and one new habit you will begin."},
    {"day": 2, "title": "Unshakeable Trust", "verse_ref": "Proverbs 3:5-6", "verse": "Trust in the LORD with all thine heart; and lean not unto thine own understanding. In all thy ways acknowledge him, and he shall direct thy paths.", "theme": "Trust",
     "reflection": "Trusting God with all your heart means trusting Him with the parts of your life you do not understand. Our own understanding is limited — it cannot see around the corner of tomorrow. But the One who numbers the stars also numbers your steps. When the road ahead looks unclear, acknowledge Him; invite Him into the decision, the worry, the waiting. He has never failed to direct a single trusting heart, and He will not begin with yours.",
     "prayer": "Lord, I confess I often lean on my own understanding. Teach me to trust You completely, and to let You direct every path I walk. Amen.",
     "action": "Surrender one decision you have been trying to figure out alone."},
    {"day": 3, "title": "Strength for Today", "verse_ref": "Philippians 4:13", "verse": "I can do all things through Christ which strengtheneth me.", "theme": "Strength",
     "reflection": "Notice the order in this verse: through Christ, then strength. The strength does not begin with you — it flows from your connection to Him. Whatever this day demands of you, Christ is not asking you to face it with your own reserves. His strength is made perfect in your weakness. So stop telling yourself you cannot; instead tell Him you need Him. The same power that raised Jesus from the dead lives in you and is more than enough for this day.",
     "prayer": "Lord Jesus, I come to You in my weakness. Be my strength today — for every task, every challenge and every moment I feel I cannot go on. Amen.",
     "action": "Name one thing you feel weak about, and speak Philippians 4:13 over it."},
    {"day": 4, "title": "The God Who Provides", "verse_ref": "Matthew 6:33", "verse": "But seek ye first the kingdom of God, and his righteousness; and all these things shall be added unto you.", "theme": "Provision",
     "reflection": "Worry is the noise of a heart that has forgotten its Provider. Jesus tells us plainly: put God's kingdom first, and every need will be handled by the Father who clothes the lilies and feeds the birds. Seeking first does not mean ignoring your responsibilities — it means ordering your life around God and trusting Him with the results. Your provision is tied to your priority. Chase Him, and provision will chase you.",
     "prayer": "Heavenly Father, I choose to seek You first today — before my fears, before my plans. Provide for my needs according to Your riches, and keep my heart at rest in You. Amen.",
     "action": "Before making your plans today, spend the first moments in prayer and the Word."},
    {"day": 5, "title": "Worry-Free Living", "verse_ref": "1 Peter 5:7", "verse": "Casting all your care upon him; for he careth for you.", "theme": "Peace",
     "reflection": "The word 'casting' is deliberate — it means throwing something away from yourself with force, the way a fisherman throws a net. God is inviting you to hurl every anxiety onto His shoulders. He does not merely tolerate your concerns; He cares for you personally, tenderly, completely. The reason you can sleep tonight is not that your problems are small, but that your God is great. Take each worry by name and cast it. Then leave it there.",
     "prayer": "Lord, I cast every burden I am carrying onto You now. Thank You that You care for me more than I can understand. Give me Your peace in exchange. Amen.",
     "action": "List your top three worries, pray over each by name, and deliberately hand them over."},
    {"day": 6, "title": "Forgiven and Free", "verse_ref": "1 John 1:9", "verse": "If we confess our sins, he is faithful and just to forgive us our sins, and to cleanse us from all unrighteousness.", "theme": "Forgiveness",
     "reflection": "Guilt is a heavy chain, but confession is the key that unlocks it. God's promise is not merely to overlook sin but to cleanse — to wash away the stain completely. He is faithful: He will always keep His word. He is just: the price was fully paid at Calvary, so forgiveness is legally yours. Whatever you have done, bring it into the light. The blood of Jesus has never met a sin it could not wash away.",
     "prayer": "Father, I confess my sins to You without hiding. Thank You for the cross that cleanses me completely. Help me to walk in the freedom of Your forgiveness today. Amen.",
     "action": "If you have wronged someone, take a step toward making it right today."},
    {"day": 7, "title": "The Power of Gratitude", "verse_ref": "1 Thessalonians 5:18", "verse": "In every thing give thanks: for this is the will of God in Christ Jesus concerning you.", "theme": "Gratitude",
     "reflection": "Gratitude is not a feeling you wait for — it is a discipline you practise. God calls you to give thanks in every thing, not for every thing. Even in difficulty there is always something: the breath in your lungs, a promise kept, a mercy renewed. A thankful heart is a magnet for joy and a shield against bitterness. When you cannot change your circumstances, you can still change your focus — and thanksgiving changes the way you see everything.",
     "prayer": "Lord, open my eyes to Your goodness today. Teach me to count blessings even in hard seasons, and fill my mouth with praise. Amen.",
     "action": "Write down five things you are grateful for and thank God for each one."},
    {"day": 8, "title": "Courage in the Storm", "verse_ref": "Joshua 1:9", "verse": "Have not I commanded thee? Be strong and of a good courage; be not afraid, neither be thou dismayed: for the LORD thy God is with thee whithersoever thou goest.", "theme": "Courage",
     "reflection": "Courage is not the absence of fear but the presence of God. Three times in one verse God says: do not be afraid, do not be dismayed. The command is repeated because the battle is real — but so is the promise. You never go anywhere alone; wherever your feet take you today, He is already there. Let that truth steady you. The God who parts seas and levels walls goes before you into every room, every challenge, every unknown.",
     "prayer": "Lord, I choose courage today, not because I am strong, but because You are with me. Go before me and make a way. Amen.",
     "action": "Step into one thing you have been avoiding out of fear."},
    {"day": 9, "title": "Waiting Well", "verse_ref": "Isaiah 40:31", "verse": "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint.", "theme": "Patience",
     "reflection": "Waiting on God is not wasted time — it is strength being stored up. The eagle does not fight the wind; it waits for the thermal and rises. Waiting on the Lord means staying close to Him while He works behind the scenes. Your season of waiting is not a delay of His plan; it is part of it. Keep hoping, keep praying, keep showing up. Renewal comes to those who wait with expectation, not resignation.",
     "prayer": "Father, in my waiting, renew my strength. Keep my heart expectant and my feet steady. Help me to trust Your perfect timing. Amen.",
     "action": "Identify one promise you are waiting on and write it down as a prayer."},
    {"day": 10, "title": "The Shepherd's Care", "verse_ref": "Psalm 23:1", "verse": "The LORD is my shepherd; I shall not want.", "theme": "Provision",
     "reflection": "A shepherd's entire job is the wellbeing of the sheep — their food, their safety, their direction, their rest. When David declares the Lord as his shepherd, he is declaring total dependence and total provision. 'I shall not want' is not a demand but a settled confidence: if the Shepherd owns everything and cares for me, I lack nothing I truly need. Today you can follow with peace, because the One leading you is good.",
     "prayer": "Lord, You are my Shepherd. Lead me to green pastures and still waters today, and quiet every anxious want in my heart. Amen.",
     "action": "Rest in God today: take time to simply be still and know He is God."},
    {"day": 11, "title": "Love Like Jesus", "verse_ref": "John 13:34", "verse": "A new commandment I give unto you, That ye love one another; as I have loved you, that ye also love one another.", "theme": "Love",
     "reflection": "Jesus did not ask us to love one another the way we feel like loving — He set His own love as the standard. His love washed dirty feet, ate with outcasts, forgave betrayers and died for enemies. That is a high bar, and only one source can supply it: the love of God poured into our hearts by the Holy Spirit. Every act of patience, kindness and forgiveness today is a small sermon about the God you serve. Love loudly, love practically.",
     "prayer": "Lord Jesus, fill me with Your love so that I may love others the way You have loved me — patiently, generously, sacrificially. Amen.",
     "action": "Show deliberate kindness to someone who cannot repay you today."},
    {"day": 12, "title": "Faith That Moves Mountains", "verse_ref": "Hebrews 11:1", "verse": "Now faith is the substance of things hoped for, the evidence of things not seen.", "theme": "Faith",
     "reflection": "Faith is not blind optimism — it is substance and evidence. It gives weight to the promises of God in the courtroom of your heart. When you cannot see the outcome, faith is the deed of ownership you hold. The heroes of Hebrews 11 were ordinary people who took God at His word. Faith does not require you to understand everything; it requires you to trust the One who does. Feed your faith with the Word, and it will carry you further than your sight ever could.",
     "prayer": "Lord, increase my faith. Help me to trust Your promises even when I cannot see how You will fulfil them. Amen.",
     "action": "Memorise one promise from Scripture and stand on it all day."},
    {"day": 13, "title": "The Gift of Peace", "verse_ref": "John 14:27", "verse": "Peace I leave with you, my peace I give unto you: not as the world giveth, give I unto you. Let not your heart be troubled, neither let it be afraid.", "theme": "Peace",
     "reflection": "Jesus' peace is not the world's peace. The world offers peace when circumstances are calm; Jesus offers peace in the middle of the storm. It is a peace that does not depend on the news, the bank balance or the opinions of others — it is anchored in His victory over every enemy, including death. You may not control your circumstances, but you can decide where your heart anchors. Let not your heart be troubled. He has already overcome the world.",
     "prayer": "Prince of Peace, rule in my heart today. Quiet the noise, calm my fears, and let Your peace guard my mind. Amen.",
     "action": "Identify one recurring anxious thought and replace it with John 14:27 each time it returns."},
    {"day": 14, "title": "Blessed to Be a Blessing", "verse_ref": "Genesis 12:2", "verse": "And I will make of thee a great nation, and I will bless thee, and make thy name great; and thou shalt be a blessing:", "theme": "Generosity",
     "reflection": "God's blessings were never meant to stop with you. From Abraham onward, God's pattern is clear: He blesses us so that we can bless others. You are a channel, not a reservoir. When you hold your time, talent and treasure with open hands, they multiply. Ask God today not only 'what will You give me?' but 'who can I become a blessing to?' Generosity is the proof that we have understood the heart of God.",
     "prayer": "Father, thank You for every blessing in my life. Make me a channel of Your goodness — let others be blessed through me today. Amen.",
     "action": "Give something away today — time, encouragement, or a practical gift."},
    {"day": 15, "title": "Hearing God's Voice", "verse_ref": "Psalm 119:105", "verse": "Thy word is a lamp unto my feet, and a light unto my path.", "theme": "Guidance",
     "reflection": "A lamp lights only the next step — not the whole road. That is how God usually guides: enough light for today, enough for the step you are taking now. Many people want a floodlight for the next five years; God gives a lamp for the next five minutes. But when you keep walking in the light of His Word, every next step becomes clear in its time. You do not need to see the whole path; you only need to know the One who made it.",
     "prayer": "Lord, Your Word is my light. Guide my next step today, and help me to obey what You have already shown me. Amen.",
     "action": "Choose one clear instruction from Scripture and obey it today."},
    {"day": 16, "title": "Run With Purpose", "verse_ref": "Hebrews 12:1", "verse": "Wherefore seeing we also are compassed about with so great a cloud of witnesses, let us lay aside every weight, and the sin which doth so easily beset us, and let us run with patience the race that is set before us,", "theme": "Perseverance",
     "reflection": "Every runner knows: extra weight slows you down. The writer of Hebrews urges us to lay aside every weight — not only sin, but anything that hinders. Even good things can become weights if they pull you off course. And notice it is a race 'set before us' — your lane, your pace, your finish line. You are not competing with anyone else. Keep your eyes on Jesus, travel light, and keep running. The crown is worth it.",
     "prayer": "Lord, show me the weights I am carrying that You never asked me to carry. Help me lay them down and run my race faithfully. Amen.",
     "action": "Identify one 'weight' (habit, worry or distraction) to lay aside this week."},
    {"day": 17, "title": "Ask, Seek, Knock", "verse_ref": "Matthew 7:7", "verse": "Ask, and it shall be given you; seek, and ye shall find; knock, and it shall be opened unto you.", "theme": "Prayer",
     "reflection": "Jesus gives His disciples three verbs — ask, seek, knock — and each one intensifies. Asking is simple; seeking is searching; knocking is persisting. God is not reluctant to answer; He is teaching you to want Him. Persistent prayer does not change God's willingness; it changes your readiness to receive. What have you stopped asking for? What door have you stopped knocking on? Bring it back to the Father today. He loves when His children ask.",
     "prayer": "Father, I ask again for the desires of my heart, seeking Your will. I knock on doors only You can open. Answer according to Your wisdom and love. Amen.",
     "action": "Revive one prayer request you have given up on."},
    {"day": 18, "title": "The Fruit of the Spirit", "verse_ref": "Galatians 5:22-23", "verse": "But the fruit of the Spirit is love, joy, peace, longsuffering, gentleness, goodness, faith, meekness, temperance: against such there is no law.", "theme": "Character",
     "reflection": "Fruit is not manufactured — it is grown. An apple tree does not strain to produce apples; it simply stays rooted and receives. The fruit of the Spirit is the natural outflow of a life rooted in Christ. You do not become loving by trying harder to be loving; you abide in the Vine and His life produces the fruit. Notice it is one fruit with nine flavours — the Spirit's character, developing in you. Stay close to Jesus, and the fruit will follow.",
     "prayer": "Holy Spirit, produce Your fruit in my life. Grow love, joy, peace, patience, kindness, goodness, faithfulness, gentleness and self-control in me. Amen.",
     "action": "Choose one fruit of the Spirit to consciously practise today."},
    {"day": 19, "title": "Forgive as You've Been Forgiven", "verse_ref": "Ephesians 4:32", "verse": "And be ye kind one to another, tenderhearted, forgiving one another, even as God for Christ's sake hath forgiven you.", "theme": "Forgiveness",
     "reflection": "Unforgiveness is a poison you drink hoping the other person dies. But forgiveness is not saying that what happened was acceptable — it is handing the debt to God and refusing to be its jailer. The standard is breathtaking: forgive as God forgave you. Freely, fully, without dragging up the record again. Is there a name that still stings when you hear it? Bring it to God. The freedom on the other side of forgiveness is worth the pain of the journey.",
     "prayer": "Father, as You have forgiven me, help me to forgive those who have hurt me. Release me from bitterness and fill that space with Your peace. Amen.",
     "action": "Pray a blessing over someone who has wronged you."},
    {"day": 20, "title": "Wise Words", "verse_ref": "Proverbs 15:1", "verse": "A soft answer turneth away wrath: but grievous words stir up anger.", "theme": "Wisdom",
     "reflection": "Your words carry power to build or to burn. A soft answer — calm, humble, measured — can disarm a fight before it begins. Harsh words, even when 'true', pour fuel on flames. Wisdom is knowing not just what to say but how and when. Before you speak today, ask three questions: Is it true? Is it kind? Is it necessary? Words spoken in love can heal wounds that years of argument never touched.",
     "prayer": "Lord, set a guard over my mouth. Let my words today be seasoned with grace, bringing peace and not strife. Amen.",
     "action": "Before responding in a tense moment today, pause and pray before you speak."},
    {"day": 21, "title": "The Joy of the Lord", "verse_ref": "Psalm 30:5", "verse": "For his anger endureth but a moment; in his favour is life: weeping may endure for a night, but joy cometh in the morning.", "theme": "Joy",
     "reflection": "The night has an end. However dark your present season feels, it is not the final chapter — joy comes in the morning. God's favour is life itself, and His mercies are new every sunrise. Sorrow is real, and the Bible never pretends otherwise; even Jesus wept. But sorrow is a visitor, not a resident. Hold on through the night, because the God who keeps watch over you has already appointed your morning.",
     "prayer": "Lord, in my weeping, remind me that morning is coming. Fill my heart with the joy that only You can give, even in the waiting. Amen.",
     "action": "Encourage someone going through a hard season with this verse."},
    {"day": 22, "title": "Hidden in God", "verse_ref": "Psalm 91:1", "verse": "He that dwelleth in the secret place of the most High shall abide under the shadow of the Almighty.", "theme": "Protection",
     "reflection": "There is a place of safety that no enemy can breach: the presence of God. Dwelling in the secret place is not a one-time visit but a lifestyle — making God your home, not your emergency shelter. The shadow of the Almighty is not a hiding place of fear but a refuge of trust. The more time you spend in His presence, the more you know you are safe in His hands, no matter what rages outside. Abide there today.",
     "prayer": "Almighty God, I choose to dwell in Your presence today. Cover me and my household under the shadow of Your wings. Amen.",
     "action": "Set aside ten minutes today for quiet time in God's presence."},
    {"day": 23, "title": "Be Still", "verse_ref": "Psalm 46:10", "verse": "Be still, and know that I am God: I will be exalted among the heathen, I will be exalted in the earth.", "theme": "Rest",
     "reflection": "Stillness is one of the hardest disciplines in a noisy world — and one of the most healing. God is not asking you to figure everything out; He is asking you to be still and know that He is God. Your striving has limits; His sovereignty has none. The battle you are fighting does not rest on your shoulders alone. Pause. Breathe. Remember whose hands hold the universe — and your life. In stillness, strength returns.",
     "prayer": "Father, quiet my racing heart. In the stillness, let me know again that You are God, and I am Yours. Amen.",
     "action": "Turn off notifications for 30 minutes and simply sit with God."},
    {"day": 24, "title": "Walk in the Light", "verse_ref": "1 John 1:7", "verse": "But if we walk in the light, as he is in the light, we have fellowship one with another, and the blood of Jesus Christ his Son cleanseth us from all sin.", "theme": "Holiness",
     "reflection": "Light exposes, but it also heals. Walking in the light means living honestly — no hidden corners, no secret compromises — in the constant presence of God. The reward is beautiful: genuine fellowship with God and with others, and the continual cleansing of Christ's blood. Darkness isolates; light connects. Whatever you are tempted to hide, bring it into the light of His love. Confession is the doorway to freedom and community.",
     "prayer": "Lord, search me and know me. Help me to live transparently before You, walking in Your light every hour of this day. Amen.",
     "action": "Share one honest struggle with a trusted fellow believer today."},
    {"day":25, "title": "The Great Commission", "verse_ref": "Matthew 28:19-20", "verse": "Go ye therefore, and teach all nations, baptizing them in the name of the Father, and of the Son, and of the Holy Ghost: Teaching them to observe all things whatsoever I have commanded you: and, lo, I am with you alway, even unto the end of the world.", "theme": "Mission",
     "reflection": "The last words of Jesus before His ascension were not a farewell but a sending. Every believer carries the gospel forward — not all will cross oceans, but all can cross the street. And notice the promise attached: I am with you always. The mission is not carried out in your own strength or eloquence; He goes with you. Someone in your world needs to hear that God loves them. You may be the only Bible they ever read.",
     "prayer": "Lord, use me where I am. Give me boldness to share Your love with the people You have placed in my life. Amen.",
     "action": "Pray for three people by name who need to know Christ."},
    {"day": 26, "title": "The Power of Humility", "verse_ref": "James 4:10", "verse": "Humble yourselves in the sight of the Lord, and he shall lift you up.", "theme": "Humility",
     "reflection": "The world says lift yourself up; God says humble yourself and let Him do the lifting. Pride builds towers that fall; humility builds foundations that last. Humility is not thinking less of yourself — it is thinking of yourself less, and of God and others more. When you bow low before the Lord, you are placing yourself in the one position from which He can exalt you safely. Let go of the need to be seen as great, and let God be great through you.",
     "prayer": "Lord, I humble myself before You. Take my pride and give me a servant's heart. Lift me up in Your time and Your way. Amen.",
     "action": "Serve someone today in a way that no one will notice."},
    {"day": 27, "title": "God's Unfailing Love", "verse_ref": "Romans 8:38-39", "verse": "For I am persuaded, that neither death, nor life, nor angels, nor principalities, nor powers, nor things present, nor things to come, nor height, nor depth, nor any other creature, shall be able to separate us from the love of God, which is in Christ Jesus our Lord.", "theme": "Love",
     "reflection": "Paul stacks every imaginable force — death, life, angels, powers, time, space — and declares that none of them can separate you from God's love. This is the great certainty of the Christian life: His love is not based on your performance but on His promise. When doubts whisper that you have wandered too far or failed too badly, answer with this verse. Nothing in all creation can cut the cord between you and the love of God in Christ.",
     "prayer": "Thank You, Father, that nothing can separate me from Your love. Let this truth be the anchor of my soul today and always. Amen.",
     "action": "Write this verse somewhere you will see it every day this week."},
    {"day": 28, "title": "A Heart of Service", "verse_ref": "Mark 10:45", "verse": "For even the Son of man came not to be ministered unto, but to minister, and to give his life a ransom for many.", "theme": "Service",
     "reflection": "If the King of kings came to serve, then greatness in His kingdom is measured by how well we serve others. Jesus did not come to be waited on; He came to wash feet and lay down His life. Every act of service — seen or unseen — echoes the heart of your Saviour. Stop waiting for a platform; start with the person in front of you. In God's economy, the way up is down, and the greatest is the servant of all.",
     "prayer": "Lord Jesus, give me Your servant heart. Show me who I can serve today, and help me to do it joyfully, as unto You. Amen.",
     "action": "Do one unrequested act of service for someone in your home or church."},
    {"day": 29, "title": "God Is Your Refuge", "verse_ref": "Psalm 46:1", "verse": "God is our refuge and strength, a very present help in trouble.", "theme": "Protection",
     "reflection": "A refuge is only useful if you run to it. God is not a distant hope but 'a very present help' — close, immediate, available in the very moment of trouble. You do not need to clean yourself up before coming; you come as you are, storm and all. The safest place in the universe is not a location but a Person. Run to Him first, not last. He is closer than your next breath.",
     "prayer": "Lord, You are my refuge. I run to You with everything on my heart. Be my strength and my very present help today. Amen.",
     "action": "Next time trouble hits, pray before you panic."},
    {"day": 30, "title": "Seek Wisdom Daily", "verse_ref": "James 1:5", "verse": "If any of you lack wisdom, let him ask of God, that giveth to all men liberally, and upbraideth not; and he shall be given him.", "theme": "Wisdom",
     "reflection": "God has an open-door policy on wisdom. He gives generously to all who ask, without making you feel foolish for asking. Wisdom is not the same as information — it is knowing how to live rightly, and it comes down from above. Facing a decision? Ask. Facing a difficult conversation? Ask. You do not need a theology degree to be wise; you need a humble heart that asks the Giver of every good gift.",
     "prayer": "Father, I ask You for wisdom today — for my decisions, my words and my relationships. Thank You that You give generously. Amen.",
     "action": "Before your next big decision, pause and specifically ask God for wisdom."},
    {"day": 31, "title": "Persevere in Doing Good", "verse_ref": "Galatians 6:9", "verse": "And let us not be weary in well doing: for in due season we shall reap, if we faint not.", "theme": "Perseverance",
     "reflection": "Harvest is seasonal — and seasons take time. It is easy to grow weary in doing good when results are slow and gratitude is scarce. But the promise stands: in due season, you will reap, if you do not faint. Keep praying, keep serving, keep sowing kindness, keep parenting faithfully, keep building what God called you to build. The fields may look empty now, but under the soil, God is growing your harvest. Do not quit before the season turns.",
     "prayer": "Lord, renew my strength when I grow weary. Help me to keep doing good, trusting that in due season I will reap if I do not give up. Amen.",
     "action": "Encourage someone who is close to giving up."},
]


# ========== VERSION LIST & MAPPINGS ==========

VERSION_LIST = [
    {"id": "en-kjv", "version": "King James Version (KJV)", "source": "bible_api", "popularity": 1},
    {"id": "en-niv", "version": "New International Version (NIV)", "source": "api_bible", "popularity": 2},
    {"id": "en-nkjv", "version": "New King James Version (NKJV)", "source": "api_bible", "popularity": 3},
    {"id": "en-amp", "version": "Amplified Bible (AMP)", "source": "api_bible_secondary", "popularity": 4},
    # {"id": "en-esv", "version": "English Standard Version (ESV)", "source": "bible_api", "popularity": 4},
    {"id": "en-nasb", "version": "New American Standard Bible (NASB)", "source": "api_bible_secondary", "popularity": 5},
    {"id": "en-csb", "version": "Christian Standard Bible (CSB)", "source": "api_bible_secondary", "popularity": 6},
    {"id": "en-nlt", "version": "New Living Translation (NLT)", "source": "api_bible", "popularity": 7},
    # {"id": "en-bsb", "version": "Berean Standard Bible (BSB)", "source": "bible_api", "popularity": 8},
    {"id": "en-web", "version": "World English Bible (WEB)", "source": "bible_api", "popularity": 9},
    # {"id": "en-nrsv", "version": "New Revised Standard Version (NRSV)", "source": "bible_api", "popularity": 10},
    # {"id": "en-rsv", "version": "Revised Standard Version (RSV)", "source": "bible_api", "popularity": 11},
    {"id": "en-asv", "version": "American Standard Version (ASV)", "source": "bible_api", "popularity": 12},
    {"id": "en-bbe", "version": "Bible in Basic English (BBE)", "source": "bible_api", "popularity": 13},
    {"id": "en-darby", "version": "Darby Bible", "source": "bible_api", "popularity": 14},
    {"id": "en-dra", "version": "Douay-Rheims (DRA)", "source": "bible_api", "popularity": 15},
    # {"id": "en-ylt", "version": "Young's Literal Translation (YLT)", "source": "bible_api", "popularity": 16},
    # {"id": "en-msg", "version": "The Message (MSG)", "source": "bible_api", "popularity": 18},
    # {"id": "en-net", "version": "NET Bible (NET)", "source": "bible_api", "popularity": 19},
    # {"id": "en-erv", "version": "Easy-to-Read Version (ERV)", "source": "bible_api", "popularity": 20},
    # {"id": "pt-almeida", "version": "João Ferreira de Almeida (Português)", "source": "bible_api", "popularity": 21},
    {"id": "ro-rccv", "version": "Cornilescu (Română)", "source": "bible_api", "popularity": 22},
    # {"id": "zh-cuv", "version": "Chinese Union Version (中文)", "source": "bible_api", "popularity": 23},
    # {"id": "cs-bkr", "version": "Bible Kralická (Čeština)", "source": "bible_api", "popularity": 24},
]

# API.Bible mapping (book name -> API.Bible book ID)
# Full reference: https://api.scripture.api.bible/
API_BIBLE_BOOKS = {
    "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV", "Numbers": "NUM",
    "Deuteronomy": "DEU", "Joshua": "JOS", "Judges": "JDG", "Ruth": "RUT",
    "1 Samuel": "1SA", "2 Samuel": "2SA", "1 Kings": "1KI", "2 Kings": "2KI",
    "1 Chronicles": "1CH", "2 Chronicles": "2CH", "Ezra": "EZR", "Nehemiah": "NEH",
    "Esther": "EST", "Job": "JOB", "Psalms": "PSA", "Proverbs": "PRO",
    "Ecclesiastes": "ECC", "Song of Solomon": "SNG", "Isaiah": "ISA", "Jeremiah": "JER",
    "Lamentations": "LAM", "Ezekiel": "EZK", "Daniel": "DAN", "Hosea": "HOS",
    "Joel": "JOL", "Amos": "AMO", "Obadiah": "OBA", "Jonah": "JON",
    "Micah": "MIC", "Nahum": "NAM", "Habakkuk": "HAB", "Zephaniah": "ZEP",
    "Haggai": "HAG", "Zechariah": "ZEC", "Malachi": "MAL", "Matthew": "MAT",
    "Mark": "MRK", "Luke": "LUK", "John": "JHN", "Acts": "ACT",
    "Romans": "ROM", "1 Corinthians": "1CO", "2 Corinthians": "2CO", "Galatians": "GAL",
    "Ephesians": "EPH", "Philippians": "PHP", "Colossians": "COL", "1 Thessalonians": "1TH",
    "2 Thessalonians": "2TH", "1 Timothy": "1TI", "2 Timothy": "2TI", "Titus": "TIT",
    "Philemon": "PHM", "Hebrews": "HEB", "James": "JAS", "1 Peter": "1PE",
    "2 Peter": "2PE", "1 John": "1JN", "2 John": "2JN", "3 John": "3JN",
    "Jude": "JUD", "Revelation": "REV"
}

# API.Bible version IDs (verified against the live API catalog)
API_BIBLE_VERSIONS = {
    "en-nkjv": "63097d2a0a2f7db3-01",
    "en-niv": "78a9f6124f344018-01",
    "en-nlt": "d6e14a625393b4da-01",
}

API_BIBLE_VERSIONS_SECONDARY = {
    "en-csb": "a556c5305ee15c3f-01",
    "en-amp": "a81b73293d3080c9-01",
    "en-nasb": "a761ca71e0b3ddcf-01",
}

# Bible-API.com translation mappings
BIBLEAPI_TRANSLATIONS = {
    "en-kjv": "kjv",
    "en-bsb": "bsb",
    "en-web": "web",
    "en-asv": "asv",
    "en-bbe": "bbe",
    "en-darby": "darby",
    "en-dra": "dra",
    "en-ylt": "ylt",
    "en-esv": "esv",
    "en-nasb": "nasb",
    "en-csb": "csb",
    "en-nlt": "nlt",
    "en-niv": "niv",
    "en-nkjv": "nkjv",
    "en-nrsv": "nrsv",
    "en-rsv": "rsv",
    "en-amp": "amp",
    "en-msg": "msg",
    "en-net": "net",
    "en-erv": "erv",
    "pt-almeida": "almeida",
    "ro-rccv": "rccv",
    "zh-cuv": "cuv",
    "cs-bkr": "bkr",
}


# ========== HELPER FUNCTIONS ==========

def get_book_by_slug(slug: str):
    """Get book by slug"""
    slug_lower = slug.lower()
    for book in BIBLE_BOOKS:
        if book['slug'] == slug_lower:
            return book
    return None


def get_book_by_name(name: str):
    """Get book by name"""
    name_lower = name.lower()
    for book in BIBLE_BOOKS:
        if book['name'].lower() == name_lower:
            return book
    return None


def get_version_name(version_id: str) -> str:
    """Get human-friendly version name"""
    return next((v['version'] for v in VERSION_LIST if v['id'] == version_id), version_id)


def get_version_source(version_id: str) -> str:
    """Get API source for a version"""
    return next((v.get('source', 'bible_api') for v in VERSION_LIST if v['id'] == version_id), 'bible_api')


def clean_text(text: str) -> str:
    """Clean verse text"""
    if not text:
        return text
    text = text.replace('…', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def dedupe_verses(raw_verses: list) -> list:
    """Remove duplicate verses"""
    seen = set()
    out = []
    for v in raw_verses:
        key = v.get('verse') or v.get('reference') or v.get('text')
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


# ========== FETCH FUNCTIONS ==========

def fetch_chapter_bibleapi(book_name: str, chapter: int, version_id: str = "en-kjv") -> tuple:
    """
    Fetch from bible-api.com (free, public domain)
    Most reliable fallback
    """
    translation = BIBLEAPI_TRANSLATIONS.get(version_id, "kjv")
    ref = f"{book_name}+{chapter}"
    url = f"{BIBLE_API_BASE}/{ref}?translation={translation}"

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            if translation != "kjv":
                print(f"Translation {translation} unavailable for {ref}; falling back to KJV")
                return fetch_chapter_bibleapi(book_name, chapter, "en-kjv")
            print(f"Bible API error for {ref}: {resp.status_code}")
            return [], ""

        data = resp.json()
        raw_verses = data.get("verses", [])

        verses = []
        for v in raw_verses:
            text = clean_text(v.get("text", "").strip())
            verses.append({
                "verse": str(v.get("verse", "")),
                "reference": f"{book_name} {chapter}:{v.get('verse', '')}",
                "text": text,
            })

        verses = dedupe_verses(verses)
        chapter_text = " ".join(v["text"] for v in verses)
        print(f"✅ Fetched from Bible API: {book_name} {chapter} ({len(verses)} verses)")
        return verses, chapter_text

    except Exception as e:
        print(f"Bible API error: {e}")
        return [], ""


def parse_api_bible_verses(content: str, book_name: str, chapter: int) -> list:
    """Extract verse-level text from API.Bible's HTML chapter content."""
    if not content:
        return []

    pattern = re.compile(
        r'<span[^>]*data-number="(\d+)"[^>]*>(.*?)</span>(.*?)(?=<span[^>]*data-number=|$)',
        re.S,
    )

    verses = []
    for match in pattern.finditer(content):
        verse_num = match.group(1)
        verse_text = re.sub(r'<[^>]+>', ' ', match.group(3))
        verse_text = html.unescape(verse_text)
        verse_text = clean_text(verse_text)
        if verse_text:
            verses.append({
                "verse": verse_num,
                "reference": f"{book_name} {chapter}:{verse_num}",
                "text": verse_text,
            })

    if not verses:
        fallback_text = clean_text(re.sub(r'<[^>]+>', ' ', content))
        if fallback_text:
            verses.append({
                "verse": "1",
                "reference": f"{book_name} {chapter}:1",
                "text": fallback_text,
            })

    return dedupe_verses(verses)


def fetch_chapter_apibible(book_name: str, chapter: int, version_id: str) -> tuple:
    """
    Fetch chapter text from API.Bible using the current REST API format.
    """
    if not API_BIBLE_KEY:
        print("API.Bible key not configured")
        return [], ""

    book_code = API_BIBLE_BOOKS.get(book_name)
    if not book_code:
        print(f"Book '{book_name}' not found in API.Bible mapping")
        return [], ""

    version_code, api_key, api_base = get_api_bible_credentials(version_id)
    if not version_code:
        print(f"Version '{version_id}' not found in API.Bible mapping")
        return [], ""

    try:
        headers = {
            "api-key": api_key,
            "Accept": "application/json",
        }

        chapter_ref = f"{book_code}.{chapter}"
        url = f"{api_base}/bibles/{version_code}/chapters/{chapter_ref}"

        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code != 200:
            print(f"API.Bible error: {resp.status_code} - {resp.text[:200]}")
            return [], ""

        data = resp.json()
        chapter_data = data.get("data", {})
        content = chapter_data.get("content", "")

        if not content:
            print(f"No chapter content found for {book_name} {chapter}")
            return [], ""

        verses = parse_api_bible_verses(content, book_name, chapter)
        chapter_text = " ".join(v["text"] for v in verses)
        print(f"Fetched from API.Bible: {book_name} {chapter} ({len(verses)} verses)")
        return verses, chapter_text

    except Exception as e:
        print(f"API.Bible fetch error: {e}")
        return [], ""

def get_api_bible_credentials(version_id):
    """
    Returns:
    version_code,
    api_key,
    api_base
    """

    if version_id in API_BIBLE_VERSIONS:
        return (
            API_BIBLE_VERSIONS[version_id],
            API_BIBLE_KEY,
            API_BIBLE_BASE
        )

    if version_id in API_BIBLE_VERSIONS_SECONDARY:
        return (
            API_BIBLE_VERSIONS_SECONDARY[version_id],
            API_BIBLE_SECONDARY_KEY,
            API_BIBLE_SECONDARY_BASE
        )

    return None, None, None


def fetch_chapter_bibleapi_smart(book_name: str, chapter: int, version_id: str) -> tuple:
    """
    Smart fetcher with fallback logic.
    API.Bible is tried first for versions mapped to it; every version falls back to Bible-API.com.
    """
    source = get_version_source(version_id)

    if source in ("api_bible", "api_bible_secondary"):
        verses, text = fetch_chapter_apibible(book_name, chapter, version_id)
        if verses:
            return verses, text
        print(f"API.Bible failed, falling back to Bible API")

    return fetch_chapter_bibleapi(book_name, chapter, version_id)


# ========== DAILY VERSE ==========

_daily_verse_cache = {"date": None, "verse": None}

def get_daily_verse() -> dict:
    """Get daily verse with caching"""
    today_str = dt.date.today().isoformat()

    if _daily_verse_cache["date"] == today_str and _daily_verse_cache["verse"]:
        return _daily_verse_cache["verse"]

    verse = None
    try:
        resp = requests.get(f"{BIBLE_API_BASE}/?random=verse", timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("text", "").strip()
            reference = data.get("reference", "").strip()
            if text and reference:
                verse = {"text": text, "reference": reference}
    except Exception as e:
        print(f"Daily verse error: {e}")

    if not verse:
        fallback_list = [
            {"text": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.", "reference": "John 3:16"},
            {"text": "The Lord is my shepherd; I shall not want.", "reference": "Psalm 23:1"},
            {"text": "I can do all this through him who gives me strength.", "reference": "Philippians 4:13"},
            {"text": "Trust in the Lord with all your heart and lean not on your own understanding.", "reference": "Proverbs 3:5"},
        ]
        verse = random.choice(fallback_list)

    _daily_verse_cache["date"] = today_str
    _daily_verse_cache["verse"] = verse
    return verse


# ========== SYNC DATA ==========

def get_user_sync_file(user_id: str) -> Path:
    safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', user_id)
    return SYNC_DATA_DIR / f"{safe_id}.json"


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
        "notes": [],
        "progress": {},
        "readingLog": [],
        "bibleYear": {"start_date": None, "completed_days": []},
        "plans": {},
        "prayers": [],
        "quizStats": {"attempts": 0, "total_correct": 0, "total_answered": 0, "best_percentage": 0.0, "history": []},
        "font_size": None,
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

    merged["font_size"] = local_data.get("font_size") or server_data.get("font_size")
    merged["theme"] = local_data.get("theme") or server_data.get("theme")
    
    return merged


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


# ========== PROFILE ANALYTICS ==========

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

    # ---- Reading plans progress ----
    plans_data = data.get('plans', {}) or {}
    plans_progress = {}
    for pid, p in plans_data.items():
        meta = READING_PLANS_BY_ID.get(pid)
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
    ]

    return result


# ========== AUDIO/TTS ==========

def _fetch_voice_rss_chunk(text: str, voice: str = "en-us") -> bytes:
    """Fetch a single chunk from Voice RSS API"""
    data = {
        "key": VOICE_RSS_API_KEY,
        "src": text,
        "hl": voice,
        "r": "0",
        "c": "mp3",
        "f": "44khz_16bit_stereo",
        "ssml": "false",
        "b64": "false"
    }
    
    try:
        response = requests.post(VOICE_RSS_URL, data=data, timeout=30)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'audio' in content_type or response.content[:3] in [b'ID3', b'\xff\xfb']:
                return response.content
        return None
    except Exception as e:
        print(f"Voice RSS error: {e}")
        return None


def text_to_speech_voicerss(text: str, voice: str = "en-us") -> bytes:
    """Convert text to speech with chunking"""
    MAX_CHARS = 4500
    
    def chunk_text(text: str, max_length: int = 4500) -> list:
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += (" " if current_chunk else "") + sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text[:max_length]]

    chunks = chunk_text(text, MAX_CHARS)
    
    if len(chunks) == 1:
        return _fetch_voice_rss_chunk(chunks[0], voice)
    
    audio_chunks = []
    for chunk in chunks:
        chunk_audio = _fetch_voice_rss_chunk(chunk, voice)
        if chunk_audio is None:
            return None
        audio_chunks.append(chunk_audio)
    
    return b''.join(audio_chunks)


# ========== FLASK ROUTES ==========

@app.route("/api/download-audio", methods=["POST"])
def download_audio():
    """Download audio file"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing text parameter"}), 400
    
    text = data['text'].strip()
    filename = data.get('filename', 'bible-audio.mp3')
    
    if not filename.endswith('.mp3'):
        filename += '.mp3'
    
    audio_data = text_to_speech_voicerss(text)
    
    if audio_data is None:
        return jsonify({"error": "Failed to generate audio"}), 500
    
    return send_file(
        io.BytesIO(audio_data),
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=filename
    )


@app.route("/api/play-audio", methods=["POST"])
def play_audio():
    """Stream audio"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Missing text parameter"}), 400
    
    text = data['text'].strip()
    audio_data = text_to_speech_voicerss(text)
    
    if audio_data is None:
        return jsonify({"error": "Failed to generate audio"}), 500
    
    return send_file(io.BytesIO(audio_data), mimetype="audio/mpeg")


@app.route("/")
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


@app.route("/search", methods=["GET", "POST"])
def search():
    api_key = API_BIBLE_KEY or os.environ.get("API_KEY")
    headers = {"api-key": api_key} if api_key else {}
    
    search_results = None
    search_performed = False
    query = ""
    
    if request.method == "POST":
        query = request.form.get("query", "").strip()
    elif request.method == "GET":
        query = request.args.get("query", "").strip()
    
    if query:
        try:
            search_bible_id = API_BIBLE_VERSIONS.get("en-niv", "78a9f6124f344018-01")
            search_url = f"{API_BIBLE_BASE}/bibles/{search_bible_id}/search"
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
            else:
                search_results = []
                print(f"Search API error: {response.status_code}")
        except Exception as e:
            print(f"Search error: {e}")
            search_results = []       
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
        user=user
    )


def _send_contact_email_resend(sender_name: str, sender_email: str, subject: str, message: str):
    """Send email via Resend"""
    if not RESEND_API_KEY:
        return False, 'Resend API key is not configured.'
    
    from_email = "MyPersonal Bible App <noreply@resend.dev>"
    to_email = os.environ.get("MAIL_TO")
    
    email_body = f"""
    <h2>New Contact Form Submission</h2>
    <p><strong>Name:</strong> {sender_name or '(not provided)'}</p>
    <p><strong>Email:</strong> {sender_email or '(not provided)'}</p>
    <p><strong>Category:</strong> {subject or '(not specified)'}</p>
    <p><strong>Message:</strong></p>
    <p style="white-space: pre-wrap;">{message}</p>
    <hr>
    <p><small>Sent from MyPersonal Bible App Contact Form</small></p>
    """
    
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": f"[MyPersonalBibleApp] {subject or 'New contact message'}",
        "html": email_body,
    }
    
    if sender_email:
        payload["reply_to"] = sender_email
    
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(RESEND_API_URL, json=payload, headers=headers, timeout=15)
        
        if response.status_code in (200, 201, 202):
            return True, 'Your message was sent successfully. Thank you!'
        else:
            print(f"Resend error: {response.status_code}")
            return False, 'Failed to send email. Please try again later.'
            
    except Exception as e:
        print(f"Email send error: {e}")
        return False, 'Failed to send email. Please try again later.'


@app.route('/contact', methods=['GET', 'POST'])
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


@app.route("/books/<book_slug>", methods=["GET", "POST"])
def books(book_slug):
    book = get_book_by_slug(book_slug)
    
    if not book:
        return f"Book '{book_slug}' not found", 404

    selected_chapter = request.form.get("chapter") or request.args.get("chapter")
    selected_version = request.form.get("version") or request.args.get("version", "en-kjv")
    verses = []
    chapter_text = ""
    error_message = None
    user = session.get('user')

    if selected_chapter:
        try:
            selected_chapter = int(selected_chapter)
            verses, chapter_text = fetch_chapter_bibleapi_smart(
                book['name'], selected_chapter, selected_version
            )

            if not verses:
                version_name = get_version_name(selected_version)
                error_message = (
                    f"Unable to load {version_name} for {book['name']} {selected_chapter}. "
                    f"Please try another version or check your internet connection."
                )
        except Exception as e:
            print(f"Chapter fetch error: {e}")
            error_message = f"Error loading chapter: {str(e)}"

    return render_template(
        "books.html",
        current_year=dt.datetime.now().year,
        book=book,
        books=BIBLE_BOOKS,
        selected_chapter=selected_chapter if selected_chapter else None,
        selected_version=selected_version,
        chapter_text=chapter_text,
        verses=verses,
        versions=VERSION_LIST,
        error_message=error_message,
        user=user
    )


@app.route('/api/chapter/<book_name>/<int:chapter>')
def api_chapter(book_name, chapter):
    selected_version = request.args.get('version', 'en-kjv')
    
    book = get_book_by_slug(book_name) or get_book_by_name(book_name)
    if not book:
        return jsonify({'error': f'Book "{book_name}" not found'}), 404
    
    if chapter < 1 or chapter > book['chapters']:
        return jsonify({'error': f'Chapter {chapter} not valid for {book["name"]}'}), 404
    
    verses, chapter_text = fetch_chapter_bibleapi_smart(book['name'], chapter, selected_version)

    if not verses:
        return jsonify({'error': 'Chapter not found or request failed'}), 404

    return jsonify({
        'book': book['name'],
        'book_slug': book['slug'],
        'chapter': chapter,
        'total_chapters': book['chapters'],
        'version': selected_version,
        'version_name': get_version_name(selected_version),
        'verse_count': len(verses),
        'chapter_text': chapter_text,
        'verses': verses,
    })


@app.route('/api/books', methods=['GET'])
def api_books():
    testament = request.args.get('testament', 'all').lower()
    
    books = BIBLE_BOOKS.copy()
    
    if testament == 'old':
        books = books[:39]
    elif testament == 'new':
        books = books[39:]
    
    return jsonify({
        'total': len(books),
        'testament': testament,
        'books': books
    })


@app.route('/api/versions', methods=['GET'])
def api_versions():
    return jsonify({
        'total': len(VERSION_LIST),
        'versions': VERSION_LIST
    })


@app.route('/api/daily-verse', methods=['GET'])
def api_daily_verse():
    daily_verse = get_daily_verse()
    return jsonify({
        'date': dt.date.today().isoformat(),
        'verse': daily_verse
    })


@app.route('/api/search', methods=['GET'])
def api_search():
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Missing search query parameter "q"'}), 400
    
    api_key = API_BIBLE_KEY or os.environ.get("API_KEY")
    headers = {"api-key": api_key} if api_key else {}
    
    try:
        search_bible_id = API_BIBLE_VERSIONS.get("en-niv", "78a9f6124f344018-01")
        search_url = f"{API_BIBLE_BASE}/bibles/{search_bible_id}/search"
        response = requests.get(search_url, headers=headers, params={"query": query, "limit": limit}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            
            if "data" in data and "verses" in data["data"]:
                for verse in data["data"]["verses"]:
                    cleaned = clean_text(verse.get("text", ""))
                    results.append({
                        "text": cleaned,
                        "reference": verse.get("reference", "")
                    })
            
            return jsonify({
                'query': query,
                'total': len(results),
                'results': results
            })
        else:
            return jsonify({'error': f'Search failed: {response.status_code}'}), response.status_code
            
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({'error': 'Search request failed'}), 500


@app.route('/api/verse/<book_name>/<int:chapter>/<int:verse>')
def api_verse(book_name, chapter, verse):
    selected_version = request.args.get('version', 'en-kjv')
    
    book = get_book_by_slug(book_name) or get_book_by_name(book_name)
    if not book:
        return jsonify({'error': f'Book "{book_name}" not found'}), 404
    
    verses, _ = fetch_chapter_bibleapi_smart(book['name'], chapter, selected_version)
    
    if not verses:
        return jsonify({'error': 'Chapter not found'}), 404
    
    target_verse = None
    for v in verses:
        if v.get('verse') == str(verse):
            target_verse = v
            break
    
    if not target_verse:
        return jsonify({'error': f'Verse {verse} not found'}), 404
    
    return jsonify({
        'book': book['name'],
        'book_slug': book['slug'],
        'chapter': chapter,
        'verse': verse,
        'reference': target_verse['reference'],
        'text': target_verse['text'],
        'version': selected_version
    })


# ========== GOOGLE OAUTH ==========

@app.route('/login/google')
def google_login():
    """Initiate Google OAuth"""
    google = OAuth2Session(
        GOOGLE_CLIENT_ID,
        redirect_uri=url_for('google_callback', _external=True),
        scope=['openid', 'email', 'profile']
    )
    
    auth_url, state = google.authorization_url(
        GOOGLE_AUTH_URL,
        access_type='offline',
        prompt='select_account'
    )
    
    session['oauth_state'] = state
    return redirect(auth_url)


@app.route('/login/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        google = OAuth2Session(
            GOOGLE_CLIENT_ID,
            state=session.get('oauth_state'),
            redirect_uri=url_for('google_callback', _external=True)
        )
        
        token = google.fetch_token(
            GOOGLE_TOKEN_URL,
            client_secret=GOOGLE_CLIENT_SECRET,
            authorization_response=request.url
        )
        
        session.pop('oauth_state', None)
        
        google = OAuth2Session(GOOGLE_CLIENT_ID, token=token)
        user_info = google.get(GOOGLE_USERINFO_URL).json()
        
        session['user'] = {
            'id': user_info['sub'],
            'name': user_info.get('name', user_info.get('email')),
            'email': user_info['email'],
            'picture': user_info.get('picture', '')
        }
        session.permanent = True
        
        print(f"Login successful: {user_info.get('email')}")
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"Login failed: {e}")
        session.pop('oauth_state', None)
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Logout user"""
    session.pop('user', None)
    return redirect(url_for('index'))


# ========== SYNC API ==========

@app.route('/api/sync', methods=['POST'])
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


@app.route('/api/sync', methods=['GET'])
def get_sync_data():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    data['streak'] = compute_streak(data.get('readingLog', []))
    data['bibleYearProgress'] = compute_bible_year_progress(data.get('bibleYear', {}))
    
    return jsonify(data)


@app.route('/api/log-reading', methods=['POST'])
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


@app.route('/api/bible-year/plan', methods=['GET'])
def bible_year_plan():
    """Public - the static 365-day reading plan. No auth needed since it's the same for everyone."""
    return jsonify({"days": BIBLE_YEAR_TOTAL_DAYS, "plan": BIBLE_YEAR_PLAN})


@app.route('/api/bible-year/progress', methods=['GET'])
def bible_year_progress():
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    progress = compute_bible_year_progress(data.get('bibleYear', {}))
    return jsonify({'authenticated': True, 'progress': progress})


@app.route('/api/bible-year/start', methods=['POST'])
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


@app.route('/api/bible-year/mark', methods=['POST'])
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


@app.route('/profile')
def user_profile():
    """Renders the user's profile / activity dashboard. Analytics are fetched
    client-side from /api/profile/analytics, matching how sync and Bible-in-a-Year
    data are already fetched client-side elsewhere in the app."""
    user = session.get('user')
    return render_template('user-profile.html', user=user, current_year=dt.datetime.now().year)


@app.route('/api/profile/analytics', methods=['GET'])
def profile_analytics():
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401

    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    analytics = compute_profile_analytics(data)
    return jsonify({'authenticated': True, 'analytics': analytics})


@app.route('/api/user', methods=['GET'])
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


@app.route('/install')
def install_guide():
    user = session.get('user')
    return render_template('install.html', user=user, current_year=dt.datetime.now().year)


@app.route('/bible-in-a-year')
def bible_in_a_year():
    """Renders the Bible in a Year tracker page. The 365-day plan and the
    signed-in user's progress are fetched client-side via
    /api/bible-year/plan and /api/bible-year/progress, matching how sync
    data is already fetched client-side elsewhere in the app."""
    user = session.get('user')
    return render_template('bible_in_a_year.html', user=user, current_year=dt.datetime.now().year)



# ========== NEW FEATURES: PLANS, TOPICS, QUIZ, COMPARE, DEVOTIONAL, PRAYERS, EXPORT ==========

@app.route('/plans')
def reading_plans_page():
    user = session.get('user')
    light_plans = [{
        "id": p["id"], "title": p["title"], "icon": p["icon"], "color": p["color"],
        "description": p["description"], "total_days": len(p["plan"])
    } for p in READING_PLANS]
    return render_template('reading-plans.html', user=user, current_year=dt.datetime.now().year,
                           plans=light_plans)


@app.route('/api/plans', methods=['GET'])
def api_plans():
    """Public - list all available reading plans with their metadata."""
    return jsonify({
        "plans": [{
            "id": p["id"], "title": p["title"], "icon": p["icon"], "color": p["color"],
            "description": p["description"], "total_days": len(p["plan"])
        } for p in READING_PLANS]
    })


@app.route('/api/plans/<plan_id>', methods=['GET'])
def api_plan_detail(plan_id):
    """Public - full day-by-day plan."""
    plan = READING_PLANS_BY_ID.get(plan_id)
    if not plan:
        return jsonify({'error': 'Plan "%s" not found' % plan_id}), 404
    return jsonify({
        "id": plan["id"], "title": plan["title"], "icon": plan["icon"], "color": plan["color"],
        "description": plan["description"], "total_days": len(plan["plan"]), "plan": plan["plan"]
    })


@app.route('/api/plans/<plan_id>/start', methods=['POST'])
def api_plan_start(plan_id):
    """Begin (or restart) a plan from today."""
    plan = READING_PLANS_BY_ID.get(plan_id)
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


@app.route('/api/plans/<plan_id>/mark', methods=['POST'])
def api_plan_mark(plan_id):
    """Mark a plan day as read (or unread). Body: {"day": 1, "completed": true}"""
    plan = READING_PLANS_BY_ID.get(plan_id)
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


@app.route('/api/plans/<plan_id>/progress', methods=['GET'])
def api_plan_progress(plan_id):
    plan = READING_PLANS_BY_ID.get(plan_id)
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


@app.route('/topics')
def topics_page():
    user = session.get('user')
    return render_template('topics.html', user=user, current_year=dt.datetime.now().year)


@app.route('/api/topics', methods=['GET'])
def api_topics():
    """Public - list all topic collections (without verses)."""
    return jsonify({
        "topics": [{
            "slug": t["slug"], "title": t["title"], "icon": t["icon"], "description": t["description"],
            "verse_count": len(t["verses"])
        } for t in TOPIC_VERSES]
    })


@app.route('/api/topics/<slug>', methods=['GET'])
def api_topic_detail(slug):
    """Public - one topic with its verses."""
    topic = TOPICS_BY_SLUG.get(slug.lower())
    if not topic:
        return jsonify({'error': 'Topic "%s" not found' % slug}), 404
    return jsonify(topic)


@app.route('/quiz')
def quiz_page():
    user = session.get('user')
    return render_template('quiz.html', user=user, current_year=dt.datetime.now().year,
                           categories=QUIZ_CATEGORIES)


@app.route('/api/quiz', methods=['GET'])
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


@app.route('/api/quiz/submit', methods=['POST'])
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


@app.route('/api/quiz/stats', methods=['GET'])
def api_quiz_stats():
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    user_id = session['user']['id']
    data = load_user_sync_data(user_id)
    return jsonify({'authenticated': True, 'stats': data.get('quizStats') or {}})


@app.route('/compare')
def compare_page():
    user = session.get('user')
    return render_template('compare.html', user=user, current_year=dt.datetime.now().year,
                           books=BIBLE_BOOKS, versions=VERSION_LIST)


@app.route('/api/compare/<book_name>/<int:chapter>', methods=['GET'])
def api_compare(book_name, chapter):
    """Fetch two translations of the same chapter side by side."""
    v1 = request.args.get('v1', 'en-kjv')
    v2 = request.args.get('v2', 'en-web')

    book = get_book_by_slug(book_name) or get_book_by_name(book_name)
    if not book:
        return jsonify({'error': 'Book "%s" not found' % book_name}), 404
    if chapter < 1 or chapter > book['chapters']:
        return jsonify({'error': 'Chapter %d not valid for %s' % (chapter, book["name"])}), 404

    verses1, _ = fetch_chapter_bibleapi_smart(book['name'], chapter, v1)
    verses2, _ = fetch_chapter_bibleapi_smart(book['name'], chapter, v2)

    if not verses1 and not verses2:
        return jsonify({'error': 'Unable to load either version. Please try again.'}), 502

    return jsonify({
        'book': book['name'],
        'book_slug': book['slug'],
        'chapter': chapter,
        'total_chapters': book['chapters'],
        'versions': [
            {'id': v1, 'name': get_version_name(v1), 'verses': verses1},
            {'id': v2, 'name': get_version_name(v2), 'verses': verses2},
        ]
    })


# Curated fallback verses for the random-verse feature (KJV, public domain)
RANDOM_FALLBACK_VERSES = [
    {"reference": "Jeremiah 29:11", "text": "For I know the thoughts that I think toward you, saith the LORD, thoughts of peace, and not of evil, to give you an expected end."},
    {"reference": "Psalm 46:10", "text": "Be still, and know that I am God: I will be exalted among the heathen, I will be exalted in the earth."},
    {"reference": "Romans 8:28", "text": "And we know that all things work together for good to them that love God, to them who are the called according to his purpose."},
    {"reference": "Joshua 1:9", "text": "Have not I commanded thee? Be strong and of a good courage; be not afraid, neither be thou dismayed: for the LORD thy God is with thee whithersoever thou goest."},
    {"reference": "Psalm 118:24", "text": "This is the day which the LORD hath made; we will rejoice and be glad in it."},
    {"reference": "Proverbs 16:3", "text": "Commit thy works unto the LORD, and thy thoughts shall be established."},
    {"reference": "Isaiah 40:31", "text": "But they that wait upon the LORD shall renew their strength; they shall mount up with wings as eagles; they shall run, and not be weary; and they shall walk, and not faint."},
    {"reference": "Matthew 5:16", "text": "Let your light so shine before men, that they may see your good works, and glorify your Father which is in heaven."},
    {"reference": "Galatians 5:22-23", "text": "But the fruit of the Spirit is love, joy, peace, longsuffering, gentleness, goodness, faith, Meekness, temperance: against such there is no law."},
    {"reference": "Psalm 34:8", "text": "O taste and see that the LORD is good: blessed is the man that trusteth in him."},
    {"reference": "Numbers 6:24", "text": "The LORD bless thee, and keep thee:"},
    {"reference": "Zephaniah 3:17", "text": "The LORD thy God in the midst of thee is mighty; he will save, he will rejoice over thee with joy; he will rest in his love, he will joy over thee with singing."},
    {"reference": "Psalm 37:4", "text": "Delight thyself also in the LORD; and he shall give thee the desires of thine heart."},
    {"reference": "Isaiah 26:3", "text": "Thou wilt keep him in perfect peace, whose mind is stayed on thee: because he trusteth in thee."},
    {"reference": "Micah 6:8", "text": "He hath shewed thee, O man, what is good; and what doth the LORD require of thee, but to do justly, and to love mercy, and to walk humbly with thy God?"},
    {"reference": "Psalm 121:1-2", "text": "I will lift up mine eyes unto the hills, from whence cometh my help. My help cometh from the LORD, which made heaven and earth."},
    {"reference": "Colossians 3:23", "text": "And whatsoever ye do, do it heartily, as to the Lord, and not unto men;"},
    {"reference": "Psalm 19:14", "text": "Let the words of my mouth, and the meditation of my heart, be acceptable in thy sight, O LORD, my strength, and my redeemer."},
    {"reference": "1 Peter 5:7", "text": "Casting all your care upon him; for he careth for you."},
    {"reference": "Psalm 27:1", "text": "The LORD is my light and my salvation; whom shall I fear? the LORD is the strength of my life; of whom shall I be afraid?"},
]


@app.route('/api/random-verse', methods=['GET'])
def api_random_verse():
    """Return a random verse from the Bible (fetched live, with curated fallback)."""
    version = request.args.get('version', 'en-kjv')

    # Try fetching a truly random verse from the live API first
    for _ in range(3):
        book = random.choice(BIBLE_BOOKS)
        chapter = random.randint(1, book['chapters'])
        try:
            verses, _ = fetch_chapter_bibleapi_smart(book['name'], chapter, version)
            if verses:
                v = random.choice(verses)
                return jsonify({
                    'reference': v['reference'],
                    'text': v['text'],
                    'book': book['name'],
                    'book_slug': book['slug'],
                    'chapter': chapter,
                    'verse': v['verse'],
                    'version': version,
                })
        except Exception as e:
            print(f"Random verse fetch error: {e}")

    # Fallback to the curated list
    v = random.choice(RANDOM_FALLBACK_VERSES)
    return jsonify({
        'reference': v['reference'],
        'text': v['text'],
        'book': '', 'book_slug': '', 'chapter': 0, 'verse': '',
        'version': 'en-kjv',
        'fallback': True,
    })


@app.route('/devotional')
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


@app.route('/prayer-journal')
def prayer_journal_page():
    user = session.get('user')
    return render_template('prayer-journal.html', user=user, current_year=dt.datetime.now().year)


@app.route('/api/export', methods=['GET'])
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
    notes = data.get('notes', []) or []
    prayers = data.get('prayers', []) or []
    reading_log = data.get('readingLog', []) or []

    # Flatten highlights into references
    highlight_refs = []
    for chapter_key, verse_list in highlights.items():
        # chapter_key looks like "John_3"
        parts = chapter_key.rsplit('_', 1)
        book_part = parts[0].replace('_', ' ') if parts else chapter_key
        chapter_part = parts[1] if len(parts) > 1 else ''
        for verse in verse_list:
            color = (highlight_colors.get(chapter_key) or {}).get(str(verse), '')
            ref = f"{book_part} {chapter_part}:{verse}"
            highlight_refs.append({'reference': ref, 'color': color or 'default'})

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
                lines.append("- %s%s" % (h['reference'], (" _(color: %s)_" % h['color']) if h.get('color') and h['color'] != 'default' else ""))
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
                suffix = " (%s)" % h['color'] if h.get('color') and h['color'] != 'default' else ""
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



@app.route('/robots.txt')
def robots_txt():
    sitemap_url = url_for('sitemap_xml', _external=True)
    content = f"User-agent: *\nAllow: /\nSitemap: {sitemap_url}\n"
    return Response(content, mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    pages = [
        url_for('index', _external=True),
        url_for('contact', _external=True),
        url_for('install_guide', _external=True),
        url_for('search', _external=True),
        url_for('reading_plans_page', _external=True),
        url_for('topics_page', _external=True),
        url_for('quiz_page', _external=True),
        url_for('compare_page', _external=True),
        url_for('devotional_page', _external=True),
        url_for('prayer_journal_page', _external=True),
        url_for('bible_in_a_year', _external=True),
    ]
    pages.extend(url_for('books', book_slug=book['slug'], _external=True) for book in BIBLE_BOOKS)
    lastmod = dt.date.today().isoformat()
    xml_urls = "\n".join(
        f"    <url>\n      <loc>{page}</loc>\n      <lastmod>{lastmod}</lastmod>\n      <changefreq>weekly</changefreq>\n      <priority>0.7</priority>\n    </url>"
        for page in pages
    )
    xml = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n{xml_urls}\n</urlset>"
    return Response(xml, mimetype='application/xml')


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


@app.route("/offline")
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


if __name__ == "__main__":
    app.run(debug=True)