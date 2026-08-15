#!/usr/bin/env python3
"""
Build the bundled Bible data files used by MyPersonal Bible.

Downloads public-domain / openly-licensed content and converts it into
compact gzipped JSON files under static/data/:

  1. kjv.json.gz        - King James Version (public domain)
                          Source: github.com/thiagobodruk/bible (en_kjv.json)
                          Used for: built-in offline search fallback

  2. commentary.json.gz - Matthew Henry's Concise Commentary (public domain)
                          Source: github.com/lyteword/mhenry-concise (markdown)
                          Used for: the Commentary tab in the reader

  3. yoruba.json.gz     - Biblica Open Yoruba Contemporary Bible (2017)
                          License: free to use with attribution (Biblica®)
                          Source: ebible.org/Scriptures/yor_usfm.zip
                          Used for: the Yoruba translation in the reader

Run:  python3 build_data.py
Requires: internet access, python3 (stdlib only).
"""
import gzip
import json
import re
import urllib.request
import zipfile
import tarfile
import io
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static", "data")

# ---- book data (same order as BIBLE_BOOKS in main.py) ----
BOOKS = [
    ("Genesis", "genesis", "GEN"), ("Exodus", "exodus", "EXO"), ("Leviticus", "leviticus", "LEV"),
    ("Numbers", "numbers", "NUM"), ("Deuteronomy", "deuteronomy", "DEU"), ("Joshua", "joshua", "JOS"),
    ("Judges", "judges", "JDG"), ("Ruth", "ruth", "RUT"), ("1 Samuel", "1-samuel", "1SA"),
    ("2 Samuel", "2-samuel", "2SA"), ("1 Kings", "1-kings", "1KI"), ("2 Kings", "2-kings", "2KI"),
    ("1 Chronicles", "1-chronicles", "1CH"), ("2 Chronicles", "2-chronicles", "2CH"), ("Ezra", "ezra", "EZR"),
    ("Nehemiah", "nehemiah", "NEH"), ("Esther", "esther", "EST"), ("Job", "job", "JOB"),
    ("Psalms", "psalms", "PSA"), ("Proverbs", "proverbs", "PRO"), ("Ecclesiastes", "ecclesiastes", "ECC"),
    ("Song of Solomon", "song-of-solomon", "SNG"), ("Isaiah", "isaiah", "ISA"), ("Jeremiah", "jeremiah", "JER"),
    ("Lamentations", "lamentations", "LAM"), ("Ezekiel", "ezekiel", "EZK"), ("Daniel", "daniel", "DAN"),
    ("Hosea", "hosea", "HOS"), ("Joel", "joel", "JOL"), ("Amos", "amos", "AMO"), ("Obadiah", "obadiah", "OBA"),
    ("Jonah", "jonah", "JON"), ("Micah", "micah", "MIC"), ("Nahum", "nahum", "NAM"),
    ("Habakkuk", "habakkuk", "HAB"), ("Zephaniah", "zephaniah", "ZEP"), ("Haggai", "haggai", "HAG"),
    ("Zechariah", "zechariah", "ZEC"), ("Malachi", "malachi", "MAL"), ("Matthew", "matthew", "MAT"),
    ("Mark", "mark", "MRK"), ("Luke", "luke", "LUK"), ("John", "john", "JHN"), ("Acts", "acts", "ACT"),
    ("Romans", "romans", "ROM"), ("1 Corinthians", "1-corinthians", "1CO"),
    ("2 Corinthians", "2-corinthians", "2CO"), ("Galatians", "galatians", "GAL"),
    ("Ephesians", "ephesians", "EPH"), ("Philippians", "philippians", "PHP"),
    ("Colossians", "colossians", "COL"), ("1 Thessalonians", "1-thessalonians", "1TH"),
    ("2 Thessalonians", "2-thessalonians", "2TH"), ("1 Timothy", "1-timothy", "1TI"),
    ("2 Timothy", "2-timothy", "2TI"), ("Titus", "titus", "TIT"), ("Philemon", "philemon", "PHM"),
    ("Hebrews", "hebrews", "HEB"), ("James", "james", "JAS"), ("1 Peter", "1-peter", "1PE"),
    ("2 Peter", "2-peter", "2PE"), ("1 John", "1-john", "1JN"), ("2 John", "2-john", "2JN"),
    ("3 John", "3-john", "3JN"), ("Jude", "jude", "JUD"), ("Revelation", "revelation", "REV"),
]
SLUG_TO_NAME = {slug: name for name, slug, _ in BOOKS}
CODE_TO_NAME = {code: name for name, _, code in BOOKS}


