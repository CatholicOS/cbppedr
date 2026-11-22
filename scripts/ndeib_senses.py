"""Split the dictionary (Nuovo Dizionario Enciclopedico Illustrato della Bibbia, TEI)
into entries and numbered senses, with their verse references and cross-references.

The output carries the sense text, which is copyrighted: it is written only to the
private folder (default ~/development/BibleGet-I-O/data-local/cbppedr/), never to
this repository.

Headwords are found as the dictionary's own reading PDF finds them: this imports
tools/tei2pdf.py from the TEI's folder (its heading classification and A-Z spine).

Usage: python ndeib_senses.py [--tei PATH] [--out PATH]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from refs import parse_refs
from units import units_for

DEFAULT_TEI = Path("/mnt/c/Users/johnr/Documents/Missio Digitalis Foundation/Alexandria Hub digitization/"
                   "Nuovo Dizionario Enciclopedico Illustrato della Bibbia/"
                   "Nuovo_Dizionario_Enciclopedico_Illustrato_della_Bibbia.tei.xml")
TEI_TOOLS = Path(os.environ.get("NDEIB_TOOLS", DEFAULT_TEI.parent / "tools"))
PRIVATE = Path(os.environ.get("CBPPEDR_PRIVATE", Path.home() / "development/BibleGet-I-O/data-local/cbppedr"))

XREF = re.compile(r"↗\s*([A-ZÀ-Ý][\w'’-]*)")
CUES = {
    "place": r"\b(città|villaggio|regione|territorio|monte|fiume|torrente|valle|località|pianura|isola|"
             r"porto|sorgente|accampamento|deserto|Tell|km|identificat[ao])\b",
    "person": r"\b(figli[oa]|moglie|marito|padre|madre|fratello|sorella|re di|regina|sacerdote|profeta|"
              r"profetessa|levita|apostolo|discendente|capo|antenato|sposò|nipote|genealogia|nome di persona)\b",
    "event": r"\b(battaglia|guerra|assedio|esilio|deportazione|concilio|rivolta|conquista)\b",
}


def _tei2pdf():
    spec = importlib.util.spec_from_file_location("tei2pdf", TEI_TOOLS / "tei2pdf.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _kind(text: str) -> str:
    """The kind whose cue word comes first: a sense opens by saying what it is."""
    lead = text[:400]
    firsts = {k: m.start() for k, rx in CUES.items() if (m := re.search(rx, lead))}
    return min(firsts, key=lambda k: firsts[k]) if firsts else "other"


def _finish(cur: dict | None, out: list[dict]) -> None:
    if not cur:
        return
    text = re.sub(r"\s+", " ", " ".join(cur.pop("chunks"))).strip()
    refs, units, unresolved = [], [], []
    for r in parse_refs(text, "ndeib"):
        printed = text[r.span[0]:r.span[1]]
        refs.append(printed)
        u = units_for(r)
        if u is None:
            unresolved.append(printed)
        else:
            units += [x for x in u if x not in units]
    xrefs = []
    for x in XREF.findall(text):
        if x not in xrefs:
            xrefs.append(x)
    cur.update(text=text, refs=refs, units=units, unresolved=unresolved, xrefs=xrefs, kind_guess=_kind(text))
    out.append(cur)


def senses(tei_path: Path) -> list[dict]:
    t2p = _tei2pdf()
    root = ET.parse(tei_path).getroot()
    conv = t2p.Converter(root)
    out: list[dict] = []
    head: str | None = None
    hkey: str | None = None  # the headword, with ~n when the same headword starts another entry
    seen: dict[str, int] = {}
    cur: dict | None = None
    for el in conv.body:
        name = t2p.tag(el)
        if id(el) in conv.headword_ids:
            _finish(cur, out)
            head = t2p.caps_run(t2p.clean_ws(t2p.text_of(el)))
            seen[head] = seen.get(head, 0) + 1
            hkey = head if seen[head] == 1 else f"{head}~{seen[head]}"
            cur = {"key": hkey, "headword": head, "sense": None, "chunks": []}
            if name == "p":
                cur["chunks"].append(t2p.text_of(el))
            continue
        if head is None or name in ("pb", "fw", "milestone", "note", "figure"):
            continue
        n = el.get("n") if name == "p" else None
        if n and re.fullmatch(r"\d+\.", n):
            sense = int(n[:-1])
            if cur and cur["sense"] is None and not cur["chunks"]:
                cur["sense"], cur["key"] = sense, f"{hkey}#{sense}"
            else:
                if cur and cur["sense"] is None:  # text before "1." belongs to the entry, not a sense
                    cur["key"] = f"{hkey}#0"
                _finish(cur, out)
                cur = {"key": f"{hkey}#{sense}", "headword": head, "sense": sense, "chunks": []}
        if cur is not None:
            cur["chunks"].append(t2p.text_of(el))
    _finish(cur, out)
    used: dict[str, int] = {}
    for r in out:  # a section that restarts its numbering repeats keys: number the repeats
        used[r["key"]] = used.get(r["key"], 0) + 1
        if used[r["key"]] > 1:
            r["key"] = f"{r['key']}~{used[r['key']]}"
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tei", type=Path, default=DEFAULT_TEI)
    ap.add_argument("--out", type=Path, default=PRIVATE / "ndeib-senses.jsonl")
    a = ap.parse_args(argv)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    rows = senses(a.tei)
    with a.out.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r["kind_guess"]] = kinds.get(r["kind_guess"], 0) + 1
    print(f"{len(rows)} senses from {len({r['headword'] for r in rows})} headwords → {a.out}: {kinds}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
