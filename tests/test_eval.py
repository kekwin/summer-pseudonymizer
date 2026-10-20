"""Regressionsport: korpusets tal må ikke blive dårligere. Skærp grænserne, når motoren forbedres."""
import json
import unittest

import _path
from pseudonymizer.evaluation import ZERO_TOLERANCE, evaluate

CORPUS = json.loads((_path.ROOT / "corpus" / "da_synthetic.json").read_text(encoding="utf-8"))


class EvalGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = evaluate(CORPUS)

    def rec(self, typ):
        return self.r["recall"][typ]["andel"]

    def test_identifiers_zero_tolerance(self):
        for t in ZERO_TOLERANCE:
            self.assertEqual(self.rec(t), 1.0, t)

    def test_known_names_and_typos(self):
        self.assertEqual(self.rec("navn-kendt"), 1.0)
        self.assertEqual(self.rec("navn-stavefejl"), 1.0)

    def test_unknown_names(self):
        self.assertEqual(self.rec("navn-ukendt"), 1.0)
        self.assertEqual(self.rec("navn-kendt-småt"), 1.0)
        self.assertEqual(self.rec("navn-ukendt-småt"), 1.0)  # navnelisten (små bogstaver tæller)
        # kendt hul: ukendte navne først i en sætning uden NER. Må kun blive bedre.
        self.assertGreaterEqual(self.rec("navn-ukendt-satsstart"), 0.8)

    def test_overmasking_not_worse(self):
        self.assertLessEqual(self.r["overmaskering"]["andel"], 0.04)

    def test_no_document_withheld_by_guard_in_corpus(self):
        self.assertEqual(self.r["tilbageholdte_dokumenter"], [])


if __name__ == "__main__":
    unittest.main()
