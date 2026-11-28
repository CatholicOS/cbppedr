"""Card details for the entries whose Wikidata match was reviewed or adjudicated.

For each such entry: an image (Wikidata P18, first value, credited from Wikimedia Commons: author as plain
text, licence name and URL), the titles of its Wikipedia articles (la it en es fr de pt) and, for a place with
exactly one P625 statement, its coordinates, unless that statement has a sourcing-circumstances (P1480)
qualifier (a conjectural site) or the place is in data/curated/disputed_sites.json (a site nobody has
identified: no pin). An automatic match is not enough: a wrong image or map on a card is worse than none. An
entry with nothing to show is left out; an image without a licence on Commons is too. A placeholder author
("Unknown author", "Anonymous") is no author.

Wikidata and Commons are queried through wikidata.py's cached, rate-limited client (generic User-Agent).

Usage: python details.py   (writes data/details.json)
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import wikidata

ROOT = Path(__file__).resolve().parent.parent
COMMONS = "https://commons.wikimedia.org/w/api.php"
LANGS = ("la", "it", "en", "es", "fr", "de", "pt")
MAX_AUTHOR = 200
SETTLED = ("reviewed", "adjudicated")
TAG = re.compile(r"<[^>]*>")
BLOCK = re.compile(r"<\s*(style|script)\b.*?<\s*/\s*\1\s*>", re.IGNORECASE | re.DOTALL)
PLACEHOLDER = re.compile(r"unknown author|unknown artist|unknown source|anonymous", re.IGNORECASE)
# what is left of a credit that credits no one: "None", "unknown illuminator", "no idea …", "Own work", a bare URL
NO_CREDIT = re.compile(r"none|unknown(\s+\w+)?|no idea\b.*|own work|https?://\S+|[\W\d_]*", re.IGNORECASE | re.DOTALL)
OWN_WORK = re.compile(r"^own work\s*[,;:]\s*", re.IGNORECASE)
ASSUMED = re.compile(r"^No machine-readable author provided\.\s*(.+?)\s+assumed \(based on copyright claims\)\.?$")
MIN_HALF = 4
LABELS = re.compile(r"\s*\b(?:Title|Source)\b.*$", re.DOTALL)
DISPUTED = ROOT / "data/curated/disputed_sites.json"
BREAK = re.compile(r"<\s*/?\s*(br|p|div|li|ul|ol|tr|td)\b[^>]*>", re.IGNORECASE)


def plain_text(value: str) -> str:
    """Markup removed: tags dropped, entities unescaped, whitespace collapsed."""
    return " ".join(html.unescape(TAG.sub("", BREAK.sub(" ", BLOCK.sub(" ", value)))).split())


def _first_p18(item: dict) -> str | None:
    for c in item.get("claims", {}).get("P18", []):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, str) and v:
            return v
    return None


def _coords(item: dict) -> dict | None:
    claims = item.get("claims", {}).get("P625", [])
    if len(claims) != 1 or claims[0].get("qualifiers", {}).get("P1480"):
        return None
    v = claims[0].get("mainsnak", {}).get("datavalue", {}).get("value")
    if isinstance(v, dict) and isinstance(v.get("latitude"), (int, float)) and isinstance(v.get("longitude"), (int, float)):
        return {"lat": v["latitude"], "lon": v["longitude"]}
    return None


def _usable(text: str) -> bool:
    """Plain credit text, not a licence template's leftovers (CSS, "Public domain" repeated, ...)."""
    return bool(text) and len(text) <= MAX_AUTHOR and not re.search(r"[{};]", text) and "public domain" not in text.lower()


