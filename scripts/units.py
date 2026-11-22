"""Resolve a parsed verse reference (CEI 2008 numbering) to CBTUDR units.

units_for(ref) -> ["btu:gn.29.34", ...], or None when any verse of the
reference is not a CEI 2008 verse in CBTUDR's map (another numbering, a
misprint): an unresolved reference is reported, never guessed.

CBTUDR is read from $CBTUDR_DIR (default ~/development/CatholicOS_org/cbtudr).
"""

from __future__ import annotations

import json
import os
import re
from functools import cache
from pathlib import Path

from refs import Ref

CBTUDR = Path(os.environ.get("CBTUDR_DIR", Path.home() / "development/CatholicOS_org/cbtudr"))


@cache
def _map(book: int) -> dict[str, list[str]]:
    (path,) = (CBTUDR / "data/maps/cei2008").glob(f"{book:02d}-*.json")
    verses = json.loads(path.read_text(encoding="utf-8"))["verses"]
    return {v["ref"]: v["units"] for v in verses}


def _lookup(book: int, chapter: int, verse: str) -> list[str] | None:
    m = _map(book)
    for key in (f"{chapter}:{verse}", f"{chapter}:{verse}@HEBREW", f"{chapter}:{verse}@GREEK"):
        if key in m:
            return m[key]
    return None


def _last_verse(book: int, chapter: int) -> int:
    nums = [int(re.match(r"\d+", k.split(":")[1]).group(0))
            for k in _map(book) if k.split(":")[0] == str(chapter)]
    return max(nums, default=0)


def _labels(book: int, chapter: int, part: str) -> list[tuple[int, str]]:
    m = re.fullmatch(r"(\d+)([a-z]?)(?:[-–](\d+)([a-z]?)(?:,(\d+)([a-z]?))?)?", part)
    if not m:
        return []
    a, a_l, b, b_l, c, c_l = m.groups()
    if b is None:
        return [(chapter, a + a_l)]
    if c is not None:  # a-b,c: from chapter:a to chapter b, verse c
        out = [(chapter, str(v)) for v in range(int(a), _last_verse(book, chapter) + 1)]
        for ch in range(chapter + 1, int(b)):
            out += [(ch, str(v)) for v in range(1, _last_verse(book, ch) + 1)]
        return out + [(int(b), str(v)) for v in range(1, int(c) + 1)]
    if a_l or b_l:
        return [(chapter, a + a_l), (chapter, b + b_l)]
    return [(chapter, str(v)) for v in range(int(a), int(b) + 1)]


def units_for(ref: Ref) -> list[str] | None:
    out: list[str] = []
    for part in ref.parts or tuple(ref.verses):
        labels = _labels(ref.book, ref.chapter, part)
        if not labels:
            return None
        for chapter, verse in labels:
            units = _lookup(ref.book, chapter, verse)
            if units is None:
                return None
            out += [u for u in units if u not in out]
    return out
