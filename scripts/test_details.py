import unittest

from details import detail, plain_text
from validate import detail_problems


def item(claims=None, sitelinks=None):
    return {"claims": claims or {}, "sitelinks": {k: {"title": v} for k, v in (sitelinks or {}).items()}}


def p18(name):
    return [{"mainsnak": {"datavalue": {"value": name}}}]


def p625(lat, lon):
    return {"mainsnak": {"datavalue": {"value": {"latitude": lat, "longitude": lon}}}}


def entity(status="reviewed", typ="place"):
    return {"type": typ, "qid": "Q1", "qid_status": status}


META = {"Artist": {"value": "A <b>painter</b>"}, "LicenseShortName": {"value": "CC BY-SA 4.0"},
        "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"}}


class DetailsTest(unittest.TestCase):
    def test_only_reviewed_or_adjudicated(self):
        it = item({"P18": p18("A.jpg")}, {"enwiki": "A"})
        self.assertIsNone(detail(entity("auto"), it, META))
        self.assertIsNone(detail(entity("unresolved"), it, META))
        self.assertIsNotNone(detail(entity("reviewed"), it, META))
        self.assertIsNotNone(detail(entity("adjudicated"), it, META))

    def test_image_from_p18_with_commons_credit(self):
        d = detail(entity(), item({"P18": p18("First one.jpg") + p18("Second.jpg")}), META)
        self.assertEqual(d["image"], {"file": "First one.jpg", "author": "A painter", "license": "CC BY-SA 4.0",
                                      "license_url": "https://creativecommons.org/licenses/by-sa/4.0"})

    def test_license_url_omitted_unless_http(self):
        for url in (None, "javascript:alert(1)", ""):
            meta = {"Artist": {"value": "X"}, "LicenseShortName": {"value": "PD"}}
            if url is not None:
                meta["LicenseUrl"] = {"value": url}
            d = detail(entity(), item({"P18": p18("A.jpg")}), meta)
            self.assertNotIn("license_url", d["image"])

    def test_author_html_stripped(self):
        self.assertEqual(plain_text('<a href="x">Jan  &amp; Co</a>\n<span>Doe</span> &lt;b&gt;'), "Jan & Co Doe <b>")
        meta = {"Artist": {"value": '<bdi><a href="//x">Ann</a></bdi>, <i>1900</i>'}, "LicenseShortName": {"value": "PD"}}
        d = detail(entity(), item({"P18": p18("A.jpg")}), meta)
        self.assertEqual(d["image"]["author"], "Ann, 1900")

    def test_two_coordinates_give_none(self):
        self.assertIsNone(detail(entity(), item({"P625": [p625(1, 2), p625(3, 4)]}), None))
        d = detail(entity(), item({"P625": [p625(31.7, 35.2)]}), None)
        self.assertEqual(d["coords"], {"lat": 31.7, "lon": 35.2})

    def test_person_has_no_coords(self):
        self.assertIsNone(detail(entity(typ="person"), item({"P625": [p625(1, 2)]}), None))

    def test_wikipedia_titles_only_for_known_languages(self):
        d = detail(entity(), item(sitelinks={"itwiki": "Roma", "enwiki": "Rome", "ruwiki": "Рим", "commonswiki": "C",
                                             "lawiki": "Roma"}), None)
        self.assertEqual(d["wikipedia"], {"la": "Roma", "it": "Roma", "en": "Rome"})

    def test_empty_detail_omitted(self):
        self.assertIsNone(detail(entity(), item(), None))


class DetailProblemsTest(unittest.TestCase):
    ENT = {"bplace:a": entity("reviewed"), "bpers:b": entity("auto", "person"), "bpers:c": entity("adjudicated", "person")}

    def probs(self, entries):
        return detail_problems({"entries": entries}, self.ENT)

    def test_clean(self):
        self.assertEqual(self.probs({"bplace:a": {"coords": {"lat": 90, "lon": -180}, "wikipedia": {"it": "A"}}}), [])

    def test_unknown_id_and_gate(self):
        p = self.probs({"bplace:zz": {"wikipedia": {"it": "A"}}, "bpers:b": {"wikipedia": {"it": "A"}}})
        self.assertEqual(len(p), 2)

    def test_ranges_and_person_coords(self):
        self.assertTrue(self.probs({"bplace:a": {"coords": {"lat": 91, "lon": 0}}}))
        self.assertTrue(self.probs({"bplace:a": {"coords": {"lat": 0, "lon": 181}}}))
        self.assertTrue(self.probs({"bpers:c": {"coords": {"lat": 0, "lon": 0}}}))

    def test_license_url_and_author_html(self):
        img = {"file": "A.jpg", "author": "x", "license": "PD", "license_url": "ftp://x"}
        self.assertTrue(self.probs({"bplace:a": {"image": img}}))
        self.assertTrue(self.probs({"bplace:a": {"image": dict(img, license_url="https://x", author="<b>x</b>")}}))
        self.assertEqual(self.probs({"bplace:a": {"image": dict(img, license_url="https://x")}}), [])


if __name__ == "__main__":
    unittest.main()
