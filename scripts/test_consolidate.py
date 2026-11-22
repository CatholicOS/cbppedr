import unittest

from consolidate import consolidate

BATCH = [{"key": "LEVI#1"}, {"key": "NOME#1"}, {"key": "NOME#1"}]
SENSES = [{"key": "LEVI#1"}, {"key": "NOME#1"}, {"key": "NOME#1~2"}]
REVIEW = [{"key": "LEVI#1", "type": "person", "id": "bpers:levi", "it": "Levi", "en": "Levi", "latin": "Levi",
           "descr_it": "x", "descr_en": "y", "relations": [{"rel": "child_of", "target": "Giacobbe",
                                                             "target_key": "NOME#1"}],
           "certain": True, "note": "private remark", "parts": None, "kind": "individual"},
          {"key": "NOME#1", "type": "none"}, {"key": "NOME#1", "type": "none", "note": "z"}]


class ConsolidateTest(unittest.TestCase):
    def test_positional_rekey_and_no_notes(self):
        out = consolidate([(BATCH, REVIEW)], SENSES)
        self.assertEqual([d["key"] for d in out], ["LEVI#1", "NOME#1", "NOME#1~2"])
        self.assertNotIn("note", out[0])
        self.assertEqual(out[0]["relations"][0]["target_key"], "NOME#1")

    def test_mismatch_raises(self):
        with self.assertRaises(ValueError):
            consolidate([(BATCH, REVIEW[:2])], SENSES)


if __name__ == "__main__":
    unittest.main()
