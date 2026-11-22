# Biblical persons, places and events — design

Date: 2026-11-21. Status: draft for approval. Once the new repository exists
this file moves to its `docs/superpowers/specs/`.

## Intent

The BibleGet reader will link the names of persons and places, and events,
to index entries, as martyrology-frontend does for the Roman Martyrology
(CRMEDR: `persons.json`, `gazetteer.json`, `events_curated.json`). The same
data can later power search. This project builds the **baseline catalog**:
who, where and what, each told apart from its homonyms. Linking each entry to
the words of each edition (mentions with offsets) is the next project, not
this one, but the catalog must make it possible: two persons who share a
name in the same verse range (Philip the tetrarch, Lk 3:1; Philip son of
Mariamne II, Mt 14:3) must already be two entries, with the evidence that
tells them apart.

Two copyrighted books in the user's possession are the main evidence:

- *Nuovo Dizionario Enciclopedico Illustrato della Bibbia* (Piemme 2005), an
  OCR'd TEI file;
- *La Bibbia di Gerusalemme* (EDB 2011): the CEI 2008 text with the Jerusalem
  Bible's notes, titles, marginal references and appendices, in one XML.

Before the catalog, both XML files get their OCR errors fixed, and the
Jerusalem Bible's titles are extracted as a private reference document.

## Order of work (decided by the user)

1. OCR fixes, Jerusalem Bible XML (checked against its scan).
2. OCR fixes, dictionary XML (no scan survives; see part 2).
3. Private document of the Jerusalem Bible's titles.
4. The catalog, approach A (below).

## Goals

- Both XML files with fewer OCR errors, every fix recorded and reversible.
- A private, readable list of the Jerusalem Bible's titles.
- A public repository with three catalogs, persons, places and events, each
  entry with a stable identifier, type, names, the CBTUDR units where the
  dictionary or the Jerusalem Bible attests it, its relations to other
  entries, a Wikidata QID where one is identified, and its evidence.

## Non-goals

- Mentions: offsets of each name in each edition's text (next project).
- The reader's index pages, search, API endpoints.
- Coordinates and maps of places (a later round, from Wikidata or an open
  gazetteer).
- Creating or editing Wikidata items; the Cathopedia Wikibase service.
- Correcting the CEI 2008 Bible text in the Jerusalem Bible XML (it came from
  bibbiaedu.it, not from the scan).

## Anti-goals

- **Misidentification.** As in CRMEDR: an unidentified person is better than
  a misidentified one. A homonym is merged, split or matched to a QID only on
  clear evidence or by a reviewer.
- **Copyrighted wording in public.** Nothing from the dictionary or the
  Jerusalem Bible is copied into the public repository: no definitions, no
  note text, no titles. Facts only (names, identities, relations, verse
  references), with the source cited by location (dictionary headword and
  sense, Jerusalem Bible note by book, reference and PDF page).
- **Silent changes to the source files.** No OCR fix without a record; no
  re-serialisation of the XML that changes bytes outside the fix.
- **Publishing the titles document.** It stays on the user's machine.

## Constraints

- Source files (Windows side, outside any repository):
  - `C:\Users\johnr\Documents\BibleGet\bibbia_gerusalemme_completa.xml`
    (12 MB) and its scan
    `AA.VV. La Bibbia di Gerusalemme - Edizioni Dehoniane Bologna - 2011.pdf`
    (3,070 page images, 1-bit JBIG2, no text layer).
  - `C:\Users\johnr\Documents\Missio Digitalis Foundation\Alexandria Hub digitization\Nuovo Dizionario Enciclopedico Illustrato della Bibbia\Nuovo_Dizionario_Enciclopedico_Illustrato_della_Bibbia.tei.xml`
    (12 MB). The `_OCR.pdf` beside it is typeset *from* the XML
    (`tools/tei2pdf.py`) and is not evidence. The original scans are lost.
- Repository conventions of the CatholicOS `c*dr` repositories (CBTUDR as
  the model): data CC0, docs/registry CC BY-ND 4.0, scripts Apache 2.0;
  identifiers are drafts until `v1.0.0`; Python scripts with tests; a
  generated registry in `registry/`.
- Verse references resolve to CBTUDR units (`btu:<book>.<ch>.<v>`) through
  the CEI 2008 map (`data/maps/cei2008/`), since both books cite in the CEI
  numbering. A reference CBTUDR cannot resolve is kept as printed and
  reported, never guessed.
- Copyrighted extracts needed for review (dictionary senses, note text) live
  only in `~/development/BibleGet-I-O/data-local/` (git-ignored, outside
  repositories), as for CBTUDR's LaBSE vectors.
- The user's standing rules: stage files explicitly; never print
  credentials; push a finished branch and open a PR.

## Part 1 — OCR fixes, Jerusalem Bible

