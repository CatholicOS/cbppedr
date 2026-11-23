import json
import tempfile
import unittest
from pathlib import Path

from build_catalog import build

DECISIONS = [
    {"key": "FILIPPO#1", "type": "person", "kind": "individual", "id": "bpers:philippus.mariamnes-filius",
     "latin": "Philippus", "it": "Filippo", "en": "Philip",
     "descr_it": "figlio di Erode il Grande e di Mariamne II", "descr_en": "son of Herod the Great and Mariamne II",
     "relations": [{"rel": "child_of", "target": "Mariamne II", "target_key": None},
                   {"rel": "child_of", "target": "Erode il Grande", "target_key": "ERODE#1"}],
     "parts": None, "certain": True},
    {"key": "FILIPPO#2", "type": "person", "kind": "individual", "id": "bpers:philippus.tetrarcha",
     "latin": "Philippus", "it": "Filippo", "en": "Philip", "descr_it": "tetrarca", "descr_en": "tetrarch",
     "relations": [], "parts": None, "certain": True},
    {"key": "ERODE#1", "type": "person", "kind": "individual", "id": "bpers:herodes-magnus",
     "latin": "Herodes", "it": "Erode il Grande", "en": "Herod the Great", "descr_it": "re", "descr_en": "king",
     "relations": [], "parts": None, "certain": True},
    {"key": "MARIAMNE#1", "type": "person", "kind": "extra-biblical", "id": "bpers:mariamne-ii",
     "latin": "Mariamne", "it": "Mariamne II", "en": "Mariamne II", "descr_it": "moglie di Erode",
     "descr_en": "wife of Herod", "relations": [], "parts": None, "certain": True},
    {"key": "LIBNA#2", "type": "place", "kind": "other", "id": "bplace:libna.castra", "latin": "Lebna",
     "it": "Libna", "en": "Libnah", "descr_it": "accampamento", "descr_en": "camp", "relations": [],
     "parts": None, "certain": False},
    {"key": "LEVANTE#1", "type": "none"},
]
UNITS = {"FILIPPO#1": ["btu:mt.14.3"], "FILIPPO#2": ["btu:lc.3.1"], "ERODE#1": ["btu:mt.2.1"],
         "MARIAMNE#1": [], "LIBNA#2": ["btu:nm.33.20"], "LEVANTE#1": []}


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.out = build(DECISIONS, UNITS, tree={})

    def test_two_philips(self):
        persons = self.out["persons"]["entries"]
        self.assertIn("bpers:philippus.mariamnes-filius", persons)
        self.assertIn("bpers:philippus.tetrarcha", persons)
        self.assertEqual(persons["bpers:philippus.tetrarcha"]["attested"], ["btu:lc.3.1"])

    def test_relations_resolved_by_key_and_name(self):
        rels = self.out["persons"]["entries"]["bpers:philippus.mariamnes-filius"]["relations"]
        self.assertIn({"rel": "child_of", "target": "bpers:mariamne-ii", "evidence": ["ndeib:FILIPPO#1"]}, rels)
        self.assertIn({"rel": "child_of", "target": "bpers:herodes-magnus", "evidence": ["ndeib:FILIPPO#1"]}, rels)

    def test_unattested_entry_kept(self):
        self.assertEqual(self.out["persons"]["entries"]["bpers:mariamne-ii"]["attested"], [])

    def test_uncertain_marked_and_none_dropped(self):
        place = self.out["places"]["entries"]["bplace:libna.castra"]
        self.assertEqual(place["review"], "uncertain")
        self.assertNotIn("LEVANTE", json.dumps(self.out))

    def test_deterministic(self):
        self.assertEqual(json.dumps(self.out, sort_keys=True),
                         json.dumps(build(DECISIONS, UNITS, tree={}), sort_keys=True))

    def test_curated_tree_adds_relations_and_entries(self):
        tree = {"entries": {"bpers:cleopatra-hierosolymitana": {
                    "type": "person", "kind": "extra-biblical", "latin": "Cleopatra", "it": "Cleopatra",
                    "en": "Cleopatra", "descr_it": "moglie di Erode il Grande", "descr_en": "wife of Herod the Great"}},
                "relations": [
                    {"source": "bpers:herodes-magnus", "rel": "spouse_of", "target": "bpers:mariamne-ii"},
                    {"source": "bpers:philippus.tetrarcha", "rel": "child_of", "target": "bpers:cleopatra-hierosolymitana"},
                    {"source": "bpers:philippus.tetrarcha", "rel": "child_of", "target": "bpers:nobody"}]}
        out = build(DECISIONS, UNITS, tree=tree)
        persons = out["persons"]["entries"]
        self.assertIn({"rel": "spouse_of", "target": "bpers:mariamne-ii", "evidence": ["bj:herodian-tree"]},
                      persons["bpers:herodes-magnus"]["relations"])
        self.assertEqual(persons["bpers:cleopatra-hierosolymitana"]["evidence"], ["bj:herodian-tree"])
        self.assertIn({"rel": "child_of", "target": "bpers:cleopatra-hierosolymitana",
                       "evidence": ["bj:herodian-tree"]}, persons["bpers:philippus.tetrarcha"]["relations"])
        self.assertTrue(any("bpers:nobody" in r for r in out["report"]["unresolved_relations"]))


