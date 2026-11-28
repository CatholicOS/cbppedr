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

    def test_description_limit_30_words_220_characters(self):
        def run(d):
            return problems({"persons": cat({"bpers:levi.iacob-filius": person(description={"it": d, "en": "ok"})}),
                             "places": cat({}), "events": cat({})})
        self.assertEqual(run(" ".join(["parola"] * 30)), [])  # 30 words, 209 characters
        self.assertEqual(len(run(" ".join(["parola"] * 31))), 1)
        self.assertEqual(len(run("x" * 221)), 1)
        self.assertEqual(run("x" * 220), [])

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
        shared = conjecture_problems("bpers:a", {"attested": ["btu:gn.29.34"], "conjectures": [good]},
                                     {"bpers:a", "bpers:b"}, src, {"bpers:b": ["btu:gn.29.34"]})
        self.assertEqual(len(shared), 1, shared)
        self.assertEqual(len(conjecture_problems("bpers:a", {"conjectures": [dict(good, opinions=[
            {"by": "ndeib:x y z", "says": "suggests", "summary": "s"}])]}, {"bpers:a", "bpers:b"}, src)), 1)
        psrc = dict(src, pub={}, **{"pub:meier-1992": {"authority": "authoritative"}})
        pub = lambda by: conjecture_problems("bpers:a", {"conjectures": [dict(good, opinions=[
            {"by": by, "says": "suggests", "summary": "s"}])]}, {"bpers:a", "bpers:b"}, psrc)
        self.assertEqual(pub("pub:meier-1992#p12"), [])
        self.assertEqual(len(pub("pub:brown-1994#p5")), 1)  # not listed
        self.assertEqual(len(pub("pub:Meier 1992")), 1)  # malformed
        psrc["pub:müller-2001"] = {"authority": "authoritative"}
        self.assertEqual(pub("pub:müller-2001#§3"), [])

        bad = dict(good, status="maybe", opinions=[{"by": "wiki:x", "says": "thinks", "summary": ""}])
        self.assertEqual(len(conjecture_problems("bpers:a", {"conjectures": [bad]}, {"bpers:a", "bpers:b"}, src)), 4)

    def test_listed_publications(self):
        from validate import publication_problems
        self.assertEqual(publication_problems({"pub:meier-1992": {"title": "A Marginal Jew", "authority": "authoritative"}}), [])
        self.assertEqual(len(publication_problems({"pub:Meier 1992": {"title": "x", "authority": "authoritative"},
                                                   "pub:brown-1994": {"authority": "maybe"}})), 2)


class EvidenceTest(unittest.TestCase):
    def run_p(self, ev):
        return problems({"persons": cat({"bpers:a": person(evidence=ev)}), "places": cat({}), "events": cat({})})

    def test_known_kinds_pass(self):
        self.assertEqual(self.run_p(["ndeib:LEVI#1", "bj:herodian-tree", "nv:btu:gn.29.34", "bj:note:At.12,12#p2648"]), [])

    def test_unknown_kind_and_unknown_verse(self):
        p = self.run_p(["wiki:Levi", "nv:btu:gn.99.1", "nv:gn.29.34"])
        self.assertEqual(len(p), 3, p)

    def test_no_evidence(self):
        self.assertEqual(len(self.run_p([])), 1)

    def test_reviewer_and_listed_publication_evidence(self):
        # a maintainer's identification: the reviewer's round and a published Catholic source
        sources = {"reviewer": {}, "pub": {}, "pub:catechismus-1997": {"title": "x", "authority": "authoritative"}}
        run = lambda ev: problems({"persons": cat({"bpers:a": person(evidence=ev)}), "places": cat({}),
                                   "events": cat({})}, sources)
        self.assertEqual(run(["reviewer:round2", "pub:catechismus-1997#391", "nv:btu:gn.29.34"]), [])
        self.assertEqual(len(run(["pub:nemo-2000#1"])), 1)  # not listed in sources.json
        self.assertEqual(len(run(["pub:Bad Key"])), 1)
        self.assertEqual(len(self.run_p(["reviewer:round2"])), 0)  # without sources: the form only


