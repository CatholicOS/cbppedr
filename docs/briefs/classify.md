# Brief: classify dictionary senses into persons, places and events

CBPPEDR is a catalog of the persons, places and events of the Bible, each with a
stable identifier, so that a Bible reader can link a name in any edition to the
right index entry. Your batch holds senses of an Italian Bible dictionary. You
decide, for each, whether it is a person, a place, an event or neither, and
propose its entry.

**Copyright:** the senses are from a copyrighted dictionary. Your decisions must
contain **facts only**: names, kinds, relations, verse units, and descriptions
**in your own words** (never copy or paraphrase a sentence of the dictionary).
Write only your output file. Do not run git. Do not edit any other file.

## Input

`~/development/BibleGet-I-O/data-local/cbppedr/batches/senses-N.jsonl`, one sense
per line: `key` (`LEVI#1`; no `#` for an entry without numbered senses; `#0` is
the text before sense 1), `headword`, `sense`, `kind_guess` (a weak machine
guess), `units` (first 12 CBTUDR units the sense cites, e.g. `btu:gn.29.34`),
`n_units`, `xrefs` (names the dictionary links to), `lead` (first 900 characters).

Helpers (run from `~/development/CatholicOS_org/cbppedr/scripts`):
- `uv run -q --with lxml python lookup.py nv btu:gn.29.34` prints the Nova
  Vulgata Latin verse (to find the Latin form of a name);
- `uv run -q --with lxml python lookup.py notes btu:mt.14.3` prints the
  Jerusalem Bible's notes on that verse (often says who a person is, or is not).

## Decide

- **type**:
  - `person`: an individual named in the Bible; also groups (tribes, peoples,
    clans: `kind: group`), pagan gods (`kind: deity`), Christ, named angels,
    Satan. People who are not named in the Bible but are needed to place
    someone (e.g. Mariamne II) only if the sense is about them: `kind:
    extra-biblical`.
  - `place`: city, region, mountain, river, sea, valley, desert, a named site
    or building (the Temple, the pool of Siloam).
  - `event`: an episode the Bible narrates or refers to (the Exodus, the
    Babylonian exile), a named battle or assembly. Not a feast, institution,
    concept or book.
  - `none`: everything else (topics, objects, concepts, books of the Bible,
    feasts, animals, plants, institutions, scholarly subjects). **God and the
    Holy Spirit are `none`** (not catalogued for linking).
  - One name that is a person, a people and a land (Israel, Edom, Moab, Judah)
    is **separate entries**: use `parts` (below).
- **kind**: persons `individual|group|deity|extra-biblical`; places
  `city|region|mountain|river|sea|valley|desert|site|building|other`; events
  `episode|battle|assembly|other`.
- **id**: `bpers:` / `bplace:` / `bevent:` + slug. The slug is the **Nova
  Vulgata Latin** name (find it with `lookup.py nv` on a unit where the name
  appears), lowercase ASCII, accents removed, words joined with `-`
  (`bpers:iohannes-baptista`, `bplace:mare-mortuum`). When the headword has
  more than one sense of the same type, or the name is borne by several
  persons you know of, add `.` and a short Latin discriminator to **every**
  one of them: `bpers:levi.iacob-filius`, `bpers:levi.alphaei-filius`,
  `bplace:libna.urbs`, `bplace:libna.castra`. Events: a short Latin phrase
  (`bevent:exilium-babylonicum`).
- **latin**, **it**, **en**: the name in the Nova Vulgata, in the Italian CEI
  form (usually the headword in title case, with its accent: `Ioiakìm`), and
  the usual English form (NABRE/RSV).
- **descr_it**, **descr_en**: at most 12 words each, your own, enough to tell it
  from its homonyms ("figlio di Giacobbe e Lia, capostipite della tribù di
  Levi" / "son of Jacob and Leah, ancestor of the tribe of Levi").
- **relations**: what the sense states, as
  `{"rel": R, "target": "<Italian name>", "target_key": "<KEY if in your batch, else null>"}`
  with R one of `child_of`, `parent_of`, `spouse_of`, `sibling_of`,
  `eponym_of` (person → the people named after him), `people_of`, `land_of`,
  `located_in` (place → region), `part_of` (event → larger event),
  `participant` (event → person/people), `same_as` (this sense is the same
  entity as another key, e.g. a variant headword).
- **parts**: when one sense covers several entities (LEVI#3, two bearers of the
  name in Jesus' genealogy; ISRAELE = Jacob, the people, the land), give a list of
  entry objects (same fields as above, each with its own `id`) instead of one.
- **certain**: `true` if the identity is clear from the sense; `false` if you
  had to guess (e.g. whether two numbered senses are one person). Uncertain
  items will be reviewed by a person.

## Output

`~/development/BibleGet-I-O/data-local/cbppedr/review/classify-N.jsonl`, one line
per sense, every sense of the batch:

```json
{"key": "LEVI#1", "type": "person", "kind": "individual", "id": "bpers:levi.iacob-filius",
 "latin": "Levi", "it": "Levi", "en": "Levi",
 "descr_it": "figlio di Giacobbe e Lia, capostipite della tribù di Levi",
 "descr_en": "son of Jacob and Leah, ancestor of the tribe of Levi",
 "relations": [{"rel": "child_of", "target": "Giacobbe", "target_key": null},
               {"rel": "child_of", "target": "Lia", "target_key": null}],
 "parts": null, "certain": true, "note": ""}
{"key": "LEVANTE#1", "type": "none"}
```

For `none`, `{"key", "type": "none"}` is enough. Work through `none` quickly;
spend the time on persons and places. Write the file progressively (append
as you go) so nothing is lost.

Report at the end: counts by type, how many uncertain, and any patterns.
