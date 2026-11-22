"""Converter of providers' own files to a list in the standard, on real raw files.
Run: python3 -m unittest tests.test_konwerter"""
import csv
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from aed_standard import schema as S  # noqa: E402
from aed_standard.konwerter import ADDRESS, ConverterError, analyze, convert  # noqa: E402
from aed_standard.wykaz import read_wykaz  # noqa: E402

RAW = os.path.join(ROOT, "datasets", "raw", "dane_gov_pl")
KROSNO = os.path.join(RAW, "krosno", "resource_54632.csv")
MARKI = os.path.join(RAW, "marki", "resource_68353.csv")
PRZEMYSL = os.path.join(RAW, "przemysl", "resource_62093.geojson")
SOURCE = {"zrodlo": "dane.gov.pl/1", "zasob": 7, "tytul": "Wykaz AED", "instytucja": "Gmina", "licencja": "CC0 1.0",
          "data_aktualizacji": "2026-11-20", "priority": 1}


def read(path):
    with open(path, "rb") as f:
        return f.read()


def auto(path):
    """Analyse, accept the proposal as is, convert."""
    data = read(path)
    a = analyze(data, os.path.basename(path))
    return a, convert(data, os.path.basename(path), {c["kolumna"]: c["pole"] for c in a["kolumny"]})


class ConverterTest(unittest.TestCase):
    def test_krosno_becomes_a_valid_list(self):
        a, (text, rep) = auto(KROSNO)
        proposal = {c["kolumna"]: c["pole"] for c in a["kolumny"]}
        self.assertEqual(proposal, {"Długość geograficzna": "dlugosc_geograficzna", "Szerokość geograficzna": "szerokosc_geograficzna",
                                    "Nazwa": "", "Lokalizacja": "nazwa", "Adres": ADDRESS, "Numer Id": "zrodlo_id"})
        # Before: the portal rejects the raw file. After: the converted file is a valid list.
        self.assertEqual(read_wykaz(read(KROSNO), SOURCE)[1]["status"], "odrzucony")
        records, report = read_wykaz(text.encode("utf-8"), SOURCE)
        self.assertEqual(report["status"], "przyjety", report["problemy"])
        n = len(list(csv.reader(io.StringIO(read(KROSNO).decode("utf-8-sig"))))) - 1
        self.assertEqual((len(records), rep["poprawne"], rep["status"]), (n, n, "przyjety"))
        self.assertEqual(next(csv.reader(io.StringIO(text))), S.FIELD_NAMES)
        r = records[1]
        self.assertEqual((r["nazwa"], r["miejscowosc"], r["nazwa_ulicy"], r["nr_budynku"], r["kod_pocztowy"], r["zrodlo_id"]),
                         ("Kampus Sportowo-dydaktyczny, portiernia", "Krosno", "Stanisława Wyspiańskiego", "20", "38-400", "2"))
        self.assertGreater(rep["kompletnosc_srednia"], 0)

    def test_marki_swapped_header_and_wrapped_rows(self):
        a, (text, rep) = auto(MARKI)
        proposal = {c["kolumna"]: c["pole"] for c in a["kolumny"]}
        # The header says longitude first, the values are latitudes: values win.
        self.assertEqual(proposal["Długość geograficzna"], "szerokosc_geograficzna")
        self.assertIn("rozpakowano", " ".join(a["uwagi"]))
        records, report = read_wykaz(text.encode("utf-8"), SOURCE)
        self.assertEqual((report["status"], len(records)), ("przyjety", rep["wiersze"]))
        self.assertTrue(all(49 <= float(r["szerokosc_geograficzna"]) <= 54.9 for r in records))

    def test_przemysl_geojson_and_constants(self):
        data = read(PRZEMYSL)
        a = analyze(data, "przemysl.geojson")
        mapping = {c["kolumna"]: c["pole"] for c in a["kolumny"]}
        self.assertEqual(mapping["city"], "miejscowosc")
        self.assertEqual(mapping["geometria: szerokość"], "szerokosc_geograficzna")
        text, rep = convert(data, "przemysl.geojson", mapping, {"dostep": "publiczny"})
        records, report = read_wykaz(text.encode("utf-8"), SOURCE)
        self.assertEqual(report["status"], "przyjety")
        self.assertEqual({r["dostep"] for r in records}, {"publiczny"})
        self.assertIn("dane_osobowe", {p["kod"] for p in rep["problemy"]})   # contact columns are flagged

    def test_errors_are_polish(self):
        data = read(KROSNO)
        with self.assertRaises(ConverterError) as ctx:
            convert(data, "k.csv", {"Nazwa": "nazwa", "Lokalizacja": "nazwa"})
        self.assertIn("dwóch kolumn", str(ctx.exception))
        with self.assertRaises(ConverterError):
            convert(data, "k.csv", {"Nazwa": "status"})
        rep = convert(data, "k.csv", {"Nazwa": "nazwa"})[1]   # no coordinates: every row rejected, with reasons
        self.assertEqual((rep["status"], rep["poprawne"]), ("odrzucony", 0))
        self.assertIn("brak_wymaganego", {p["kod"] for p in rep["problemy"]})


if __name__ == "__main__":
    unittest.main()