class MentionsTest(unittest.TestCase):
    H = "a" * 64
    IDS = {"bpers:levi", "bplace:roma"}
    UNITS = {"btu:gn.29.34", "btu:est.1.1"}

    def doc(self, *mentions, key="btu:gn.29.34"):
        return {"edition": "NVBSE", "units": {key: {"hash": self.H, "mentions": list(mentions)}}}

    def check(self, doc):
        from validate import mention_problems
        return mention_problems(doc, self.IDS, self.UNITS, "t")

    def m(self, **kw):
        d = {"start": 0, "end": 4, "check": "0123abcd", "entry": "bpers:levi"}
        d.update(kw)
        return d

    def test_clean(self):
        d = self.doc(self.m(), {"start": 5, "end": 9, "check": "0123abcd", "candidates": ["bpers:levi", "bplace:roma"]},
                     key="btu:est.1.1@GREEK")
        self.assertEqual(self.check(d), [])

    def test_mention_needs_entry_xor_candidates(self):
        both = self.m(candidates=["bpers:levi"])
        neither = {"start": 0, "end": 4, "check": "0123abcd"}
        empty = {"start": 0, "end": 4, "check": "0123abcd", "candidates": []}
        for bad in (both, neither, empty):
            self.assertTrue(self.check(self.doc(bad)), bad)

    def test_candidates_sorted_unique(self):
        for c in (["bplace:roma", "bpers:levi"], ["bpers:levi", "bpers:levi"]):
            self.assertTrue(self.check(self.doc({"start": 0, "end": 4, "check": "0123abcd", "candidates": c})))

    def test_mention_ids_must_exist(self):
        self.assertTrue(self.check(self.doc(self.m(entry="bpers:nemo"))))
        self.assertTrue(self.check(self.doc({"start": 0, "end": 4, "check": "0123abcd",
                                             "candidates": ["bpers:levi", "bpers:nemo"]})))

    def test_mention_span_inside_text(self):
        for bad in (self.m(start=4, end=4), self.m(start=-1, end=3), self.m(start=5, end=2)):
            self.assertTrue(self.check(self.doc(bad)), bad)

    def test_hash_check_and_unit_key(self):
        self.assertTrue(self.check(self.doc(self.m(check="XYZ"))))
        self.assertTrue(self.check(self.doc(self.m(check="0123ABCD"))))
        d = self.doc(self.m())
        d["units"]["btu:gn.29.34"]["hash"] = "A" * 64
        self.assertTrue(self.check(d))
        self.assertTrue(self.check(self.doc(self.m(), key="btu:gn.99.1")))
        self.assertTrue(self.check(self.doc(self.m(), key="btu:gn.29.34@LATIN")))

    def test_non_string_ids_are_problems_not_errors(self):
        self.assertTrue(self.check(self.doc(self.m(entry=["bpers:levi"]))))
        self.assertTrue(self.check(self.doc({"start": 0, "end": 4, "check": "0123abcd",
                                             "candidates": [["bpers:levi"], "bplace:roma"]})))
        self.assertTrue(self.check(self.doc({"start": 0, "end": 4, "check": "0123abcd", "candidates": [1]})))

    def test_tradition_suffix_only_on_esther(self):
        self.assertEqual(self.check(self.doc(self.m(), key="btu:est.1.1@HEBREW")), [])
        self.assertTrue(self.check(self.doc(self.m(), key="btu:gn.29.34@GREEK")))

    def test_unknown_properties_rejected(self):
        d = self.doc(self.m(text=1))
        self.assertTrue(self.check(d))
        d = self.doc(self.m())
        d["units"]["btu:gn.29.34"]["words"] = 1
        self.assertTrue(self.check(d))
        d = self.doc(self.m())
        d["extra"] = 1
        self.assertTrue(self.check(d))
        d = self.doc(self.m())
        d["$comment"] = "free"
        self.assertEqual(self.check(d), [])

    def test_curated_unit_wins(self):
        from extract_mentions import merged_mentions
        a = {"edition": "NVBSE", "units": {"u1": {"hash": "h", "mentions": [1]}, "u2": {"hash": "h", "mentions": [2]},
                                           "u3": {"hash": "h", "mentions": [3]}}}
        c = {"edition": "NVBSE", "units": {"u1": {"hash": "h", "mentions": [9]}, "u2": {"hash": "h", "mentions": []},
                                           "u4": {"hash": "h", "mentions": [4]}}}
        m = merged_mentions(a, c)
        self.assertEqual({k: v["mentions"] for k, v in m["units"].items()}, {"u1": [9], "u3": [3], "u4": [4]})
        self.assertEqual(a["units"]["u1"]["mentions"], [1])