def _with(*extra):
    return DECISIONS + list(extra)


def _person(key, eid, it, relations=()):
    return {"key": key, "type": "person", "kind": "individual", "id": eid, "latin": it, "it": it, "en": it,
            "descr_it": "x", "descr_en": "x", "relations": list(relations), "parts": None, "certain": True}


class ResolveTest(unittest.TestCase):
    def rels(self, decisions, eid):
        return build(decisions, UNITS, tree={})["persons"]["entries"][eid]["relations"]

    def test_name_never_resolves_to_a_discriminated_id(self):
        d = _with(_person("GESU#2", "bpers:iesus.iustus", "Gesù"),
                  _person("MARIA#1", "bpers:maria.mater", "Maria", [{"rel": "parent_of", "target": "Gesù"}]))
        self.assertEqual(self.rels(d, "bpers:maria.mater"), [])

    def test_ambiguous_key_does_not_fall_back_to_the_name(self):
        d = _with({"key": "ABIA", "type": "person", "parts": [
                      dict(_person("ABIA", "bpers:abia.rex", "Abia"), relations=[]),
                      dict(_person("ABIA", "bpers:abia.filius", "Abia"), relations=[])]},
                  _person("X#1", "bpers:x", "X", [{"rel": "child_of", "target": "Erode il Grande", "target_key": "ABIA"}]))
        self.assertEqual(self.rels(d, "bpers:x"), [])

    def test_kinship_needs_a_person(self):
        d = _with(_person("Y#1", "bpers:y", "Y", [{"rel": "child_of", "target": "Libna", "target_key": "LIBNA#2"}]))
        self.assertEqual(self.rels(d, "bpers:y"), [])


if __name__ == "__main__":
    unittest.main()


class PartUnitsTest(unittest.TestCase):
    def test_parts_take_their_own_units(self):
        decisions = [{"key": "ABIA", "type": "person", "parts": [
            {"type": "person", "kind": "individual", "id": "bpers:abia.rex-iudae", "it": "Abia", "en": "Abijah",
             "latin": "Abia", "descr_it": "re", "descr_en": "king"},
            {"type": "person", "kind": "individual", "id": "bpers:abia.samuelis-filius", "it": "Abia",
             "en": "Abijah", "latin": "Abia", "descr_it": "figlio", "descr_en": "son"}]}]
        units = {"ABIA": ["btu:1reg.14.31", "btu:1sam.8.2"]}
        part_units = {"ABIA": {"bpers:abia.rex-iudae": ["btu:1reg.14.31"],
                               "bpers:abia.samuelis-filius": ["btu:1sam.8.2"]}}
        out = build(decisions, units, tree={}, part_units=part_units)["persons"]["entries"]
        self.assertEqual(out["bpers:abia.rex-iudae"]["attested"], ["btu:1reg.14.31"])
        self.assertEqual(out["bpers:abia.samuelis-filius"]["attested"], ["btu:1sam.8.2"])


