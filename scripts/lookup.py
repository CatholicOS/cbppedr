"""Reviewer helpers: the Nova Vulgata verse of a unit, and the Jerusalem Bible notes on it.

Both print copyrighted or private text to the terminal only; nothing is written.

Usage: python lookup.py nv btu:gn.29.34
       python lookup.py notes btu:mt.14.3
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from functools import cache
from pathlib import Path

from lxml import etree

from units import CBTUDR, _map

NV_TEXT = Path(os.environ.get("NV_TEXT", Path.home() / "development/BibleGet-I-O/NVBSE-vatican/text"))
BJ_XML = Path(os.environ.get("BJ_XML", "/mnt/c/Users/johnr/Documents/BibleGet/bibbia_gerusalemme_completa.xml"))
HERE = Path(__file__).resolve().parent
UNIT = re.compile(r"btu:([a-z0-9]+)\.(\d+)\.(\d+)")


@cache
def _segments() -> dict[str, int]:
    books = json.loads((CBTUDR / "data/books.json").read_text(encoding="utf-8"))["books"]
    return {b["segment"]: b["number"] for b in books}


def _parse(unit: str) -> tuple[int, int, int]:
    m = UNIT.match(unit)
    if not m:
        raise ValueError(f"not a unit: {unit}")
    return _segments()[m.group(1)], int(m.group(2)), int(m.group(3))


def nv_verse(unit: str) -> str:
    book, ch, v = _parse(unit)
    (path,) = NV_TEXT.glob(f"{book:02d}-*.tsv")
    with path.open(encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh, delimiter="\t") if r["chapter"] == str(ch) and r["verse"] == str(v)]
    return " ".join(r["text"] for r in rows)


@cache
def _bj():
    return etree.parse(str(BJ_XML), etree.XMLParser(huge_tree=True, resolve_entities=False)).getroot()


@cache
def _bj_code(book: int) -> str:
    codes = json.loads((HERE / "books_it.json").read_text(encoding="utf-8"))["bj"]
    return next(c for c, n in codes.items() if n == book and re.fullmatch(r"\d?[A-Z][a-z]+", c))


def _cei_refs(book: int, unit: str) -> list[tuple[int, int]]:
    out = []
    for ref, units in _map(book).items():
        if unit in units or any(u.startswith(unit + ".") for u in units):
            ch, v = ref.split("@")[0].split(":")
            out.append((int(ch), int(re.match(r"\d+", v).group(0))))
    return out


def _covers(ref: str, ch: int, v: int) -> bool:
    m = re.match(r"(\d+),(\d+)[a-z]?(?:\s*[-–]\s*(?:(\d+),)?(\d+))?", ref.strip())
    if not m:
        return False
    c1, v1, c2, v2 = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
    end = (int(c2) if c2 else c1, int(v2) if v2 else v1)
    return (c1, v1) <= (ch, v) <= end


def bj_notes(unit: str) -> list[dict]:
    book, _, _ = _parse(unit)
    code = _bj_code(book)
    refs = _cei_refs(book, unit)
    out = []
    for b in _bj().iter("book"):
        if b.get("code") != code:
            continue
        last_page = None
        for n in b.iter():
            if n.get("pdf_page"):
                last_page = n.get("pdf_page")
            if n.tag != "note" or n.get("source") != "BJ":
                continue
            if any(_covers(n.get("ref", ""), ch, v) for ch, v in refs):
                page = last_page
                out.append({"ref": f"{code} {n.get('ref')}", "page": int(page) if page else None,
                            "text": re.sub(r"\s+", " ", "".join(n.itertext())).strip()})
    return out


def main(argv: list[str]) -> int:
    what, unit = argv[1], argv[2]
    if what == "nv":
        print(nv_verse(unit))
    else:
        for n in bj_notes(unit):
            print(f"[{n['ref']} @p{n['page']}] {n['text']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