**What is checked:** everything that came from the scan: notes with
`source="BJ"` (10,203), BJ headings (`part`, `section`, `psalm`), marginal
references (`xref`), the introductions (`div type="intro"`) and the
appendices. Not the verse text, not the CEI notes and headings
(`source="CEI"`, from bibbiaedu.it). The file says it was already corrected
against the scan once; this pass finds what that one missed.

**Safety first:** `git init` the `Documents\BibleGet` folder, a local
repository with no remote, ignoring the PDF and the CSVs; commit the file as
it is. Each batch of fixes is one commit, so every fix can be reviewed with
`git diff` and undone.

**Finding candidates** (a script; the builder chooses the exact heuristics):
- words not in an Italian word list and not frequent in the file itself;
  words one edit away from a frequent word ("meonato"/"neonato");
- words split by a stray space ("me ttersi") or joined; hyphenation left over
  from line ends ("ciotto- li" inside a cell is the printed layout and stays);
- verse references that cannot exist in CEI 2008 (chapter or verse out of
  range), using the endpoint's CEI2008 index or the versification snapshot;
- broken characters: mixed-up quotes, `l'` vs `l’`, Greek or Hebrew
  transliteration with wrong diacritics only where the scan shows otherwise.

**Checking:** each candidate's page (`pdf_page`) is rendered with
`pdftoppm` and the line read on the image. A fix is made only when the
image shows it. Candidates the image does not settle are listed in
`ocr-review.md` next to the XML, for the user.

**Editing:** text replaced in place in the file, never by parsing and
re-writing the XML; the file must still parse after each batch, and the diff
must touch only the fixed words.

**Scale:** thousands of candidates are possible. Checking images can be
split among subagents by book; the builder sizes batches.

## Part 2 — OCR fixes, dictionary

No scan, so only fixes the context settles for certain: a non-word whose
correction is the only Italian word that fits ("meonato" in a sentence about
a newborn), a split word, an impossible verse reference whose right form is
certain from the other references in the same entry or from the cited
verse's content. Each is marked in TEI as a conjecture, keeping the reading:

```xml
<choice><sic>meonato</sic><corr resp="#claude" cert="high">neonato</corr></choice>
```

with a `<respStmt xml:id="claude">` added to the TEI header. Doubtful cases
stay as printed and go to `ocr-review.md`. Same git safety as part 1 (ignore
the PDF and `tools/__pycache__`). `tools/tei2pdf.py` should render `<choice>`
as the correction; the builder checks it still runs.

## Part 3 — titles of the Jerusalem Bible (private)

`C:\Users\johnr\Documents\BibleGet\Bibbia_di_Gerusalemme_titoli.md`: per
book, the BJ headings in printed order with their level (`part` as the outer
level, `section` and `psalm` under it) and the reference of the first verse
after each heading (e.g. `Gen 1,1 — L'opera dei sei giorni`). Only BJ titles;
the CEI 2008 titles (`source="CEI"`, `type="s"`, `"sr"`) are left out. A
header line says it is copyrighted and for personal use. Generated by a
script kept with the private tools, never committed to a public repository.

## Part 4 — the catalog

### Repository

New CatholicOS repository **CBPPEDR**, *Common Biblical Persons, Places and
Events Data Repository* (name is my proposal), laid out like CBTUDR. Creating
it on GitHub is outward-facing: confirm with the user first.

### Entity types and identifiers

Three types, three catalogs, three indices:

| Type | Prefix | Example |
|---|---|---|
| person (also groups: tribes, peoples) | `bpers:` | `bpers:philippus.mariamnes-filius` |
| place (cities, regions, rivers, mountains) | `bplace:` | `bplace:libna.urbs` |
| event | `bevent:` | `bevent:exilium-babylonicum` |

The slug is the Nova Vulgata Latin name, as CBTUDR uses the Nova Vulgata,
plus a short Latin discriminator when the name is shared. The QID is a
field, never the key: many biblical persons have no Wikidata item, and the
user plans to move from Wikidata to a Cathopedia Wikibase. All identifiers
are drafts until `v1.0.0`. Whether tribes and peoples are persons or a
fourth type is left to the builder to propose; default: persons with
`kind: "group"`.

### Coverage and scope (decided by the user)

- **Complete coverage.** The catalog aims at every person, place and event
  of the Bible, not only the dictionary's. A name the dictionary lacks
  (found by the STEPBible check, or by the Jerusalem Bible's index and
  notes) becomes an entry of ours, built from the verse that attests it,
  with that verse as its evidence. STEPBible only points to it; none of its
  data is copied.
