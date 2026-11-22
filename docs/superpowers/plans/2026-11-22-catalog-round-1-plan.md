# CBPPEDR round 1 (baseline catalog) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local CBPPEDR repository holding the first catalogs of biblical persons, places and events, built from the dictionary's senses and the Jerusalem Bible's evidence, with CBTUDR units, relations, Wikidata QIDs where certain, and a STEPBible gap report.

**Architecture:** Public scripts read the two private XML files and write facts only. Private intermediates (anything carrying book wording) go to `~/development/BibleGet-I-O/data-local/cbppedr/`. Public data lives in `data/{persons,places,events}.json`, generated from reviewed decision files in `data/curated/`, with a registry in `registry/` and reports in `docs/`.

**Tech Stack:** Python 3.12, pytest, lxml, run with `uv run --with lxml --with pytest`; CBTUDR local clone (`CBTUDR_DIR`, default `~/development/CatholicOS_org/cbtudr`); Wikidata API via `urllib` with an on-disk cache.

**Spec:** `docs/superpowers/specs/2026-11-21-biblical-persons-places-events-design.md` (part 4), copied into the repo in Task 1.

## Global Constraints

- Repository: `~/development/CatholicOS_org/cbppedr`, local git only; **no GitHub repository and no push** until the user confirms (spec: outward-facing).
- Licences as CBTUDR: data CC0 (`LICENSE-CC0`), docs/registry CC BY-ND 4.0, scripts Apache 2.0 (`scripts/LICENSE`).
- Identifiers `bpers:`, `bplace:`, `bevent:` + Nova Vulgata Latin slug (lowercase ASCII, `-` between words) + `.` + Latin discriminator when shared; drafts until `v1.0.0`.
- Nothing worded by the dictionary or the Jerusalem Bible in the repository: no definitions, note text or titles. Descriptions are our own, a few words, `it` and `en`.
- Evidence cites by location only: `ndeib:<HEADWORD>#<sense>`, `bj:note:<book> <ref>@p<page>`, `bj:index:<NAME>`, `bj:tree:<n>`, `bj:chrono:p<page>`.
- Verse references resolve to CBTUDR units through `data/maps/cei2008/`; unresolvable references are kept as printed in a report, never guessed.
- Merging, splitting and QIDs follow "better unidentified than misidentified": automatic only with clear evidence; otherwise a review item.
- Wikidata: generic User-Agent `cbppedr-catalog/0.1`; responses cached under `data-local/cbppedr/wikidata-cache/`; at most 1 request per second.
- STEPBible TIPNR (CC BY 4.0) is read from `data-local/stepbible/tipnr.txt` only for the gap report; none of its data enters `data/`.

## Review Focus

1. A dictionary sense that cites no verse (common for minor places): it must still become an entry candidate, with `attested: []`, not be dropped.
2. References in the dictionary's other numberings (Vulgate/LXX psalms, Hebrew Esther, Greek Daniel): the resolver must report them unresolved rather than map them to the wrong unit.
3. Homonyms within one headword whose senses are sub-sections (FILISTEI 1–5): the splitter must not create five entries automatically; sense-to-entry is a reviewed decision.
4. The same person under two Italian spellings (Ioiakìm / Ioiachìn; Erode Antipa / Antipa): merging by name alone must not happen; only by shared units plus a reviewed decision.
5. Wikidata items for the same name (Philip the Apostle, Philip the Evangelist, Philip the Tetrarch, Herod Philip I): a QID is auto-accepted only when its own statements or description agree with the entry's relations or attested books.

---

### Task 1: Repository scaffold

**Files:** Create `README.md`, `LICENSE`, `LICENSE-CC0`, `scripts/LICENSE` (copied from CBTUDR), `AGENTS.md`, `.gitignore`, `docs/superpowers/specs/…design.md`, `docs/superpowers/plans/…this plan`, `pyproject.toml` (pytest config: `testpaths = ["scripts"]`), `data/`, `registry/`.

- [ ] README states purpose, the three types, ID grammar, licence split, "drafts until v1.0.0", and that no text of the source books is included.
- [ ] `git init -b main`, commit. Verify `git status` clean, no remote (`git remote` empty).

### Task 2: Verse references → CBTUDR units

**Files:** `scripts/refs.py`, `scripts/units.py`, `scripts/test_refs.py`, `scripts/test_units.py`, `scripts/books_it.json`

**Interfaces:**
- Produces: `parse_refs(text, profile, default_book=None) -> list[Ref]` (same contract as `BibleGet/tools/ocr/refs.py`, ported; profiles `bj`, `ndeib`); `units_for(ref: Ref) -> list[str] | None` (None = unresolved), reading `$CBTUDR_DIR/data/maps/cei2008/NN-*.json` (`ref` `"ch:v"`, or `"ch:v@HEBREW"`/`"@GREEK"` for Esther; a bare verse in a two-tradition book tries `@GREEK` only when `@HEBREW` lacks it).
- Tests: `units_for(parse_refs("Gn 29,34","ndeib")[0]) == ["btu:gn.29.34"]`; a range `Lc 3,23-24` gives two units; `Sal 151,2` → None; `Gb 40,25` resolves (CEI numbering); `Est 1,1a` resolves to the Greek unit.

### Task 3: Dictionary senses (private intermediate)

**Files:** `scripts/ndeib_senses.py`, `scripts/test_ndeib_senses.py`

