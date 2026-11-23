# Data format

The structure of every file. What each term means (types, kinds, relations, `same_as` and `possibly_same_as`, labels, evidence, sources, statuses) is in [vocabulary.md](vocabulary.md).

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
  "conjectures": [{"rel": "possibly_same_as", "target": "<id>", "status": "supported",
                   "opinions": [{"by": "bj:note:…", "says": "suggests", "summary": "…"}]}],
  "qid": "Q… | null",
  "qid_status": "auto | reviewed | adjudicated | unresolved",
  "evidence": ["ndeib:FILIPPO#1"],
  "review": "uncertain"
}}}
```

- **Identifiers:** `bpers:`, `bplace:`, `bevent:` + the Nova Vulgata Latin name as a lowercase ASCII slug, words joined by `-`, plus `.` and a short Latin discriminator when the name is shared (`bpers:philippus.tetrarcha`). Drafts until `v1.0.0`.
- **attested:** the [CBTUDR](https://github.com/CatholicOS/cbtudr) units where the entry appears, by name or by a designation the context ties to it, edition-independently, in the order the sources cite them. Verses that refer to it only by a pronoun, or not at all, are not attested. They are not yet the list of every mention (that is the next project: mentions with offsets per edition).
- **labels** (only where needed): for an attested unit where the entry is not called by its catalogued names, how each edition names it there: `as` is `name` (another name the entry bears: Cephas, Saul, Zion) or `designation` (a title or description the context ties to it: "the king of Israel" in the Joram narrative); `editions` maps each edition that carries it (`NVBSE`, `VGCL`, `CEI2008`, `NABRE`, `DRB`) to the label as printed, at most six words. An edition missing from the map does not name or designate the entry in that verse (e.g. "the prophet" in 2 Kgs 2:24 is only the NABRE's), so an application can keep only the units its edition supports.
- **relations:** `child_of`, `parent_of`, `spouse_of`, `sibling_of`, `eponym_of`, `people_of`, `land_of`, `located_in`, `part_of`, `participant`, `same_as`; stated one way, from the entry to `target`, as the evidence states it. Each relation's meaning and the types of its source and target: [vocabulary.md](vocabulary.md#relations).
- **conjectures** (only where any): identities and attestations the text does not settle; see [Conjectures](#conjectures).
- **qid / qid_status:** the entry's Wikidata item and how it was set (`auto`, `reviewed`, `adjudicated`, `unresolved`).
- **evidence:** locations, never text. `ndeib:<HEADWORD>#<sense>` is a sense of the *Nuovo Dizionario Enciclopedico Illustrato della Bibbia* (`~n` numbers a repeated headword or a restarted numbering); `bj:herodian-tree` the Jerusalem Bible's Hasmonean and Herodian family tree, curated as explicit relations between ids in `data/curated/bj-tree.json`; `bj:note:<Book>.<ref>#p<page>` or `bj:intro:<section>#p<page>` a note or introduction of the Jerusalem Bible that states the fact. `nv:<unit>` (e.g. `nv:btu:ne.12.36`) is a verse of the Nova Vulgata, cited where the Bible text alone establishes the entry or tells it from its homonyms (a patronym, an office, a place, a time); STEPBible's TIPNR may point to such verses, but is never itself the evidence.
- **review: "uncertain":** the reviewer could not settle the identity from the source (for example, whether two senses are one person).

## Conjectures

