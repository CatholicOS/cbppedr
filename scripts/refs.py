"""Find verse references in Italian text (CEI 2008 abbreviations and numbering).

parse_refs("Gn 25,6; Nm 21,11", profile="ndeib") -> [Ref(book=1, ...), Ref(book=4, ...)]

Profiles differ in their abbreviations (data/books.json): in the Bibbia di
Gerusalemme "Gn" is Jonah, in the dictionary it is Genesis.
"""

from __future__ import annotations

import json
import re
from functools import cache
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent

VERSE = r"\d+[a-z]?"
REF = re.compile(
    r"(?<![\w,])(?:(?P<book>[1-3]\s?[A-Z][a-zà-ù]{0,4}|[A-Z][a-zà-ù]{0,4})\s+)?"
    r"(?P<ch>\d+),(?P<vs>" + VERSE + r"(?:[-–]" + VERSE + r"(?:,\d+[a-z]?)?)?"
    r"(?:\." + VERSE + r"(?:[-–]" + VERSE + r")?)*)"
)


BOOK = r"(?P<book>[1-3]\s?[A-Z][a-zà-ù]{0,4}|[A-Z][a-zà-ù]{0,4})"
CHAPTER_ONLY = re.compile(r"(?<![\w,])" + BOOK + r"\s+\d+(?![\d,\w])")
UNIT = re.compile(r"\s*(?:litri|l|metri|m|cm|mm|km|chilometri|kg|chili|grammi|g|ettari|ha|sicli|%)\b")

# what may stand between two references of one list: "; ", ", ", " e ", " cf. ", " s.; "
CONTINUATION = re.compile(r"^(?:\s|[;,–-]|\be\b|\bcf\.|\bss?\.|\+)*$")


class Ref(NamedTuple):
    book: int
    chapter: int
    verses: list[str]
    span: tuple[int, int]
    end_chapter: int | None = None
    parts: tuple[str, ...] = ()


@cache
def _books(profile: str) -> dict[str, int]:
    return json.loads((HERE / "books_it.json").read_text(encoding="utf-8"))[profile]


def _lookup(token: str, profile: str) -> int | None:
    books = _books(profile)
    return books.get(token) or books.get(re.sub(r"^([1-3])\s", r"\1", token)) \
        or books.get(re.sub(r"^([1-3])", r"\1 ", token))


def parse_refs(text: str, profile: str, default_book: int | None = None) -> list[Ref]:
    current = default_book
    refs: list[Ref] = []
    last_end: int | None = None
    matches = sorted([*REF.finditer(text), *CHAPTER_ONLY.finditer(text)], key=lambda m: m.start())
    for m in matches:
        if m.re is CHAPTER_ONLY:
            book = _lookup(m.group("book"), profile)
            if book is not None:
                current, last_end = book, m.end()
            continue
        if not m.group("book") and (int(m.group("ch")) == 0 or UNIT.match(text, m.end())):
            continue  # a measure such as "1,87 litri", not a reference
        gap = text[last_end:m.start()] if last_end is not None else None
        if not m.group("book") and (gap is None or not CONTINUATION.match(gap)):
            current = default_book
        last_end = m.end()
        if m.group("book"):
            current = _lookup(m.group("book"), profile)
            start = m.start("book")
        else:
            start = m.start("ch")
        if current is None:
            continue
        vs = m.group("vs")
        end_chapter = None
        range_ch = re.match(VERSE + r"[-–](\d+),", vs)
        if range_ch:
            end_chapter = int(range_ch.group(1))
        verses = [re.match(r"\d+[a-z]?", part).group(0) for part in vs.split(".")]
        refs.append(Ref(current, int(m.group("ch")), verses, (start, m.end()), end_chapter, tuple(vs.split("."))))
    return refs
