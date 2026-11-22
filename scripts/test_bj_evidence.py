import tempfile
import unittest
from pathlib import Path

from bj_evidence import chrono, index, tree

XML = """<?xml version="1.0" encoding="UTF-8"?>
<bible>
<appendix title="Tavola cronologica" pdf_pages="3004-3024">
 <row pdf_page="3010" y="1"><cell x="11.6-45.2"><l>Ott. 539: riga di prova divisa in Ba-</l><l>bilonia.</l></cell>
  <cell x="48.0-81.7"><l>538: Seconda cella di prova.</l><l>Rinvio di prova (Esd 5,14).</l></cell></row>
</appendix>
<appendix title="Dinastie Asmonea e Erodiana" pdf_pages="3025-3025"><tree pdf_page="3025">
 <person level="0">Antipatro</person>
 <person level="1">11. Erode il Grande 37-4 a.C. ∞ Mariamne I ∞ Mariamne II</person>
 <person level="2">[da Mariamne II] 12. Erode Filippo</person>
 <person level="2">[da Cleopatra] 12c. Filippo tetrarca ∞ Salomè</person>
</tree></appendix>
<appendix title="Indice alfabetico delle note più importanti" pdf_pages="3030-3040">
 <entry pdf_page="3030">Abbà Mt 23,9; Mc 14,36.</entry>
 <entry pdf_page="3030">ABIATÀR Mc 2,26; v. EBIATÀR.</entry>
 <entry pdf_page="3030">ABRAMO: - voce di prova Gen 12,1; 15,6; Gv 8,56.</entry>
</appendix>
</bible>
"""


class EvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d = Path(tempfile.mkdtemp())
        cls.p = d / "bj.xml"
        cls.p.write_text(XML, encoding="utf-8")

    def test_index_names_only(self):
        rows = index(self.p)
        self.assertEqual([r["name"] for r in rows], ["ABIATÀR", "ABRAMO"])
        self.assertEqual(rows[0]["units"], ["btu:mc.2.26"])
        self.assertEqual(rows[0]["see"], ["EBIATÀR"])
        self.assertIn("btu:io.8.56", rows[1]["units"])

    def test_tree(self):
        rows = tree(self.p)
        herod = rows[1]
        self.assertEqual((herod["n"], herod["name"], herod["parent"]), (11, "Erode il Grande", "Antipatro"))
        self.assertEqual(herod["spouses"], ["Mariamne I", "Mariamne II"])
        self.assertEqual(herod["dates"], "37-4 a.C.")
        self.assertEqual((rows[2]["n"], rows[2]["name"], rows[2]["mother"]), (12, "Erode Filippo", "Mariamne II"))
        self.assertEqual((rows[3]["n"], rows[3]["name"]), (12, "Filippo tetrarca"))

    def test_chrono_right_column_only(self):
        rows = chrono(self.p)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["page"], 3010)
        self.assertEqual(rows[0]["units"], ["btu:esd.5.14"])
        self.assertIn("538: Seconda cella di prova.", rows[0]["text"])


if __name__ == "__main__":
    unittest.main()