The catalog states an identity (`same_as`) or an attestation only when the Bible text establishes it, or an authoritative source states it as fact ([levels of certainty](vocabulary.md#how-sure-is-a-statement)). What the text leaves open but scholars propose is recorded as a **conjecture** on the entry, with each opinion for or against it and whose opinion it is:

```json
"conjectures": [
  {"rel": "possibly_attested_at", "unit": "btu:1sam.14.49", "status": "supported",
   "opinions": [{"by": "bj:note:1Sam.14,49#p597", "says": "identifies", "summary": "Ishvi is another form of the name Ishbaal"},
                {"by": "tipnr:Ishvi@1Sa.14.49", "says": "identifies", "summary": "listed as the same person, without a reference"}]}]
```

- **rel:** `possibly_same_as` (with `target`, another entry: the two may be one) or `possibly_attested_at` (with `unit`: a figure in that verse, unnamed or named otherwise, may be this entry).
- **opinions:** `by` is a source location, `says` one of `identifies`, `suggests`, `doubts`, `rejects`, and `summary` a few words of our own (never the source's text).
- **Sources** (`data/curated/sources.json`) say whose opinion it is and how much it weighs. *Authoritative*: a published scholarly work cited by location, such as a note or a book's introduction in the Jerusalem Bible (`bj:note:<Book>.<ref>#p<page>`, `bj:intro:<section>#p<page>`) or a sense of the dictionary (`ndeib:<KEY>`, the headword with `#<sense>` where its senses are numbered). Another published work is cited as `pub:<first author's surname>-<year>#p<page>` and listed in `sources.json` with its own authority: authoritative when it is Catholic or peer-reviewed. *Non-authoritative*: a claim without references, such as STEPBible's TIPNR (`tipnr:<name>`), a reviewer's inference (`reviewer:<round>`), or a work that is neither Catholic nor peer-reviewed, kept as a lead until an authoritative source is found.
- **status**, computed by the build from the authoritative opinions only: `supported` (one identifies or suggests it, none doubts or rejects it), `disputed` (they disagree), `rejected` (one rejects it, none is for it), `doubted` (they only doubt it), `unsupported` (no authoritative opinion yet).
- A conjecture never changes `attested` or `same_as`.

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

The reviewed decisions the catalogs are built from, in `data/curated/`. Ids are as in the catalogs; units are CBTUDR units.

| File | Holds | Shape |
|---|---|---|
| `senses.json` | the reviewed decision for every dictionary sense: type, id, names, descriptions, relations by name; `parts` when one sense covers several entities; `certain: false` marks an entry `review: uncertain`. Hand-maintained: never regenerate it with `consolidate.py`. | `{"decisions": [{"key": "ABARIM", "type": "place", "kind": "mountain", "id": "bplace:abarim", "latin", "it", "en", "descr_it", "descr_en", "relations": [{"rel": "located_in", "target": "Moab", "target_key": null}], "certain": true}]}` |
| `part-units.json` | for a sense with several entities, the units of each (generated by `part_units.py` from the private reviews) | `{"parts": {"<sense key>": {"<id>": ["btu:…"]}}}` |
| `unit-corrections.json` | a sense's corrected units, where the units it cites are not where the entity appears; overrides `part-units.json` | `{"units": {"FILIPPO#2": {"bpers:philippus.tetrarcha": ["btu:lc.3.1"]}}}` |
| `entries.json` | entries curated by hand, with their own units, evidence and relations by id. An id not built from a sense is created (then `type`, `kind`, `latin`, `it`, `en`, `descr_it`, `descr_en` are required); an existing one is extended. | `{"entries": {"bpers:aasbai": {"type": "person", "kind": "individual", "latin": "Aasbai", "it": "Acasbài", "en": "Ahasbai", "descr_it", "descr_en", "attested": ["btu:2sam.23.34"], "evidence": ["nv:btu:2sam.23.34"], "relations": [{"rel": "parent_of", "target": "<id>", "evidence": ["nv:btu:2sam.23.34"]}]}}}` |
| `bj-tree.json` | the Jerusalem Bible's Herodian tree: its entries, and its relations between ids | `{"entries": {"<id>": {"type", "kind", "latin", "it", "en", "descr_it", "descr_en"}}, "relations": [{"source": "<id>", "rel": "spouse_of", "target": "<id>"}]}` |
| `unattested.json` | by id, the units a citation attached to an entry that, on review, do not refer to it. Applied after the curated entries, so a review always wins; a removal a curated entry contradicts is reported. | `{"entries": {"<id>": ["btu:…"]}}` |
| `labels.json` | by id and unit, how each edition names or designates the entry where it is not called by its catalogued names | `{"entries": {"<id>": {"btu:2reg.2.24": {"as": "designation", "editions": {"NABRE": "The prophet"}}}}}` |
| `conjectures.json` | the conjectures, with every opinion; the build adds each to its source entry with a computed `status` | `{"conjectures": [{"source": "<id>", "rel": "possibly_same_as", "target": "<id>", "opinions": [{"by": "bj:note:…", "says": "suggests", "summary": "…"}]}, {"source": "<id>", "rel": "possibly_attested_at", "unit": "btu:…", "opinions": […]}]}` |
| `sources.json` | the register of sources conjectures may cite: whose opinion, its authority, its locator format | `{"sources": {"bj": {"title", "authority": "authoritative", "locator"}}}` |
| `qids.json` | the Wikidata matches, with the candidates kept for review and the items judged wrong | `{"qids": {"<id>": {"qid": "Q… \| null", "status": "auto \| reviewed \| adjudicated \| unresolved", "candidates": ["Q…"], "rejected": ["Q…"], "deduped": true, "by": "jev-1.14.0", "p_same": 0.9}}}`; `by`, `p_same`: the model that adjudicated the item and its probability; `rejected`: items a reviewer judged wrong, never picked, and an entry holding one is matched again; `deduped`: the automatic pick was cleared because another entry had the same item, so the next run judges it again |

## Build report

`docs/build-report.md`, regenerated by every build, lists what it could not settle or apply:

- **Merged:** ids several senses were merged into.
- **Unresolved relations:** relations whose target could not be identified (its name is shared, or the types do not fit the relation).
- **Type conflicts:** an id given two types (by two senses, or by a sense and a curated entry).
- **Uncertain:** entries marked `review: uncertain`.
- **Stale removals / stale labels:** removals or labels for units the entry no longer has.
- **Conflicting removals:** a reviewed removal of a unit that a curated entry adds.
- **Unresolved conjectures:** a conjecture whose entry, target or unit is missing.

## Pipeline

All scripts in `scripts/`; the private inputs (the two books, and intermediates carrying their text) stay outside the repository, in `~/development/BibleGet-I-O/data-local/cbppedr/`.

1. `ndeib_senses.py`: the dictionary's senses, their references and units (private).
2. `bj_evidence.py`: the Jerusalem Bible's index of names, family tree and chronology (private).
3. Review (briefs in `docs/briefs/`), then `consolidate.py` → `data/curated/senses.json` and `part_units.py` → `data/curated/part-units.json`.
4. `build_catalog.py` (also reads the curated corrections, entries and tree) → the catalogs and `docs/build-report.md`.
5. `wikidata.py` → `data/curated/qids.json`; rebuild to apply.
6. `validate.py`, `stepbible_check.py` → `docs/stepbible-gaps.md`, `generate_registry.py` → `registry/`.
7. `export_texts.py` → the editions' text by unit (private), then `audit_attested.py`: the attested verses that no edition's text (Nova Vulgata, Clementine Vulgate, CEI 2008, NABRE, Douay-Rheims, exported by unit from the BibleGet database, private) names the entry in; the list is reviewed: the verses that do not refer to the entry go to `unattested.json`, the others get their `labels`. A verse with a label is accounted for, so a clean catalog has none flagged.

Tests: `cd scripts && uv run --with lxml python -m unittest discover -s .`
