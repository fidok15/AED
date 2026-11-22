"""Converter input formats and position notations, on real samples (datasets/probki-formatow, datasets/raw).
Run: python3 -m unittest tests.test_formaty"""
import csv
import io
import os
import sys
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from aed_standard import uklady  # noqa: E402
from aed_standard.konwerter import ConverterError, analyze, convert  # noqa: E402
from aed_standard.sources import haversine_m  # noqa: E402
from aed_standard.wykaz import read_wykaz  # noqa: E402

P = os.path.join(ROOT, "datasets", "probki-formatow")
RAW = os.path.join(ROOT, "datasets", "raw")
SOURCE = {"zrodlo": "dane.gov.pl/1", "zasob": 7, "tytul": "Wykaz AED", "instytucja": "Gmina", "licencja": "CC0 1.0",
          "data_aktualizacji": "2026-11-20", "priority": 1}
# Reference points: Warsaw AED no. 622 (Otwarte dane Warszawy) and an AED in Mikołów, projected by the ArcGIS server
# itself (query with outSR=...), 22.11.2026. -> (epsg, easting, northing, lat, lon)
REFERENCE = [
    (2180, 637629.9866838823, 484418.3574796999, 52.20861707000007, 21.014874889000055),
    (2178, 7501016.743972357, 5786110.771797601, 52.20861707000007, 21.014874889000055),
    (3857, 2339365.1717278375, 6837934.349569154, 52.20861707000007, 21.014874889000055),
    (2177, 6563331.2889, 5560706.8423999995, 50.17901139979465, 18.88670500068242),
    (2180, 491913.09601212543, 256872.23063698132, 50.17901139979465, 18.88670500068242),
]


def read(*path):
    with open(os.path.join(*path), "rb") as f:
        return f.read()


def auto(data, name, constants=None):
    a = analyze(data, name)
    text, rep = convert(data, name, {c["kolumna"]: c["pole"] for c in a["kolumny"]}, constants)
    return a, text, rep, read_wykaz(text.encode("utf-8"), SOURCE)


class CoordinateSystemsTest(unittest.TestCase):
    def test_planar_systems_within_a_millimetre(self):
        for epsg, e, n, lat, lon in REFERENCE:
            got = uklady.convert(uklady.EPSG[epsg], e, n)
            self.assertLess(haversine_m(got[0], got[1], lat, lon), 0.01, epsg)

    def test_one_cell_notations(self):
        for text, expect in (("52.2297, 21.0122", (52.2297, 21.0122)), ("21,0122 52,2297", (21.0122, 52.2297)),
                             ("POINT(21.0122 52.2297)", (21.0122, 52.2297)), ("52.2297;21.0122", (52.2297, 21.0122))):
            self.assertEqual(uklady.point(text)[:2], expect)
        lat, lon, kind = uklady.point("52°13'47\"N 21°00'44\"E")
        self.assertEqual((round(lat, 5), round(lon, 5), kind), (52.22972, 21.01222, "latlon"))
        self.assertIsNone(uklady.dms("49.78 22.77"))   # bare numbers are not degrees-minutes
        self.assertIsNone(uklady.point("ul. Jasna 12"))

    def test_csv_with_puwg1992_columns_and_dms_and_one_column(self):
        rows = [("Urząd", "637629.99", "484418.36"), ("Szkoła", "637277.42", "480524.77")]
        data = ("nazwa;miejscowosc;X;Y\n" + "".join("%s;Warszawa;%s;%s\n" % r for r in rows)).encode()
        a, text, rep, (records, report) = auto(data, "puwg.csv")
        self.assertIn("PUWG 1992", " ".join(a["uwagi"]))
        self.assertEqual(report["status"], "przyjety", report["problemy"])
        self.assertLess(haversine_m(float(records[0]["szerokosc_geograficzna"]), float(records[0]["dlugosc_geograficzna"]),
                                    52.20861707, 21.01487489), 1)
        dms = "nazwa,miejscowosc,szerokosc,dlugosc\nUrząd,Warszawa,52°12'31\"N,21°0'53\"E\n".encode()
        records = auto(dms, "dms.csv")[3][0]
        self.assertEqual((records[0]["szerokosc_geograficzna"][:6], records[0]["dlugosc_geograficzna"][:6]), ("52.208", "21.014"))
        one = "nazwa,miejscowosc,położenie\nUrząd,Warszawa,\"52.2086, 21.0149\"\nHala,Warszawa,\"21.01, 52.23\"\n".encode()
        records = auto(one, "one.csv")[3][0]
        self.assertEqual([r["szerokosc_geograficzna"] for r in records], ["52.2086", "52.23"])
        wkt = "nazwa,miejscowosc,wkt\nUrząd,Warszawa,SRID=2180;POINT(637629.99 484418.36)\n".encode()
        self.assertEqual(auto(wkt, "wkt.csv")[3][0][0]["szerokosc_geograficzna"][:7], "52.2086")


