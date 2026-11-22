import unittest

from overlap import longest_shared_run


class OverlapTest(unittest.TestCase):
    def test_counts_consecutive_words_ignoring_case_and_punctuation(self):
        self.assertEqual(longest_shared_run("Figlio di Saul, amico di Davide", "il figlio di saul amico fedele"), 4)

    def test_no_overlap(self):
        self.assertEqual(longest_shared_run("città della Sefela", "un accampamento nel deserto"), 0)
