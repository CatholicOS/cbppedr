"""Find descriptions that follow their source's wording: our descriptions must be our own words.

Compares each entry's Italian description with the dictionary senses it cites (private text)
and lists those sharing a run of LIMIT or more consecutive words. Nothing of the source is printed.

Usage: python overlap.py [LIMIT]   (default 6; exit 1 if any description reaches it)
"""

from __future__ import annotations

import json
import re
import sys

from build_catalog import PRIVATE, ROOT

WORD = re.compile(r"[^\W\d_]+")


def _words(text: str) -> list[str]:
    return [w.lower() for w in WORD.findall(text)]


def longest_shared_run(a: str, b: str) -> int:
    x, y = _words(a), _words(b)
    best, prev = 0, [0] * (len(y) + 1)
    for i in range(1, len(x) + 1):
        cur = [0] * (len(y) + 1)
        for j in range(1, len(y) + 1):
            if x[i - 1] == y[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def main() -> int:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    texts = {}
    for line in (PRIVATE / "ndeib-senses.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            s = json.loads(line)
            texts[s["key"]] = s["text"]
    hits = []
    for name in ("persons", "places", "events"):
        for eid, e in json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))["entries"].items():
            d = (e.get("description") or {}).get("it") or ""
            keys = [ev.split(":", 1)[1] for ev in e.get("evidence", []) if ev.startswith("ndeib:")]
            run = max((longest_shared_run(d, texts.get(k, "")) for k in keys), default=0)
            if run >= limit:
                hits.append((run, eid))
    for run, eid in sorted(hits, reverse=True):
        print(f"{run}\t{eid}")
    print(f"{len(hits)} descriptions share {limit}+ consecutive words with their source")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
