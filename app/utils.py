"""Shared text helpers."""
import re


def clean_text(text: str) -> str:
    """Clean verse text."""
    if not text:
        return text
    text = text.replace('…', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def dedupe_verses(raw_verses: list) -> list:
    """Remove duplicate verses."""
    seen = set()
    out = []
    for v in raw_verses:
        key = v.get('verse') or v.get('reference') or v.get('text')
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out



