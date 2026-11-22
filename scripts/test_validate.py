import unittest

from validate import conjecture_problems, problems, unnamed_problems


def cat(entries):
    return {"$comment": "x", "entries": entries}


def person(**kw):
    e = {"type": "person", "kind": "individual", "names": {"la": "Levi", "it": "Levi", "en": "Levi"},
         "description": {"it": "figlio di Giacobbe", "en": "son of Jacob"}, "attested": ["btu:gn.29.34"],
         "relations": [], "qid": None, "qid_status": "unresolved", "evidence": ["ndeib:LEVI#1"]}
    e.update(kw)
    return e


class ValidateTest(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(problems({"persons": cat({"bpers:levi.iacob-filius": person()}),
                                   "places": cat({}), "events": cat({})}), [])

    def test_bad_id_prefix_and_form(self):
        p = problems({"persons": cat({"bplace:levi": person(), "bpers:Levi": person()}), "places": cat({}),
                      "events": cat({})})
        self.assertEqual(len(p), 2)

    def test_missing_target_unknown_unit_long_description(self):
        e = person(relations=[{"rel": "child_of", "target": "bpers:nemo", "evidence": ["ndeib:X"]}],
                   attested=["btu:gn.99.1"], description={"it": "x " * 120, "en": "ok"})
        p = problems({"persons": cat({"bpers:levi": e}), "places": cat({}), "events": cat({})})
        self.assertTrue(any("bpers:nemo" in x for x in p))
        self.assertTrue(any("btu:gn.99.1" in x for x in p))
        self.assertTrue(any("description" in x for x in p))

    def test_same_id_in_two_catalogs(self):
        p = problems({"persons": cat({"bpers:a": person()}), "places": cat({}),
                      "events": cat({"bpers:a": person(type="event")})})
        self.assertTrue(p)


if __name__ == "__main__":
    unittest.main()


class RuleTest(unittest.TestCase):
    def run_p(self, persons, places=None):
        return problems({"persons": cat(persons), "places": cat(places or {}), "events": cat({})})

    def test_relation_vocabulary_and_target_type(self):
        place = dict(person(), type="place", kind="city")
        p = self.run_p({"bpers:a": person(relations=[{"rel": "friend_of", "target": "bpers:b", "evidence": ["ndeib:A#1"]},
                                                    {"rel": "child_of", "target": "bplace:c", "evidence": ["ndeib:A#1"]}]),
                        "bpers:b": person()}, {"bplace:c": place})
        self.assertEqual(len(p), 2, p)

    def test_kind_qid_format_and_duplicate_qid(self):
        p = self.run_p({"bpers:a": person(kind="hero"),
                        "bpers:b": person(qid="Q12", qid_status="auto"),
                        "bpers:c": person(qid="Q12", qid_status="auto"),
                        "bpers:d": person(qid="12", qid_status="auto")})
        self.assertEqual(len(p), 4, p)


class LabelsTest(unittest.TestCase):
    def test_label_rules(self):
        e = person(attested=["btu:gn.29.34"], labels={
            "btu:gn.29.34": {"as": "designation", "editions": {"NABRE": "the third son"}},
            "btu:gn.1.1": {"as": "title", "editions": {"KJV": "one two three four five six seven"}}})
        p = problems({"persons": cat({"bpers:a": e}), "places": cat({}), "events": cat({})})
        self.assertEqual(len(p), 4, p)


class UnnamedTest(unittest.TestCase):
    def test_unnamed_rules(self):
        cats = {"persons": cat({"bpers:a": person()}), "places": cat({}), "events": cat({})}
        good = {"type": "person", "description": {"it": "moglie di Levi", "en": "wife of Levi"},
                "attested": ["btu:gn.29.34"], "evidence": ["nv:btu:gn.29.34"],
                "tie": {"rel": "spouse_of", "target": "bpers:a"}}
        bad = dict(good, attested=[], tie={"rel": "located_in", "target": "bpers:zz"})
        self.assertEqual(unnamed_problems({"anon:a.uxor": good}, cats), [])
        self.assertEqual(len(unnamed_problems({"bpers:x": bad}, cats)), 3)
        self.assertEqual(len(unnamed_problems({"anon:a.uxor": dict(good, attested=None, type=None)}, cats)), 2)

    def test_malformed_label_and_relation_evidence_reported(self):
        e = person(labels={"btu:gn.29.34": "Levi"},
                   relations=[{"rel": "child_of", "target": "bpers:a", "evidence": ["wiki:x"]}])
        p = problems({"persons": cat({"bpers:a": e}), "places": cat({}), "events": cat({})})
        self.assertEqual(len(p), 2, p)


class ConjectureTest(unittest.TestCase):
    def test_conjecture_rules(self):
        src = {"bj": {}, "tipnr": {}}
        good = {"rel": "possibly_same_as", "target": "bpers:b", "status": "supported",
                "opinions": [{"by": "bj:note:1Sam.14,49#p597", "says": "identifies", "summary": "Ishvi is Ishbaal"}]}
        self.assertEqual(conjecture_problems("bpers:a", {"conjectures": [good]}, {"bpers:a", "bpers:b"}, src), [])
        at = {"rel": "possibly_attested_at", "unit": "btu:gn.29.34", "status": "unsupported",
              "opinions": [{"by": "tipnr:Levi@Gen.29.34", "says": "suggests", "summary": "a lead"}]}
        self.assertEqual(conjecture_problems("bpers:a", {"conjectures": [at]}, {"bpers:a"}, src), [])
        bad = dict(good, status="maybe", opinions=[{"by": "wiki:x", "says": "thinks", "summary": ""}])
        self.assertEqual(len(conjecture_problems("bpers:a", {"conjectures": [bad]}, {"bpers:a", "bpers:b"}, src)), 4)


class EvidenceTest(unittest.TestCase):
    def run_p(self, ev):
        return problems({"persons": cat({"bpers:a": person(evidence=ev)}), "places": cat({}), "events": cat({})})

    def test_known_kinds_pass(self):
        self.assertEqual(self.run_p(["ndeib:LEVI#1", "bj:herodian-tree", "nv:btu:gn.29.34"]), [])

    def test_unknown_kind_and_unknown_verse(self):
        p = self.run_p(["wiki:Levi", "nv:btu:gn.99.1", "nv:gn.29.34"])
        self.assertEqual(len(p), 3, p)

    def test_no_evidence(self):
        self.assertEqual(len(self.run_p([])), 1)
