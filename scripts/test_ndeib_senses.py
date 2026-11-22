import tempfile
import unittest
from pathlib import Path

from ndeib_senses import senses

TEI = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc><titleStmt><title/></titleStmt></fileDesc></teiHeader>
<text><body>
<head n="2">LEGGE</head>
<head n="2">I. NELL'ANTICO TESTAMENTO</head>
<p>Voce di prova senza persone (Es 20,1).</p>
<milestone unit="separator" rend="—"/>
<head n="2">LEVANTE</head>
<p n="1.">1. Voce di prova per una direzione (Gn 25,6).</p>
<milestone unit="separator" rend="—"/>
<p>LEVATRICE. Voce di prova in linea (Ez 16,4).</p>
<milestone unit="separator" rend="—"/>
<head n="2">LEVI</head>
<p n="1.">1. Prova: figlio di ↗Giacobbe e ↗Lia (Gn 29,34).</p>
<p>Prova di un rinvio a ↗Sichem (Gn 34,25 s.).</p>
<p n="2.">2. Prova: un apostolo (Mc 2,14).</p>
<p n="3.">3. Prova: nomi di una genealogia (Lc 3,24.29).</p>
<head n="3">II. ALTRO</head>
<p n="1.">1. Una seconda numerazione nella stessa voce (Nm 3,17).</p>
<milestone unit="separator" rend="—"/>
<head n="2">LIBNA</head>
<p n="1.">1. Prova: una città nella ↗Sefela (Gs 10,29 s.; 15,42).</p>
<p n="2.">2. Prova: un accampamento (Nm 33,20).</p>
<milestone unit="separator" rend="—"/>
<head n="2">LIBNA</head>
<p>Altra voce con lo stesso lemma (Gs 15,42).</p>
<milestone unit="separator" rend="—"/>
<head n="2">LIBNI</head>
<p n="1.">1. Prova: figlio di qualcuno, in Es 6,17.</p>
<p n="2.">2. Prova: un levita (1 Cr 6,14 <choice><sic>meonato</sic><corr>neonato</corr></choice>).</p>
</body></text></TEI>
"""


class SensesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = Path(tempfile.mkdtemp())
        (d / "t.xml").write_text(TEI, encoding="utf-8")
        cls.s = {x["key"]: x for x in senses(d / "t.xml")}

    def test_headwords_not_subsections(self):
        heads = {x["headword"] for x in self.s.values()}
        self.assertIn("LEVATRICE", heads)
        self.assertNotIn("I. NELL'ANTICO TESTAMENTO", heads)

    def test_levi_has_three_person_senses(self):
        levi = [k for k in self.s if k.startswith("LEVI#") and "~" not in k]
        self.assertEqual(sorted(levi), ["LEVI#1", "LEVI#2", "LEVI#3"])
        self.assertEqual(self.s["LEVI#1"]["kind_guess"], "person")
        self.assertEqual(self.s["LEVI#1"]["xrefs"], ["Giacobbe", "Lia", "Sichem"])
        self.assertIn("btu:gn.29.34", self.s["LEVI#1"]["units"])
        self.assertIn("btu:gn.34.25", self.s["LEVI#1"]["units"])

    def test_place_and_other(self):
        self.assertEqual(self.s["LIBNA#1"]["kind_guess"], "place")
        self.assertEqual(self.s["LEVANTE#1"]["kind_guess"], "other")

    def test_unnumbered_entry_is_one_sense(self):
        self.assertIn("LEVATRICE", self.s)
        self.assertIsNone(self.s["LEVATRICE"]["sense"])

    def test_restarted_numbering_gets_unique_keys(self):
        self.assertIn("LEVI#1~2", self.s)
        self.assertEqual(len(self.s), len(set(self.s)))

    def test_repeated_headword_gets_unique_keys(self):
        self.assertIn("LIBNA~2", self.s)
        self.assertIn("LIBNA#1", self.s)

    def test_sic_is_skipped(self):
        self.assertNotIn("meonato", self.s["LIBNI#2"]["text"])
        self.assertIn("neonato", self.s["LIBNI#2"]["text"])


if __name__ == "__main__":
    unittest.main()
