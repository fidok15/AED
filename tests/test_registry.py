"""Source registry aed_standard/sources.json. Run: python3 -m unittest tests.test_registry"""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from aed_standard import registry as R  # noqa: E402

VALID = {"id": "testowo", "label": "Testowo", "zrodlo": "dane.gov.pl/999999", "priority": 1, "file": "x.csv",
         "format": "csv", "record_id": {"column": "Id"}, "fields": {"nazwa": "Nazwa"}}


class RegistryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, data):
        path = os.path.join(self.tmp.name, "sources.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
        return path

    def test_real_registry_is_valid(self):
        sources, licences, errors = R.load_registry()
        self.assertEqual(errors, [])
        self.assertEqual([s["id"] for s in sources],
                         ["krosno", "marki", "przemysl", "legionowo", "warszawa", "openstreetmap"])
        self.assertEqual(licences["ODbL 1.0 (© OpenStreetMap contributors)"], "ODbL 1.0")
        self.assertEqual([s["copy_values_on_merge"] for s in sources], [True] * 5 + [False])

    def test_bad_entries_are_skipped_with_polish_errors(self):
        bad = [dict(VALID, id="pole", zrodlo="a", fields={"ulica": "Street"}),  # unknown target field
               dict(VALID, id="naprawa", zrodlo="b", fixes=["magic"]),          # unknown fix
               dict(VALID, id="prio", zrodlo="c", priority=0),                  # 0 is reserved for zgloszenie
               dict(VALID, id="dubel"),                                         # duplicate zrodlo
               {k: v for k, v in dict(VALID, id="bezformatu", zrodlo="e").items() if k != "format"}]
        sources, _, errors = R.load_registry(self.write({"licences": {}, "sources": [VALID] + bad}))
        self.assertEqual([s["id"] for s in sources], ["testowo"])
        self.assertEqual(len(errors), 5, errors)
        for name in ("pole", "naprawa", "prio", "dubel", "bezformatu"):
            self.assertTrue(any(name in e for e in errors), name)
        self.assertIn("ulica", " ".join(errors))

    def test_unknown_key_is_an_error(self):  # catches typos such as "feilds"
        sources, _, errors = R.load_registry(self.write({"licences": {}, "sources": [dict(VALID, feilds={})]}))
        self.assertEqual(sources, [])
        self.assertTrue(any("feilds" in e for e in errors), errors)

    def test_submission_zrodlo_is_reserved(self):
        _, _, errors = R.load_registry(self.write({"licences": {}, "sources": [dict(VALID, zrodlo=R.SUBMISSION)]}))
        self.assertEqual(len(errors), 1)

    def test_broken_json_raises(self):
        with self.assertRaises(ValueError):
            R.load_registry(self.write("{ nie json"))
        with self.assertRaises(ValueError):
            R.load_registry(self.write({"sources": []}))


if __name__ == "__main__":
    unittest.main()
