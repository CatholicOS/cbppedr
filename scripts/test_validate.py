import unittest

from validate import problems


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
        p = self.run_p({"bpers:a": person(relations=[{"rel": "friend_of", "target": "bpers:b", "evidence": []},
                                                    {"rel": "child_of", "target": "bplace:c", "evidence": []}]),
                        "bpers:b": person()}, {"bplace:c": place})
        self.assertEqual(len(p), 2, p)

    def test_kind_qid_format_and_duplicate_qid(self):
        p = self.run_p({"bpers:a": person(kind="hero"),
                        "bpers:b": person(qid="Q12", qid_status="auto"),
                        "bpers:c": person(qid="Q12", qid_status="auto"),
                        "bpers:d": person(qid="12", qid_status="auto")})
        self.assertEqual(len(p), 4, p)
