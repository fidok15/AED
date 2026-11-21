"""Harvester XML feed on the real registry (service database seeded from datasets/raw) and the portal's own XSD."""
import datetime
import hashlib
import os
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET

import aed_standard
from falcon import testing

from aed_service import app as svc
from aed_service.feed import write_feed

try:
    import xmlschema
except ImportError:
    xmlschema = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XSD = os.path.join(ROOT, "backend", "data", "harvester", "xml_import_otwarte_dane_1_13.xsd")
URL = "https://api.mcod.local/static/aed"
DAY = datetime.date(2026, 11, 21)


def ext_idents(xml):
    return [e.text for e in ET.fromstring(xml).iter("extIdent")]


def resource_url(xml):
    return next(ET.fromstring(xml).iter("url")).text


class FeedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = svc.open_db(os.path.join(cls.tmp.name, "t.db"))
        cls.csv = svc.publication_csv(cls.db)
        cls.smaller = cls.csv[:cls.csv.rstrip().rfind(b"\n") + 1]  # same export without its last record

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.tmp.cleanup()

    def test_export_has_records_and_http_export_is_the_same(self):
        self.assertGreater(len(self.csv.splitlines()), 100)
        self.assertEqual(testing.TestClient(svc.build_app(self.db)).simulate_get("/api/aed/eksport/dane-gov-pl.csv").content,
                         self.csv)

    @unittest.skipUnless(xmlschema, "brak biblioteki xmlschema: uv run ... --with xmlschema python -m unittest")
    def test_xml_matches_portal_xsd(self):
        xmlschema.XMLSchema(XSD).validate(aed_standard.feed_files(self.csv, URL, DAY)["zasilanie.xml"])

    def test_ids_stable_and_csv_name_follows_data(self):
        a, same, b = (aed_standard.feed_files(c, URL, DAY) for c in (self.csv, self.csv, self.smaller))
        self.assertEqual(a, same)
        self.assertEqual(ext_idents(a["zasilanie.xml"]), ext_idents(b["zasilanie.xml"]))
        self.assertEqual(ext_idents(a["zasilanie.xml"]), ["aed-polska", "aed-polska-csv"])
        self.assertNotEqual(sorted(a), sorted(b))
        self.assertNotEqual(a["zasilanie.md5"], b["zasilanie.md5"])
        self.assertTrue(resource_url(a["zasilanie.xml"]).startswith(URL + "/aed_dane_gov_pl-"))

    def test_write_feed_keeps_old_versions_and_md5_matches(self):
        with tempfile.TemporaryDirectory() as out:
            first = write_feed(self.csv, out, URL)[0]
            old = time.mktime((DAY - datetime.timedelta(days=3)).timetuple())
            os.utime(os.path.join(out, first), (old, old))
            second = write_feed(self.smaller, out, URL)[0]
            self.assertTrue(os.path.exists(os.path.join(out, first)))
            with open(os.path.join(out, "zasilanie.xml"), "rb") as f:
                xml = f.read()
            self.assertEqual(resource_url(xml), URL + "/" + second)
            with open(os.path.join(out, "zasilanie.md5")) as f:
                self.assertEqual(f.read().strip(), hashlib.md5(xml).hexdigest())
            write_feed(self.csv, out, URL)  # back to a known version: its data date is the day it first appeared
            with open(os.path.join(out, "zasilanie.xml"), "rb") as f:
                self.assertEqual(next(ET.fromstring(f.read()).iter("dataDate")).text,
                                 (DAY - datetime.timedelta(days=3)).isoformat())


if __name__ == "__main__":
    unittest.main()