**Interfaces:**
- Consumes: Task 2; the TEI path (`NDEIB_TEI` env or `--tei`).
- Produces: `data-local/cbppedr/ndeib-senses.jsonl`, one sense per line: `{"key": "LEVI#1", "headword": "LEVI", "sense": 1 | null, "refs": [printed refs], "units": [...], "unresolved": [...], "xrefs": ["Giacobbe", "Lia"], "kind_guess": "person"|"place"|"event"|"other", "text": <sense text, private>}`. Headwords: reuse the classification of `tools/tei2pdf.py` (`Converter._classify_heads`, imported from the NDEIB folder) so entries match the reading PDF; text inside `<sic>` is skipped (corrections only).
- Tests (fixture TEI with LEVI 1–3, LIBNA 1–2, LEVANTE, LEVATRICE as `<p>WORD.` start, and "I. NELL'ANTICO TESTAMENTO" subsection head): LEVI yields 3 senses with `kind_guess` person; LIBNA#1 place; LEVANTE `other`; the subsection head is not a headword; xrefs from `↗Giacobbe` → `"Giacobbe"`.
- `kind_guess` from cue words (place: città, villaggio, regione, monte, fiume, valle, località, Tell, km; person: figlio, figlia, moglie, re di, sacerdote, profeta, levita, apostolo, discendente; event: battaglia, guerra, esilio, concilio, festa?) — a guess for review, nothing more.

### Task 4: Classification review (subagents, letter batches)

- [ ] Batch the senses by initial letter groups; each reviewer (brief `docs/briefs/classify.md`, kept in the repo without book text) reads the private senses and writes `data-local/cbppedr/review/classify-<batch>.jsonl`: `{"key", "type": "person"|"place"|"event"|"none", "kind", "entry": "<proposed id>", "latin": "<NV form>", "descr_it", "descr_en", "split_of": null | "<key>", "same_as": null | "<key>", "note"}`. Latin form taken from the Nova Vulgata verse of an attested unit (`~/development/BibleGet-I-O/NVBSE-vatican/text/*.tsv`).
- [ ] Decisions committed as facts only: `data/curated/senses.json` (key → type, id, latin, descriptions, merge/split), no sense text.

### Task 5: Jerusalem Bible evidence (private intermediate)

**Files:** `scripts/bj_evidence.py`, `scripts/test_bj_evidence.py`

**Interfaces:**
- Produces in `data-local/cbppedr/`: `bj-index.jsonl` (`{"name", "refs", "units", "see": [...]}` from the *Indice alfabetico delle note*), `bj-tree.jsonl` (`{"n", "name", "level", "parent_n", "spouses": [...], "dates"}` from *Dinastie Asmonea e Erodiana*), `bj-chrono.jsonl` (`{"page", "cells": [...], "refs", "units"}` rows of the *Tavola cronologica*, right column only), `bj-notes-names.jsonl` (for each BJ note: `{"book","ref","page","names": [capitalised words]}` — names only, no text).
- Tests on fixtures: index line `ABIATÀR Mc 2,26; v. EBIATÀR.` → name, units `["btu:mc.2.26"]`, see `["EBIATÀR"]`; tree line `11. Erode il Grande 37-4 a.C. ∞ Mariamne I ∞ Mariamne II` → n 11, spouses 2.

### Task 6: Build the catalogs

**Files:** `scripts/build_catalog.py`, `scripts/test_build_catalog.py`, `data/persons.json`, `data/places.json`, `data/events.json`

**Interfaces:**
- Consumes: `data/curated/senses.json`, the Task 2/5 outputs, `data/curated/relations.json`, `data/curated/events.json`.
- Produces each catalog `{"$comment", "entries": {id: {"type","kind","names":{"la","it","en"},"description":{"it","en"},"attested":[units],"relations":[{"rel","target","evidence"}],"qid":null,"qid_status":"unresolved","evidence":[...]}}}`.
- Relations: from `↗` cross-references when the reviewer marked the relation type; from the tree (parent, spouse); `part_of` for events.
- Tests: Philip son of Mariamne II and Philip the tetrarch are two entries; `bpers:philippus.mariamnes-filius` has relation `child_of` → `bpers:mariamne-ii` with evidence `bj:note:Mt 14,3@p…`; an entry with no units keeps `attested: []`; building twice gives byte-identical output.

### Task 7: Wikidata matching

**Files:** `scripts/wikidata.py`, `scripts/test_wikidata.py`, `data/curated/qids.json`
- Search by Italian and English label (`wbsearchentities`), fetch candidates' P31, descriptions and sitelinks; auto only when exactly one candidate is a human/fictional human/biblical figure (persons) or a place item (places) **and** its description or claims mention a related entry or a book of the attested units; else `unresolved` with candidates listed for review.
- Tests with cached fixtures (no network): the two Philips resolve to different QIDs or stay unresolved, never the same QID.

### Task 8: STEPBible gap report and registry

**Files:** `scripts/stepbible_check.py`, `scripts/generate_registry.py`, `scripts/validate.py`, `docs/stepbible-gaps.md`, `registry/*.md`
- Gap report: TIPNR persons/places whose references (OSIS → CBTUDR book numbers, same chapter:verse) match no entry's attested units: listed by book, as round-2 work. Two TIPNR individuals that one of our entries covers: listed as possible merge errors.
- Validate: ids unique and well-formed, every relation target exists, every unit exists in CBTUDR, no field longer than 200 chars except `$comment` (guard against copied text).
- Registry: one table per type, by letter.
