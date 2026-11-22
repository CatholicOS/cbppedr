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
| `data/curated/` | the reviewed decisions the catalogs are built from: senses, per-entity verse lists and corrections, entries curated by hand, the Herodian tree's relations, Wikidata items |
| `registry/` | the catalogs as readable tables, generated |
| `docs/schema.md` | the format of an entry and the build pipeline |
| `docs/build-report.md`, `docs/stepbible-gaps.md` | what the last build merged or left open, and the names it still misses |
| `scripts/` | the build, validation, Wikidata matching and report scripts (Python, `python -m unittest`) |

## Status

Baseline (round 1), built from the dictionary's headwords, the Jerusalem Bible's Herodian tree, and the persons the dictionary covers only in a book's article (the prophets of the Twelve, Ezekiel, Matthew, Judith, Tobit and Tobias), curated by hand. 49 headwords listing many bearers of one name (Shemaiah, Shimei, Hananiah, Jonathan…), whose first review kept only some, were reviewed again for the rest:
1,712 persons, 708 places and 22 events, validated with no problems. 337 entries have a Wikidata
item matched automatically (2 more set by a reviewer): a candidate of the class "human biblical figure", or the only fitting candidate
whose description is explicitly biblical. The rest list their candidates for review. A relation
is resolved only by its sense key, or by a name no homonym shares. The others stay unresolved,
not guessed.

Round 2 will cover:

- the names TIPNR has and the baseline lacks (`docs/stepbible-gaps.md`): begun with the 118 names TIPNR cites in six or more verses, each established from the Nova Vulgata text itself (`nv:` evidence); the rest remain;
- verses that a dictionary citation attached to an entry but that do not name it: begun with an audit against five editions' text (`scripts/audit_attested.py`). The 8,058 verses in passages that never name their entry were reviewed verse by verse, and, with 104 verses two homonyms claimed, 7,638 removed (`data/curated/unattested.json`): whole chapters cited for one person, a neighbouring headword's verses taken for the previous one (Netophah got the verses on snow, the Italian *neve*), mistyped references (Job at Is 14:14 for Ez 14:14, now corrected). The verses that do not name their entry inside passages that do name it remain to be reviewed;
- other names an entry bears in the text (Saul for Paul, Cephas for Peter, Azariah for Abednego), not yet recorded, and probable duplicate entries the audit found (Joshua, Rabbah, Barnabas, Jehoahaz/Shallum);
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
