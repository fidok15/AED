"""Geocoding with the GUGiK service (aed_standard/geokod.py) in the converter. Offline with recorded answers; one live
test, skipped without network. Run: python3 -m unittest tests.test_geokod"""
import csv
import io
import os
import sys
import unittest
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from aed_standard import geokod  # noqa: E402
from aed_standard.konwerter import analyze, convert  # noqa: E402

P = os.path.join(ROOT, "datasets", "probki-formatow")


def point(city, street, number, code, x, y, acc="1"):
    return {"city": city, "street": street, "number": number, "code": code, "teryt": "126101", "simc": "0950463",
            "x": x, "y": y, "accuracy": acc, "city_accuracy": "1"}


# Shapes of real answers from services.gugik.gov.pl/uug (22.11.2026), cut to the fields we read.
ANSWERS = {
    "Kraków, Bosacka 18": {"type": "address", "results": {"1": point("Kraków", "Bosacka", "18", "31-505",
                                                                     "19.9497341305729", "50.0678250085422")}},
    "Kraków, Bosacka": {"type": "street", "results": {"1": point("Kraków", "Bosacka", "", "", "19.95", "50.07")}},
    "Kraków, Bosacka 999": {"type": "address", "results": None},
    "Kraków, Pokoju 44": {"type": "address", "results": {
        "1": point("Kraków", "Aleja Pokoju", "44", "31-564", "19.98", "50.06", "0.8"),
        "2": point("Kraków", "Aleja Żubrowa", "44", "30-232", "19.88", "50.08", "0.8")}},
    "Kraków, Działowskiego 1": {"type": "address", "results": {
        "1": point("Kraków", "Stanisława Działowskiego", "1", "30-399", "19.8727576", "49.9888943", "0.6")}},
}


def fake(params):
    if params["request"] == "GetAddressReverse":
        return {"type": "address", "results": {"1": point("Krosno", "Rynek", "2", "38-400", "21.76", "49.69")}}
    if params["address"] == "Kraków, Totus Tuus 34":
        raise OSError("timeout")
    return ANSWERS.get(params["address"], {"type": "address", "results": None})


class GeocoderTest(unittest.TestCase):
    def setUp(self):
        self.g = geokod.Geocoder(fetch=fake, pause=0)

    def test_only_an_address_point_of_the_building_is_a_position(self):
        res, why = self.g.address("Kraków", "Bosacka", "18", "31-505")
        self.assertEqual((res["lat"], res["lon"], res["teryt"], res["simc"], why), (50.067825, 19.9497341, "126101", "0950463", None))
        self.assertIn("brak numeru", self.g.address("Kraków", "Bosacka", "")[1])      # would be the street axis
        self.assertIn("nie znalazła", self.g.address("Kraków", "Bosacka", "999")[1])
        self.assertIn("kilka punktów", self.g.address("Kraków", "Pokoju", "44")[1])   # Pokoju or Żubrowa
        self.assertIn("nie odpowiedziała", self.g.address("Kraków", "Totus Tuus", "34")[1])
        self.assertIsNotNone(self.g.address("Kraków", "Działowskiego", "1")[0])       # same last word: accepted
        self.assertIn("kod pocztowy", self.g.address("Kraków", "Działowskiego", "1", "31-000")[1])
        self.assertEqual(self.g.address("Kraków", "Bosacka", "18", "30-001")[0]["uwaga"][:25], "kod pocztowy w pliku 30-0")

    def test_cache_and_limit(self):
        g = geokod.Geocoder(fetch=fake, pause=0, limit=1)
        g.address("Kraków", "Bosacka", "18")
        self.assertIsNotNone(g.address("Kraków", "Bosacka", "18")[0])                  # from the cache
        self.assertIn("limit 1", g.address("Kraków", "Bosacka", "999")[1])
        self.assertEqual(g.calls, 1)

    def test_converter_fills_rows_without_position_and_says_where_it_comes_from(self):
        data = ("nazwa,adres,miejscowosc,dostep\nDworzec,ul. Bosacka 18,Kraków,publiczny\nUrząd,ul. Bosacka 999,Kraków,"
                "publiczny\nKrosno,,Krosno,publiczny\n").encode()
        a = analyze(data, "a.csv")
        mapping = {c["kolumna"]: c["pole"] for c in a["kolumny"]}
        self.assertEqual(mapping["adres"], "_adres")
        text, rep = convert(data, "a.csv", mapping, geocoder=geokod.Geocoder(fetch=fake, pause=0))
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual((rows[0]["szerokosc_geograficzna"], rows[0]["kod_terc"], rows[0]["kod_simc"]),
                         ("50.067825", "126101", "0950463"))
        # 0.3.0: the method is a column of its own; the description is left to the provider
        self.assertEqual((rows[0]["sposob_ustalenia_polozenia"], rows[0]["opis_lokalizacji"]), ("geokodowanie_adresu", ""))
        self.assertEqual(rows[1]["szerokosc_geograficzna"], "")
        geo = rep["geokodowanie"]
        self.assertEqual((geo["uzupelnione"], geo["nieuzupelnione"], rep["poprawne"]), (1, 1, 1))
        self.assertIn("GUGiK", geo["komunikat"])
        self.assertIsNone(convert(data, "a.csv", mapping)[1]["geokodowanie"])   # off unless asked

    def test_codes_for_rows_with_coordinates_only_in_the_same_town(self):
        data = ("nazwa,lat,lon,miejscowosc\nA,49.69,21.76,Krosno\nB,49.69,21.76,Jasło\n").encode()
        mapping = {c["kolumna"]: c["pole"] for c in analyze(data, "b.csv")["kolumny"]}
        text, rep = convert(data, "b.csv", mapping, geocoder=geokod.Geocoder(fetch=fake, pause=0))
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual([(r["kod_terc"], r["kod_simc"]) for r in rows], [("126101", "0950463"), ("", "")])
        self.assertEqual((rep["geokodowanie"]["uzupelnione"], rep["geokodowanie"]["kody_uzupelnione"]), (0, 1))


def online():
    try:
        urllib.request.urlopen(geokod.URL, timeout=5)
        return True
    except Exception:
        return False


@unittest.skipUnless(os.environ.get("AED_TEST_ONLINE", "1") != "0" and online(), "brak dostępu do services.gugik.gov.pl")
class LiveTest(unittest.TestCase):
    def test_krakow_bip_docx(self):
        with open(os.path.join(P, "krakow-bip-impuls-zycia.docx"), "rb") as f:
            data = f.read()
        mapping = {c["kolumna"]: c["pole"] for c in analyze(data, "k.docx")["kolumny"]}
        _, rep = convert(data, "k.docx", mapping, {"miejscowosc": "Kraków"}, geocoder=geokod.Geocoder())
        self.assertGreaterEqual(rep["geokodowanie"]["uzupelnione"], 25)   # 29 of 31 on 22.11.2026
        self.assertGreaterEqual(rep["poprawne"], 25)


if __name__ == "__main__":
    unittest.main()
