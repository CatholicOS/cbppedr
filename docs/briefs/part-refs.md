# Brief: give each entity of a multi-entity sense its own verse references

Some senses of the Italian Bible dictionary describe several entities at once:
four men called Abijah, or Benjamin the son of Jacob, the tribe and its
territory. Each entity already has its identifier. What is missing is which of the
sense's verse references belong to which entity.

**Copyright:** the sense text is copyrighted; your output holds only identifiers
and reference numbers. Write only your output file; no git.

## Input

`~/development/BibleGet-I-O/data-local/cbppedr/batches/parts-N.jsonl`, one sense
per line: `key`, `parts` (each `id`, Italian name, short English description),
`text` (the sense), `refs` (the verse references found in the text, in order:
`i` = number, `printed` = as written, `at` = character offset in `text`).

## Decide

For each reference `i`, the entity (or entities) it attests: usually the person or
place whose description it follows or is embedded in. A reference cited only for
comparison or background that attests none of the entities (e.g. a parallel
passage about someone else) goes to none.

- A person and the tribe or land named after him: references about the ancestor
  himself go to the person; about the tribe's members, territory, cities, to the
  group or land as the text indicates.
- When you can't tell which of two entities a reference attests, give it to both.

## Output

`~/development/BibleGet-I-O/data-local/cbppedr/review/parts-N.jsonl`, one line per
input sense:

```json
{"key": "ABIA", "assign": {"bpers:abia.rex-iudae": [0, 1, 2], "bpers:abia.samuelis-filius": [3]}, "none": [4]}
```

Every reference number of the sense appears at least once (in `assign` or
`none`). Every part id appears in `assign`, possibly with `[]` when the text cites
no verse for it.

Report at the end: senses done, and any where the text did not let you assign.
