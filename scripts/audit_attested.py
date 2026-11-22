"""Flag attested verses that do not name their entry, in any edition checked.

A dictionary citation of a whole passage attaches every verse in it to one entry, though
most of those verses do not name it. This audit reads each edition's text keyed by CBTUDR
unit (private, exported from the BibleGet database: JSON objects {unit: text}, one file per
edition) and lists, for each person and place, the attested units where no edition contains
any of the entry's names (Latin, Italian, English). The list is for review: a verse may
name the entry by another name, or not at all.

Names are compared loosely: accents, case and spelling variants (j/i, v/u, y/i, k/c, ph/f,
h, double letters) are ignored, and a long word matches by its stem, so Latin inflection
(Abner, Abneri) is no obstacle. Events are not audited: verses narrate them without naming
them. A unit with a reviewed label (data/curated/labels.json: another name or a designation,
by edition) is accounted for.

Usage: python audit_attested.py [TEXTS_DIR] > audit.tsv   (id, unit, names tried)
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXTS = Path(os.environ.get("TEXTS", Path.home() / "development/BibleGet-I-O/data-local/cbppedr/texts"))
_STOP = """filius filia filii fili uxor mons montes torrens urbs regio terra mare lacus porta
    turris uallis desertum fons flumen fluuius rex de et in ad of the son daughter wife mount
    river brook city land sea lake gate tower ualley desert spring king il la le lo di del della
    dei degli figlio figlia moglie monte fiume torrente citta terra lago porta torre ualle deserto
    sorgente re trans iuxta beyond near oltre presso"""
# Words too common to identify a name of three letters or fewer, in any of the editions' languages.
FUNCTION = set("""et in ad de te se si ne me an on am as at be by he is it no of or so to us we
    il la le lo un da di ed ex""".split())


def lite(s: str) -> str:
    """Case, accents, ligatures and j/v only: keeps the h and double letters a short name needs."""
    s = unicodedata.normalize("NFKD", s.lower().replace("æ", "ae").replace("œ", "oe"))
    s = "".join(c for c in s if not unicodedata.combining(c)).replace("j", "i").replace("v", "u")
    return re.sub(r"[^a-z]+", " ", s)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower().replace("æ", "ae").replace("œ", "oe"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("j", "i").replace("v", "u").replace("y", "i").replace("k", "c").replace("ph", "f").replace("h", "")
    s = re.sub(r"[^a-z]+", " ", s)
    return re.sub(r"(.)\1", r"\1", s)


STOP = {w for raw in _STOP.split() for w in lite(raw).split()}


def stems(entry: dict) -> set[str]:
    """The entry's name words. A long word matches by its stem (a trailing '*'), compared in
    the loose spelling of norm(); a short one (three letters or fewer once normalized) must match a whole word
    in the stricter spelling of lite() (a leading '=': Heth stays heth, not et), and never when
    it is a common function word (On, Am). A person matches on any word of a name (Simon or
    Peter); a place only on the name's first word, its head (Bethany, not the Jordan of
    "Bethany beyond the Jordan")."""
    out = set()
    for name in entry.get("names", {}).values():
        toks = [t for t in lite(name or "").split() if t not in STOP]
        if entry.get("type") == "place":
            toks = toks[:1]
        for tok in toks:
            full = norm(tok).strip()
            if len(full) <= 3:
                if tok not in FUNCTION:
                    out.add("=" + tok)
            else:
                out.add(full[:max(4, len(full) - 2)] + "*")
    return out


def named(text: str, keys: set[str]) -> bool:
    """Whether a verse's raw text names one of the keys."""
    words, short = set(norm(text).split()), set(lite(text).split())
    for k in keys:
        if k.endswith("*"):
            if any(w.startswith(k[:-1]) for w in words):
                return True
        elif k.lstrip("=") in short:
            return True
    return False


def audit(entries: dict, texts: list[dict[str, str]]) -> list[tuple[str, str, list[str]]]:
    flagged = []
    for eid, e in entries.items():
        if e.get("type") == "event":
            continue
        keys = stems(e)  # no usable key (a name like "On"): every unlabelled unit is flagged
        labelled = set(e.get("labels") or {})
        for u in e.get("attested", []):
            if u in labelled:
                continue
            found = False
            for t in texts:
                if u in t and named(t[u], keys):
                    found = True
                    break
            if not found:
                flagged.append((eid, u, sorted(keys)))
    return flagged


def main(argv: list[str]) -> int:
    tdir = Path(argv[1]) if len(argv) > 1 else TEXTS
    texts = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(tdir.glob("*.json"))]
    if not texts:
        print(f"no texts in {tdir}", file=sys.stderr)
        return 1
    entries = {}
    for f in ("persons", "places"):
        entries.update(json.loads((ROOT / f"data/{f}.json").read_text(encoding="utf-8"))["entries"])
    for eid, u, keys in audit(entries, texts):
        print(eid, u, " ".join(keys), sep="\t")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
