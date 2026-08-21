#!/usr/bin/env python3
"""Build app/static/data/headings.json.gz: per-verse section headings for the
Bible reader, bundled from the Berean Standard Bible (public domain).

Source: BSB-publishing/bsb2usfm (official Berean Bible GitHub), release v5.9,
file BSB_int_usfm.zip. The BSB text is dedicated to the public domain:
https://github.com/BSB-publishing/bsb2usfm/blob/main/LICENSE

Output format:
{
  "meta": {"source": "Berean Standard Bible (public domain)", "generated": "..."},
  "books": {
     "genesis":  {"1": {"1": "The Creation", "3": "The First Day", ...}, ...},
     ...
  }
}
Each heading is attached to the verse it introduces (the first verse number
that follows it in the USFM), so it renders before that verse regardless of
which Bible version the reader is displaying.
"""
import gzip
import io
import json
import os
import re
import sys
import urllib.request
import zipfile
import datetime as dt

DOWNLOAD_URL = (
    "https://github.com/BSB-publishing/bsb2usfm/releases/download/v5.9/"
    "BSB_int_usfm.zip"
)
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "app", "static", "data", "headings.json.gz")

# Book slugs in canonical order (matches BIBLE_BOOKS; BSB zip numbers files
# 01..39 for the OT and 41..67 for the NT, same order).
BOOK_SLUGS = [
    "genesis", "exodus", "leviticus", "numbers", "deuteronomy", "joshua",
    "judges", "ruth", "1-samuel", "2-samuel", "1-kings", "2-kings",
    "1-chronicles", "2-chronicles", "ezra", "nehemiah", "esther", "job",
    "psalms", "proverbs", "ecclesiastes", "song-of-solomon", "isaiah",
    "jeremiah", "lamentations", "ezekiel", "daniel", "hosea", "joel", "amos",
    "obadiah", "jonah", "micah", "nahum", "habakkuk", "zephaniah", "haggai",
    "zechariah", "malachi", "matthew", "mark", "luke", "john", "acts",
    "romans", "1-corinthians", "2-corinthians", "galatians", "ephesians",
    "philippians", "colossians", "1-thessalonians", "2-thessalonians",
    "1-timothy", "2-timothy", "titus", "philemon", "hebrews", "james",
    "1-peter", "2-peter", "1-john", "2-john", "3-john", "jude", "revelation",
]
assert len(BOOK_SLUGS) == 66, len(BOOK_SLUGS)

HEADING_MARKERS = {"s", "s1", "s2", "s3", "ms", "ms1", "ms2"}


def clean_heading(raw: str) -> str:
    """Strip USFM inline markers, cross references and footnotes from a heading."""
    text = raw.strip()
    if not text:
        return ""
    # drop trailing cross-reference display, e.g. \r ( ... \ref*)
    text = re.sub(r"\\r\s*\(.*$", "", text)
    # drop footnotes \f ... \f* and cross refs \x ... \x*
    text = re.sub(r"\\f[^\n]*?\\f\*", "", text)
    text = re.sub(r"\\x[^\n]*?\\x\*", "", text)
    # remove any remaining USFM markers: \word and closing * markers
    text = re.sub(r"\\[a-zA-Z]+[0-9]*\b", "", text)
    text = text.replace("\\*", "")
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # drop stray punctuation-only results
    if re.fullmatch(r"[|().,;:—\-–'\" ]+", text):
        return ""
    return text


def parse_book_usfm(data: str) -> dict:
    """Return {chapter_str: {verse_str: heading}} for one book."""
    headings = {}
    current_chapter = None
    pending = []  # headings waiting for their verse
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"\\c\s+(\d+)", line)
        if m:
            current_chapter = str(int(m.group(1)))
            headings.setdefault(current_chapter, {})
            pending = []
            continue
        m = re.match(r"\\(s\d?|ms\d?)\s+(.*)", line)
        if m and current_chapter:
            cleaned = clean_heading(m.group(2))
            if cleaned and len(cleaned) >= 2:
                pending.append(cleaned)
            continue
        # verses may share a line with the paragraph marker (\p \v 3 ...),
        # and several verses may share one line; headings attach to the FIRST
        # verse number that follows them
        vm = re.search(r"\\v\s+(\d+)\b", line)
        if vm and current_chapter and pending:
            verse = str(int(vm.group(1)))
            for h in pending:
                if verse not in headings[current_chapter]:
                    headings[current_chapter][verse] = h
            pending = []
    # strip empty chapters
    return {c: v for c, v in headings.items() if v}


def main():
    print(f"Downloading BSB USFM: {DOWNLOAD_URL}")
    req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "MyPersonal-Bible-headings-builder/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        blob = resp.read()
    print(f"Downloaded {len(blob)} bytes")

    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        files = sorted(n for n in zf.namelist() if n.lower().endswith(".usfm"))
        # order: OT files numbered 01..39, NT files numbered 41..67
        def file_index(name):
            base = os.path.basename(name)
            return int(base[:2])
        files = sorted(files, key=file_index)
        if len(files) != 66:
            print(f"Expected 66 USFM files, got {len(files)}")
            sys.exit(1)

        books = {}
        total = 0
        for slug, name in zip(BOOK_SLUGS, files):
            data = zf.read(name).decode("utf-8", errors="replace")
            chapters = parse_book_usfm(data)
            count = sum(len(v) for v in chapters.values())
            total += count
            books[slug] = chapters
            print(f"  {slug:18s} chapters with headings: {len(chapters):3d}  headings: {count}")

    payload = {
        "meta": {
            "source": "Berean Standard Bible (public domain)",
            "source_url": "https://github.com/BSB-publishing/bsb2usfm",
            "generated": dt.date.today().isoformat(),
        },
        "books": books,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with gzip.open(OUT_PATH, "wb") as f:
        f.write(raw.encode("utf-8"))
    print(f"\nWrote {OUT_PATH} ({len(raw)} raw chars, {total} headings total)")


if __name__ == "__main__":
    main()
