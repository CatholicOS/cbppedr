"""Match catalog entries to Wikidata items, strictly: better unidentified than misidentified.

An item is accepted automatically ("auto") only when exactly one candidate
- is of a fitting kind (P31: a human, biblical figure, group or deity for persons;
  a settlement, region, landform, site, ... or anything with coordinates for places), and
- for an entry with homonyms (an id with a "." discriminator): its description names a
  related entry (a parent, spouse, ...) and it is biblical; otherwise: it is biblical.
Everything else stays "unresolved", with its candidates kept for review.

Wikidata is queried at most once a second with a generic User-Agent, and every
response is cached in the private folder, so a rerun costs nothing.

An item of the class "human biblical figure" (Q20643955) counts as biblical; so does a
description with a biblical word, and, for a homonym, a biblical setting. Candidates listed
under "rejected" in qids.json (judged wrong on review) are never picked.

Usage: python wikidata.py [--rematch]   (updates data/curated/qids.json)
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = Path(os.environ.get("CBPPEDR_PRIVATE", Path.home() / "development/BibleGet-I-O/data-local/cbppedr"))
CACHE = PRIVATE / "wikidata-cache"
API = "https://www.wikidata.org/w/api.php"
UA = "cbppedr-catalog/0.1 (biblical persons and places catalog)"

BIBLICAL_FIGURE = "Q20643955"
# human, human biblical figure, mythical character, deity, tribe, ethnic group, people, mythical entity,
# figure that may or may not be fictional, angel. Not fictional or television characters.
PERSON_KINDS = {"Q5", BIBLICAL_FIGURE, "Q4271324", "Q178885", "Q133311", "Q41710", "Q2472587", "Q24334685",
                "Q21070598", "Q235113"}
PLACE_KINDS = {"Q515", "Q486972", "Q82794", "Q8502", "Q4022", "Q839954", "Q15661340", "Q3957", "Q532",
               "Q23397", "Q165", "Q8514", "Q39816", "Q35666", "Q1620908", "Q2221906", "Q15284", "Q12280",
               "Q107425", "Q34763", "Q41176", "Q44613", "Q1081138", "Q35509", "Q5119", "Q46831"}
# Whole words only: "bibl" once matched "bibliographer", "Israel" "Israeli", "ancient" anything old.
BIBLICAL = re.compile(r"\b(biblical|Bible|biblic[oaie]|bibliche|Bibbia|Old Testament|New Testament|"
                      r"Antico Testamento|Nuovo Testamento|Hebrew Bible|Gospels?|Vangel[oi]|apostle|apostolo|"
                      r"prophet|profeta|Torah)\b", re.IGNORECASE)
# A biblical setting: enough for a homonym whose relative is also named.
SETTING = re.compile(r"\b(Canaan|Canaanite|Judaea|Judea|Giudea|Samaria|Galilee|Galilea|Moab|Moabite|Edom|"
                     r"Edomite|Philistines?|Philistia|Filistei|Shephelah|Negev|Sinai|Herod|Erode|Herodian|"
                     r"Hasmonean|Maccabees?|Maccabei|Jesus|Gesù)\b", re.IGNORECASE)

Search = Callable[[str, str], list[str]]
Get = Callable[[list[str]], dict[str, dict]]


def _kinds(entity: dict) -> set[str]:
    out = set()
    for c in entity.get("claims", {}).get("P31", []):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(v, dict) and "id" in v:
            out.add(v["id"])
    return out


def _description(entity: dict) -> str:
    return " ".join(d.get("value", "") for d in entity.get("descriptions", {}).values())


def _fits(entry: dict, entity: dict) -> bool:
    kinds = _kinds(entity)
    if entry["type"] == "person":
        return bool(kinds & PERSON_KINDS)
    if entry["type"] == "place":
        return bool(kinds & PLACE_KINDS) or "P625" in entity.get("claims", {})
    return True


def _names_hit(names: list[str], text: str) -> bool:
    """A relative's whole name in the description; its single words ("Great", "John") prove nothing."""
    return any(len(n) >= 4 and re.search(rf"\b{re.escape(n)}\b", text, re.IGNORECASE) for n in names if n)


def _biblical(entity: dict, setting: bool) -> bool:
    d = _description(entity)
    return BIBLICAL_FIGURE in _kinds(entity) or bool(BIBLICAL.search(d)) or (setting and bool(SETTING.search(d)))


def match(eid: str, entry: dict, search: Search, get: Get) -> tuple[str | None, str, list[str]]:
    cands: list[str] = []
    for text, lang in ((entry["names"].get("it"), "it"), (entry["names"].get("en"), "en")):
        for q in search(text, lang) if text else []:
            if q not in cands:
                cands.append(q)
    entities = get(cands) if cands else {}
    rejected = set(entry.get("_rejected", []))
    fitting = [q for q in cands if q in entities and q not in rejected and _fits(entry, entities[q])]
    if entry["type"] == "person" and "." in eid.split(":", 1)[1]:
        picks = [q for q in fitting if _names_hit(entry.get("_rel_names", []), _description(entities[q]))
                 and _biblical(entities[q], setting=True)]
    elif entry["type"] == "person":
        picks = [q for q in fitting if _biblical(entities[q], setting=False)]
    else:  # a place: a regional word once matched a Spanish town, an army base and a mint
        picks = [q for q in fitting if _biblical(entities[q], setting=False)]
    if len(picks) == 1:
        return picks[0], "auto", cands
    return None, "unresolved", cands


