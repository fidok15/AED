"""scripts/download_aed_data.py takes the dane.gov.pl datasets from aed_standard/sources.json."""
import importlib.util
import json
import os
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location("download_aed_data", os.path.join(ROOT, "scripts", "download_aed_data.py"))
dl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dl)


class DownloadRegistryTest(unittest.TestCase):
    def test_registry_reproduces_previous_dataset_list(self):
        self.assertEqual(dl.dane_gov_datasets(dl.REGISTRY_PATH), {
            3624: ("krosno", None), 4955: ("marki", None), 4581: ("przemysl", None),
            39512: ("warszawa", None), 40593: ("legionowo", {2625221})})

    def test_broken_entry_skips_only_that_dataset(self):
        sources = [{"id": "ok", "dane_gov_pl": {"dataset_id": 1}},
                   {"id": "bez-zbioru", "dane_gov_pl": {}},
                   {"dane_gov_pl": {"dataset_id": 3}},
                   {"id": "zle-zasoby", "dane_gov_pl": {"dataset_id": 4, "resources": 5}}]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sources.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"licences": {}, "sources": sources}, f)
            errors = []
            self.assertEqual(dl.dane_gov_datasets(path, errors), {1: ("ok", None)})
        self.assertEqual(len(errors), 3, errors)


if __name__ == "__main__":
    unittest.main()
