"""Build data/persons.json, data/places.json and data/events.json from the reviewed
sense decisions (data/curated/senses.json), the units each sense cites, the
Jerusalem Bible's Herodian tree as curated in data/curated/bj-tree.json (explicit ids), and
the entries curated by hand in data/curated/entries.json (explicit ids, units and evidence).

Facts only: names, kinds, our own short descriptions, units, relations and the
location of the evidence (ndeib:<KEY>, bj:herodian-tree). No source text.

Usage: python build_catalog.py   (reads the private sense units and tree; writes data/ and docs/build-report.md)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = Path(os.environ.get("CBPPEDR_PRIVATE", Path.home() / "development/BibleGet-I-O/data-local/cbppedr"))
TYPES = {"person": "persons", "place": "places", "event": "events"}
COMMENT = {
    "persons": "Persons of the Bible (individuals, groups, deities, and extra-biblical persons needed as relation targets). Draft pending committee review.",
    "places": "Places of the Bible. Draft pending committee review.",
    "events": "Events the Bible narrates or refers to. Draft pending committee review.",
}


def _entries_of(d: dict) -> list[dict]:
    if d.get("type") in (None, "none"):
        return []
    if d.get("parts"):
        return [dict(p, key=d["key"], certain=p.get("certain", d.get("certain", True))) for p in d["parts"]]
    return [d]


def _add_relation(entry: dict, rel: str, target: str, evidence: str) -> None:
    for r in entry["relations"]:
        if r["rel"] == rel and r["target"] == target:
            if evidence not in r["evidence"]:
                r["evidence"].append(evidence)
            return
    entry["relations"].append({"rel": rel, "target": target, "evidence": [evidence]})


# The type a relation's target must have (None: any). same_as: the source's own type.
TARGET_TYPE = {"child_of": "person", "parent_of": "person", "spouse_of": "person", "sibling_of": "person",
               "participant": "person", "located_in": "place", "part_of": "same", "land_of": "person",
               "people_of": "place", "eponym_of": None, "same_as": "same"}
SOURCE_TYPE = {"child_of": "person", "parent_of": "person", "spouse_of": "person", "sibling_of": "person",
               "participant": "event", "land_of": "place", "people_of": "person", "eponym_of": "person"}
TREE_EVIDENCE = "bj:herodian-tree"


def _discriminated(eid: str) -> bool:
    return "." in eid.split(":", 1)[1]


def conjecture_status(opinions: list[dict], sources: dict[str, dict]) -> str:
    """From the authoritative opinions only: supported (one identifies or suggests it, none doubts
    or rejects it), disputed (they disagree), rejected (they only doubt or reject it); unsupported
    when no authoritative source has spoken (non-authoritative leads only)."""
    stances = {o.get("says") for o in opinions
               if (sources.get(str(o.get("by", "")).split(":")[0]) or {}).get("authority") == "authoritative"}
    pro, con = bool(stances & {"identifies", "suggests"}), bool(stances & {"doubts", "rejects"})
    return "disputed" if pro and con else "supported" if pro else "rejected" if con else "unsupported"


def build(decisions: list[dict], units: dict[str, list[str]], tree: dict | None = None,
          part_units: dict[str, dict[str, list[str]]] | None = None,
          qids: dict[str, dict] | None = None, curated: dict[str, dict] | None = None,
          removed: dict[str, list[str]] | None = None,
          labels: dict[str, dict[str, dict]] | None = None,
          conjectures: list[dict] | None = None, sources: dict[str, dict] | None = None) -> dict:
    part_units = part_units or {}
    curated = curated or {}
    tree = tree or {}
    qids = qids or {}
    out = {t: {"$comment": COMMENT[t], "entries": {}} for t in TYPES.values()}
    report = {"merged": [], "unresolved_relations": [], "type_conflicts": [], "uncertain": [], "stale_removals": [], "conflicting_removals": [], "stale_labels": [], "unresolved_conjectures": []}
    by_id: dict[str, dict] = {}
    key_ids: dict[str, list[str]] = {}
    pending: list[tuple[str, dict, str]] = []

    for d in decisions:
        for e in _entries_of(d):
            t = TYPES.get(e.get("type"))
            if not t or not e.get("id"):
                continue
            eid = e["id"]
            key_ids.setdefault(d["key"], []).append(eid)
            ev = f"ndeib:{d['key']}"
            if eid in by_id:
                entry = by_id[eid]
                if entry["type"] != e["type"]:
                    report["type_conflicts"].append(f"{eid}: {entry['type']} vs {e['type']} ({d['key']})")
                    continue
                report["merged"].append(f"{eid} ← {d['key']}")
            else:
                entry = {"type": e["type"], "kind": e.get("kind"),
                         "names": {"la": e.get("latin"), "it": e.get("it"), "en": e.get("en")},
                         "description": {"it": e.get("descr_it"), "en": e.get("descr_en")},
                         "attested": [], "relations": [], "qid": None, "qid_status": "unresolved",
                         "evidence": []}
                by_id[eid] = entry
                out[t]["entries"][eid] = entry
            own = part_units.get(d["key"], {}).get(eid)  # curated: a part's own verses, or a sense's corrected ones
            if d.get("parts") and len(d["parts"]) > 1 and own is None:
                report.setdefault("parts_without_own_units", []).append(f"{eid} ({d['key']})")
            for u in own if own is not None else units.get(d["key"], []):
                if u not in entry["attested"]:
                    entry["attested"].append(u)
            if ev not in entry["evidence"]:
                entry["evidence"].append(ev)
            if not e.get("certain", True):
                entry["review"] = "uncertain"
                report["uncertain"].append(eid)
            for r in e.get("relations") or []:
                pending.append((eid, r, ev))

    for eid, e in (tree.get("entries") or {}).items():
        if eid in by_id:
            if TREE_EVIDENCE not in by_id[eid]["evidence"]:
                by_id[eid]["evidence"].append(TREE_EVIDENCE)
            continue
        t = TYPES[e["type"]]
        entry = {"type": e["type"], "kind": e.get("kind"),
                 "names": {"la": e.get("latin"), "it": e.get("it"), "en": e.get("en")},
                 "description": {"it": e.get("descr_it"), "en": e.get("descr_en")},
                 "attested": [], "relations": [], "qid": None, "qid_status": "unresolved",
                 "evidence": [TREE_EVIDENCE]}
        by_id[eid] = entry
        out[t]["entries"][eid] = entry

    curated_relations: list[tuple[str, dict]] = []
    for eid, e in curated.items():  # explicit entries: own units, evidence and relations by id
        if eid not in by_id:
            entry = {"type": e["type"], "kind": e.get("kind"),
                     "names": {"la": e.get("latin"), "it": e.get("it"), "en": e.get("en")},
                     "description": {"it": e.get("descr_it"), "en": e.get("descr_en")},
                     "attested": [], "relations": [], "qid": None, "qid_status": "unresolved",
                     "evidence": []}
            by_id[eid] = entry
            out[TYPES[e["type"]]]["entries"][eid] = entry
        entry = by_id[eid]
        if e.get("type") and e["type"] != entry["type"]:
            report["type_conflicts"].append(f"{eid}: {entry['type']} vs {e['type']} (curated)")
        for field in ("attested", "evidence"):
            entry[field] += [x for x in e.get(field, []) if x not in entry[field]]
        curated_relations += [(eid, r) for r in e.get("relations") or []]

    for eid, gone in (removed or {}).items():  # reviewed: cited verses that do not refer to the entry
        entry = by_id.get(eid)
        added = set((curated.get(eid) or {}).get("attested") or [])
        report["stale_removals"].extend(f"{eid} {u}" for u in gone if entry is None or u not in entry["attested"])
        report["conflicting_removals"].extend(f"{eid} {u}" for u in gone if u in added)
        if entry is not None:
            entry["attested"] = [u for u in entry["attested"] if u not in set(gone)]

    for eid, labs in (labels or {}).items():  # how each edition names or designates the entry there
        entry = by_id.get(eid)
        kept = {u: lab for u, lab in labs.items() if entry is not None and u in entry["attested"]}
        report["stale_labels"].extend(f"{eid} {u}" for u in labs if u not in kept)
        if kept:
            entry["labels"] = dict(sorted(kept.items(), key=lambda x: entry["attested"].index(x[0])))

    for c in conjectures or []:  # identities the text does not state, with each scholar's opinion
        src, tgt, unit = c.get("source"), c.get("target"), c.get("unit")
        ok = src in by_id and (tgt in by_id and tgt != src if c.get("rel") == "possibly_same_as" else bool(unit))
        if not ok:
            report["unresolved_conjectures"].append(f"{src} {c.get('rel')} {tgt or unit}")
            continue
        built = {"rel": c["rel"], **({"target": tgt} if tgt else {"unit": unit}),
                 "status": conjecture_status(c.get("opinions") or [], sources or {}), "opinions": c.get("opinions") or []}
        by_id[src].setdefault("conjectures", []).append(built)

    names: dict[str, set[str]] = {}
    for eid, entry in by_id.items():
        for n in (entry["names"]["it"], entry["names"]["la"], entry["names"]["en"]):
            if n:
                names.setdefault(n.lower(), set()).add(eid)

    def resolve(name: str | None, key: str | None) -> str | None:
        """A target by its sense key; by name only when the name is unique and its id has no
        homonym marker (a discriminated id means other bearers exist, catalogued or not)."""
        if key and key in key_ids:
            ids = list(dict.fromkeys(key_ids[key]))
            if len(ids) == 1:
                return ids[0]
            hits = [i for i in ids if i in names.get((name or "").lower(), set())]
            return hits[0] if len(hits) == 1 else None
        hits = names.get((name or "").lower(), set())
        if len(hits) == 1 and not _discriminated(next(iter(hits))):
            return next(iter(hits))
        return None

    def fits(eid: str, rel: str, target: str) -> bool:
        want = TARGET_TYPE.get(rel)
        if want == "same":
            want = by_id[eid]["type"]
        source_ok = SOURCE_TYPE.get(rel) in (None, by_id[eid]["type"])
        return source_ok and (want is None or by_id[target]["type"] == want)

    for eid, r, ev in pending:
        target = resolve(r.get("target"), r.get("target_key"))
        if target and target != eid and fits(eid, r["rel"], target):
            _add_relation(by_id[eid], r["rel"], target, ev)
        else:
            report["unresolved_relations"].append(f"{eid} {r['rel']} {r.get('target')}")

    for r in tree.get("relations") or []:
        src, tgt = r["source"], r["target"]
        if src in by_id and tgt in by_id and src != tgt and fits(src, r["rel"], tgt):
            _add_relation(by_id[src], r["rel"], tgt, TREE_EVIDENCE)
        else:
            report["unresolved_relations"].append(f"{src} {r['rel']} {tgt} ({TREE_EVIDENCE})")

    for src, r in curated_relations:
        tgt = r["target"]
        if tgt in by_id and src != tgt and fits(src, r["rel"], tgt) and r.get("evidence"):
            for ev in r["evidence"]:
                _add_relation(by_id[src], r["rel"], tgt, ev)
        else:
            report["unresolved_relations"].append(f"{src} {r['rel']} {tgt} (curated)")

    for eid, entry in by_id.items():
        if eid in qids:
            entry["qid"], entry["qid_status"] = qids[eid].get("qid"), qids[eid].get("status", "unresolved")

    for t in out.values():
        t["entries"] = dict(sorted(t["entries"].items()))
    out["report"] = report
    return out


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    decisions = json.loads((ROOT / "data/curated/senses.json").read_text(encoding="utf-8"))["decisions"]
    units = {s["key"]: s["units"] for s in _jsonl(PRIVATE / "ndeib-senses.jsonl")}
    tree_path = ROOT / "data/curated/bj-tree.json"
    tree = json.loads(tree_path.read_text(encoding="utf-8")) if tree_path.exists() else {}
    pu_path = ROOT / "data/curated/part-units.json"
    part_units = json.loads(pu_path.read_text(encoding="utf-8"))["parts"] if pu_path.exists() else {}
    uc_path = ROOT / "data/curated/unit-corrections.json"
    for key, fixed in (json.loads(uc_path.read_text(encoding="utf-8"))["units"] if uc_path.exists() else {}).items():
        part_units.setdefault(key, {}).update(fixed)
    q_path = ROOT / "data/curated/qids.json"
    qids = json.loads(q_path.read_text(encoding="utf-8"))["qids"] if q_path.exists() else {}
    c_path = ROOT / "data/curated/entries.json"
    curated = json.loads(c_path.read_text(encoding="utf-8"))["entries"] if c_path.exists() else {}
    r_path = ROOT / "data/curated/unattested.json"
    removed = json.loads(r_path.read_text(encoding="utf-8"))["entries"] if r_path.exists() else {}
    l_path = ROOT / "data/curated/labels.json"
    labels = json.loads(l_path.read_text(encoding="utf-8"))["entries"] if l_path.exists() else {}
    cj_path, src_path = ROOT / "data/curated/conjectures.json", ROOT / "data/curated/sources.json"
    conjectures = json.loads(cj_path.read_text(encoding="utf-8"))["conjectures"] if cj_path.exists() else []
    sources = json.loads(src_path.read_text(encoding="utf-8"))["sources"] if src_path.exists() else {}
    out = build(decisions, units, tree, part_units, qids, curated, removed, labels, conjectures, sources)
    report = out.pop("report")
    for t, data in out.items():
        (ROOT / "data" / f"{t}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# Build report", "", "Generated by `scripts/build_catalog.py`; do not edit.", ""]
    for k, items in report.items():
        lines += [f"## {k.replace('_', ' ').capitalize()} ({len(items)})", ""] + [f"- {i}" for i in items] + [""]
    (ROOT / "docs/build-report.md").write_text("\n".join(lines), encoding="utf-8")
    print({t: len(d["entries"]) for t, d in out.items()}, {k: len(v) for k, v in report.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