class QidTest(unittest.TestCase):
    def test_qids_applied(self):
        qids = {"bpers:herodes-magnus": {"qid": "Q43945", "status": "auto", "candidates": []},
                "bpers:philippus.tetrarcha": {"qid": None, "status": "unresolved", "candidates": ["Q1"]}}
        out = build(DECISIONS, UNITS, tree={}, qids=qids)["persons"]["entries"]
        self.assertEqual((out["bpers:herodes-magnus"]["qid"], out["bpers:herodes-magnus"]["qid_status"]),
                         ("Q43945", "auto"))
        self.assertEqual(out["bpers:philippus.tetrarcha"]["qid"], None)


class SingleSenseOverrideTest(unittest.TestCase):
    def test_curated_units_correct_a_single_entity_sense(self):
        units = dict(UNITS, **{"FILIPPO#2": ["btu:lc.3.1", "btu:act.12.1", "btu:mt.16.13"]})
        out = build(DECISIONS, units, tree={}, part_units={"FILIPPO#2": {"bpers:philippus.tetrarcha": ["btu:lc.3.1"]}})
        self.assertEqual(out["persons"]["entries"]["bpers:philippus.tetrarcha"]["attested"], ["btu:lc.3.1"])


class RemovedUnitsTest(unittest.TestCase):
    def test_removed_units_dropped_and_stale_reported(self):
        out = build(DECISIONS, UNITS, tree={}, removed={"bpers:philippus.tetrarcha": ["btu:lc.3.1", "btu:gn.1.1"]},
                    curated={"bpers:philippus.tetrarcha": {"attested": ["btu:mc.6.17"]}})
        self.assertEqual(out["persons"]["entries"]["bpers:philippus.tetrarcha"]["attested"], ["btu:mc.6.17"])
        self.assertEqual(out["report"]["stale_removals"], ["bpers:philippus.tetrarcha btu:gn.1.1"])

    def test_removal_wins_over_curated_and_is_reported(self):
        out = build(DECISIONS, UNITS, tree={}, removed={"bpers:philippus.tetrarcha": ["btu:mc.6.17"]},
                    curated={"bpers:philippus.tetrarcha": {"attested": ["btu:mc.6.17"]}})
        self.assertEqual(out["persons"]["entries"]["bpers:philippus.tetrarcha"]["attested"], ["btu:lc.3.1"])
        self.assertEqual(out["report"]["conflicting_removals"], ["bpers:philippus.tetrarcha btu:mc.6.17"])

    def test_curated_type_mismatch_and_relation_without_evidence_reported(self):
        out = build(DECISIONS, UNITS, tree={}, curated={"bpers:philippus.tetrarcha": {
            "type": "place", "relations": [{"rel": "child_of", "target": "bpers:herodes-magnus", "evidence": []}]}})
        self.assertIn("bpers:philippus.tetrarcha: person vs place (curated)", out["report"]["type_conflicts"])
        self.assertIn("bpers:philippus.tetrarcha child_of bpers:herodes-magnus (curated)", out["report"]["unresolved_relations"])


class LabelsTest(unittest.TestCase):
    def test_labels_on_attested_units_only(self):
        lab = {"as": "designation", "editions": {"NABRE": "the tetrarch"}}
        out = build(DECISIONS, UNITS, tree={}, labels={"bpers:philippus.tetrarcha": {"btu:lc.3.1": lab, "btu:gn.1.1": lab}})
        self.assertEqual(out["persons"]["entries"]["bpers:philippus.tetrarcha"]["labels"], {"btu:lc.3.1": lab})
        self.assertEqual(out["report"]["stale_labels"], ["bpers:philippus.tetrarcha btu:gn.1.1"])


