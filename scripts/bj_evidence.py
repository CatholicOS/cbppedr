"""Evidence from the appendices of La Bibbia di Gerusalemme (EDB 2011):
the index of names in the notes, the Hasmonean and Herodian family tree, and the
biblical column of the chronological table.

The chronological rows carry the book's wording, so all output goes to the
private folder (default ~/development/BibleGet-I-O/data-local/cbppedr/).

Usage: python bj_evidence.py [--xml PATH] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from lxml import etree

from refs import parse_refs
from units import units_for

DEFAULT_XML = Path("/mnt/c/Users/johnr/Documents/BibleGet/bibbia_gerusalemme_completa.xml")
PRIVATE = Path(os.environ.get("CBPPEDR_PRIVATE", Path.home() / "development/BibleGet-I-O/data-local/cbppedr"))
RIGHT_COLUMN_FROM = 47.0  # cells starting right of this x (% of page width) are Palestinian/biblical history


def _root(path: Path):
    return etree.parse(str(path), etree.XMLParser(huge_tree=True, resolve_entities=False)).getroot()


def _appendix(root, title_prefix: str):
    for a in root.iter("appendix"):
        if a.get("title", "").startswith(title_prefix):
            return a
    return None


def _units(text: str) -> tuple[list[str], list[str]]:
    units, unresolved = [], []
    for r in parse_refs(text, "bj"):
        u = units_for(r)
        if u is None:
            unresolved.append(text[r.span[0]:r.span[1]])
        else:
            units += [x for x in u if x not in units]
    return units, unresolved


def index(path: Path) -> list[dict]:
    """Entries of the index of notes whose head is a name (capitals): persons and places."""
    a = _appendix(_root(path), "Indice alfabetico delle note")
    out = []
    for e in a.iter("entry") if a is not None else []:
        text = re.sub(r"\s+", " ", "".join(e.itertext())).strip()
        m = re.match(r"([A-ZÀ-Ý][A-ZÀ-Ýʿʾ'’ -]*[A-ZÀ-Ý])(?=[\s:,.]|$)", text)
        if not m or not re.search(r"[A-ZÀ-Ý]{2}", m.group(1)):
            continue
        name = m.group(1).strip()
        rest = text[m.end():]
        see = [s.strip(" .;") for s in re.findall(r"\bv\.\s+([A-ZÀ-Ý][A-ZÀ-Ýʿʾ'’ -]+)", rest)]
        units, unresolved = _units(rest)
        out.append({"name": name, "page": int(e.get("pdf_page", 0)), "units": units,
                    "unresolved": unresolved, "see": see})
    return out


PERSON = re.compile(r"^(?:\[da (?P<mother>[^\]]+)\]\s*)?(?:(?P<n>\d+)([a-z])?\.\s*)?(?P<rest>.*)$")


def tree(path: Path) -> list[dict]:
    a = _appendix(_root(path), "Dinastie Asmonea e Erodiana")
    out: list[dict] = []
    stack: list[dict] = []
    for p in a.iter("person") if a is not None else []:
        level = int(p.get("level", 0))
        text = re.sub(r"\s+", " ", "".join(p.itertext())).strip()
        m = PERSON.match(text)
        rest = re.sub(r"\[[^\]]*\]", "", m.group("rest")).strip()
        parts = [s.strip() for s in rest.split("∞")]
        head = parts[0]
        dm = re.search(r"(†\s*\d+|\d+(?:-\d+)?(?:\s*a\.C\.)?)\s*$", head)
        dates = dm.group(1).strip() if dm else None
        name = head[:dm.start()].strip() if dm else head
        while stack and stack[-1]["level"] >= level:
            stack.pop()
        row = {"n": int(m.group("n")) if m.group("n") else None, "name": name, "level": level,
               "parent": stack[-1]["name"] if stack else None, "mother": m.group("mother"),
               "spouses": [s for s in parts[1:] if s], "dates": dates, "text": text}
        out.append(row)
        stack.append(row)
    return out


def _cell_text(cell) -> str:
    text = ""
    for line in cell.iter("l"):
        t = (line.text or "").strip()
        text = text[:-1] + t if text.endswith("-") else (text + " " + t).strip()
    return text


def chrono(path: Path) -> list[dict]:
    a = _appendix(_root(path), "Tavola cronologica")
    out = []
    for row in a.iter("row") if a is not None else []:
        for cell in row.iter("cell"):
            x = cell.get("x", "0-0").split("-")[0]
            if float(x) < RIGHT_COLUMN_FROM:
                continue
            text = _cell_text(cell)
            units, unresolved = _units(text)
            out.append({"page": int(row.get("pdf_page", 0)), "text": text, "units": units,
                        "unresolved": unresolved})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--xml", type=Path, default=DEFAULT_XML)
    ap.add_argument("--out-dir", type=Path, default=PRIVATE)
    a = ap.parse_args(argv)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    for name, fn in (("bj-index", index), ("bj-tree", tree), ("bj-chrono", chrono)):
        rows = fn(a.xml)
        with (a.out_dir / f"{name}.jsonl").open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{name}: {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
