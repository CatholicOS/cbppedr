# Vocabulary

Every controlled term CBPPEDR uses, what it means, and when it may be used. The file formats are in [schema.md](schema.md).

## How sure is a statement?

A catalog statement says **where an entry is** (its verses) or **who it is** (its identity with another entry). Each one is recorded at one of three levels of certainty, and never at a higher one than its evidence allows:

| Level | About verses | About identity | Rests on |
|---|---|---|---|
| **Established** | `attested` | `same_as` | the Bible text itself (`nv:` evidence), or an authoritative source that states it as fact |
| **Proposed** | conjecture `possibly_attested_at` | conjecture `possibly_same_as` | an authoritative source that offers it as probable or possible, or that is contradicted by another |
| **Lead** | conjecture `possibly_attested_at` | conjecture `possibly_same_as` | only non-authoritative sources (STEPBible's TIPNR, a reviewer's inference): status `unsupported` |

A statement at a lower level never changes one at a higher level. Rule of the whole catalog: **better unidentified than misidentified.**

There are 31 `same_as` links, each stated one way. 21 rest on the text (`nv:` evidence: a verse that equates the names, a parallel passage with the same parents, office and events, a renaming), 13 of them also cited to the dictionary; the other 10 rest on the dictionary alone, which states each as fact ("identico", "è un'altra forma di", "va identificata"). Every link the dictionary only hedged ("forse", "probabilmente", "è più probabile"), or that an authoritative source doubts, is a conjecture instead: 16 were moved there on review, among them Ben-hadad I = the Ben-hadad of Ahab's wars (two kings, say the Jerusalem Bible's notes), Seba = Sheba, Riblah on the border = Riblah of Hamath, Thaddaeus = Judas son of James. One link was removed outright, because it pointed at the wrong person (Heled, David's warrior, = the Heldai of Zech 6, whom the dictionary itself tells apart), and three that were stated in both directions now are stated once.

## Identifiers

| Prefix | Meaning | Example |
|---|---|---|
| `bpers:` | a person or group of persons (a people, a tribe, a family, a deity) | `bpers:philippus.tetrarcha` |
| `bplace:` | a place | `bplace:lobna.urbs` |
| `bevent:` | an event | `bevent:exilium-babylonicum` |
| `anon:` | a provisional key for a person no edition names; not a catalog id (see [Unnamed persons](#unnamed-persons)) | `anon:lot.uxor` |
| `btu:` | a [CBTUDR](https://github.com/CatholicOS/cbtudr) textual unit: a verse, edition-independent | `btu:2reg.2.24` |

An id is the Nova Vulgata Latin name as a lowercase ASCII slug (words joined by `-`), plus `.` and a short Latin discriminator when anyone else in the Bible bears the name. Ids are drafts until `v1.0.0`.

## Types and kinds

`type` is the catalog an entry belongs to; `kind` refines it.

| type | kind | Meaning |
|---|---|---|
| person | `individual` | one human being |
| | `group` | a people, tribe, clan, family or other collective (the Amalekites, the Levites of Kohath) |
| | `deity` | a god or goddess worshipped in the Bible's world (Baal, Molech) |
| | `extra-biblical` | a historical person the Bible does not name but the sources need (Mariamne II in the Herodian tree) |
| place | `city` | a town, village or city |
| | `region` | a land, territory or district |
| | `mountain` | a mountain, hill or range |
| | `river` | a river, wadi or stream |
| | `sea` | a sea or lake |
| | `valley` | a valley or plain |
| | `desert` | a wilderness |
| | `site` | a named spot: a spring, well, stone, field, threshing floor, camp |
| | `building` | a structure: the Temple, a gate, a tower, a palace |
| | `other` | none of the above |
| event | `episode` | a narrated occurrence (the Babylonian exile) |
| | `battle` | a battle or campaign |
| | `assembly` | a gathering (a council) |
| | `other` | none of the above |

## Verses: `attested` and `labels`

- **attested**: the units where the entry appears, by name or by a designation the context ties to it. Verses that refer to the entry only by a pronoun, or not at all, are not attested (they were removed on review: `data/curated/unattested.json`). `attested` lists where the sources place the entry; it is not yet every mention of it.
- **labels**: for an attested unit where the entry is not called by one of its catalogued names, how each edition calls it there. `as` is one of:
  - `name`: another name the entry bears (Cephas for Peter, Saul for Paul, Zion for Jerusalem);
  - `designation`: a title, office, kinship term or description the context ties to the entry ("the king of Israel" in the Joram narrative, "the man of God" for Elisha).

  `editions` maps each edition that prints the label to the label as printed (at most six words). An edition missing from it does not name or designate the entry in that verse.

### Editions

| Code | Edition | Language |
|---|---|---|
| `NVBSE` | Nova Vulgata (Bibliorum Sacrorum Editio) | Latin |
| `VGCL` | Vulgata Clementina | Latin |
| `CEI2008` | La Sacra Bibbia CEI 2008 | Italian |
| `NABRE` | New American Bible Revised Edition | English |
| `DRB` | Douay-Rheims Bible | English |

## Relations

Stated one way, from the entry (the *source*) to `target`, as the evidence states it; the inverse is not repeated. Every relation carries its evidence.

| rel | Meaning: the entry (source) … | Source | Target | Example |
|---|---|---|---|---|
| `child_of` | is a son or daughter of the target | person | person | Aaron `child_of` Jochebed |
| `parent_of` | is a father or mother of the target | person | person | Ahasbai `parent_of` Eliphelet |
| `spouse_of` | is a husband or wife of the target | person | person | Abijah `spouse_of` Hezron |
| `sibling_of` | is a brother or sister of the target | person | person | Aaron `sibling_of` Moses |
| `eponym_of` | gave its name to the target, a people or a place | person | any | Amalek `eponym_of` the Amalekites |
| `people_of` | (a people) is the people of the target land | person | place | the Assyrians `people_of` Assyria |
| `land_of` | (a land) is the land of the target people | place | person | Ammon `land_of` the Ammonites |
| `located_in` | lies in the target (a town in a region), or lives or rules there | any | place | Accad `located_in` Shinar |
| `part_of` | is a part of the target: a wall of a city, a peak of a range, a clan of a tribe | any | same type | the Broad Wall `part_of` Jerusalem |
| `participant` | (an event) has the target among its participants | event | person | David's census `participant` David |
| `same_as` | is the same person or place as the target, which the catalog keeps as a separate entry | any | same type | Adonijah the signer `same_as` Adonikam |

`build_catalog.py` resolves a relation only when its source and target have these types (otherwise it is reported as unresolved), and `validate.py` checks them again.

- **same_as** links two entries the catalog has kept apart, because the sources treated them apart (two dictionary headwords, two name forms), when the evidence establishes they are one: the text (a parallel passage with the same parents, office and events, e.g. Hoshea renamed Joshua in Nm 13:16) or an authoritative source stating it as fact. Both entries keep their ids; neither is deleted.
- **possibly_same_as** is not a relation: it is a [conjecture](#conjectures), for an identity the text does not establish.

### Evidence

Locations, never text.

| Prefix | Source | Format |
|---|---|---|
| `nv:` | a verse of the Nova Vulgata, where the Bible text alone establishes the statement (a patronym, an office, a place, a time) | `nv:btu:ne.12.36` |
| `ndeib:` | a sense of the *Nuovo Dizionario Enciclopedico Illustrato della Bibbia* (Piemme 2005) | `ndeib:FILIPPO#1`; a headword without numbered senses has no `#` (`ndeib:IS-BAAL`); `~n` numbers a repeated headword |
| `bj:herodian-tree` | the Jerusalem Bible's Hasmonean and Herodian family tree | `bj:herodian-tree` |
| `bj:note:`, `bj:intro:` | a note or a book introduction of the Jerusalem Bible that states the fact (an identity the text implies but does not state) | `bj:note:At.12,12#p2648` (John Mark is the Mark of Col 4:10, Phlm 24, 2 Tim 4:11, 1 Pet 5:13) |

STEPBible's TIPNR may point to a verse or an identity, but is never itself evidence.

## Conjectures

Identities and attestations the Bible text does not settle but someone proposes. Each is recorded on the entry with every opinion for or against it.

| Term | Meaning |
|---|---|
| `possibly_same_as` | the entry may be the same as `target` (another entry) |
| `possibly_attested_at` | a figure in `unit`, unnamed or named otherwise, may be the entry (Ishvi of 1 Sam 14:49 may be Ishbaal) |

**Opinions.** `by`: where the opinion is (a source location); `says`: the opinion's stance; `summary`: a few words of our own.

| says | The source … |
|---|---|
| `identifies` | states the identification |
| `suggests` | offers it as probable or possible |
| `doubts` | calls it uncertain or unlikely |
| `rejects` | denies it |

**Sources** (`data/curated/sources.json`): whose opinion it is, and its weight.

| Source | Whose opinion | Locator | Authority |
|---|---|---|---|
| `bj` | *La Bibbia di Gerusalemme* (EDB 2011): its notes and book introductions | `bj:note:<Book>.<chapter,verse>#p<page>` (`bj:note:1Sam.14,49#p597`), `bj:intro:<section>#p<page>` | authoritative |
| `ndeib` | the *Nuovo Dizionario Enciclopedico Illustrato della Bibbia* | `ndeib:<KEY>`: the headword, with `#<sense>` where the dictionary numbers its senses (`ndeib:IS-BAAL`, `ndeib:FILIPPO#1`) | authoritative |
| `tipnr` | STEPBible's TIPNR, which cites no references | `tipnr:Ishvi@1Sa.14.49` | non-authoritative |
| `reviewer` | a CBPPEDR reviewer's inference from the text | `reviewer:round2` | non-authoritative |

A source is **authoritative** when it is a published scholarly work, cited by a location a reader can check. A claim with no reference behind it is **non-authoritative**: it is kept as a lead until an authoritative source is found.

**Status**, computed by the build from the authoritative opinions only:

| status | Meaning |
|---|---|
| `supported` | an authoritative source identifies or suggests it, and none doubts or rejects it |
| `disputed` | authoritative sources disagree |
| `rejected` | an authoritative source rejects it, and none is for it |
| `doubted` | authoritative sources only doubt it |
| `unsupported` | no authoritative source has spoken: a lead only |

## Wikidata

| qid_status | Meaning |
|---|---|
| `auto` | matched by the strict automatic rule (a candidate of the class "human biblical figure", or the only fitting, explicitly biblical candidate) |
| `reviewed` | set by a person |
| `unresolved` | no item accepted; `candidates` in `data/curated/qids.json` are kept for review, `rejected` lists items judged wrong |

## Other markers

- **review: `uncertain`**: the reviewer could not settle the identity from the source (for example, whether two senses are one person).

## Unnamed persons

Persons the Bible mentions or presupposes but no edition names, kept outside the catalogs (`data/unnamed.json`).

| Term | Meaning |
|---|---|
| `anon:<entry>.<role>` | provisional key: the catalog entry the person is tied to, and a Latin role (`anon:lot.uxor`, `anon:pharao-oppressionis.filia`) |
| `attested` | units that mention or designate the person |
| `implied_by` | units whose wording presupposes the person without mentioning them ("he took another wife" presupposes a first one) |
| `tie` | `{rel, target}`: `spouse_of`, `child_of`, `parent_of` or `sibling_of` a catalog entry |
| `named_in` | editions that name the person (none yet); when one does, the person moves into the catalog |
| `editions_checked` | the editions searched for a name |

A person only biologically implied (every man's father) is not recorded.
