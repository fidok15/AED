"""scripts/download_aed_data.py takes the dane.gov.pl datasets from aed_standard/sources.json."""
import importlib.util
import os
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


if __name__ == "__main__":
    unittest.main()
