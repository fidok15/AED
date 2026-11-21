"""Merging AED lists (wykazy) published on dane.gov.pl, on real raw files. Run: python3 -m unittest tests.test_wykaz"""
import csv
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from aed_standard.build import build_registry, publication_export, to_csv  # noqa: E402
from aed_standard.wykaz import merge_wykazy, read_wykaz  # noqa: E402

RAW = os.path.join(ROOT, "datasets", "raw")
LEGIONOWO = os.path.join(RAW, "dane_gov_pl", "legionowo", "resource_2625221.csv")
KROSNO = os.path.join(RAW, "dane_gov_pl", "krosno", "resource_54632.csv")


def read(path):
    with open(path, "rb") as f:
        return f.read()


def source(dataset, resource, institution, licence="CC0 1.0", priority=1):
    return {"zrodlo": "dane.gov.pl/%s" % dataset, "zasob": resource, "tytul": "Wykaz AED", "instytucja": institution,
            "licencja": licence, "data_aktualizacji": "2026-11-20", "priority": priority}


def rows(data):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


class ReadWykazTest(unittest.TestCase):
    def test_legionowo_is_a_valid_list(self):
        records, rep = read_wykaz(read(LEGIONOWO), source(40593, 1, "Gmina Miejska Legionowo"))
        self.assertEqual(rep["status"], "przyjety")
        self.assertEqual(len(records), len(rows(read(LEGIONOWO))))
        r = records[0]
        self.assertEqual((r["zrodlo"], r["licencja"], r["status"], r["wprowadzajacy_nazwa"]),
                         ("dane.gov.pl/40593", "CC0 1.0", "niepotwierdzony", "Gmina Miejska Legionowo"))
        self.assertTrue(r["id_aed"].startswith("AED-"))

    def test_krosno_is_rejected_with_polish_messages(self):
        records, rep = read_wykaz(read(KROSNO), source(3624, 2, "Miasto Krosno"))
        self.assertEqual((records, rep["status"]), ([], "odrzucony"))
        self.assertIn("nieznana_kolumna", {p["kod"] for p in rep["problemy"]})
        self.assertTrue(any("dlugosc_geograficzna" in p["komunikat"] for p in rep["problemy"]))

    def test_bad_rows_skipped_private_and_osm_rows_kept_out(self):
        data = read(LEGIONOWO).decode("utf-8-sig").splitlines()
        header = data[0] + ",dostep,zrodlo"
        extra = ((1, ",publiczny,"), (2, ",publiczny,"), (3, ",prywatny,"), (4, ",,openstreetmap"))
        good, bad, private, osm = (data[i] + s for i, s in extra)
        bad = bad.replace("52.421807", "52,421807", 1)  # unquoted decimal comma: one value too many
        csv_bytes = "\n".join([header, good, bad, private, osm]).encode("utf-8")
        records, rep = read_wykaz(csv_bytes, source(40593, 1, "Legionowo"))
        self.assertEqual(rep["status"], "czesciowo")
        self.assertTrue({"liczba_kolumn", "dane_osm"} <= {p["kod"] for p in rep["problemy"]})
        self.assertEqual(len(records), 2)  # good + private; publication drops private later
        national, _, report = merge_wykazy([(source(40593, 1, "Legionowo"), csv_bytes, None)])
        self.assertEqual(len(national), 1)
        self.assertEqual(report["pominiete_przy_publikacji"], {"dostep prywatny": 1})

    def test_row_licence_more_restrictive_than_dataset_is_kept(self):
        data = read(LEGIONOWO).decode("utf-8-sig").splitlines()
        csv_bytes = "\n".join([data[0] + ",licencja", data[1] + ",CC BY 4.0", data[2] + ","]).encode("utf-8")
        records, _ = read_wykaz(csv_bytes, source(40593, 1, "Legionowo"))
        self.assertEqual([r["licencja"] for r in records], ["CC BY 4.0", "CC0 1.0"])

    def test_licence_outside_standard_rejects_list(self):
        _, rep = read_wykaz(read(LEGIONOWO), source(40593, 1, "Legionowo", licence="CC BY-SA 4.0"))
        self.assertEqual([p["kod"] for p in rep["problemy"]], ["licencja"])


class MergeWykazyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records, _, _ = build_registry(RAW)
        cls.ministry = to_csv(publication_export(records)).encode("utf-8")  # the ministry's own register as a list

    def test_merge_real_lists(self):
        items = [
            (source(1, 10, "Ministerstwo Cyfryzacji", priority=0), self.ministry, None),
            (source(40593, 11, "Gmina Miejska Legionowo"), read(LEGIONOWO), None),
            (source(3624, 12, "Miasto Krosno"), read(KROSNO), None),
            (source(4955, 13, "Miasto Marki"), None, "Adres zasobu nie odpowiada."),
        ]
        national, pairs, report = merge_wykazy(items)
        statuses = [w["status"] for w in report["wykazy"]]
        self.assertEqual(statuses, ["przyjety", "przyjety", "odrzucony", "odrzucony"])
        n_ministry, n_legionowo = len(rows(self.ministry)), len(rows(read(LEGIONOWO)))
        # Legionowo's AEDs are already in the ministry's register (same points): merged, not doubled.
        self.assertGreater(report["polaczenia"], 0)
        self.assertLess(len(national), n_ministry + n_legionowo)
        self.assertGreaterEqual(len(national), n_ministry)
        self.assertTrue(all(r["licencja"] != "ODbL 1.0" and r["dostep"] != "prywatny" for r in national))
        self.assertEqual(len({r["id_aed"] for r in national}), len(national))
        # Higher-priority list (ministry) keeps its id; the Legionowo source is recorded as a link.
        self.assertTrue(any("dane.gov.pl/40593:" in r["powiazane_zrodla"] for r in national))

        # The national file is itself a valid list in the standard (round trip).
        out = to_csv(national).encode("utf-8")
        again, rep = read_wykaz(out, source(1, 99, "Ministerstwo Cyfryzacji"))
        self.assertEqual((rep["status"], len(again)), ("przyjety", len(national)))


class PublicExportRulesTest(unittest.TestCase):
    HEAD = ("id_aed,zrodlo_id,nazwa,miejscowosc,szerokosc_geograficzna,dlugosc_geograficzna,dostep,"
            "dysponent_email,dysponent_telefon,numer_seryjny\n")

    def test_repeated_ids_stay_unique_and_contacts_are_blanked(self):
        body = "".join("AED-ABCDEFGHIJKL,dup,Punkt %d,Warszawa,52.%d,21,publiczny,jan.kowalski@example.pl,600100200,SN%d\n"
                       % (i, i, i) for i in range(1, 4))
        national, _, _ = merge_wykazy([(source(1, 1, "Gmina"), (self.HEAD + body).encode("utf-8"), None)])
        self.assertEqual(len(national), 3)
        self.assertEqual(len({r["id_aed"] for r in national}), 3)
        for r in national:  # hard rule 6: no contact details in the open dataset
            self.assertEqual((r["dysponent_email"], r["dysponent_telefon"], r["numer_seryjny"]), ("", "", ""))
        self.assertNotIn("kowalski", to_csv(national))


if __name__ == "__main__":
    unittest.main()