class FormatsTest(unittest.TestCase):
    def test_kml_and_kmz_from_google_my_maps(self):
        # Koszalin "Punkty Życia" (Google Moje Mapy linked from koszalin.pl), KML export and the original KMZ.
        for name in ("koszalin-mymaps.kml", "koszalin-mymaps.kmz"):
            a, text, rep, (records, report) = auto(read(P, name), name, {"miejscowosc": "Koszalin"})
            self.assertEqual(a["format"], name[-3:])
            self.assertEqual((report["status"], len(records)), ("przyjety", 35), report["problemy"])
            self.assertEqual((records[0]["nazwa"], records[0]["szerokosc_geograficzna"][:7]), ("Punkt Życia #1", "54.1979"))
            self.assertIn("Rejtana", records[0]["opis_lokalizacji"])

    def test_gml_json_csv_of_przemysl_agree(self):
        # The same 21 AED published by Przemyśl in four formats: each gives the same positions.
        files = ("resource_62092.xml", "resource_62093.geojson", "resource_62094.json", "resource_62095.csv")
        results = []
        for name in files:
            a, text, rep, (records, report) = auto(read(RAW, "dane_gov_pl", "przemysl", name), name)
            self.assertEqual((report["status"], len(records)), ("przyjety", 21), name)
            results.append(sorted((r["zrodlo_id"], r["szerokosc_geograficzna"][:8], r["dlugosc_geograficzna"][:8]) for r in records))
        self.assertTrue(all(r == results[0] for r in results), results)

    def test_arcgis_json_web_mercator_and_puwg2000(self):
        a, text, rep, (records, report) = auto(read(P, "arcgis-warszawa-epsg3857.json"), "aed.json")
        self.assertEqual((a["format"], report["status"], len(records)), ("arcgis", "przyjety", 3))
        # Faithful structure of a FeatureServer layer in EPSG:2177 (fields of a Mikołów layer; values invented).
        a, text, rep, (records, report) = auto(read(P, "arcgis-epsg2177-struktura.json"), "aed.json", {"miejscowosc": "Mikołów"})
        self.assertIn("2176", " ".join(a["uwagi"]))
        r = records[0]
        self.assertLess(haversine_m(float(r["szerokosc_geograficzna"]), float(r["dlugosc_geograficzna"]), 50.179011, 18.886705), 1)

    def test_warsaw_api_json_list_of_features(self):
        a, text, rep, (records, report) = auto(read(RAW, "warszawa_api", "defibrylatory.json"), "warszawa.json")
        self.assertEqual(a["format"], "geojson")
        self.assertGreater(len(records), 700)
        self.assertEqual({r["wewnatrz_budynku"] for r in records} - {"tak", "nie", ""}, set())

    def test_html_table_and_docx_table_without_coordinates(self):
        a, text, rep, (records, report) = auto(read(P, "krakow-lista.html"), "krakow.html")
        self.assertEqual([c["kolumna"] for c in a["kolumny"]][:2], ["Nazwa", "Nazwa (2)"])   # name and address split
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual((rows[1]["nazwa_ulicy"], rows[1]["kod_pocztowy"], rows[1]["miejscowosc"]), ("Totus Tuus", "30-610", "Kraków"))
        self.assertEqual((rep["status"], rep["bez_wspolrzednych"]), ("odrzucony", 4))
        self.assertIn("4 wierszy ma adres bez współrzędnych", rep["bez_wspolrzednych_komunikat"])
        a, text, rep, _ = auto(read(P, "krakow-bip-impuls-zycia.docx"), "krakow.docx", {"miejscowosc": "Kraków"})
        self.assertIn("tytułowe", " ".join(a["uwagi"]))
        self.assertEqual((a["format"], a["wiersze"], rep["bez_wspolrzednych"]), ("docx", 31, 31))
        self.assertEqual(len(list(csv.DictReader(io.StringIO(text)))), 31)   # the file to complete keeps every row

    def test_gpx_and_ods(self):
        gpx = ('<?xml version="1.0"?><gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"><wpt lat="52.2086" '
               'lon="21.0149"><name>Urząd</name><desc>Hol</desc></wpt></gpx>').encode()
        records = auto(gpx, "aed.gpx", {"miejscowosc": "Warszawa"})[3][0]
        self.assertEqual((records[0]["nazwa"], records[0]["opis_lokalizacji"]), ("Urząd", "Hol"))
        ns = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:table="urn:oasis:names:tc:opendocument:'
              'xmlns:table:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"')
        cell = '<table:table-cell office:value-type="%s" %s><text:p>%s</text:p></table:table-cell>'
        content = ('<office:document-content %s><office:body><office:spreadsheet><table:table table:name="AED">'
                   '<table:table-row>%s%s%s<table:table-cell table:number-columns-repeated="1000"/></table:table-row>'
                   '<table:table-row>%s%s%s</table:table-row></table:table></office:spreadsheet></office:body>'
                   '</office:document-content>') % (ns, cell % ("string", "", "nazwa"), cell % ("string", "", "lat"),
                                                    cell % ("string", "", "lon"), cell % ("string", "", "Urząd"),
                                                    cell % ("float", 'office:value="52.2086"', "52,21"),
                                                    cell % ("float", 'office:value="21.0149"', "21,01"))
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet")
            z.writestr("content.xml", content)
        a, text, rep, (records, report) = auto(buf.getvalue(), "aed.ods", {"miejscowosc": "Warszawa"})
        self.assertEqual((a["format"], [c["kolumna"] for c in a["kolumny"]]), ("ods", ["nazwa", "lat", "lon"]))
        self.assertEqual(records[0]["szerokosc_geograficzna"], "52.2086")

    def test_unreadable_formats_get_polish_advice(self):
        for data, words in ((b"%PDF-1.4 ...", "nie jest formatem odczytywalnym maszynowo"),
                            (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\0" * 100, "(.xlsx)"),
                            (b"\x89PNG\r\n\x1a\n" + b"\0" * 50, "skan"),
                            (b'<?xml version="1.0"?><!DOCTYPE kml [<!ENTITY e SYSTEM "file:///etc/passwd">]><kml>&e;</kml>', "DOCTYPE"),
                            (b'<?xml version="1.0"?><root><a/></root>', "nie KML")):
            with self.assertRaises(ConverterError) as ctx:
                analyze(data, "plik.csv")   # the extension does not matter: the content decides
            self.assertIn(words, str(ctx.exception))
        bomb = io.BytesIO()
        with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("doc.kml", "<kml>" + " " * (60 * 2 ** 20) + "</kml>")
        with self.assertRaises(ConverterError) as ctx:
            analyze(bomb.getvalue(), "a.kmz")
        self.assertIn("po rozpakowaniu", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