def needs_match(prev: dict, rematch: bool) -> bool:
    """An entry judged in an earlier run is judged again on --rematch, after an error, or when its item was rejected."""
    return rematch or bool(prev.get("error")) or (prev.get("qid") in prev.get("rejected", []))


def dedupe(qids: dict[str, dict]) -> None:
    """An item auto-matched to two entries, or to an entry while another has it reviewed, fits neither for sure."""
    holders: dict[str, list[str]] = {}
    for eid, v in qids.items():
        if v.get("qid"):
            holders.setdefault(v["qid"], []).append(eid)
    for qid, eids in holders.items():
        if len(eids) > 1:
            for eid in eids:
                if qids[eid]["status"] == "auto":
                    qids[eid].update(qid=None, status="unresolved")


# --- network, cached ---------------------------------------------------------

_last = [0.0]


def _call(params: dict) -> dict:
    key = urllib.parse.urlencode(sorted(params.items()))
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (re.sub(r"[^\w.-]", "_", key)[:180] + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    wait = 1.0 - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(f"{API}?{key}&format=json", headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:  # throttled: wait as long as the service asks
            retry = int(e.headers.get("Retry-After", "0") or 0) if e.headers else 0
            print(f"HTTP {e.code} on {key}; waiting", file=sys.stderr)
            time.sleep(max(retry, 30 * (attempt + 1)))
        except Exception as e:  # slow service or network
            print(f"{type(e).__name__} on {key}; retrying", file=sys.stderr)
            time.sleep(15 * (attempt + 1))
    else:
        raise RuntimeError(f"Wikidata did not answer: {key}")
    _last[0] = time.time()
    path.write_text(json.dumps(data), encoding="utf-8")
    return data


def search(text: str, lang: str) -> list[str]:
    data = _call({"action": "wbsearchentities", "search": text, "language": lang, "uselang": lang,
                  "type": "item", "limit": "10"})
    return [s["id"] for s in data.get("search", [])]


def get(ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(ids), 50):
        data = _call({"action": "wbgetentities", "ids": "|".join(sorted(ids[i:i + 50])),
                      "props": "descriptions|claims", "languages": "en|it"})
        out.update(data.get("entities", {}))
    return out


def main() -> int:
    rematch = "--rematch" in sys.argv  # re-judge every non-reviewed entry (from the cache) under the current rule
    catalogs = {n: json.loads((ROOT / "data" / f"{n}.json").read_text(encoding="utf-8")) for n in ("persons", "places")}
    by_id = {eid: e for c in catalogs.values() for eid, e in c["entries"].items()}
    path = ROOT / "data/curated/qids.json"
    curated = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {
        "$comment": "Wikidata items of the entries. auto: passed the evidence bar (scripts/wikidata.py); "
                    "reviewed: decided by a person; unresolved: candidates listed for review.",
        "qids": {}}
    for eid, e in by_id.items():
        if curated["qids"].get(eid, {}).get("status") == "reviewed":
            continue
        prev = curated["qids"].get(eid, {})
        e = dict(e, _rejected=prev.get("rejected", []), _rel_names=[(by_id.get(r["target"]) or {}).get("names", {}).get(n) or ""
                                for r in e["relations"] for n in ("en", "it")])
        if prev and not needs_match(prev, rematch):
            continue  # done in an earlier run
        try:
            qid, status, cands = match(eid, e, search, get)
            kept = cands[:10] + ([qid] if qid and qid not in cands[:10] else [])
            curated["qids"][eid] = {"qid": qid, "status": status, "candidates": kept}
            if prev.get("rejected"):
                curated["qids"][eid]["rejected"] = prev["rejected"]
        except RuntimeError as err:
            print(err, file=sys.stderr)
            curated["qids"][eid] = {"qid": None, "status": "unresolved", "candidates": [], "error": True}
        if len(curated["qids"]) % 100 == 0:
            path.write_text(json.dumps(curated, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    curated["qids"] = {k: v for k, v in curated["qids"].items() if k in by_id or v.get("status") == "reviewed"}
    dedupe(curated["qids"])
    curated["qids"] = dict(sorted(curated["qids"].items()))
    path.write_text(json.dumps(curated, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    statuses: dict[str, int] = {}
    for v in curated["qids"].values():
        statuses[v["status"]] = statuses.get(v["status"], 0) + 1
    print(statuses)
    return 0


if __name__ == "__main__":
    sys.exit(main())
