"""Check the catalogs against the repository's rules.

- identifiers: bpers:/bplace:/bevent: matching their catalog, lowercase ASCII slug,
  optional "." discriminator, unique across catalogs;
- every relation target exists; every attested unit exists in CBTUDR;
- descriptions at most 15 words and 120 characters (our own few words, never source text);
- names: Italian and English present;
- evidence: at least one location, each a dictionary sense (ndeib:), the Herodian tree
  (bj:herodian-tree) or a Nova Vulgata verse (nv:<CBTUDR unit>, an existing unit);
- labels: each on an attested unit, `as` name or designation, editions from the known list,
  each label at most six words;
- data/unnamed.json (persons no edition names): anon: keys, units and nv: evidence that exist,
  a tie to an existing entry;
- kinds from the schema's list for the type; relations from the schema's vocabulary, with a
  target of the type the relation needs; Wikidata items well formed and held by one entry only.

Usage: python validate.py   (exit 1 if there are problems)
"""

from __future__ import annotations

import json
import re
import sys
from functools import cache
from pathlib import Path

from build_catalog import TARGET_TYPE
from units import CBTUDR

ROOT = Path(__file__).resolve().parent.parent
PREFIX = {"persons": "bpers", "places": "bplace", "events": "bevent"}
TYPE = {"persons": "person", "places": "place", "events": "event"}
KINDS = {"person": {"individual", "group", "deity", "extra-biblical"},
         "place": {"city", "region", "mountain", "river", "sea", "valley", "desert", "site", "building", "other"},
         "event": {"episode", "battle", "assembly", "other"}}
QID = re.compile(r"^Q[1-9][0-9]*$")
EVIDENCE = re.compile(r"^(ndeib:.+|bj:herodian-tree|nv:btu:\S+)$")
EDITIONS = {"NVBSE", "VGCL", "CEI2008", "NABRE", "DRB"}
ID = re.compile(r"^(bpers|bplace|bevent):[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)?$")


@cache
def _units() -> frozenset[str]:
    out = set()
    for f in (CBTUDR / "data/units").glob("*.json"):
        out.update(u["id"] for u in json.loads(f.read_text(encoding="utf-8"))["units"])
    return frozenset(out)