def _half(text: str) -> str | None:
    for sep in ("", " "):
        n = len(text) - len(sep)
        if n >= 2 * MIN_HALF and n % 2 == 0 and text[:n // 2] + sep + text[:n // 2] == text:
            return text[:n // 2]
    return None


def _halved(text: str) -> str:
    """A credit pasted twice ("Ann DoeAnn Doe", "Ann Doe Ann Doe") as one; a text that merely repeats a
    shorter run ("xxxx") is left as it is."""
    half = _half(text)
    return half if half is not None and _half(half) is None else text


def credit(text: str) -> str:
    """A credit cleaned: cut before a run of "Title"/"Source" labels, doubled halves collapsed,
    placeholders ("Unknown author", "Anonymous", "Unknown source") removed, Commons' "No machine-readable
    author provided. X assumed …" read as X and a leading "Own work," dropped; "" when nothing that credits
    anyone remains ("None", "[1]", "unknown illuminator", "no idea …", "Own work", a bare URL)."""
    text = _halved(LABELS.sub("", text).strip())
    text = OWN_WORK.sub("", ASSUMED.sub(r"\1", text))
    text = " ".join(PLACEHOLDER.sub(" ", text).split())
    if text.startswith("(") and text.endswith(")") and text.count("(") == 1 and text.count(")") == 1:
        text = text[1:-1].strip()  # what a placeholder qualified: "Anonymous (Meister 3)"
    return "" if NO_CREDIT.fullmatch(text) else text


def author_of(meta: dict) -> str:
    """The credit: the uploader's Artist, else Credit, else Attribution; "" when none is usable."""
    for key in ("Artist", "Credit", "Attribution"):
        text = credit(plain_text(meta.get(key, {}).get("value", "")))
        if _usable(text):
            return text
    return ""


def _image(name: str, commons: dict | None) -> dict | None:
    meta = commons or {}
    lic = plain_text(meta.get("LicenseShortName", {}).get("value", ""))
    if not lic:
        return None
    author = author_of(meta)
    if not author and lic.lower().startswith("cc by"):
        return None  # attribution is the licence's condition: without an author it cannot be met
    img = {"file": name, "author": author, "license": lic}
    url = meta.get("LicenseUrl", {}).get("value", "").strip()
    if re.match(r"^https?://\S+$", url):
        img["license_url"] = url
    return {k: v for k, v in img.items() if v}


def detail(entity: dict, wikidata_item: dict, commons: dict | None, disputed: bool = False) -> dict | None:
    if entity.get("qid_status") not in SETTLED or not entity.get("qid"):
        return None
    out: dict = {}
    name = _first_p18(wikidata_item)
    image = _image(name, commons) if name else None
    if image:
        out["image"] = image
    links = wikidata_item.get("sitelinks", {})
    wiki = {lang: links[f"{lang}wiki"]["title"] for lang in LANGS if links.get(f"{lang}wiki", {}).get("title")}
    if wiki:
        out["wikipedia"] = wiki
    coords = _coords(wikidata_item) if entity.get("type") == "place" and not disputed else None
    if coords:
        out["coords"] = coords
    return out or None


def fetch_items(qids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(qids), 50):
        batch = sorted(qids[i:i + 50])
        params = {"action": "wbgetentities", "ids": "|".join(batch), "props": "claims|sitelinks"}
        data = wikidata._call(params)
        if not set(batch) <= set(data.get("entities", {})):  # cache file names are truncated: batches can collide
            data = wikidata._call(params, refresh=True)
        out.update(data.get("entities", {}))
    return out


def _title(name: str) -> str:
    """A Commons file name as MediaWiki normalises it: underscores as spaces, first letter upper-case."""
    name = " ".join(name.replace("_", " ").split())
    return name[:1].upper() + name[1:]


def _commons_meta(data: dict, name: str) -> dict | None:
    for page in data.get("query", {}).get("pages", {}).values():
        info = page.get("imageinfo") or []
        if info and _title(page.get("title", "")) == "File:" + _title(name):
            return info[0].get("extmetadata")
    return None


def fetch_commons(name: str) -> dict | None:
    """The file's extmetadata; refetched once when the (cached) answer is for another file, else None."""
    params = {"action": "query", "titles": f"File:{name}", "prop": "imageinfo", "iiprop": "extmetadata"}
    meta = _commons_meta(wikidata._call(params, COMMONS), name)
    if meta is None:
        meta = _commons_meta(wikidata._call(params, COMMONS, refresh=True), name)
    return meta


def main() -> int:
    entries = {}
    for n in ("persons", "places"):
        entries.update(json.loads((ROOT / "data" / f"{n}.json").read_text(encoding="utf-8"))["entries"])
    chosen = {eid: e for eid, e in entries.items() if e.get("qid_status") in SETTLED and e.get("qid")}
    disputed = set(json.loads(DISPUTED.read_text(encoding="utf-8"))["entries"]) if DISPUTED.exists() else set()
    try:
        items = fetch_items(sorted({e["qid"] for e in chosen.values()}))
        details = {}
        for eid in sorted(chosen):
            item = items.get(chosen[eid]["qid"], {})
            name = _first_p18(item)
            d = detail(chosen[eid], item, fetch_commons(name) if name else None, eid in disputed)
            if d:
                details[eid] = d
    except RuntimeError as err:
        print(err, file=sys.stderr)
        return 1
    doc = {"$comment": "Card details for the entries whose Wikidata match was reviewed or adjudicated: an image "
                       "(Wikidata P18, credited from Wikimedia Commons), Wikipedia titles and, for a place with one "
                       "P625 that is neither qualified as conjectural (P1480) nor a disputed site "
                       "(data/curated/disputed_sites.json), its coordinates. Generated by scripts/details.py.",
           "entries": details}
    (ROOT / "data/details.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(details)} entries with details")
    return 0


if __name__ == "__main__":
    sys.exit(main())
