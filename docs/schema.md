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
- **mentioned** (only where any): the CBTUDR units, in CBTUDR order, where the entry is named in the Nova Vulgata (NVBSE) text by a settled mention (`data/mentions/`) but that no source cites, so they are not in `attested` and never repeat it. A reviewed removal (`unattested.json`) is never added back here. Candidate mentions under review add nothing. An index of the entry uses `attested` and `mentioned` together.
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
- **Sources** (`data/curated/sources.json`) say whose opinion it is and how much it weighs. *Authoritative*: a published scholarly work cited by location, such as a note or a book's introduction in the Jerusalem Bible (`bj:note:<Book>.<ref>#p<page>`, `bj:intro:<section>#p<page>`; the page is omitted where the scan lacks it) or a sense of the dictionary (`ndeib:<KEY>`, the headword with `#<sense>` where its senses are numbered). Another published work is cited as `pub:<first author's surname>-<year>#p<page>` and listed in `sources.json` with its own authority: authoritative when it is Catholic or peer-reviewed. *Non-authoritative*: a claim without references, such as STEPBible's TIPNR (`tipnr:<name>`), a reviewer's inference (`reviewer:<round>`), or a work that is neither Catholic nor peer-reviewed, kept as a lead until an authoritative source is found.
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

## Mentions

`data/mentions/nvbse.json` says where the catalogs' persons and places are named in the Nova Vulgata (NVBSE). It is generated by `scripts/extract_mentions.py` from the edition's private text, and holds no words of it:

```json
{"$comment": "...", "edition": "NVBSE", "units": {
  "btu:gn.29.34": {"hash": "<64 hex>", "mentions": [
    {"start": 12, "end": 16, "check": "<8 hex>", "entry": "bpers:levi.iacob-filius"},
    {"start": 30, "end": 36, "check": "<8 hex>", "candidates": ["bpers:...", "bplace:..."]}]}}}
```

- the key is a CBTUDR unit; Esther's two texts are `btu:…@GREEK` and `btu:…@HEBREW` (no other book takes a suffix);
- `start`/`end`: the span, in UTF-16 code units of the edition's `text_plain` for that unit, `0 <= start < end`;
- `hash`: SHA-256 (64 lowercase hex digits) of that `text_plain` in UTF-8. A consumer whose text hashes differently must ignore the unit;
- `check`: the first 8 hex digits of the SHA-256 of the span's UTF-8 text, so a consumer can confirm it reads the same words;
- `entry`: the mention is settled, one catalog entry;
- `candidates`: the mention is under review: two or more ids (sorted, unique) it may be, or one whose identification is not yet sure. Exactly one of `entry` and `candidates` is present.
- no other property is allowed at any level (but `$comment` at the top), so the file can hold no words of the text.

In an Old Testament unit (deuterocanonical books included, by the book's `testament` in CBTUDR's `data/books.json`), a form is a candidate for a person only when the person is attested (`attested`) somewhere in the Old Testament (places are not limited: Antioch and Cilicia of Maccabees are those of Acts); a span left with no candidate is not a mention (*Maria*, the seas named in Gn 1:10, has only New Testament bearers). New Testament units are not limited, since they name Old Testament persons (Isaias, Melchisedech) that the sources cite only in the Old. A mention is settled when the entry's NVBSE designation label for that unit matches and is found only once in the unit, counted on its own before the longest form at a position wins (found more than once, each occurrence is a `candidates` of that entry), or exactly one of the form's entries is attested (`attested`, not `mentioned`) in the unit. Outside its attested units, a form settles only when all hold: it belongs to one entry only, or, of the entries that share it, exactly one is attested in the unit's book, in the unit's chapter or in at least 3 units of the book (*Eden* in Genesis, the garden), and that one is meant; that entry is attested elsewhere in the same book (the unit's book code); the form is not one of the entry's `partial` forms; it is not a stoplist word; and the unit attests no entry (person or place alike: a people and its land), not found there, one of whose forms has a word with the form's stem (its first 4 letters, case, ligatures and doubled letters folded: Helles where Heles is attested), which would make that entry a candidate with it; no span nested in it is settled to another entry attested in the unit (*desertum Sin* around the attested wilderness of Zin's *Sin*: candidates of both); and the unit is not one a review removed from the entry (`unattested.json`). Anything else is under review, so a name whose only catalogued bearer belongs to another book is a `candidates` of one: it may be an uncatalogued namesake.

