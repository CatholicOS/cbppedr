"""Check the catalogs against the repository's rules.

- identifiers: bpers:/bplace:/bevent: matching their catalog, lowercase ASCII slug,
  optional "." discriminator, unique across catalogs;
- every relation target exists; every attested unit exists in CBTUDR;
- descriptions at most 15 words and 120 characters (our own few words, never source text);
- names: Italian and English present;
- evidence: at least one location, each a dictionary sense (ndeib:), the Herodian tree
  (bj:herodian-tree) or a Nova Vulgata verse (nv:<CBTUDR unit>, an existing unit);
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


def main() -> int:
    catalogs = {n: json.loads((ROOT / "data" / f"{n}.json").read_text(encoding="utf-8")) for n in PREFIX}
    p = problems(catalogs)
    for x in p:
        print(x)
    print(f"{sum(len(c['entries']) for c in catalogs.values())} entries, {len(p)} problems")
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
