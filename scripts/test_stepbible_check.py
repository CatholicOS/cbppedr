import tempfile
import unittest
from pathlib import Path

from stepbible_check import gaps, read_tipnr

T = "\t"
TIPNR = "\n".join([
    "$========== PERSON(s)" + T * 3,
    "Philip@Mat.14.3-Luk=G5376H" + T + "Son of Herod",
    "– Named" + T + "Philip@Mat.14.3-Luk" + T + "G5376H" + T + "Philip" + T + "Mat.14.3; Mrk.6.17",
    "– Total" + T + "Philip" + T + "Philip" + T + "G5376H" + T + "Mat.14.3; Mrk.6.17; " + T + "2",
    "$========== PERSON(s)" + T * 3,
    "Libni@Exo.6.17=H3845" + T + "Son of Gershon",
    "– Named" + T + "Libni@Exo.6.17" + T + "H3845" + T + "Libni" + T + "Exo.6.17; Num.3.18",
    "$========== PLACE" + T * 3,
    "Libnah@Num.33.20=H3841" + T + "Libnah",
    "– Named" + T + "Libnah@Num.33.20" + T + "H3841" + T + "Libnah" + T + "Num.33.20",
    "",
])


class StepTest(unittest.TestCase):
    def setUp(self):
        p = Path(tempfile.mkdtemp()) / "t.txt"
        p.write_text(TIPNR, encoding="utf-8")
        self.recs = read_tipnr(p)

    def test_read(self):
        self.assertEqual([(r["name"], r["type"]) for r in self.recs],
                         [("Philip@Mat.14.3-Luk", "person"), ("Libni@Exo.6.17", "person"), ("Libnah@Num.33.20", "place")])
        self.assertIn("btu:mt.14.3", self.recs[0]["units"])

    def test_gaps_need_name_and_verse(self):
        entries = [{"type": "person", "en": "Philip", "attested": {"btu:mt.14.3"}},
                   {"type": "person", "en": "Levi", "attested": {"btu:ex.6.17"}},
                   {"type": "place", "en": "Libna", "attested": {"btu:nm.33.20"}}]
        self.assertEqual([r["name"] for r in gaps(self.recs, entries)], ["Libni@Exo.6.17"])


if __name__ == "__main__":
    unittest.main()