- **Who is an entry:**
  - Christ, the named angels (Michael, Gabriel, Raphael) and Satan are
    person entries. God and the Holy Spirit are not catalogued for linking.
  - Pagan gods (Baal, Dagon, Moloch) are person entries of `kind: "deity"`.
  - A name that is a person, a people and a land (Israel, Edom, Judah,
    Moab) is three entries, linked to one another (eponym of; people of;
    land of), because the text uses each sense separately.
  - Persons never named in the Bible but needed as relation targets
    (Mariamne II, Aziz of Emesa) are entries with empty `attested`; their
    slug uses the Latin form from Josephus or Wikidata, and `kind` says
    they are extra-biblical.
- **Events:** only those the Bible narrates or refers to; the table's
  world-history column is left out unless the Bible refers to the event.
  Grain: whole episodes ("the Exodus", "the Babylonian exile") plus named
  battles and assemblies (Aphek, Gilboa, the Council of Jerusalem in
  Acts 15); smaller incidents (each plague) are parts of an episode
  (`part_of`), not entries.
- **Dictionary numbering is not always homonymy:** some numbered senses
  are sub-sections (FILISTEI 1–5 are periods of history). Splitting senses
  into entries is therefore a reviewed step, not automatic.
- **Dates (my call):** an event carries the date the chronological table
  gives, as a field marked approximate, with the table as its evidence.

### Entry content (public)

- `id`, `type`, `kind` (individual, group; city, region, …; event kinds)
- `names`: Latin (Nova Vulgata), Italian (CEI 2008 form), English where
  known; variants
- `description`: a few words of our own per language, to tell homonyms
  apart ("son of Herod the Great and Mariamne II; first husband of
  Herodias"); written by us, never copied
- `attested`: CBTUDR units where the sources place the entry
- `relations`: to other entries (father, mother, spouse, child, sibling;
  place of; part of; participant in), each with its evidence
- `qid` and `qid_status`: auto, reviewed, unresolved (CRMEDR's statuses)
- `evidence`: citations by location: dictionary headword + sense number;
  Jerusalem Bible note (book, reference, PDF page); index-of-notes entry;
  family-tree number; STEPBible check result

### Building the baseline (approach A)

1. **Dictionary senses.** Split the TEI into entries (separated by
   `milestone unit="separator"`; headword in `head n="2|3"` or in a leading
   `<p>WORD.`; subsection heads such as "I. NELL'ANTICO TESTAMENTO" are not
   headwords). Each numbered sense (`p n="1."`) is a candidate entry. Classify
   each sense as person, place, event or none (topics such as LEVANTE are
   dropped); the builder chooses rules plus review, and may use a classifier
   for suggestions, reviewed by a person. Extract its verse references and
   its `↗` cross-references as relations.
2. **Jerusalem Bible evidence.** The *Indice alfabetico delle note più
   importanti* (744 entries; names in capitals with references and `v.` see-
   also) maps names to the notes that discuss them. Notes that say who a
   person is or is not split or confirm senses: the note on Mt 14,3 identifies
   Herodias's first husband as a son of Herod the Great by Mariamne II, not
   Philip the tetrarch. The
   *Dinastie Asmonea e Erodiana* tree gives numbered persons and relations.
   The *Tavola cronologica* is the source of the events baseline, with the
   dictionary's event headwords.
3. **Merging.** Join dictionary senses, index entries and tree persons into
   entries; each disagreement between sources is a review item, decided by
   the user.
4. **Wikidata.** Match each entry to a QID only on strong evidence (label
   plus attested references or relations agreeing); otherwise `unresolved`.
   Results cached locally, so the slow service is queried once per entry.
5. **STEPBible check.** Compare with STEPBible's TIPNR proper-names list
   (CC BY 4.0) to find persons and places the baseline misses or merges;
   the result is a report and review items, and no STEPBible data enters the
   repository.

### Review

As in CBTUDR and CRMEDR, review items go to the user; the format (a report
in `docs/` with a decisions file, or the BibleGet review screen) is left to
the builder, the simpler first. **My calls:** review comes in batches of a
known size, one letter of the dictionary (or one book, for verse-built
entries) at a time; the automatic rules are strict, so fewer items reach
the user; the catalog is published as a draft with unresolved items marked,
as CBTUDR is, without waiting for every item.

## Approaches considered

- **A. From the dictionary (chosen):** dictionary senses as the skeleton,
  Jerusalem Bible notes, index and tree to confirm or split, chronological
  table for events, Wikidata after. Misses minor names the dictionary lacks;
  the STEPBible check finds them.
- **B. From the Bible text:** every capitalised name in an edition,
  clustered, then disambiguated. More complete but noisy; clustering and
  resolving it is much more work. Not chosen.
- **C. From an existing open list (STEPBible TIPNR):** already
  disambiguated, but CC BY, which does not fit CC0 data. Used only as a
  check (step 5).

## Left to the builder

The OCR heuristics and batch sizes; the Italian word list; the sense
classifier; the JSON layout of the catalogs and registry; the review format;
script names. Each is recorded in the plan.
