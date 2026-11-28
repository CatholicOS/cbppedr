import unittest

from details import author_of, detail, plain_text
from validate import detail_problems, disputed_problems


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

    def test_author_style_block_dropped(self):
        self.assertEqual(plain_text("<style>.a { color: red; }</style><span>Ann</span><script>x()</script>"), "Ann")

    def test_author_boilerplate_falls_back_to_credit(self):
        meta = {"Artist": {"value": "Public domainPublic domainfalsefalse"}, "Credit": {"value": "<b>Ann</b> Doe"},
                "LicenseShortName": {"value": "PD"}}
        self.assertEqual(detail(entity(), item({"P18": p18("A.jpg")}), meta)["image"]["author"], "Ann Doe")
        meta = {"Artist": {"value": "x" * 300}, "Attribution": {"value": "Bob"}, "LicenseShortName": {"value": "PD"}}
        self.assertEqual(detail(entity(), item({"P18": p18("A.jpg")}), meta)["image"]["author"], "Bob")
        meta = {"Artist": {"value": "a { b }"}, "LicenseShortName": {"value": "PD"}}
        self.assertNotIn("author", detail(entity(), item({"P18": p18("A.jpg")}), meta)["image"])

    def test_cc_by_without_author_omitted(self):
        it = item({"P18": p18("A.jpg")})
        for lic in ("CC BY 4.0", "cc by-sa 3.0"):
            self.assertIsNone(detail(entity(), it, {"LicenseShortName": {"value": lic}}))
        for lic in ("CC0", "Public domain"):
            self.assertIn("image", detail(entity(), it, {"LicenseShortName": {"value": lic}}))

    def test_batch_cache_mismatch_refetches(self):
        import details
        calls = []

        def fake(params, api=details.wikidata.API, refresh=False):
            calls.append(refresh)
            ids = params["ids"].split("|")
            return {"entities": {i: {} for i in (ids[:1] if not refresh else ids)}}

        real, details.wikidata._call = details.wikidata._call, fake
        try:
            self.assertEqual(set(details.fetch_items(["Q1", "Q2"])), {"Q1", "Q2"})
        finally:
            details.wikidata._call = real
        self.assertEqual(calls, [False, True])

    def test_two_coordinates_give_none(self):
        self.assertIsNone(detail(entity(), item({"P625": [p625(1, 2), p625(3, 4)]}), None))
        d = detail(entity(), item({"P625": [p625(31.7, 35.2)]}), None)
        self.assertEqual(d["coords"], {"lat": 31.7, "lon": 35.2})

    def test_p1480_qualifier_gives_none(self):
        qualified = dict(p625(30.0, 35.0), qualifiers={"P1480": [{"datavalue": {"value": {"id": "Q18122778"}}}]})
        self.assertIsNone(detail(entity(), item({"P625": [qualified]}), None))
        other = dict(p625(30.0, 35.0), qualifiers={"P580": [{}]})
        self.assertEqual(detail(entity(), item({"P625": [other]}), None)["coords"], {"lat": 30.0, "lon": 35.0})

    def test_disputed_site_has_no_coords(self):
        it = item({"P625": [p625(30.0, 35.0)]}, {"enwiki": "A"})
        self.assertEqual(detail(entity(), it, None, disputed=True), {"wikipedia": {"en": "A"}})
        self.assertIsNone(detail(entity(), item({"P625": [p625(30.0, 35.0)]}), None, disputed=True))

    def test_placeholder_authors_are_no_author(self):
        for artist in ("Unknown author", "unknown ARTIST", "Anonymous", "Unknown authorUnknown author",
                       "AnonymousUnknown author", "Unknown artist Unknown artist"):
            self.assertEqual(author_of({"Artist": {"value": artist}}), "", artist)
        self.assertEqual(author_of({"Artist": {"value": "Anonymous"}, "Credit": {"value": "Bob"}}), "Bob")
        self.assertIsNone(detail(entity(), item({"P18": p18("A.jpg")}),
                                 {"Artist": {"value": "Unknown author"}, "LicenseShortName": {"value": "CC BY 4.0"}}))
        self.assertEqual(author_of({"Artist": {"value": "AnonymousUnknown author (Meister 3)"}}), "Meister 3")
        for credit in ("None", "[1]", "Unknown source", "unknown"):
            self.assertEqual(author_of({"Credit": {"value": credit}}), "", credit)

    def test_more_credits_that_credit_no_one(self):
        for text in ("unknown illuminator", "Unknown painter", "no idea - see source", "Own work",
                     "https://example.org/a?b=1", "http://example.org/x.htm"):
            self.assertEqual(author_of({"Artist": {"value": text}}), "", text)
        self.assertEqual(author_of({"Credit": {"value": "Own work, Rama"}}), "Rama")
        self.assertEqual(author_of({"Artist": {"value": "No machine-readable author provided. Ann Doe assumed "
                                                         "(based on copyright claims)."}}), "Ann Doe")
        self.assertEqual(author_of({"Artist": {"value": "Ann (http://example.org)"}}), "Ann (http://example.org)")

    def test_doubled_author_collapses(self):
        self.assertEqual(author_of({"Artist": {"value": "Ann DoeAnn Doe"}}), "Ann Doe")
        self.assertEqual(author_of({"Artist": {"value": "Ann Doe Ann Doe"}}), "Ann Doe")
        self.assertEqual(author_of({"Artist": {"value": "Anna"}}), "Anna")
        self.assertEqual(author_of({"Artist": {"value": "MM"}}), "MM")
        self.assertEqual(author_of({"Artist": {"value": "Ann (2011)"}}), "Ann (2011)")

    def test_author_cut_before_title_and_source_labels(self):
        self.assertEqual(author_of({"Artist": {"value": "Ann Doe Title A picture Source/Photographer A book"}}),
                         "Ann Doe")
        self.assertEqual(author_of({"Artist": {"value": "Ann Doe Source A book"}}), "Ann Doe")
        self.assertEqual(author_of({"Artist": {"value": "Title A picture"}, "Credit": {"value": "Bob"}}), "Bob")
        self.assertEqual(author_of({"Artist": {"value": "Ann Titlewise"}}), "Ann Titlewise")

    def test_commons_title_mismatch_refetches_then_omits(self):
        import details
        calls = []

        def answer(title):
            return {"query": {"pages": {"1": {"title": title, "imageinfo": [{"extmetadata": {"X": 1}}]}}}}

        def fake(params, api=None, refresh=False):
            calls.append(refresh)
            return answer("File:Other.jpg" if not refresh else "File:My file.jpg")

        def always_wrong(params, api=None, refresh=False):
            calls.append(refresh)
            return answer("File:Other.jpg")

        real = details.wikidata._call
        try:
            details.wikidata._call = fake
            self.assertEqual(details.fetch_commons("my_file.jpg"), {"X": 1})
            self.assertEqual(calls, [False, True])
            calls.clear()
            details.wikidata._call = always_wrong
            self.assertIsNone(details.fetch_commons("My file.jpg"))
            self.assertEqual(calls, [False, True])
            calls.clear()
            details.wikidata._call = lambda params, api=None, refresh=False: answer("File:My file.jpg")
            self.assertEqual(details.fetch_commons("My_file.jpg"), {"X": 1})
        finally:
            details.wikidata._call = real

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
        self.assertTrue(self.probs({"bplace:a": {"image": dict(img, license_url="https://x", author="a { b }")}}))
        self.assertTrue(self.probs({"bplace:a": {"image": dict(img, license_url="https://x", author="y" * 201)}}))
        noauth = {"file": "A.jpg", "license": "CC BY-SA 4.0"}
        self.assertTrue(self.probs({"bplace:a": {"image": noauth}}))
        self.assertEqual(self.probs({"bplace:a": {"image": dict(noauth, license="CC0")}}), [])

    def test_coords_on_a_disputed_site(self):
        p = detail_problems({"entries": {"bplace:a": {"coords": {"lat": 0, "lon": 0}}}}, self.ENT, {"bplace:a"})
        self.assertEqual(len(p), 1)

    def test_placeholder_author(self):
        img = {"file": "A.jpg", "author": "Unknown authorUnknown author", "license": "PD"}
        self.assertTrue(self.probs({"bplace:a": {"image": img}}))

    def test_disputed_sites_file(self):
        ent = {"bplace:a": entity(), "bpers:c": entity("adjudicated", "person")}
        self.assertEqual(disputed_problems({"$comment": "x", "entries": ["bplace:a"]}, ent), [])
        self.assertEqual(len(disputed_problems({"entries": ["bplace:zz", "bpers:c", "bplace:a", "bplace:a"]}, ent)), 3)
        self.assertTrue(disputed_problems({"entries": {"bplace:a": 1}}, ent))


if __name__ == "__main__":
    unittest.main()