class MentionsStrictShapeTest(MentionsTest):
    def test_trailing_newline_refused_in_hash_check_and_strings(self):
        from validate import mention_text_problems
        self.assertTrue(self.check(self.doc(self.m(check="0123abcd\n"))))
        d = self.doc(self.m())
        d["units"]["btu:gn.29.34"]["hash"] = self.H + "\n"
        self.assertTrue(self.check(d))
        self.assertTrue(mention_text_problems({"edition": "NVBSE\n"}, "t"))

    def test_non_object_documents_are_problems_not_errors(self):
        from validate import mention_docs_problems
        for bad in ([], None, "x"):
            self.assertTrue(self.check(bad))
            self.assertTrue(mention_docs_problems(bad, {"edition": "NVBSE", "units": {}}, self.IDS, self.UNITS))
            self.assertTrue(mention_docs_problems(self.doc(self.m()), bad, self.IDS, self.UNITS))

    def test_units_must_be_a_dict(self):
        self.assertTrue(self.check({"edition": "NVBSE", "units": []}))
        self.assertTrue(self.check({"edition": "NVBSE"}))
        self.assertEqual(self.check({"edition": "NVBSE", "units": {}}), [])

    def test_structurally_invalid_input_is_not_merged(self):
        from validate import mention_docs_problems
        gen = self.doc(self.m())
        cur = {"edition": "NVBSE", "units": {"btu:gn.29.34": None}}
        p = mention_docs_problems(gen, cur, self.IDS, self.UNITS)
        self.assertTrue(any("malformed" in x for x in p))
        ok = {"edition": "NVBSE", "units": {"btu:gn.29.34": {"hash": self.H, "mentions": []}}}
        self.assertEqual(mention_docs_problems(gen, ok, self.IDS, self.UNITS), [])
        self.assertTrue(mention_docs_problems({"edition": "NVBSE", "units": []}, ok, self.IDS, self.UNITS))


class MentionsKeyTextTest(unittest.TestCase):
    def test_text_in_any_property_name_refused(self):
        from validate import mention_text_problems
        doc = {"edition": "NVBSE", "Et dixit": 1, "units": {"btu:gn.1.1": {"hash": "a" * 64, "Et dixit": 2, "mentions": [
            {"start": 0, "end": 4, "check": "0123abcd", "entry": "bpers:levi", "Et dixit": 3}]}}}
        self.assertEqual(len(mention_text_problems(doc, "t")), 3)

    def test_clean_and_comment_allowed(self):
        from validate import mention_text_problems
        doc = {"$comment": "Free text", "edition": "NVBSE", "units": {"btu:gn.1.1": {"hash": "a" * 64, "mentions": [
            {"start": 0, "end": 4, "check": "0123abcd", "candidates": ["bpers:levi"]}]}}}
        self.assertEqual(mention_text_problems(doc, "t"), [])


class MentionedFieldTest(unittest.TestCase):
    def check(self, mentioned, attested=("btu:gn.29.34",)):
        from validate import problems
        e = {"type": "person", "kind": "individual", "names": {"it": "a", "en": "a"}, "description": {},
             "attested": list(attested), "relations": [], "evidence": ["ndeib:A#1"], "mentioned": mentioned}
        return problems({"persons": {"entries": {"bpers:a": e}}, "places": {"entries": {}}, "events": {"entries": {}}})

    def test_known_unique_and_not_attested(self):
        self.assertEqual(self.check(["btu:gn.1.1", "btu:gn.1.2"]), [])
        self.assertTrue(self.check(["btu:gn.99.99"]))
        self.assertTrue(self.check(["btu:gn.29.34"]))
        self.assertTrue(self.check(["btu:gn.1.1", "btu:gn.1.1"]))

    def test_malformed_mentioned_is_a_problem_not_an_error(self):
        for bad in ([["btu:gn.1.1"]], 5, "btu:gn.1.1", [1]):
            self.assertTrue(self.check(bad), bad)


class MentionsNoTextTest(unittest.TestCase):
    def check(self, value):
        from validate import mention_text_problems
        doc = {"$comment": "free text is allowed here", "edition": "NVBSE", "units": {
            "btu:gn.1.1": {"hash": "a" * 64, "mentions": [{"start": 0, "end": 4, "check": "0123abcd", "entry": value}]}}}
        return mention_text_problems(doc, "t")

    def test_ids_and_hex_pass(self):
        self.assertEqual(self.check("bpers:levi"), [])
        self.assertEqual(self.check("bplace:roma.x"), [])

    def test_text_refused(self):
        self.assertTrue(self.check("In principio erat Verbum"))
        self.assertTrue(self.check("Levi"))

    def test_text_in_a_key_or_list_refused(self):
        doc = {"edition": "NVBSE", "units": {"btu:gn.1.1": {"hash": "a" * 64, "mentions": [
            {"start": 0, "end": 4, "check": "0123abcd", "candidates": ["bpers:levi", "Et dixit"]}], "text": "Et dixit"}}}
        from validate import mention_text_problems
        self.assertEqual(len(mention_text_problems(doc, "t")), 2)
