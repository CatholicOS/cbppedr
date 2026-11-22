# Data format

## Catalogs

`data/persons.json`, `data/places.json`, `data/events.json`: each is

```json
{"$comment": "…", "entries": {"<id>": {
  "type": "person | place | event",
  "kind": "individual | group | deity | extra-biblical | city | region | mountain | river | sea | valley | desert | site | building | other | episode | battle | assembly",
  "names": {"la": "Nova Vulgata form", "it": "CEI form", "en": "usual English form"},
  "description": {"it": "≤ 15 words, our own", "en": "≤ 15 words, our own"},
  "attested": ["btu:mt.14.3", "…"],
  "labels": {"btu:gal.2.9": {"as": "name", "editions": {"NVBSE": "Cephas", "CEI2008": "Cefa", "NABRE": "Kephas"}}},
  "relations": [{"rel": "child_of", "target": "<id>", "evidence": ["ndeib:FILIPPO#1", "bj:herodian-tree"]}],
  "qid": "Q… | null",
  "qid_status": "auto | reviewed | unresolved",
  "evidence": ["ndeib:FILIPPO#1"],
  "review": "uncertain"
}}}
```

- **Identifiers:** `bpers:`, `bplace:`, `bevent:` + the Nova Vulgata Latin name as a lowercase ASCII slug, words joined by `-`, plus `.` and a short Latin discriminator when the name is shared (`bpers:philippus.tetrarcha`). Drafts until `v1.0.0`.
- **attested:** the [CBTUDR](https://github.com/CatholicOS/cbtudr) units where the sources place the entry, in the order cited. They locate the entry, edition-independently; they are not yet the list of every mention (that is the next project: mentions with offsets per edition).
- **labels** (only where needed): for an attested unit where the entry is not called by its catalogued names, how each edition names it there: `as` is `name` (another name the entry bears: Cephas, Saul, Zion) or `designation` (a title or description the context ties to it: "the king of Israel" in the Joram narrative); `editions` maps each edition that carries it (`NVBSE`, `VGCL`, `CEI2008`, `NABRE`, `DRB`) to the label as printed, at most six words. An edition missing from the map does not name or designate the entry in that verse (e.g. "the prophet" in 2 Kgs 2:24 is only the NABRE's), so an application can keep only the units its edition supports.
- **relations:** `child_of`, `parent_of`, `spouse_of`, `sibling_of`, `eponym_of`, `people_of`, `land_of`, `located_in`, `part_of`, `participant`, `same_as`; stated one way, as the source states it.
- **evidence:** locations, never text. `ndeib:<HEADWORD>#<sense>` is a sense of the *Nuovo Dizionario Enciclopedico Illustrato della Bibbia* (`~n` numbers a repeated headword or a restarted numbering); `bj:herodian-tree` the Jerusalem Bible's Hasmonean and Herodian family tree, curated as explicit relations between ids in `data/curated/bj-tree.json`. `nv:<unit>` (e.g. `nv:btu:ne.12.36`) is a verse of the Nova Vulgata, cited where the Bible text alone establishes the entry or tells it from its homonyms (a patronym, an office, a place, a time); STEPBible's TIPNR may point to such verses, but is never itself the evidence.
- **review: "uncertain":** the reviewer could not settle the identity from the source (for example, whether two senses are one person).

## Unnamed persons

`data/unnamed.json` holds the persons the Bible mentions or presupposes but no edition checked names (Lot's wife, Pharaoh's daughter who raised Moses, Peter's mother-in-law). A catalog id needs a name, so they are kept apart, under a provisional key `anon:<the entry they are tied to>.<role>` (`anon:lot.uxor`), until an edition or source that names them is added; they then move into the catalog.

```json
{"anon:lot.uxor": {"type": "person", "kind": "individual",
  "description": {"it": "…", "en": "Lot's wife, turned into a pillar of salt"},
  "attested": ["btu:gn.19.26", "…"], "implied_by": [],
  "tie": {"rel": "spouse_of", "target": "bpers:lot"},
  "named_in": {}, "evidence": ["nv:btu:gn.19.26"],
  "editions_checked": ["NVBSE", "VGCL", "CEI2008", "NABRE", "DRB"]}}
```

- **attested:** the units that mention or designate the person; **implied_by:** units whose wording presupposes the person without mentioning them ("he took another wife" presupposes a first one). A person merely biologically implied (every man's father) is not recorded.
- **named_in:** editions that give a name, by edition (none yet); **editions_checked:** the editions searched.

## Curated inputs

- `data/curated/senses.json`: the reviewed decision for every dictionary sense (type, identifier, names, descriptions, relations; `parts` when one sense covers several entities).
- `data/curated/part-units.json`: for a sense with several entities, the units of each.
- `data/curated/qids.json`: the Wikidata matches, with candidates kept for unresolved ones.
- `data/curated/unit-corrections.json`: a sense's corrected units, where the units it cites are not where the entity appears (by sense key and id).
- `data/curated/entries.json`: entries curated by hand, with explicit ids, units (the Nova Vulgata verses that name them), evidence and relations; an entry already built from a sense is extended. First use: the persons the dictionary treats only in a book's article, a sense classified as the book (`none`).
- `data/curated/bj-tree.json`: the Herodian tree's entries and relations.
- `data/curated/labels.json`: by id and unit, the reviewed labels (see **labels** above).
- `data/curated/unattested.json`: by id, the units a citation attached to an entry but that, on review, do not refer to it (a whole passage cited for one person, a misread reference, a homonym's verse). They are removed before the curated entries are applied, so a curated entry can still add a unit back.

## Pipeline

All scripts in `scripts/`; the private inputs (the two books, and intermediates carrying their text) stay outside the repository, in `~/development/BibleGet-I-O/data-local/cbppedr/`.

1. `ndeib_senses.py`: the dictionary's senses, their references and units (private).
2. `bj_evidence.py`: the Jerusalem Bible's index of names, family tree and chronology (private).
3. Review (briefs in `docs/briefs/`), then `consolidate.py` → `data/curated/senses.json` and `part_units.py` → `data/curated/part-units.json`.
4. `build_catalog.py` (also reads the curated corrections, entries and tree) → the catalogs and `docs/build-report.md`.
5. `wikidata.py` → `data/curated/qids.json`; rebuild to apply.
6. `validate.py`, `stepbible_check.py` → `docs/stepbible-gaps.md`, `generate_registry.py` → `registry/`.
7. `audit_attested.py`: the attested verses that no edition's text (Nova Vulgata, Clementine Vulgate, CEI 2008, NABRE, Douay-Rheims, exported by unit from the BibleGet database, private) names the entry in; the list is reviewed, and the verses that do not refer to the entry go to `unattested.json`.

Tests: `cd scripts && uv run --with lxml python -m unittest discover -s .`
