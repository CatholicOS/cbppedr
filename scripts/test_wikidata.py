import unittest
from wikidata import match, needs_match

ENTITIES = {
    "Q1": {"id": "Q1", "descriptions": {"en": {"value": "son of Herod the Great and Mariamne II"}},
           "claims": {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q5"}}}}]}},
    "Q2": {"id": "Q2", "descriptions": {"en": {"value": "tetrarch of Iturea, son of Herod the Great and Cleopatra"}},
           "claims": {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q5"}}}}]}},
    "Q3": {"id": "Q3", "descriptions": {"en": {"value": "apostle of Jesus"}},
           "claims": {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q5"}}}}]}},
    "Q9": {"id": "Q9", "descriptions": {"en": {"value": "French singer"}},
           "claims": {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q5"}}}}]}},
    "Q20": {"id": "Q20", "descriptions": {"en": {"value": "biblical city in the Shephelah"}},
            "claims": {"P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q15661340"}}}}]}},
}
SEARCH = {"Filippo": ["Q1", "Q2", "Q3", "Q9"], "Philip": ["Q1", "Q2", "Q3", "Q9"], "Libna": ["Q20"],
          "Libnah": ["Q20"]}


def fake_search(text, lang):
    return SEARCH.get(text, [])


def fake_get(ids):
    return {i: ENTITIES[i] for i in ids if i in ENTITIES}


def entry(eid, it, en, typ="person", rel_names=(), descr_en=""):
    return eid, {"type": typ, "names": {"it": it, "en": en, "la": it}, "description": {"en": descr_en},
                 "_rel_names": list(rel_names)}


class WikidataTest(unittest.TestCase):
    def test_homonyms_need_a_related_name(self):
        eid, e = entry("bpers:philippus.mariamnes-filius", "Filippo", "Philip", rel_names=["Mariamne II"])
        self.assertEqual(match(eid, e, fake_search, fake_get), ("Q1", "auto", ["Q1", "Q2", "Q3", "Q9"]))
        eid, e = entry("bpers:philippus.tetrarcha", "Filippo", "Philip", rel_names=["Cleopatra"])
        self.assertEqual(match(eid, e, fake_search, fake_get)[:2], ("Q2", "auto"))

    def test_ambiguous_stays_unresolved(self):
        eid, e = entry("bpers:philippus.evangelista", "Filippo", "Philip", rel_names=["Stefano"])
        qid, status, cands = match(eid, e, fake_search, fake_get)
        self.assertEqual((qid, status), (None, "unresolved"))
        self.assertIn("Q3", cands)

    def test_unique_place(self):
        eid, e = entry("bplace:libna.urbs", "Libna", "Libnah", typ="place")
        self.assertEqual(match(eid, e, fake_search, fake_get)[:2], ("Q20", "auto"))


if __name__ == "__main__":
    unittest.main()


class DedupeTest(unittest.TestCase):
    def test_shared_auto_qid_is_demoted(self):
        from wikidata import dedupe
        q = {"bplace:libna.urbs": {"qid": "Q20", "status": "auto", "candidates": ["Q20"]},
             "bplace:libna.castra": {"qid": "Q20", "status": "auto", "candidates": ["Q20"]},
             "bpers:x": {"qid": "Q5", "status": "auto", "candidates": ["Q5"]},
             "bpers:y": {"qid": "Q5", "status": "reviewed", "candidates": []}}
        dedupe(q)
        self.assertEqual(q["bplace:libna.urbs"]["status"], "unresolved")
        self.assertIsNone(q["bplace:libna.castra"]["qid"])
        self.assertEqual(q["bpers:x"]["status"], "unresolved")
        self.assertEqual(q["bpers:y"]["qid"], "Q5")


def _ent(qid, descr, *kinds):
    return {"id": qid, "descriptions": {"en": {"value": descr}},
            "claims": {"P31": [{"mainsnak": {"datavalue": {"value": {"id": k}}}} for k in kinds]}}


class StrictnessTest(unittest.TestCase):
    """Regressions from the round-1 review: wrong items the old rule accepted."""

    def run_match(self, eid, typ, ents, rel_names=()):
        ents = {e["id"]: e for e in ents}
        _, e = entry(eid, "Nome", "Name", typ=typ, rel_names=rel_names)
        return match(eid, e, lambda text, lang: list(ents), lambda ids: {i: ents[i] for i in ids if i in ents})

    def test_fictional_character_is_not_a_person(self):
        r = self.run_match("bpers:iesus-christus", "person",
                           [_ent("Q1", "character in The Simpsons, depiction of Jesus", "Q15632617")])
        self.assertEqual(r[:2], (None, "unresolved"))

    def test_cues_are_whole_words(self):
        for descr in ("Israeli basketball player", "Italian bibliographer", "ancient Greek sculptor"):
            r = self.run_match("bpers:stephanus", "person", [_ent("Q1", descr, "Q5")])
            self.assertEqual(r[:2], (None, "unresolved"), descr)
        r = self.run_match("bplace:tarsus", "place", [_ent("Q2", "ancient city in Bithynia", "Q515")])
        self.assertEqual(r[:2], (None, "unresolved"))
        r = self.run_match("bplace:ephratha", "place", [_ent("Q3", "Israeli settlement in the West Bank", "Q486972")])
        self.assertEqual(r[:2], (None, "unresolved"))

    def test_human_biblical_figure_class_suffices(self):
        r = self.run_match("bpers:abraham", "person",
                           [_ent("Q9181", "founding figure of the Abrahamic religions", "Q20643955"),
                            _ent("Q91", "president of the United States", "Q5")])
        self.assertEqual(r[:2], ("Q9181", "auto"))

    def test_generic_words_of_a_relative_are_no_evidence(self):
        r = self.run_match("bpers:herodes.antipas", "person",
                           [_ent("Q1", "son of Alexander the Great, king in Judea", "Q5")],
                           rel_names=["Herod the Great"])
        self.assertEqual(r[:2], (None, "unresolved"))

    def test_pick_is_kept_among_candidates(self):
        ents = [_ent(f"Q{i}", "French singer", "Q5") for i in range(1, 12)] + \
               [_ent("Q99", "figure of the Old Testament", "Q20643955")]
        r = self.run_match("bpers:abdias", "person", ents)
        self.assertEqual(r[0], "Q99")
        self.assertIn("Q99", r[2])


class NeedsMatchTest(unittest.TestCase):
    def test_a_rejected_item_is_judged_again(self):
        self.assertTrue(needs_match({"qid": "Q1", "status": "auto", "rejected": ["Q1"]}, rematch=False))

    def test_a_kept_item_is_not(self):
        self.assertFalse(needs_match({"qid": "Q1", "status": "auto", "rejected": ["Q2"]}, rematch=False))
        self.assertFalse(needs_match({"qid": None, "status": "unresolved"}, rematch=False))

    def test_errors_and_rematch_are(self):
        self.assertTrue(needs_match({"qid": None, "error": True}, rematch=False))
        self.assertTrue(needs_match({"qid": "Q1"}, rematch=True))


class PlaceAndRejectTest(unittest.TestCase):
    def test_a_regional_word_does_not_make_a_place_biblical(self):
        ents = {"Q1": _ent("Q1", "capital of Galilea Municipality, Spain", "Q515")}
        _, e = entry("bplace:galilaea", "Galilea", "Galilee", typ="place")
        r = match("bplace:galilaea", e, lambda t, l: ["Q1"], lambda ids: ents)
        self.assertEqual(r[:2], (None, "unresolved"))

    def test_rejected_candidate_is_never_picked(self):
        ents = {"Q7": _ent("Q7", "translator of the Hebrew Bible into Greek", "Q5")}
        _, e = entry("bpers:aquila", "Aquila", "Aquila")
        e["_rejected"] = ["Q7"]
        r = match("bpers:aquila", e, lambda t, l: ["Q7"], lambda ids: ents)
        self.assertEqual(r[:2], (None, "unresolved"))