class ConjecturesTest(unittest.TestCase):
    SOURCES = {"bj": {"authority": "authoritative"}, "tipnr": {"authority": "non-authoritative"}}

    def test_status_from_authoritative_opinions_only(self):
        from build_catalog import conjecture_status as st
        bj = lambda says: {"by": "bj:note:1Sam.14,49#p597", "says": says}
        tip = {"by": "tipnr:Ishvi@1Sa.14.49", "says": "identifies"}
        self.assertEqual(st([tip], self.SOURCES), "unsupported")
        self.assertEqual(st([tip, bj("identifies")], self.SOURCES), "supported")
        self.assertEqual(st([bj("suggests"), bj("doubts")], self.SOURCES), "disputed")
        self.assertEqual(st([bj("rejects")], self.SOURCES), "rejected")
        self.assertEqual(st([bj("doubts"), tip], self.SOURCES), "doubted")

    def test_a_publication_has_its_own_weight(self):
        from build_catalog import conjecture_status as st
        src = dict(self.SOURCES, pub={"authority": "per publication"},
                   **{"pub:meier-1992": {"authority": "authoritative"}, "pub:blog-2020": {"authority": "non-authoritative"}})
        self.assertEqual(st([{"by": "pub:meier-1992#p12", "says": "suggests"}], src), "supported")
        self.assertEqual(st([{"by": "pub:blog-2020", "says": "identifies"}], src), "unsupported")
        self.assertEqual(st([{"by": "pub:unlisted-1999", "says": "identifies"}], src), "unsupported")

    def test_built_on_the_source_entry_unresolved_reported(self):
        c = {"source": "bpers:philippus.tetrarcha", "target": "bpers:herodes-magnus", "rel": "possibly_same_as",
             "opinions": [{"by": "tipnr:X@Mat.1.1", "says": "identifies", "summary": "x"}]}
        at = {"source": "bpers:philippus.tetrarcha", "rel": "possibly_attested_at", "unit": "btu:mc.8.27",
              "opinions": [{"by": "bj:note:Mc.8,27#p1", "says": "suggests", "summary": "x"}]}
        typo = dict(at, rel="possibly_atested_at")
        out = build(DECISIONS, UNITS, tree={}, conjectures=[c, dict(c, target="bpers:nobody"), at, typo,
                                                            dict(at, unit="btu:mc.99.1")],
                    sources=self.SOURCES, known_units={"btu:mc.8.27"})
        got = out["persons"]["entries"]["bpers:philippus.tetrarcha"]["conjectures"]
        self.assertEqual([(g.get("target") or g.get("unit"), g["status"]) for g in got],
                         [("bpers:herodes-magnus", "unsupported"), ("btu:mc.8.27", "supported")])
        self.assertEqual(out["report"]["unresolved_conjectures"],
                         ["bpers:philippus.tetrarcha possibly_same_as bpers:nobody",
                          "bpers:philippus.tetrarcha possibly_atested_at btu:mc.8.27",
                          "bpers:philippus.tetrarcha possibly_attested_at btu:mc.99.1"])


class CuratedEntriesTest(unittest.TestCase):
    CURATED = {
        "bpers:amos.propheta": {
            "type": "person", "kind": "individual", "latin": "Amos", "it": "Amos", "en": "Amos",
            "descr_it": "profeta", "descr_en": "prophet", "attested": ["btu:am.1.1"],
            "evidence": ["ndeib:AMOS#0"],
            "relations": [{"rel": "child_of", "target": "bpers:herodes-magnus", "evidence": ["ndeib:AMOS#0"]},
                          {"rel": "located_in", "target": "bpers:herodes-magnus", "evidence": ["ndeib:AMOS#0"]}]},
        "bpers:philippus.tetrarcha": {"attested": ["btu:mc.6.17"], "evidence": ["ndeib:ERODE#1"]},
    }

    def setUp(self):
        self.out = build(DECISIONS, UNITS, tree={}, curated=self.CURATED)
        self.p = self.out["persons"]["entries"]

    def test_new_entry_with_own_units_and_evidence(self):
        e = self.p["bpers:amos.propheta"]
        self.assertEqual((e["attested"], e["evidence"], e["names"]["la"]), (["btu:am.1.1"], ["ndeib:AMOS#0"], "Amos"))
        self.assertEqual(e["relations"], [{"rel": "child_of", "target": "bpers:herodes-magnus",
                                           "evidence": ["ndeib:AMOS#0"]}])

    def test_wrong_target_type_reported(self):
        self.assertIn("bpers:amos.propheta located_in bpers:herodes-magnus (curated)",
                      self.out["report"]["unresolved_relations"])

    def test_existing_entry_extended(self):
        e = self.p["bpers:philippus.tetrarcha"]
        self.assertEqual(e["attested"], ["btu:lc.3.1", "btu:mc.6.17"])
        self.assertEqual(e["evidence"], ["ndeib:FILIPPO#2", "ndeib:ERODE#1"])
