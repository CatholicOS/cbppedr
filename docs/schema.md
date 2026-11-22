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
  "relations": [{"rel": "child_of", "target": "<id>", "evidence": ["ndeib:FILIPPO#1", "bj:herodian-tree"]}],
  "qid": "Q… | null",
  "qid_status": "auto | reviewed | unresolved",
  "evidence": ["ndeib:FILIPPO#1"],
  "review": "uncertain"
}}}
```

- **Identifiers:** `bpers:`, `bplace:`, `bevent:` + the Nova Vulgata Latin name as a lowercase ASCII slug, words joined by `-`, plus `.` and a short Latin discriminator when the name is shared (`bpers:philippus.tetrarcha`). Drafts until `v1.0.0`.
- **attested:** the [CBTUDR](https://github.com/CatholicOS/cbtudr) units where the sources place the entry, in the order cited. They locate the entry, edition-independently; they are not yet the list of every mention (that is the next project: mentions with offsets per edition).
- **relations:** `child_of`, `parent_of`, `spouse_of`, `sibling_of`, `eponym_of`, `people_of`, `land_of`, `located_in`, `part_of`, `participant`, `same_as`; stated one way, as the source states it.
- **evidence:** locations, never text. `ndeib:<HEADWORD>#<sense>` is a sense of the *Nuovo Dizionario Enciclopedico Illustrato della Bibbia* (`~n` numbers a repeated headword or a restarted numbering); `bj:herodian-tree` the Jerusalem Bible's Hasmonean and Herodian family tree, curated as explicit relations between ids in `data/curated/bj-tree.json`.
- **review: "uncertain":** the reviewer could not settle the identity from the source (for example, whether two senses are one person).

## Curated inputs

- `data/curated/senses.json`: the reviewed decision for every dictionary sense (type, identifier, names, descriptions, relations; `parts` when one sense covers several entities).
- `data/curated/part-units.json`: for a sense with several entities, the units of each.
- `data/curated/qids.json`: the Wikidata matches, with candidates kept for unresolved ones.

## Pipeline

All scripts in `scripts/`; the private inputs (the two books, and intermediates carrying their text) stay outside the repository, in `~/development/BibleGet-I-O/data-local/cbppedr/`.

1. `ndeib_senses.py`: the dictionary's senses, their references and units (private).
2. `bj_evidence.py`: the Jerusalem Bible's index of names, family tree and chronology (private).
3. Review (briefs in `docs/briefs/`), then `consolidate.py` → `data/curated/senses.json` and `part_units.py` → `data/curated/part-units.json`.
4. `build_catalog.py` → the catalogs and `docs/build-report.md`.
5. `wikidata.py` → `data/curated/qids.json`; rebuild to apply.
6. `validate.py`, `stepbible_check.py` → `docs/stepbible-gaps.md`, `generate_registry.py` → `registry/`.

Tests: `cd scripts && uv run --with lxml python -m unittest discover -s .`