def download(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "MyPersonalBible/2.2 data-builder"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def save_gz(path: str, obj):
    with gzip.open(path, "wb") as f:
        f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    print(f"  wrote {path} ({os.path.getsize(path) / 1024:.0f} KB)")


def build_kjv():
    print("[1/3] Building KJV index...")
    raw = json.loads(download("https://raw.githubusercontent.com/thiagobodruk/bible/master/json/en_kjv.json").decode("utf-8-sig"))
    books = []
    for b in raw:
        name = b["name"]
        slug = next((s for n, s, _ in BOOKS if n.lower() == name.lower()), None)
        if not slug:
            print(f"  !! no slug for '{name}', skipping")
            continue
        chapters = []
        for ch in b["chapters"]:
            chapters.append([clean_kjv(v) for v in ch])
        books.append({"name": name, "slug": slug, "chapters": chapters})
    save_gz(os.path.join(DATA_DIR, "kjv.json.gz"), {"books": books})


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def clean_kjv(text: str) -> str:
    # remove section headings like [A Psalm of David.] and braces around supplied words
    text = re.sub(r"\[.*?\]", "", text or "")
    text = text.replace("{", "").replace("}", "")
    return clean(text)


def build_commentary():
    print("[2/3] Building Matthew Henry commentary...")
    raw = download("https://github.com/lyteword/mhenry-concise/archive/refs/heads/main.tar.gz", timeout=180)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tar:
        data = {}
        for member in tar.getmembers():
            if not member.isfile():
                continue
            parts = member.name.split("/")
            if len(parts) != 3:
                continue
            filename = parts[2]
            # accept both "chapter-3.md" and (for Psalms) "psalm-3.md"
            m = re.match(r"^(?:chapter|psalm)-(\d+)\.md$", filename)
            if not m:
                continue
            folder = parts[1]
            if folder not in SLUG_TO_NAME:
                continue
            chapter = int(m.group(1))
            text = tar.extractfile(member).read().decode("utf-8", errors="replace")
            parsed = parse_commentary_md(text)
            if parsed:
                data.setdefault(folder, {})[chapter] = parsed
    save_gz(os.path.join(DATA_DIR, "commentary.json.gz"), {"books": data})
    n = sum(len(chs) for chs in data.values())
    print(f"  {len(data)} books, {n} chapters with commentary")


def parse_commentary_md(text: str):
    # strip YAML front matter
    m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.S)
    if m:
        text = text[m.end():]
    sections = re.split(r"^##\s+", text, flags=re.M)[1:]
    outline = ""
    out_sections = []
    for sec in sections:
        lines = sec.split("\n")
        title = lines[0].strip()
        body = clean("\n".join(lines[1:]))
        if title.lower().startswith("chapter outline"):
            outline = body
        else:
            out_sections.append({"title": title, "text": body})
    if not out_sections and not outline:
        return None
    return {"outline": outline, "sections": out_sections}


def build_yoruba():
    print("[3/3] Building Yoruba Bible...")
    raw = download("https://ebible.org/Scriptures/yor_usfm.zip", timeout=180)
    books = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".usfm"):
                continue
            code = os.path.basename(name).split("-")[1][:3].upper()
            book_name = CODE_TO_NAME.get(code)
            if not book_name:
                continue
            content = zf.read(name).decode("utf-8", errors="replace")
            chapters = parse_usfm(content)
            if chapters:
                books[book_name] = chapters
    out_books = []
    for name, slug, _ in BOOKS:
        if name in books:
            out_books.append({"name": name, "slug": slug, "chapters": books[name]})
    save_gz(os.path.join(DATA_DIR, "yoruba.json.gz"), {"books": out_books})
    total = sum(len(b["chapters"]) for b in out_books)
    print(f"  {len(out_books)} books, {total} chapters")


def parse_usfm(content: str):
    """Parse eBible.org USFM into chapters = [[verse_text, ...], ...]"""
    chapters = []
    current = None  # list of [num, text]
    for line in content.split("\n"):
        line = line.strip()
        cm = re.match(r"\\c\s+(\d+)", line)
        if cm:
            if current is not None:
                chapters.append(current)
            current = []
            continue
        if current is None:
            continue
        # find verse markers on this line
        segments = list(re.finditer(r"\\v\s+(\d+)\s+(.*)", line))
        if segments:
            for i, vm in enumerate(segments):
                end = segments[i + 1].start() if i + 1 < len(segments) else len(line)
                text = line[vm.start(2):end].strip()
                # strip footnotes and inline markers from the verse text only
                text = re.sub(r"\\f\s.*?\\f\*", " ", text)
                text = re.sub(r"\\[a-z0-9]+\*?\s?", " ", text)
                current.append([int(vm.group(1)), text])
        elif line and not line.startswith("\\") and current:
            # continuation of the previous verse's text
            current[-1][1] += " " + line
    if current is not None:
        chapters.append(current)
    return [[clean(t) for _, t in sorted(ch, key=lambda x: x[0])] for ch in chapters]


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    build_kjv()
    build_commentary()
    build_yoruba()
    print("\nDone. Files are in static/data/")