`data/mentions/nvbse_curated.json` has the same shape and holds hand corrections. A unit in it replaces the generated unit as a whole; a unit with `"mentions": []` removes that unit's mentions. `merged_mentions()` in `extract_mentions.py` applies it, and `validate.py` checks both files and the merge (ids exist, keys are known units, shapes above), though not the spans against the text, which is private.

## Curated inputs

The reviewed decisions the catalogs are built from, in `data/curated/`. Ids are as in the catalogs; units are CBTUDR units.

| File | Holds | Shape |
|---|---|---|
| `senses.json` | the reviewed decision for every dictionary sense: type, id, names, descriptions, relations by name; `parts` when one sense covers several entities; `certain: false` marks an entry `review: uncertain`. Hand-maintained: never regenerate it with `consolidate.py`. | `{"decisions": [{"key": "ABARIM", "type": "place", "kind": "mountain", "id": "bplace:abarim", "latin", "it", "en", "descr_it", "descr_en", "relations": [{"rel": "located_in", "target": "Moab", "target_key": null}], "certain": true}]}` |
| `part-units.json` | for a sense with several entities, the units of each (generated by `part_units.py` from the private reviews) | `{"parts": {"<sense key>": {"<id>": ["btu:…"]}}}` |
| `unit-corrections.json` | a sense's corrected units, where the units it cites are not where the entity appears; overrides `part-units.json` | `{"units": {"FILIPPO#2": {"bpers:philippus.tetrarcha": ["btu:lc.3.1"]}}}` |
| `entries.json` | entries curated by hand, with their own units, evidence and relations by id. An id not built from a sense is created (then `type`, `kind`, `latin`, `it`, `en`, `descr_it`, `descr_en` are required); an existing one is extended. | `{"entries": {"bpers:aasbai": {"type": "person", "kind": "individual", "latin": "Aasbai", "it": "Acasbài", "en": "Ahasbai", "descr_it", "descr_en", "attested": ["btu:2sam.23.34"], "evidence": ["nv:btu:2sam.23.34"], "relations": [{"rel": "parent_of", "target": "<id>", "evidence": ["nv:btu:2sam.23.34"]}]}}}` |
| `bj-tree.json` | the Jerusalem Bible's Herodian tree: its entries, and its relations between ids | `{"entries": {"<id>": {"type", "kind", "latin", "it", "en", "descr_it", "descr_en"}}, "relations": [{"source": "<id>", "rel": "spouse_of", "target": "<id>"}]}` |
| `disputed_sites.json` | place ids whose site nobody has identified (wilderness stations, sites known only from the text): `details.py` gives them no coordinates whatever Wikidata holds | `{"entries": ["bplace:ceelatha"]}` |
| `unattested.json` | by id, the units a citation attached to an entry that, on review, do not refer to it. Applied after the curated entries, so a review always wins; a removal a curated entry contradicts is reported. | `{"entries": {"<id>": ["btu:…"]}}` |
| `labels.json` | by id and unit, how each edition names or designates the entry where it is not called by its catalogued names | `{"entries": {"<id>": {"btu:2reg.2.24": {"as": "designation", "editions": {"NABRE": "The prophet"}}}}}` |
| `conjectures.json` | the conjectures, with every opinion; the build adds each to its source entry with a computed `status` | `{"conjectures": [{"source": "<id>", "rel": "possibly_same_as", "target": "<id>", "opinions": [{"by": "bj:note:…", "says": "suggests", "summary": "…"}]}, {"source": "<id>", "rel": "possibly_attested_at", "unit": "btu:…", "opinions": […]}]}` |
| `forms.json` | by id, the Latin forms under which a person or place may appear in the Nova Vulgata text: its Latin name and the NVBSE labels of its units that name it (not designations), with case forms of every declinable word (and of the head of a multiword place name: mons, vallis, mare, desertum, so *montem Hor*, with an -um adjective after a neuter head agreeing: *mari Rubro*; a capitalised head, *Mare Rubrum*, also gives its forms with the head lower-case, as the text writes them), both ae/æ spellings, minus stoplist words (`scripts/stoplist_la.txt`); a form shared with another entry's name is kept, for the matcher to resolve. A multiword name also gives the forms of its first word and, for a person, of its last (none from a stoplist word, such as *Tres* of *Tres Tabernae*); these are listed again under `partial`, by id (only where any), and the matcher settles them only in the entry's attested units. A place head gives its declined forms there too (*Mons*, *Montem*). Two exceptions: a component that an NVBSE name label of the entry gives as a whole name (*Petrus* for *Simon Petrus*) is a full form, not partial; and a person's last word that is a catalogued place name gives no partial forms. A lower-case one-word form is looked for only where its entry is attested, and only when it is not partial (*praetorium*, not *via*). Generated by `forms.py`; an id already present is hand-corrected and kept, with its `partial` | `{"forms": {"bpers:petrus": ["Petrus", "Petri", "Petro", "Petrum", "Petre"], "bpers:simon-petrus": ["Simon Petrus", "…", "Simon", "Petrus", "…"]}, "partial": {"bpers:simon-petrus": ["Simon", "Petrus", "…"]}}` |
| `sources.json` | the register of sources conjectures may cite: whose opinion, its authority, its locator format | `{"sources": {"bj": {"title", "authority": "authoritative", "locator"}}}` |
| `qids.json` | the Wikidata matches, with the candidates kept for review and the items judged wrong | `{"qids": {"<id>": {"qid": "Q… \| null", "status": "auto \| reviewed \| adjudicated \| unresolved", "candidates": ["Q…"], "rejected": ["Q…"], "deduped": true, "by": "jev-1.14.0", "p_same": 0.9}}}`; `by`, `p_same`: the model that adjudicated the item and its probability; `rejected`: items a reviewer judged wrong, never picked, and an entry holding one is matched again; `deduped`: the automatic pick was cleared because another entry had the same item, so the next run judges it again |
| `details.json` | Card details, by id, only for entries whose `qid_status` is `reviewed` or `adjudicated` (an automatic match is not enough for a picture or a map). `image`: the first Wikidata P18 file with its Wikimedia Commons credit: `file` (name on Commons), `author` (plain text: all HTML removed; a placeholder such as "Unknown author", "Anonymous", "unknown illuminator", "Own work" or a bare URL counts as none, Commons' "No machine-readable author provided. X assumed" gives X, a credit pasted twice is kept once, and one that runs into Commons' "Title"/"Source" labels is cut before them), `license` (short name), `license_url` (only when present and http(s)); an image without a licence on Commons is left out. `wikipedia`: article titles by language (`la it en es fr de pt`, from the item's sitelinks). `coords`: `{lat, lon}` from P625, only for a place, only when the item has exactly one P625 statement, that statement has no sourcing-circumstances (P1480) qualifier, and the place is not in `curated/disputed_sites.json`. Empty fields are omitted, and so are entries with nothing. Generated by `details.py` (from the Wikidata and Commons caches in the private folder; the network on a first run) | `{"entries": {"bplace:roma": {"image": {"file": "…", "author": "…", "license": "CC BY-SA 4.0", "license_url": "https://…"}, "wikipedia": {"it": "Roma"}, "coords": {"lat": 41.9, "lon": 12.5}}}}` |

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
5. `wikidata.py` → `data/curated/qids.json`; rebuild to apply. Then `details.py` → `data/details.json`.
6. `validate.py`, `stepbible_check.py` → `docs/stepbible-gaps.md`, `generate_registry.py` → `registry/`.
7. `export_texts.py` → the editions' text by unit (private), then `audit_attested.py`: the attested verses that no edition's text (Nova Vulgata, Clementine Vulgate, CEI 2008, NABRE, Douay-Rheims, exported by unit from the BibleGet database, private) names the entry in; the list is reviewed: the verses that do not refer to the entry go to `unattested.json`, the others get their `labels`. A verse with a label is accounted for, so a clean catalog has none flagged.

Tests: `cd scripts && uv run --with lxml python -m unittest discover -s .`
