import hashlib
import unittest

from extract_mentions import check, extract, find, resolve, utf16


def texts(**units):
    """Invented sentences by unit key (a `__` in the key stands for `@`)."""
    out = {}
    for key, text in units.items():
        key = "btu:" + key.replace("__", "@").replace("_", ".")
        out[key] = {"text": text, "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    return out


def catalogs(persons=None, places=None):
    return {"persons": {"entries": persons or {}}, "places": {"entries": places or {}}}


def person(*attested, labels=None):
    entry = {"type": "person", "attested": list(attested)}
    if labels:
        entry["labels"] = labels
    return entry


def designation(text):
    return {"as": "designation", "editions": {"NVBSE": text, "VGCL": text}}


class UnitHelpersTest(unittest.TestCase):
    def test_utf16_counts_astral_as_two(self):
        self.assertEqual(utf16("a𝔄b", 2), 3)
        self.assertEqual(utf16("abc", 2), 2)

    def test_check_is_first_8_hex_of_sha256(self):
        self.assertEqual(check("Petrus"), hashlib.sha256("Petrus".encode("utf-8")).hexdigest()[:8])
        self.assertEqual(len(check("Petrus")), 8)


class FindTest(unittest.TestCase):
    def test_whole_words_only(self):
        forms = {"bpers:petrus": ["Petrus", "Petri"]}
        self.assertEqual(find("Petrusque venit", forms), [])
        self.assertEqual(find("domus Petri", forms), [(6, 11, "bpers:petrus")])
        self.assertEqual(find("xPetri", forms), [])

    def test_non_ascii_letters_are_letters(self):
        forms = {"bpers:petrus": ["Petrus"]}
        self.assertEqual(find("Petrusë", forms), [])
        self.assertEqual(find("æPetrus", forms), [])
        self.assertEqual(find("(Petrus),", forms), [(1, 7, "bpers:petrus")])

    def test_initial_capital(self):
        forms = {"bpers:petrus": ["Petrus"], "bpers:pharao": ["rex Aegypti"]}
        self.assertEqual(find("et petrus abiit", forms), [])
        self.assertEqual(find("dixit rex Aegypti", forms), [(6, 17, "bpers:pharao")])

    def test_lower_case_single_word_form_is_not_a_name(self):
        forms = {"bloc:via-maris": ["via maris", "via", "viam"]}
        self.assertEqual(find("in via et viam", forms), [])
        self.assertEqual(find("in via maris", forms), [(3, 12, "bloc:via-maris")])

    def test_longest_form_first_at_a_position(self):
        forms = {"bpers:simon": ["Simon"], "bpers:petrus": ["Simon Petrus", "Petrus"]}
        self.assertEqual(find("Simon Petrus dixit", forms),
                         [(0, 12, "bpers:petrus"), (6, 12, "bpers:petrus")])

    def test_shared_form_gives_one_hit_per_entry(self):
        forms = {"bpers:b": ["Zacharias"], "bpers:a": ["Zacharias"]}
        self.assertEqual(find("Zacharias", forms), [(0, 9, "bpers:a"), (0, 9, "bpers:b")])


class ResolveTest(unittest.TestCase):
    def test_designation_is_settled_even_if_a_stop_word(self):
        hits = [(0, 5, "bpers:x")]
        self.assertEqual(resolve("puero", hits, set(), designated={(0, 5, "bpers:x")}),
                         [{"start": 0, "end": 5, "check": check("puero"), "entry": "bpers:x"}])

    def test_unattested_unique_form_needs_outside_leave(self):
        self.assertIn("candidates", resolve("Vita", [(0, 4, "bpers:x")], set())[0])
        self.assertEqual(resolve("Vita", [(0, 4, "bpers:x")], set(), outside=lambda w, i: True)[0]["entry"], "bpers:x")

    def test_stop_word_attested_is_settled(self):
        self.assertEqual(resolve("Vita", [(0, 4, "bpers:x")], {"bpers:x"}),
                         [{"start": 0, "end": 4, "check": check("Vita"), "entry": "bpers:x"}])


class ExtractTest(unittest.TestCase):
    def run_one(self, text, forms, persons=None, places=None, stop=frozenset(), key="gn_1_1", partial=None,
                removed=None, testaments=None):
        """Without catalogs, every entry of `forms` is attested elsewhere in the same book (Genesis)."""
        if persons is None and places is None:
            persons = {id_: person("btu:gn.50.1") for id_ in forms}
        body, report = extract(texts(**{key: text}), forms, catalogs(persons, places), stop, partial, removed,
                               testaments)
        unit = next(iter(body["units"].values()), None)
        return (unit["mentions"] if unit else []), report

    def test_unique_name_is_settled(self):
        mentions, _ = self.run_one("Et dixit Petrus ad eos", {"bpers:petrus": ["Petrus"]})
        self.assertEqual(mentions, [{"start": 9, "end": 15, "check": check("Petrus"), "entry": "bpers:petrus"}])

    def test_body_shape(self):
        body, _ = extract(texts(gn_1_1="Et dixit Petrus", gn_1_2="nihil"), {"bpers:petrus": ["Petrus"]},
                          catalogs({"bpers:petrus": person("btu:gn.50.1")}), frozenset())
        self.assertEqual(body["edition"], "NVBSE")
        self.assertIn("$comment", body)
        self.assertEqual(list(body["units"]), ["btu:gn.1.1"])
        self.assertEqual(body["units"]["btu:gn.1.1"]["hash"],
                         hashlib.sha256("Et dixit Petrus".encode("utf-8")).hexdigest())

    def test_shared_name_settled_by_attestation(self):
        forms = {"bpers:zacharias.a": ["Zacharias"], "bpers:zacharias.b": ["Zacharias"]}
        persons = {"bpers:zacharias.a": person("btu:lc.1.5"), "bpers:zacharias.b": person("btu:zac.1.1")}
        mentions, _ = self.run_one("Fuit Zacharias", forms, persons, key="lc_1_5")
        self.assertEqual(mentions[0]["entry"], "bpers:zacharias.a")
        self.assertNotIn("candidates", mentions[0])

    def test_shared_name_unattested_is_under_review(self):
        forms = {"bpers:zacharias.b": ["Zacharias"], "bpers:zacharias.a": ["Zacharias"]}
        mentions, report = self.run_one("Fuit Zacharias", forms)
        self.assertEqual(mentions, [{"start": 5, "end": 14, "check": check("Zacharias"),
                                     "candidates": ["bpers:zacharias.a", "bpers:zacharias.b"]}])
        self.assertEqual(report["under_review"][0]["words"], "Zacharias")

    def test_shared_name_attested_by_both_is_under_review(self):
        forms = {"bpers:z.a": ["Zacharias"], "bpers:z.b": ["Zacharias"]}
        persons = {"bpers:z.a": person("btu:gn.1.1"), "bpers:z.b": person("btu:gn.1.1")}
        mentions, _ = self.run_one("Fuit Zacharias", forms, persons)
        self.assertEqual(mentions[0]["candidates"], ["bpers:z.a", "bpers:z.b"])

    def test_person_and_place_sharing_a_form_is_shared(self):
        forms = {"bpers:edom": ["Edom"], "bloc:edom": ["Edom"]}
        mentions, _ = self.run_one("in Edom", forms)
        self.assertEqual(mentions[0]["candidates"], ["bloc:edom", "bpers:edom"])

    def test_stop_word_form_is_a_candidate_of_one(self):
        mentions, _ = self.run_one("Vita longa est", {"bpers:vita": ["Vita"]}, stop=frozenset({"vita"}))
        self.assertEqual(mentions, [{"start": 0, "end": 4, "check": check("Vita"), "candidates": ["bpers:vita"]}])

    def test_every_occurrence_is_marked(self):
        mentions, _ = self.run_one("Petrus et Petrus", {"bpers:petrus": ["Petrus"]})
        self.assertEqual([(m["start"], m["end"]) for m in mentions], [(0, 6), (10, 16)])

    def test_nested_spans_kept_crossing_dropped(self):
        forms = {"bpers:pharao": ["rex Aegypti"], "bloc:aegyptus": ["Aegypti"]}
        mentions, report = self.run_one("dixit rex Aegypti", forms)
        self.assertEqual([(m["start"], m["end"], m["entry"]) for m in mentions],
                         [(6, 17, "bpers:pharao"), (10, 17, "bloc:aegyptus")])
        self.assertEqual(report["crossing"], [])
        forms = {"bpers:a": ["Alpha Beta"], "bpers:b": ["Beta Gamma"], "bpers:c": ["Delta"]}
        mentions, report = self.run_one("Alpha Beta Gamma Delta", forms)
        self.assertEqual([m["entry"] for m in mentions], ["bpers:c"])
        self.assertEqual(len(report["crossing"]), 1)
        crossing = report["crossing"][0]
        self.assertEqual(crossing["unit"], "btu:gn.1.1")
        self.assertEqual(sorted(s["words"] for s in crossing["spans"]), ["Alpha Beta", "Beta Gamma"])
        self.assertEqual(report["counts"]["crossing"], 2)

    def test_positions_are_utf16(self):
        mentions, _ = self.run_one("𝔄 Petrus", {"bpers:petrus": ["Petrus"]})
        self.assertEqual((mentions[0]["start"], mentions[0]["end"]), (3, 9))

    def test_attested_entry_not_found_is_reported(self):
        persons = {"bpers:petrus": person("btu:gn.1.1"), "bpers:paulus": person("btu:gn.1.1")}
        _, report = self.run_one("Petrus venit", {"bpers:petrus": ["Petrus"], "bpers:paulus": ["Paulus"]},
                                 persons)
        self.assertEqual(report["unmatched"], [{"unit": "btu:gn.1.1", "entry": "bpers:paulus"}])
        self.assertEqual(report["counts"]["unmatched"], 1)

    def test_designation_settled_only_in_its_unit(self):
        persons = {"bpers:aaron": person("btu:gn.1.1", labels={"btu:gn.1.1": designation("patrem suum")})}
        body, report = extract(texts(gn_1_1="vidit patrem suum", gn_1_2="vidit patrem suum"),
                               {"bpers:aaron": ["Aaron"]}, catalogs(persons), frozenset({"patrem"}))
        self.assertEqual(list(body["units"]), ["btu:gn.1.1"])
        self.assertEqual(body["units"]["btu:gn.1.1"]["mentions"],
                         [{"start": 6, "end": 17, "check": check("patrem suum"), "entry": "bpers:aaron"}])
        self.assertEqual(report["unmatched"], [])

    def test_lower_case_single_word_designation_is_looked_for(self):
        persons = {"bpers:x": person("btu:gn.1.1", labels={"btu:gn.1.1": designation("puero")})}
        mentions, _ = self.run_one("dixit puero", {"bpers:x": ["Xystus"]}, persons)
        self.assertEqual(mentions, [{"start": 6, "end": 11, "check": check("puero"), "entry": "bpers:x"}])

    def test_name_label_is_not_read_from_the_catalog(self):
        persons = {"bpers:petrus": person("btu:gn.1.1", labels={
            "btu:gn.1.1": {"as": "name", "editions": {"NVBSE": "Cephas"}}})}
        mentions, report = self.run_one("Cephas venit", {"bpers:petrus": ["Petrus"]}, persons)
        self.assertEqual(mentions, [])
        self.assertEqual(report["unmatched"], [{"unit": "btu:gn.1.1", "entry": "bpers:petrus"}])

    def test_esther_suffix_dropped_for_attestation_and_designation(self):
        forms = {"bpers:mardochaeus.a": ["Mardochaeus"], "bpers:mardochaeus.b": ["Mardochaeus"]}
        persons = {"bpers:mardochaeus.a": person("btu:est.2.5"), "bpers:mardochaeus.b": person("btu:esd.2.2"),
                   "bpers:assuerus": person("btu:est.2.5", labels={"btu:est.2.5": designation("regis")})}
        body, report = extract(texts(est_2_5__HEBREW="Mardochaeus servus regis", est_2_5__GREEK="Mardochaeus"),
                               forms | {"bpers:assuerus": ["Assuerus"]}, catalogs(persons), frozenset())
        hebrew = body["units"]["btu:est.2.5@HEBREW"]["mentions"]
        self.assertEqual([m["entry"] for m in hebrew], ["bpers:mardochaeus.a", "bpers:assuerus"])
        self.assertEqual(body["units"]["btu:est.2.5@GREEK"]["mentions"][0]["entry"], "bpers:mardochaeus.a")
        # found in one of Esther's two texts: the attestation is matched
        self.assertEqual(report["unmatched"], [])

    def test_unique_name_attested_only_in_another_book_is_under_review(self):
        # a Susanna-like case: the catalog's only bearer of the name is attested in another book
        persons = {"bpers:susanna": person("btu:lc.8.3")}
        mentions, _ = self.run_one("Erat Susanna pulchra", {"bpers:susanna": ["Susanna"]}, persons, key="dn_13_2")
        self.assertEqual(mentions, [{"start": 5, "end": 12, "check": check("Susanna"),
                                     "candidates": ["bpers:susanna"]}])

    def test_unique_name_attested_in_the_same_book_is_settled(self):
        persons = {"bpers:susanna": person("btu:dn.13.1")}
        mentions, _ = self.run_one("Erat Susanna pulchra", {"bpers:susanna": ["Susanna"]}, persons, key="dn_13_2")
        self.assertEqual(mentions[0]["entry"], "bpers:susanna")

    def test_mentioned_does_not_count_for_the_book(self):
        persons = {"bpers:susanna": dict(person("btu:lc.8.3"), mentioned=["btu:dn.13.1"])}
        mentions, _ = self.run_one("Erat Susanna", {"bpers:susanna": ["Susanna"]}, persons, key="dn_13_2")
        self.assertEqual(mentions[0]["candidates"], ["bpers:susanna"])

    def test_partial_form_outside_attested_units_is_under_review(self):
        forms = {"bplace:tres-tabernae": ["Tres Tabernae", "Tres"]}
        places = {"bplace:tres-tabernae": person("btu:act.28.15")}
        mentions, _ = self.run_one("Tres viri", forms, places=places, key="act_28_1",
                                   partial={"bplace:tres-tabernae": ["Tres"]})
        self.assertEqual(mentions[0]["candidates"], ["bplace:tres-tabernae"])
        mentions, _ = self.run_one("ad Tres Tabernae et Tres", forms, places=places, key="act_28_15",
                                   partial={"bplace:tres-tabernae": ["Tres"]})
        self.assertEqual([m["entry"] for m in mentions], ["bplace:tres-tabernae"] * 2)

    def test_partial_form_inside_an_attested_unit_is_settled(self):
        forms = {"bpers:simon-petrus": ["Simon Petrus", "Petrus"]}
        persons = {"bpers:simon-petrus": person("btu:gn.1.1")}
        mentions, _ = self.run_one("dixit Petrus", forms, persons, partial={"bpers:simon-petrus": ["Petrus"]})
        self.assertEqual(mentions[0]["entry"], "bpers:simon-petrus")

    def test_stop_form_outside_attested_units_is_under_review_inside_settled(self):
        persons = {"bplace:media": person("btu:gn.1.1")}
        mentions, _ = self.run_one("Media nocte", {"bplace:media": ["Media"]}, places=persons,
                                   stop=frozenset({"media"}), key="gn_1_2")
        self.assertEqual(mentions[0]["candidates"], ["bplace:media"])
        mentions, _ = self.run_one("in Media", {"bplace:media": ["Media"]}, places=persons,
                                   stop=frozenset({"media"}))
        self.assertEqual(mentions[0]["entry"], "bplace:media")

    def test_outside_form_not_settled_where_a_same_stem_entry_is_attested_unmatched(self):
        # a Hor-like case: the unit attests a mountain whose own form is spelled otherwise there; another
        # place's one-word form found there is not taken for it
        forms = {"bplace:hor.a": ["Hor"], "bplace:mons-hor.b": ["mons Hor"]}
        places = {"bplace:hor.a": person("btu:nm.34.7"), "bplace:mons-hor.b": person("btu:nm.20.22")}
        mentions, report = self.run_one("venerunt ad montem Hor", forms, places=places, key="nm_20_22")
        self.assertEqual(mentions[0]["candidates"], ["bplace:hor.a", "bplace:mons-hor.b"])
        self.assertEqual(report["unmatched"], [{"unit": "btu:nm.20.22", "entry": "bplace:mons-hor.b"}])

    def test_same_stem_guard_folds_case_doubled_letters_and_ligatures(self):
        # a Helles/Heles-like case: one person's name in the unit where a near-homonym is attested
        forms = {"bpers:helles.a": ["Helles"], "bpers:heles.b": ["Heles"]}
        persons = {"bpers:helles.a": person("btu:1par.2.39"), "bpers:heles.b": person("btu:1par.27.10")}
        mentions, _ = self.run_one("Helles princeps", forms, persons, key="1par_27_10")
        self.assertEqual(mentions[0]["candidates"], ["bpers:heles.b", "bpers:helles.a"])
        forms = {"bpers:aeneas.a": ["Aeneas"], "bpers:aenon.b": ["Ænon"]}
        persons = {"bpers:aeneas.a": person("btu:gn.50.1"), "bpers:aenon.b": person("btu:gn.1.1")}
        mentions, _ = self.run_one("Aeneas venit", forms, persons)
        self.assertEqual(mentions[0]["entry"], "bpers:aeneas.a")
        persons["bpers:aenon.b"] = person("btu:gn.1.1")
        forms["bpers:aenon.b"] = ["Æneam"]
        mentions, _ = self.run_one("Aeneas venit", forms, persons)
        self.assertEqual(mentions[0]["candidates"], ["bpers:aeneas.a", "bpers:aenon.b"])

    def test_same_stem_guard_crosses_persons_and_places_and_needs_an_unmatched_entry(self):
        # a Gessuraei-like case: a people's name where the land of a near-homonym is attested
        forms = {"bpers:gessuraei.a": ["Gesuri"], "bplace:gessur.b": ["Gessur"]}
        persons = {"bpers:gessuraei.a": person("btu:ios.13.2")}
        places = {"bplace:gessur.b": person("btu:ios.12.5")}
        mentions, _ = self.run_one("terminos Gesuri", forms, persons, places, key="ios_12_5")
        self.assertEqual(mentions[0]["candidates"], ["bpers:gessuraei.a", "bplace:gessur.b"])
        mentions, _ = self.run_one("terminos Gesuri", forms, persons, places, key="ios_12_6")
        self.assertEqual(mentions[0]["entry"], "bpers:gessuraei.a")
        forms = {"bplace:hor.a": ["Hor"], "bplace:mons-hor.b": ["mons Hor"]}
        places = {"bplace:hor.a": person("btu:nm.34.7"), "bplace:mons-hor.b": person("btu:nm.20.22")}
        mentions, _ = self.run_one("ad mons Hor", forms, places=places, key="nm_20_22")
        self.assertEqual([m.get("entry") for m in mentions], ["bplace:mons-hor.b", "bplace:hor.a"])

    def test_repeated_designation_is_a_candidate_of_one_each_time(self):
        persons = {"bpers:rex": person("btu:gn.1.1", labels={"btu:gn.1.1": designation("regem")})}
        mentions, _ = self.run_one("viderunt regem et duxerunt regem", {"bpers:rex": ["Sedecias"]}, persons)
        self.assertEqual([m.get("candidates") for m in mentions], [["bpers:rex"], ["bpers:rex"]])
        mentions, _ = self.run_one("viderunt regem", {"bpers:rex": ["Sedecias"]}, persons)
        self.assertEqual(mentions[0]["entry"], "bpers:rex")

    def test_outside_settle_refused_when_a_nested_hit_settles_another_attested_entry(self):
        # a Zin-like case: "desertum Sin" of one wilderness, attested elsewhere in the book, around the
        # "Sin" of another wilderness that the unit attests
        forms = {"bplace:desertum-sin": ["desertum Sin"], "bplace:sin.zin": ["Sin"]}
        places = {"bplace:desertum-sin": person("btu:nm.33.11"), "bplace:sin.zin": person("btu:nm.13.21")}
        mentions, _ = self.run_one("in desertum Sin", forms, places=places, key="nm_13_21")
        self.assertEqual([(m.get("entry"), m.get("candidates")) for m in mentions],
                         [(None, ["bplace:desertum-sin", "bplace:sin.zin"]), ("bplace:sin.zin", None)])

    def test_outside_settle_kept_when_the_nested_hit_is_not_attested_or_the_same_entry(self):
        forms = {"bplace:desertum-sin": ["desertum Sin", "Sin"], "bplace:sin.zin": ["Sinai"]}
        places = {"bplace:desertum-sin": person("btu:nm.33.11"), "bplace:sin.zin": person("btu:nm.13.21")}
        mentions, _ = self.run_one("in desertum Sin", forms, places=places, key="nm_13_21",
                                   partial={"bplace:desertum-sin": ["Sin"]})
        self.assertEqual(mentions[0]["entry"], "bplace:desertum-sin")
        forms = {"bplace:desertum-sin": ["desertum Sin"], "bplace:sin.zin": ["Sin"]}
        places = {"bplace:desertum-sin": person("btu:nm.33.11"), "bplace:sin.zin": person("btu:nm.13.1")}
        mentions, _ = self.run_one("in desertum Sin", forms, places=places, key="nm_13_21")
        self.assertEqual(mentions[0]["entry"], "bplace:desertum-sin")

    def test_reviewed_removal_is_never_settled_outside(self):
        # an Iudaea-like case: the unit was reviewed as not naming the region (an adjective there)
        places = {"bplace:iudaea": person("btu:act.26.20")}
        mentions, _ = self.run_one("mulieris Iudaeae", {"bplace:iudaea": ["Iudaeae"]}, places=places,
                                   key="act_16_1", removed={"bplace:iudaea": ["btu:act.16.1"]})
        self.assertEqual(mentions[0]["candidates"], ["bplace:iudaea"])
        mentions, _ = self.run_one("mulieris Iudaeae", {"bplace:iudaea": ["Iudaeae"]}, places=places,
                                   key="act_16_2", removed={"bplace:iudaea": ["btu:act.16.1"]})
        self.assertEqual(mentions[0]["entry"], "bplace:iudaea")

    def test_lower_case_canonical_form_matches_only_where_attested(self):
        places = {"bplace:praetorium": person("btu:io.18.33")}
        forms = {"bplace:praetorium": ["praetorium"]}
        mentions, report = self.run_one("intravit in praetorium", forms, places=places, key="io_18_33")
        self.assertEqual(mentions, [{"start": 12, "end": 22, "check": check("praetorium"),
                                     "entry": "bplace:praetorium"}])
        self.assertEqual(report["unmatched"], [])
        mentions, _ = self.run_one("intravit in praetorium", forms, places=places, key="io_18_34")
        self.assertEqual(mentions, [])

    def test_lower_case_partial_form_never_matches(self):
        places = {"bplace:via-maris": person("btu:is.8.23")}
        mentions, _ = self.run_one("per via", {"bplace:via-maris": ["via Maris", "via"]}, places=places,
                                   key="is_8_23", partial={"bplace:via-maris": ["via"]})
        self.assertEqual(mentions, [])

    def test_designation_repeats_counted_before_longest_span(self):
        persons = {"bpers:a": person("btu:gn.1.1", labels={"btu:gn.1.1": designation("rex")}),
                   "bpers:b": person("btu:gn.1.1", labels={"btu:gn.1.1": designation("rex Israel")})}
        mentions, _ = self.run_one("rex Israel et rex", {"bpers:a": ["Alpha"], "bpers:b": ["Beta"]}, persons)
        self.assertEqual([(m.get("entry"), m.get("candidates")) for m in mentions],
                         [("bpers:b", None), (None, ["bpers:a"])])

    def test_entry_found_only_in_a_crossing_span_is_still_a_rival(self):
        forms = {"bpers:a": ["Helles"], "bpers:b": ["Urbs Nova", "Heles"], "bpers:c": ["Nova Roma"]}
        persons = {"bpers:a": person("btu:gn.50.1"), "bpers:b": person("btu:gn.1.1"), "bpers:c": person("btu:gn.50.2")}
        mentions, _ = self.run_one("Helles Urbs Nova Roma", forms, persons)
        self.assertEqual(mentions[0]["candidates"], ["bpers:a", "bpers:b"])

    TESTAMENTS = {"gn": "OT", "ex": "OT", "idt": "OT", "lc": "NT", "io": "NT", "mt": "NT"}

    def test_candidates_only_from_the_units_testament(self):
        # a Gen 1:10-like case: a form whose only bearers are attested in the New Testament
        forms = {"bpers:maria.a": ["Maria"], "bpers:maria.b": ["Maria"]}
        persons = {"bpers:maria.a": person("btu:lc.1.27"), "bpers:maria.b": person("btu:io.19.25")}
        mentions, report = self.run_one("vocavit Maria", forms, persons, testaments=self.TESTAMENTS)
        self.assertEqual(mentions, [])
        self.assertEqual(report["counts"]["mentions"], 0)
        # a Miriam-like Old Testament bearer is the only candidate left
        forms["bpers:maria.soror-moysi"] = ["Maria"]
        persons["bpers:maria.soror-moysi"] = person("btu:ex.15.20")
        mentions, _ = self.run_one("vocavit Maria", forms, persons, testaments=self.TESTAMENTS)
        self.assertEqual(mentions[0]["candidates"], ["bpers:maria.soror-moysi"])
        # the New Testament is unchanged: it names Old Testament persons too (Isaias, Melchisedech)
        mentions, _ = self.run_one("vocavit Maria", forms, persons, key="mt_2_5", testaments=self.TESTAMENTS)
        self.assertEqual(mentions[0]["candidates"], ["bpers:maria.a", "bpers:maria.b", "bpers:maria.soror-moysi"])
        persons = {"bpers:isaias": person("btu:ex.1.1")}
        mentions, _ = self.run_one("Isaias", {"bpers:isaias": ["Isaias"]}, persons, key="lc_4_17",
                                   testaments=self.TESTAMENTS)
        self.assertEqual(mentions[0]["candidates"], ["bpers:isaias"])

    def test_places_are_not_limited_by_testament(self):
        # Antioch, Cilicia, Cyprus in Maccabees are the places of Acts
        places = {"bplace:antiochia": person("btu:act.11.26")}
        mentions, _ = self.run_one("in Antiochiam", {"bplace:antiochia": ["Antiochiam"]}, places=places,
                                   key="gn_1_1", testaments=self.TESTAMENTS)
        self.assertEqual(mentions[0]["candidates"], ["bplace:antiochia"])

    def test_deuterocanonical_books_are_old_testament(self):
        persons = {"bpers:holophernes": person("btu:idt.2.4")}
        mentions, _ = self.run_one("Holophernes", {"bpers:holophernes": ["Holophernes"]}, persons, key="gn_1_1",
                                   testaments=self.TESTAMENTS)
        self.assertEqual(mentions[0]["candidates"], ["bpers:holophernes"])

    def test_outside_settle_needs_the_same_testament(self):
        persons = {"bpers:susanna": person("btu:lc.8.3")}
        mentions, _ = self.run_one("Susanna", {"bpers:susanna": ["Susanna"]}, persons, key="io_1_1",
                                   testaments=self.TESTAMENTS)
        self.assertEqual(mentions[0]["candidates"], ["bpers:susanna"])  # same Testament, other book
        mentions, _ = self.run_one("Susanna", {"bpers:susanna": ["Susanna"]}, persons, key="gn_1_1",
                                   testaments=self.TESTAMENTS)
        self.assertEqual(mentions, [])  # other Testament: no mention at all

    def test_shared_form_settles_to_its_one_bearer_attested_in_the_book(self):
        # an Eden-like case: the garden is attested in Genesis, the Levite and the region elsewhere
        forms = {"bplace:eden.paradisus": ["Eden"], "bplace:eden.region": ["Eden"], "bpers:eden.levita": ["Eden"]}
        persons = {"bpers:eden.levita": person("btu:2par.29.12")}
        places = {"bplace:eden.paradisus": person("btu:gn.2.8", "btu:gn.2.15", "btu:gn.3.23"),
                  "bplace:eden.region": person("btu:am.1.5")}
        mentions, _ = self.run_one("ad orientem Eden", forms, persons, places, key="gn_3_24")
        self.assertEqual(mentions[0]["entry"], "bplace:eden.paradisus")
        places["bplace:eden.region"] = person("btu:gn.3.1")  # a second firm bearer: the chapter
        mentions, _ = self.run_one("ad orientem Eden", forms, persons, places, key="gn_3_24")
        self.assertEqual(mentions[0]["candidates"], ["bpers:eden.levita", "bplace:eden.paradisus", "bplace:eden.region"])
        mentions, _ = self.run_one("ad orientem Eden", forms, persons, places, key="ex_1_1")
        self.assertEqual(len(mentions[0]["candidates"]), 3)

    def test_shared_form_settles_by_book_only_with_the_chapter_or_three_units(self):
        forms = {"bpers:iason.a": ["Iason"], "bpers:iason.b": ["Iason"]}
        persons = {"bpers:iason.a": person("btu:2mac.2.23"), "bpers:iason.b": person("btu:1mac.8.17")}
        mentions, _ = self.run_one("ambiebat Iason", forms, persons, key="2mac_4_7")
        self.assertEqual(mentions[0]["candidates"], ["bpers:iason.a", "bpers:iason.b"])  # one unit elsewhere
        mentions, _ = self.run_one("ambiebat Iason", forms, persons, key="2mac_2_24")
        self.assertEqual(mentions[0]["entry"], "bpers:iason.a")  # same chapter
        persons["bpers:iason.a"] = person("btu:2mac.1.1", "btu:2mac.2.23", "btu:2mac.9.1")
        mentions, _ = self.run_one("ambiebat Iason", forms, persons, key="2mac_4_7")
        self.assertEqual(mentions[0]["entry"], "bpers:iason.a")  # three units in the book
        # a second bearer cited once in the book still keeps it under review (a Hebron-like case)
        persons["bpers:iason.b"] = person("btu:2mac.12.1")
        mentions, _ = self.run_one("ambiebat Iason", forms, persons, key="2mac_4_7")
        self.assertEqual(mentions[0]["candidates"], ["bpers:iason.a", "bpers:iason.b"])

    def test_shared_form_settle_keeps_the_guards(self):
        forms = {"bplace:a": ["Sela"], "bpers:b": ["Sela"]}
        places = {"bplace:a": person("btu:gn.3.5")}
        persons = {"bpers:b": person("btu:am.1.5")}
        mentions, _ = self.run_one("Sela", forms, persons, places, key="gn_3_1", stop=frozenset({"sela"}))
        self.assertIn("candidates", mentions[0])
        mentions, _ = self.run_one("Sela", forms, persons, places, key="gn_3_1", partial={"bplace:a": ["Sela"]})
        self.assertIn("candidates", mentions[0])
        # a same-stem entry attested in the unit but not found is a rival
        forms["bpers:c"] = ["Selah"]
        persons["bpers:c"] = person("btu:gn.3.1")
        mentions, _ = self.run_one("Sela", forms, persons, places, key="gn_3_1")
        self.assertEqual(mentions[0]["candidates"], ["bpers:b", "bpers:c", "bplace:a"])

    def test_longest_span_wins_across_names_and_designations(self):
        # a canonical "rex Aegypti" and a designation "rex" at the same start: only the longer is kept
        persons = {"bpers:pharao": person("btu:gn.1.1"),
                   "bpers:b": person("btu:gn.1.1", labels={"btu:gn.1.1": designation("rex")})}
        mentions, _ = self.run_one("rex Aegypti venit", {"bpers:pharao": ["rex Aegypti"], "bpers:b": ["Beta"]},
                                   persons)
        self.assertEqual([(m["start"], m["end"], m.get("entry")) for m in mentions], [(0, 11, "bpers:pharao")])
        # a designation alone at its start is still kept and settled
        mentions, _ = self.run_one("rex venit", {"bpers:pharao": ["rex Aegypti"], "bpers:b": ["Beta"]}, persons)
        self.assertEqual([m.get("entry") for m in mentions], ["bpers:b"])

    def test_esther_book_is_est(self):
        persons = {"bpers:aman": person("btu:est.3.1")}
        body, _ = extract(texts(est_3_2__GREEK="Aman"), {"bpers:aman": ["Aman"]}, catalogs(persons), frozenset())
        self.assertEqual(body["units"]["btu:est.3.2@GREEK"]["mentions"][0]["entry"], "bpers:aman")

    def test_counts(self):
        forms = {"bpers:petrus": ["Petrus"], "bpers:z.a": ["Zacharias"], "bpers:z.b": ["Zacharias"]}
        _, report = self.run_one("Petrus et Zacharias", forms)
        self.assertEqual(report["counts"]["settled"], 1)
        self.assertEqual(report["counts"]["under_review"], 1)
        self.assertEqual(report["counts"]["units"], 1)


if __name__ == "__main__":
    unittest.main()
