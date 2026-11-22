import unittest

from generate_registry import table


class RegistryTest(unittest.TestCase):
    def test_table_by_letter(self):
        cat = {"entries": {
            "bpers:levi.iacob-filius": {"names": {"it": "Levi", "en": "Levi", "la": "Levi"},
                                        "description": {"en": "son of Jacob"}, "attested": ["btu:gn.29.34"],
                                        "qid": "Q1", "kind": "individual"},
            "bpers:aaron": {"names": {"it": "Aronne", "en": "Aaron", "la": "Aaron"},
                            "description": {"en": "brother of Moses"}, "attested": [], "qid": None,
                            "kind": "individual"}}}
        md = table("Persons", cat)
        self.assertLess(md.index("## A"), md.index("## L"))
        self.assertIn("| `bpers:aaron` | Aronne | Aaron | brother of Moses | individual | 0 | |", md)
        self.assertIn("[Q1](https://www.wikidata.org/wiki/Q1)", md)


if __name__ == "__main__":
    unittest.main()