def problems(catalogs: dict[str, dict]) -> list[str]:
    out: list[str] = []
    seen: dict[str, str] = {}
    for name, cat in catalogs.items():
        for eid in cat["entries"]:
            if eid in seen:
                out.append(f"{eid}: in both {seen[eid]} and {name}")
            seen[eid] = name
    units = _units()
    types = {eid: e.get("type") for cat in catalogs.values() for eid, e in cat["entries"].items()}
    holders: dict[str, list[str]] = {}
    for name, cat in catalogs.items():
        for eid, e in cat["entries"].items():
            if not ID.match(eid) or not eid.startswith(PREFIX[name] + ":"):
                out.append(f"{eid}: malformed or wrong prefix for {name}")
            if e.get("type") != TYPE[name]:
                out.append(f"{eid}: type {e.get('type')} in {name}")
            for lang in ("it", "en"):
                if not (e.get("names") or {}).get(lang):
                    out.append(f"{eid}: no {lang} name")
                d = (e.get("description") or {}).get(lang) or ""
                if len(d) > 120 or len(d.split()) > 15:
                    out.append(f"{eid}: {lang} description too long ({len(d.split())} words)")
            for u in e.get("attested", []):
                if u not in units:
                    out.append(f"{eid}: unknown unit {u}")
            for u, lab in (e.get("labels") or {}).items():
                if u not in e.get("attested", []):
                    out.append(f"{eid}: label on unattested {u}")
                if not isinstance(lab, dict) or not isinstance(lab.get("editions"), dict):
                    out.append(f"{eid}: label {u} malformed")
                    continue
                if lab.get("as") not in ("name", "designation"):
                    out.append(f"{eid}: label {u} as {lab.get('as')}")
                if not lab["editions"]:
                    out.append(f"{eid}: label {u} in no edition")
                for ed, text in lab["editions"].items():
                    if ed not in EDITIONS:
                        out.append(f"{eid}: label {u} unknown edition {ed}")
                    if not isinstance(text, str) or not text.strip() or len(text.split()) > 6:
                        out.append(f"{eid}: label {u} {ed} empty, not text, or longer than six words")
            if not e.get("evidence"):
                out.append(f"{eid}: no evidence")
            for ev in e.get("evidence", []):
                if not EVIDENCE.match(ev):
                    out.append(f"{eid}: unknown evidence {ev}")
                elif ev.startswith("nv:") and ev[3:] not in units:
                    out.append(f"{eid}: evidence verse {ev} is not a unit")
            if e.get("kind") not in KINDS.get(e.get("type"), set()):
                out.append(f"{eid}: kind {e.get('kind')} not allowed for a {e.get('type')}")
            if e.get("qid") is not None:
                if not QID.match(str(e["qid"])):
                    out.append(f"{eid}: malformed qid {e['qid']}")
                holders.setdefault(str(e["qid"]), []).append(eid)
            for r in e.get("relations", []):
                if r["rel"] not in TARGET_TYPE:
                    out.append(f"{eid}: unknown relation {r['rel']}")
                if not r.get("evidence") or any(not EVIDENCE.match(str(ev)) for ev in r["evidence"]):
                    out.append(f"{eid}: relation {r['rel']} {r['target']} without known evidence")
                if r["target"] not in seen:
                    out.append(f"{eid}: relation {r['rel']} to missing {r['target']}")
                    continue
                want = TARGET_TYPE.get(r["rel"])
                want = e.get("type") if want == "same" else want
                if want and types[r["target"]] != want:
                    out.append(f"{eid}: {r['rel']} needs a {want}, {r['target']} is a {types[r['target']]}")
    for qid, eids in holders.items():
        if len(eids) > 1:
            out += [f"{eid}: qid {qid} shared with {', '.join(x for x in eids if x != eid)}" for eid in eids]
    return out


ANON = re.compile(r"^anon:[a-z0-9]+(?:-[a-z0-9]+)*\.[a-z0-9]+(?:-[a-z0-9]+)*$")
TIES = {"spouse_of", "child_of", "parent_of", "sibling_of"}


def unnamed_problems(unnamed: dict, catalogs: dict[str, dict]) -> list[str]:
    """data/unnamed.json: persons no edition names, kept apart from the catalogs."""
    out: list[str] = []
    units = _units()
    ids = {eid for cat in catalogs.values() for eid in cat["entries"]}
    for key, e in unnamed.items():
        if not ANON.match(key):
            out.append(f"{key}: malformed key")
        if e.get("type") != "person":
            out.append(f"{key}: type {e.get('type')}")
        units_of = list(e.get("attested") or []) + list(e.get("implied_by") or [])
        if not units_of:
            out.append(f"{key}: neither attested nor implied")
        for u in units_of:
            if u not in units:
                out.append(f"{key}: unknown unit {u}")
        for ev in e.get("evidence") or [None]:
            if not ev or not ev.startswith("nv:") or ev[3:] not in units:
                out.append(f"{key}: evidence {ev}")
        tie = e.get("tie")
        if tie is not None and not isinstance(tie, dict):
            out.append(f"{key}: tie malformed")
        elif tie and (tie.get("rel") not in TIES or tie.get("target") not in ids):
            out.append(f"{key}: tie {tie}")
        for lang in ("it", "en"):
            d = (e.get("description") or {}).get(lang) or ""
            if not d or len(d) > 120 or len(d.split()) > 15:
                out.append(f"{key}: {lang} description missing or too long")
    return out


def main() -> int:
    catalogs = {n: json.loads((ROOT / "data" / f"{n}.json").read_text(encoding="utf-8")) for n in PREFIX}
    p = problems(catalogs)
    u_path = ROOT / "data/unnamed.json"
    if u_path.exists():
        p += unnamed_problems(json.loads(u_path.read_text(encoding="utf-8"))["entries"], catalogs)
    for x in p:
        print(x)
    print(f"{sum(len(c['entries']) for c in catalogs.values())} entries, {len(p)} problems")
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
