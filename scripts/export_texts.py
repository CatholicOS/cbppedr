"""Export editions' text keyed by CBTUDR unit, for audit_attested.py (private output).

The texts are under copyright, so the output goes to the private folder, never to the
repository. Each row of an edition's table is mapped to its units through CBTUDR's maps
(`data/maps/<edition>/NN-book.json`, refs `chapter:verse`, with the sub-verse and the
`@GREEK`/`@HEBREW` origin where the edition has them).

Usage: PSQL="docker exec bg-eval-db psql -U bibleget -d bibleget" python export_texts.py NVBSE CEI2008 NABRE VGCL DRB
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shlex
import subprocess
import sys
from collections import defaultdict

from audit_attested import TEXTS
from units import CBTUDR

PSQL = os.environ.get("PSQL", "docker exec bg-eval-db psql -U bibleget -d bibleget")
QUERY = ("select book, chapter, coalesce(nullif(verseequiv, ''), verse::text), coalesce(verseorigin, ''), "
         "regexp_replace(text, E'[\\\\n\\\\r\\\\t]+', ' ', 'g') from \"{}\" order by \"verseID\"")
PLAIN_QUERY = ("select book, chapter, coalesce(nullif(verseequiv, ''), verse::text), coalesce(verseorigin, ''), "
               "text_plain, coalesce(text_tradition, '') from \"{}\" order by \"verseID\"")


def maps(edition: str) -> dict[tuple[int, str], list[str]]:
    out = {}
    for p in (CBTUDR / "data/maps" / edition.lower()).glob("*.json"):
        for v in json.loads(p.read_text(encoding="utf-8"))["verses"]:
            out[(int(p.name[:2]), v["ref"])] = v["units"]
    return out


def row_units(book: str, chapter: str, verse: str, origin: str, refs: dict[tuple[int, str], list[str]]) -> list[str]:
    ref = f"{chapter}:{verse}"
    units = refs.get((int(book), f"{ref}@{origin}" if origin else ref))
    if not units and origin and not any((int(book), f"{ref}@{o}") in refs for o in ("GREEK", "HEBREW")):
        units = refs.get((int(book), ref))  # the map does not split this verse by origin
    return units or []


def plain_by_unit(rows: list[list[str]], refs: dict[tuple[int, str], list[str]]) -> tuple[dict[str, dict], int]:
    """The stored text_plain by unit key, with its SHA-256; units fed by several rows of one text are left out."""
    fed: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for r in rows:
        book, chapter, verse, origin, text = r[:5]
        tradition = r[5] if len(r) > 5 and r[5] else origin
        for u in row_units(book, chapter, verse, origin, refs):
            fed[u].append((tradition, text))
    out: dict[str, dict] = {}
    skipped = 0

    def put(key: str, text: str) -> None:
        out[key] = {"text": text, "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()}

    for u, items in fed.items():
        traditions = {t for t, _ in items}
        if {"GREEK", "HEBREW"} <= traditions:
            if len(items) == len(traditions):
                for t, text in items:
                    put(f"{u}@{t}", text)
                continue
        elif len(items) == 1:
            put(u, items[0][1])
            continue
        skipped += 1
    return out, skipped


def by_unit(rows: list[list[str]], refs: dict[tuple[int, str], list[str]]) -> tuple[dict[str, str], int]:
    texts: dict[str, list[str]] = defaultdict(list)
    unmapped = 0
    for book, chapter, verse, origin, text in rows:
        units = row_units(book, chapter, verse, origin, refs)
        if not units:
            unmapped += 1
            continue
        for u in units:
            texts[u].append(html.unescape(re.sub(r"<[^>]+>", " ", text)))
    return {u: " ".join(t) for u, t in texts.items()}, unmapped


def main(argv: list[str]) -> int:
    TEXTS.mkdir(parents=True, exist_ok=True)
    plain = "--plain" in argv
    for edition in [a for a in argv[1:] if a != "--plain"]:
        if not re.fullmatch(r"[A-Z0-9_]+", edition):
            print(f"not an edition table name: {edition!r}", file=sys.stderr)
            return 1
        query = PLAIN_QUERY if plain else QUERY
        out = subprocess.run(shlex.split(PSQL) + ["-AtF", "\t", "-c", query.format(edition)],
                             capture_output=True, text=True, check=True).stdout
        if plain:
            units, skipped = plain_by_unit([l.split("\t", 5) for l in out.splitlines()], maps(edition))
            (TEXTS / f"{edition}-plain.json").write_text(json.dumps(units, ensure_ascii=False), encoding="utf-8")
            print(edition, len(units), "units;", skipped, "units over several rows left out", file=sys.stderr)
            continue
        texts, unmapped = by_unit([l.split("\t", 4) for l in out.splitlines()], maps(edition))
        (TEXTS / f"{edition}.json").write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")
        print(edition, len(texts), "units;", unmapped, "rows unmapped")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
