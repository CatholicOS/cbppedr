# CBPPEDR

The home of the **Common Biblical Persons, Places and Events Data Repository**, curated by the
**Catholic Engineering Task Force** of the
[Catholic Digital Commons Foundation](https://github.com/CatholicOS).

## What is CBPPEDR?

Many people and places in the Bible share a name. There are four Philips in the New Testament, and Libna is both a city of Judah and a camp in the desert. A Bible application that links names to an index needs to know which one each passage means.

CBPPEDR gives each **person**, **place** and **event** of the Bible a stable identifier, with:

- its names in Latin (the Nova Vulgata's form), Italian and English;
- a short description of our own, written to tell it apart from its homonyms;
- the [CBTUDR](https://github.com/CatholicOS/cbtudr) textual units where it appears, so the same entry serves every Bible edition;
- its relations to other entries (parent, spouse, child; place of; part of);
- its Wikidata item, where one passes a strict automatic rule or a reviewer's decision;
- the evidence for all of the above, cited by location.

```text
bpers:philippus.herodiadis-maritus   Philip, son of Herod the Great, first husband of Herodias (Mt 14:3)
bpers:philippus.tetrarcha            Philip, son of Herod the Great, tetrarch of Ituraea (Lk 3:1)
bplace:lobna.urbs                    Libnah, a city of the Shephelah
bplace:lebna.castra                  Libnah, a camp of Israel in the desert
bevent:exilium-babylonicum           the Babylonian exile
```

The three types have separate catalogs, so an application can build a separate index of each.

**The rule is: better unidentified than misidentified.** Two persons are merged, a person is split, or a Wikidata item is attached only on clear evidence or by a reviewer.

## Sources

The baseline is built with two printed works as evidence: the *Nuovo Dizionario Enciclopedico Illustrato della Bibbia* (Piemme 2005) and the notes and appendices of *La Bibbia di Gerusalemme* (EDB 2011). Both are under copyright: **this repository holds no text from them**, only facts (names, identities, relations, verse references), and cites them by location (headword and sense, note and page). STEPBible's TIPNR list (CC BY 4.0) is used only to find names the baseline misses; none of its data is included.

All identifiers are **drafts pending committee review** until release `v1.0.0`.

## Repository contents

| Path | What it holds |
|---|---|
| `data/persons.json`, `data/places.json`, `data/events.json` | the three catalogs |
| `data/unnamed.json` | persons the Bible mentions but no edition names, kept apart until one does |
| `data/curated/` | the reviewed decisions the catalogs are built from: senses, per-entity verse lists and corrections, entries curated by hand, the Herodian tree's relations, Wikidata items |
| `registry/` | the catalogs as readable tables, generated |
| `docs/vocabulary.md` | every term the data uses: types and kinds, relations (`same_as`…), labels, conjectures (`possibly_same_as`…), evidence and sources, statuses |
| `docs/schema.md` | the format of every file, the build report and the pipeline |
| `docs/build-report.md`, `docs/stepbible-gaps.md` | what the last build merged or left open, and the names it still misses |
| `scripts/` | the build, validation, Wikidata matching and report scripts (Python, `python -m unittest`) |

## Status

Baseline (round 1), built from the dictionary's headwords, the Jerusalem Bible's Herodian tree, and the persons the dictionary covers only in a book's article (the prophets of the Twelve, Ezekiel, Matthew, Judith, Tobit and Tobias), curated by hand. 49 headwords listing many bearers of one name (Shemaiah, Shimei, Hananiah, Jonathan…), whose first review kept only some, were reviewed again for the rest:
3,171 persons, 1,094 places and 22 events (with round 2 so far), validated with no problems. 778 entries have a Wikidata
item matched automatically (11 more set by a reviewer): a candidate of the class "human biblical figure", or the only fitting candidate
whose description is explicitly biblical. The rest list their candidates for review. A relation
is resolved only by its sense key, or by a name no homonym shares. The others stay unresolved,
not guessed.

Round 2 will cover:

- the names TIPNR has and the baseline lacks (`docs/stepbible-gaps.md`): done but for 448: each name checked against the Nova Vulgata text itself (`nv:` evidence), 1,911 new entries and 119 extended; most of the rest are TIPNR individuals the Nova Vulgata does not name (an unnamed wife or son, a common noun such as "the guard"), or already covered under the Nova Vulgata's verse numbering;
- verses that a dictionary citation attached to an entry but that do not refer to it: done for every verse no edition names the entry in, by an audit against five editions' text (`scripts/audit_attested.py`) and a verse-by-verse review. 15,579 verses are removed (`data/curated/unattested.json`): whole chapters cited for one person, a neighbouring headword's verses taken for the previous one (Netophah got the verses on snow, the Italian *neve*), mistyped references (Job at Is 14:14 for Ez 14:14, now corrected), and verses that refer to their entry only by a pronoun. A verse that designates its entry by a title the context ties to it ("the king of Israel" in the Joram narrative) is kept;
- other names and designations: recorded per verse and per edition (`labels`: Cephas for Peter, "the king of Israel" for Joram, with the editions that print them; 1,138 verses), so an application can keep only what its edition says. Probable duplicates the text identifies are linked by `same_as` (Hoshea/Joshua, the two Rabbahs, Shallum/Jehoahaz);
- scholarly conjectures: 152 identities and attestations the text does not settle (Ishvi of 1 Sam 14:49 as Ishbaal, Thaddaeus as Judas son of James, the beloved disciple as John), each with the opinions for and against it and whose they are - the Jerusalem Bible's notes and the dictionary (authoritative), STEPBible's TIPNR and reviewers' inferences (leads only); 77 supported, 12 disputed, 7 rejected, 18 doubted, 38 leads. Verses attested only on such a conjecture were moved to it;
- persons the Bible mentions but no edition names (Lot's wife, Peter's mother-in-law): kept apart in `data/unnamed.json` under provisional `anon:` keys, until an edition or source names them;
- the 1,069 relations left unresolved, and the 260 entries marked uncertain;
- evidence keys under the wrong headword, where the dictionary's parser missed a headword
  (e.g. a sense of Nebuchadnezzar cited as NABU);
- reviewing the Wikidata candidates. Many well-known entries (Jerusalem, the Herods, the Philips) have the right item among their candidates but did not pass the automatic rule.

## Licences

The licensing follows the proposal open in every CDCF registry (e.g. [CatholicOS/crpdr#2](https://github.com/CatholicOS/crpdr/issues/2)):

| Part | Licence |
|---|---|
| `data/`: identifiers, names, relations, unit lists | [CC0 1.0](LICENSE-CC0) |
| `docs/` and `registry/` | [CC BY-ND 4.0](LICENSE) |
| `scripts/` | [Apache 2.0](scripts/LICENSE) |
