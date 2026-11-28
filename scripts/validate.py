"""Check the catalogs against the repository's rules.

- identifiers: bpers:/bplace:/bevent: matching their catalog, lowercase ASCII slug,
  optional "." discriminator, unique across catalogs;
- every relation target exists; every attested unit exists in CBTUDR;
- descriptions at most 30 words and 220 characters per language (our own words, never source text);
- names: Italian and English present;
- evidence: at least one location, each a dictionary sense (ndeib:), the Herodian tree
  (bj:herodian-tree), a Jerusalem Bible note or introduction (bj:note:, bj:intro:), a Nova Vulgata verse
  (nv:<CBTUDR unit>, an existing unit), a reviewer's round (reviewer:round2) or a publication listed in
  data/curated/sources.json (pub:<key>#<locator>);
- labels: each on an attested unit, `as` name or designation, editions from the known list,
  each label at most six words;
- conjectures: a known relation and target, a status, opinions with a source from
  data/curated/sources.json, a well-formed locator, a stance and a short summary;
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

from build_catalog import SOURCE_TYPE, TARGET_TYPE
from units import CBTUDR

ROOT = Path(__file__).resolve().parent.parent
PREFIX = {"persons": "bpers", "places": "bplace", "events": "bevent"}
TYPE = {"persons": "person", "places": "place", "events": "event"}
KINDS = {"person": {"individual", "group", "deity", "extra-biblical"},
         "place": {"city", "region", "mountain", "river", "sea", "valley", "desert", "site", "building", "other"},
         "event": {"episode", "battle", "assembly", "other"}}
QID = re.compile(r"^Q[1-9][0-9]*$")
EVIDENCE = re.compile(r"^(ndeib:.+|bj:herodian-tree|bj:(note:[0-9]?[A-Za-z]+\.[^#\s]+|intro:[A-Za-z0-9-]+)(#p\d+)?|nv:btu:\S+)$")
EDITIONS = {"NVBSE", "VGCL", "CEI2008", "NABRE", "DRB"}
MAX_DESCRIPTION_WORDS, MAX_DESCRIPTION_CHARS = 30, 220
ID = re.compile(r"^(bpers|bplace|bevent):[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)?$")


@cache
def _units() -> frozenset[str]:
    out = set()
    for f in (CBTUDR / "data/units").glob("*.json"):
        out.update(u["id"] for u in json.loads(f.read_text(encoding="utf-8"))["units"])
    return frozenset(out)


def _evidence_ok(ev: str, sources: dict[str, dict] | None) -> bool:
    """A location (ndeib:, bj:, nv:), or a reviewer's round (reviewer:round2) or a publication listed in
    sources.json with its authority (pub:catechismus-1997#391): a reviewed identification's sources.
    Without `sources`, a publication is checked for its form only."""
    if EVIDENCE.match(ev) or LOCATOR["reviewer"].match(ev):
        return True
    if not LOCATOR["pub"].match(ev):
        return False
    return sources is None or ev.split("#")[0] in sources


def problems(catalogs: dict[str, dict], sources: dict[str, dict] | None = None) -> list[str]:
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
                if len(d) > MAX_DESCRIPTION_CHARS or len(d.split()) > MAX_DESCRIPTION_WORDS:
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
            mentioned = e.get("mentioned", [])
            if not isinstance(mentioned, list) or not all(isinstance(u, str) for u in mentioned):
                out.append(f"{eid}: mentioned is not a list of unit keys")
                mentioned = []
            if len(set(mentioned)) != len(mentioned):
                out.append(f"{eid}: mentioned units repeat")
            for u in mentioned:
                if u not in units:
                    out.append(f"{eid}: unknown mentioned unit {u}")
                elif u in e.get("attested", []):
                    out.append(f"{eid}: mentioned unit {u} is already attested")
            if not e.get("evidence"):
                out.append(f"{eid}: no evidence")
            for ev in e.get("evidence", []):
                if not _evidence_ok(ev, sources):
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
                if SOURCE_TYPE.get(r["rel"]) not in (None, e.get("type")):
                    out.append(f"{eid}: {r['rel']} needs a {SOURCE_TYPE[r['rel']]} as its source")
                want = TARGET_TYPE.get(r["rel"])
                want = e.get("type") if want == "same" else want
                if want and types[r["target"]] != want:
                    out.append(f"{eid}: {r['rel']} needs a {want}, {r['target']} is a {types[r['target']]}")
    for qid, eids in holders.items():
        if len(eids) > 1:
            out += [f"{eid}: qid {qid} shared with {', '.join(x for x in eids if x != eid)}" for eid in eids]
    return out


CONJ_RELS = {"possibly_same_as", "possibly_attested_at"}
STANCES = {"identifies", "suggests", "doubts", "rejects"}
STATUSES = {"supported", "disputed", "rejected", "doubted", "unsupported"}
LOCATOR = {"bj": re.compile(r"^bj:(note:[0-9]?[A-Za-z]+\.[^#\s]+|intro:[A-Za-z0-9-]+)(#p\d+)?$"),
           "ndeib": re.compile(r"^ndeib:[A-ZÀ-ÖØ-Ý0-9][A-ZÀ-ÖØ-Ý0-9 ,'’().~-]*(#[0-9IVX]+)?$"), "tipnr": re.compile(r"^tipnr:\S+@\S+$"),
           "reviewer": re.compile(r"^reviewer:\S+$"),
           "pub": re.compile(r"^pub:[a-zà-ÿ][a-z0-9à-ÿ]*(?:-[a-z0-9à-ÿ]+)*-\d{4}[a-z]?(#[^\s#]+)?$")}


def publication_problems(sources: dict[str, dict]) -> list[str]:
    """Every publication listed in sources.json: a well-formed pub: key, a title and an authority."""
    out = []
    for key, v in sources.items():
        if not key.startswith("pub:"):
            continue
        if not LOCATOR["pub"].match(key) or "#" in key:
            out.append(f"sources.json: publication key {key!r}")
        if not v.get("title") or v.get("authority") not in ("authoritative", "non-authoritative"):
            out.append(f"sources.json: {key} needs a title and an authority")
    return out


def conjecture_problems(eid: str, e: dict, ids: set[str], sources: dict[str, dict],
                        attested_of: dict[str, list[str]] | None = None) -> list[str]:
    """An entry's conjectures: a known relation and target, a status, and opinions each with a
    known source, a well-formed locator, a stance and a short summary in our own words. A
    conjecture must not already be in `attested`: two possibly-same entries share no unit, and a
    possibly-attested unit is not attested."""
    out: list[str] = []
    attested_of = attested_of or {}
    for c in e.get("conjectures") or []:
        if not isinstance(c, dict):
            out.append(f"{eid}: conjecture malformed")
            continue
        if c.get("rel") not in CONJ_RELS or (c.get("target") not in ids if c.get("rel") == "possibly_same_as"
                                             else c.get("unit") not in _units()):
            out.append(f"{eid}: conjecture {c.get('rel')} {c.get('target') or c.get('unit')}")
        if c.get("status") not in STATUSES:
            out.append(f"{eid}: conjecture status {c.get('status')}")
        if not c.get("opinions"):
            out.append(f"{eid}: conjecture {c.get('target') or c.get('unit')} without opinions")
        shared = set(e.get("attested") or []) & set(attested_of.get(c.get("target"), []))
        if c.get("rel") == "possibly_same_as" and shared:
            out.append(f"{eid}: conjecture {c['target']} already shares attested {sorted(shared)}")
        if c.get("rel") == "possibly_attested_at" and c.get("unit") in (e.get("attested") or []):
            out.append(f"{eid}: conjecture unit {c['unit']} is already attested")
        for o in c.get("opinions") or []:
            by = str(o.get("by", ""))
            src = by.split(":")[0]
            if src not in sources or src not in LOCATOR or not LOCATOR[src].match(by):
                out.append(f"{eid}: conjecture opinion by {by!r}")
            elif src == "pub" and sources.get(by.split("#")[0], {}).get("authority") not in ("authoritative", "non-authoritative"):
                out.append(f"{eid}: publication {by.split('#')[0]!r} not listed in sources.json with its authority")
            if o.get("says") not in STANCES:
                out.append(f"{eid}: conjecture opinion says {o.get('says')!r}")
            summ = o.get("summary") or ""
            if not summ or len(summ) > 160 or len(summ.split()) > 20:
                out.append(f"{eid}: conjecture opinion summary missing or too long")
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


HEX64 = re.compile(r"[0-9a-f]{64}")
HEX8 = re.compile(r"[0-9a-f]{8}")
UNIT_KEY = re.compile(r"^(btu:\S+?)(@(?:GREEK|HEBREW))?$")
TOP_KEYS = frozenset({"$comment", "edition", "units"})
UNIT_KEYS = frozenset({"hash", "mentions"})
MENTION_KEYS = frozenset({"start", "end", "check", "entry", "candidates"})


def _unit_key_ok(key: str, units: set[str] | frozenset[str]) -> bool:
    """A known unit; a tradition suffix (@GREEK, @HEBREW) only on Esther's."""
    k = UNIT_KEY.match(key)
    return bool(k) and k.group(1) in units and (not k.group(2) or k.group(1).startswith("btu:est."))


def _unknown_keys(where: str, d: dict, allowed: frozenset[str]) -> list[str]:
    return [f"{where}: unknown property" for k in d if k not in allowed]


def _id_problems(where: str, m: dict, ids: set[str]) -> list[str]:
    if "entry" in m:
        e = m["entry"]
        return [] if isinstance(e, str) and e in ids else [f"{where}: unknown entry {e!r}"]
    c = m["candidates"]
    if not isinstance(c, list) or not c:
        return [f"{where}: candidates empty"]
    if not all(isinstance(x, str) for x in c):
        return [f"{where}: candidates must be id strings"]
    out = [] if c == sorted(set(c)) else [f"{where}: candidates not sorted and unique"]
    return out + [f"{where}: unknown candidate {x}" for x in c if x not in ids]


def _mention_problems(where: str, m: object, ids: set[str]) -> list[str]:
    if not isinstance(m, dict):
        return [f"{where}: mention malformed"]
    out = []
    s, e = m.get("start"), m.get("end")
    if not (isinstance(s, int) and isinstance(e, int) and not isinstance(s, bool) and not isinstance(e, bool)
            and 0 <= s < e):
        out.append(f"{where}: span {s}-{e} (need 0 <= start < end)")
    if not isinstance(m.get("check"), str) or not HEX8.fullmatch(m["check"]):
        out.append(f"{where}: check {m.get('check')!r} is not 8 lowercase hex digits")
    if ("entry" in m) == ("candidates" in m):
        out.append(f"{where}: needs entry or candidates, not both nor neither")
    else:
        out += _id_problems(where, m, ids)
    return out + _unknown_keys(where, m, MENTION_KEYS)


def mention_problems(doc: dict, ids: set[str], units: set[str] | frozenset[str], name: str,
                     curated: bool = False) -> list[str]:
    """A mentions file: the edition, and per unit key (a CBTUDR unit, with @GREEK/@HEBREW for Esther's
    two texts) its hash and mentions. The text is private, so spans are checked only for their shape."""
    if not isinstance(doc, dict):
        return [f"{name}: document is not an object"]
    out = []
    if doc.get("edition") != "NVBSE":
        out.append(f"{name}: edition {doc.get('edition')!r}")
    out += _unknown_keys(name, doc, TOP_KEYS)
    if not isinstance(doc.get("units"), dict):
        return out + [f"{name}: units is not an object"]
    for key, u in doc["units"].items():
        where = f"{name} {key}"
        if not _unit_key_ok(key, units):
            out.append(f"{where}: not a known unit (a tradition suffix only on Esther)")
        if not isinstance(u, dict) or not isinstance(u.get("mentions"), list):
            out.append(f"{where}: malformed")
            continue
        out += _unknown_keys(where, u, UNIT_KEYS)
        if not isinstance(u.get("hash"), str) or not HEX64.fullmatch(u["hash"]):
            out.append(f"{where}: hash is not 64 lowercase hex digits")
        if not u["mentions"] and not curated:
            out.append(f"{where}: no mentions")
        for i, m in enumerate(u["mentions"]):
            out += _mention_problems(f"{where} #{i}", m, ids)
    return out


ALLOWED_STRING = re.compile(r"NVBSE|(bpers|bplace):\S+|btu:\S+?(@(GREEK|HEBREW))?|[0-9a-f]+")


def mention_text_problems(doc: object, name: str, path: str = "") -> list[str]:
    """Every string in a mentions file, but `$comment`, is NVBSE, an entry id, a unit key or lowercase hex,
    and every property name is a unit key (under /units) or one the format defines: a regeneration can
    never commit the edition's text. A refused property is not looked into."""
    out: list[str] = []
    if isinstance(doc, dict):
        for k, v in doc.items():
            if path == "/units" and not ALLOWED_STRING.fullmatch(str(k)):
                out.append(f"{name} {path}: key {str(k)[:20]!r} is not a unit key")
                continue
            if path != "/units" and k not in TOP_KEYS | UNIT_KEYS | MENTION_KEYS:
                out.append(f"{name} {path}: property {str(k)[:20]!r} is not part of the format")
                continue
            if k != "$comment":
                out += mention_text_problems(v, name, f"{path}/{k}")
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            out += mention_text_problems(v, name, f"{path}[{i}]")
    elif isinstance(doc, str) and not ALLOWED_STRING.fullmatch(doc):
        out.append(f"{name} {path}: string {doc[:20]!r} is neither an id, a unit key nor hex")
    return out


def mention_file_problems(ids: set[str]) -> list[str]:
    from extract_mentions import merged_mentions
    gen_path = ROOT / "data/mentions/nvbse.json"
    cur_path = ROOT / "data/mentions/nvbse_curated.json"
    if not gen_path.exists():
        return []
    units = _units()
    gen = json.loads(gen_path.read_text(encoding="utf-8"))
    cur = json.loads(cur_path.read_text(encoding="utf-8")) if cur_path.exists() else {"edition": "NVBSE", "units": {}}
    return mention_docs_problems(gen, cur, ids, units)


def _well_formed(doc: object) -> bool:
    if not isinstance(doc, dict):
        return False
    units = doc.get("units")
    return isinstance(units, dict) and all(isinstance(u, dict) and isinstance(u.get("mentions"), list)
                                           for u in units.values())


def mention_docs_problems(gen: dict, cur: dict, ids: set[str], units: set[str] | frozenset[str]) -> list[str]:
    """The generated and curated mentions files, and their merge when both are well formed (a malformed
    one is reported, not merged)."""
    from extract_mentions import merged_mentions
    out = mention_text_problems(gen, "nvbse.json") + mention_text_problems(cur, "nvbse_curated.json")
    out += mention_problems(gen, ids, units, "nvbse.json") + mention_problems(cur, ids, units, "nvbse_curated.json", True)
    if _well_formed(gen) and _well_formed(cur):
        out += mention_problems(merged_mentions(gen, cur), ids, units, "merged")
    return out


def main() -> int:
    catalogs = {n: json.loads((ROOT / "data" / f"{n}.json").read_text(encoding="utf-8")) for n in PREFIX}
    src_path = ROOT / "data/curated/sources.json"
    sources = json.loads(src_path.read_text(encoding="utf-8"))["sources"] if src_path.exists() else {}
    p = problems(catalogs, sources)
    ids = {eid for cat in catalogs.values() for eid in cat["entries"]}
    attested_of = {eid: e.get("attested", []) for cat in catalogs.values() for eid, e in cat["entries"].items()}
    p += publication_problems(sources)
    for cat in catalogs.values():
        for eid, e in cat["entries"].items():
            p += conjecture_problems(eid, e, ids, sources, attested_of)
    u_path = ROOT / "data/unnamed.json"
    if u_path.exists():
        p += unnamed_problems(json.loads(u_path.read_text(encoding="utf-8"))["entries"], catalogs)
    p += mention_file_problems(ids)
    for x in p:
        print(x)
    print(f"{sum(len(c['entries']) for c in catalogs.values())} entries, {len(p)} problems")
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
