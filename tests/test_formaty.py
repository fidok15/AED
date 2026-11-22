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


def ods(rows_xml):
    ns = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:table="urn:oasis:names:tc:opendocument:'
          'xmlns:table:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet")
        z.writestr("content.xml", '<office:document-content %s><office:body><office:spreadsheet><table:table '
                   'table:name="AED">%s</table:table></office:spreadsheet></office:body></office:document-content>'
                   % (ns, rows_xml))
    return buf.getvalue()


ODS_HEADER = ('<table:table-row><table:table-cell><text:p>nazwa</text:p></table:table-cell><table:table-cell><text:p>'
              'lat</text:p></table:table-cell><table:table-cell><text:p>lon</text:p></table:table-cell></table:table-row>')
ODS_ROW = ('<table:table-row table:number-rows-repeated="%d"><table:table-cell><text:p>Urząd</text:p></table:table-cell>'
           '<table:table-cell><text:p>52.2</text:p></table:table-cell><table:table-cell><text:p>21.0</text:p>'
           '</table:table-cell></table:table-row>')


class ReviewFixesTest(unittest.TestCase):
    """Codex review of the formats layer, 22.11.2026."""

    def test_overpass_export_is_osm_as_a_whole(self):
        # Real structure of an Overpass API JSON export; the elements are invented.
        overpass = ('{"version": 0.6, "generator": "Overpass API 0.7.62", "osm3s": {"timestamp_osm_base": '
                    '"2026-11-22T00:00:00Z", "copyright": "The data included in this document is from www.openstreetmap.org. '
                    'The data is made available under ODbL."}, "elements": [{"type": "node", "id": 1, "lat": 52.2, '
                    '"lon": 21.0, "tags": {"emergency": "defibrillator", "name": "Przykład"}}, {"type": "node", "id": 2, '
                    '"lat": 52.3, "lon": 21.1, "tags": {"emergency": "defibrillator"}}]}').encode()
        a, text, rep, (records, report) = auto(overpass, "export.json", {"miejscowosc": "Warszawa"})
        self.assertIn("Overpass", " ".join(a["uwagi"]))
        self.assertEqual((rep["poprawne"], report["status"], records), (0, "odrzucony", []))
        self.assertEqual({p["wiersz"] for p in rep["problemy"] if p["kod"] == "dane_osm"}, {1, 2})
        geojson = ('{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"@id": "node/7", '
                   '"name": "Przykład"}, "geometry": {"type": "Point", "coordinates": [21.0, 52.2]}}]}').encode()
        self.assertEqual(auto(geojson, "aed.geojson", {"miejscowosc": "Warszawa"})[2]["poprawne"], 0)
        kml = ('<kml xmlns="http://www.opengis.net/kml/2.2"><Document><description>© OpenStreetMap contributors'
               '</description><Placemark><name>A</name><Point><coordinates>21.0,52.2</coordinates></Point></Placemark>'
               '</Document></kml>').encode()
        self.assertEqual(auto(kml, "a.kml", {"miejscowosc": "Warszawa"})[2]["poprawne"], 0)
        # A word that merely contains "odbl" (odblaskowy) is not a licence.
        own = ('<kml xmlns="http://www.opengis.net/kml/2.2"><Placemark><name>Szafka odblaskowa</name><Point>'
               '<coordinates>21.0,52.2</coordinates></Point></Placemark></kml>').encode()
        self.assertEqual(auto(own, "a.kml", {"miejscowosc": "Warszawa"})[2]["poprawne"], 1)

    def test_one_osm_object_in_an_own_list_rejects_only_that_row(self):
        mixed = ('{"type": "FeatureCollection", "features": ['
                 '{"type": "Feature", "properties": {"@id": "node/7", "name": "Z mapy"}, '
                 '"geometry": {"type": "Point", "coordinates": [21.0, 52.2]}}, '
                 '{"type": "Feature", "properties": {"name": "Urząd Gminy"}, '
                 '"geometry": {"type": "Point", "coordinates": [21.1, 52.3]}}]}').encode()
        a, text, rep, (records, report) = auto(mixed, "aed.geojson", {"miejscowosc": "Warszawa"})
        self.assertEqual([r["nazwa"] for r in records], ["Urząd Gminy"])
        self.assertEqual({p["wiersz"] for p in rep["problemy"] if p["kod"] == "dane_osm"}, {1})
        self.assertIn("tylko te wiersze", " ".join(a["uwagi"]))
        licence = mixed.replace(b'"@id": "node/7"', b'"licencja_danych": "ODbL 1.0"')
        self.assertEqual([r["nazwa"] for r in auto(licence, "aed.geojson", {"miejscowosc": "Warszawa"})[3][0]], ["Urząd Gminy"])
        # A licence of the collection itself still marks the whole file.
        whole = mixed.replace(b'"type": "FeatureCollection",', b'"type": "FeatureCollection", "license": "ODbL",')
        self.assertEqual(auto(whole, "aed.geojson", {"miejscowosc": "Warszawa"})[2]["poprawne"], 0)

    def test_gml_points_in_two_systems(self):
        gml = ('<gml:FeatureCollection xmlns:gml="http://www.opengis.net/gml">'
               '<gml:featureMember><gml:name>A</gml:name><gml:Point srsName="EPSG:4326"><gml:pos>52.2086 21.0149</gml:pos>'
               '</gml:Point></gml:featureMember><gml:featureMember><gml:name>B</gml:name><gml:Point srsName="EPSG:2180">'
               '<gml:pos>256872.23 491913.10</gml:pos></gml:Point></gml:featureMember></gml:FeatureCollection>').encode()
        records = auto(gml, "a.gml", {"miejscowosc": "Warszawa"})[3][0]
        got = {r["nazwa"]: (float(r["szerokosc_geograficzna"]), float(r["dlugosc_geograficzna"])) for r in records}
        self.assertLess(haversine_m(*got["A"], 52.2086, 21.0149), 1)
        self.assertLess(haversine_m(*got["B"], 50.179011, 18.886705), 1)

    def test_lines_and_areas_have_no_position(self):
        kml = ('<kml xmlns="http://www.opengis.net/kml/2.2"><Placemark><name>Trasa</name><LineString><coordinates>'
               '21.0,52.2 21.1,52.3</coordinates></LineString></Placemark><Placemark><name>Punkt</name><Point>'
               '<coordinates>21.0,52.2</coordinates></Point></Placemark></kml>').encode()
        a, text, rep, (records, report) = auto(kml, "a.kml", {"miejscowosc": "Warszawa"})
        self.assertEqual([r["nazwa"] for r in records], ["Punkt"])
        self.assertIn("linie lub obszary", " ".join(a["uwagi"]))
        geo = ('{"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "Park"}, '
               '"geometry": {"type": "Polygon", "coordinates": [[[21.0, 52.2], [21.1, 52.2], [21.0, 52.3], [21.0, 52.2]]]}}, '
               '{"type": "Feature", "properties": {"name": "Urząd"}, "geometry": {"type": "Point", "coordinates": [21.0, 52.2]}}]}')
        a, text, rep, (records, report) = auto(geo.encode(), "a.geojson", {"miejscowosc": "Warszawa"})
        self.assertEqual(([r["nazwa"] for r in records], "Park" in " ".join(a["uwagi"])), (["Urząd"], True))
        gml = ('<gml:FeatureCollection xmlns:gml="http://www.opengis.net/gml"><gml:featureMember><gml:name>Ścieżka</gml:name>'
               '<gml:LineString><gml:coordinates>21.0,52.2 21.1,52.3</gml:coordinates></gml:LineString></gml:featureMember>'
               '</gml:FeatureCollection>').encode()
        self.assertIn("linie lub obszary", " ".join(analyze(gml, "a.gml")["uwagi"]))
        gpx = ('<gpx xmlns="http://www.topografix.com/GPX/1/1"><wpt lat="52.2" lon="21.0"><name>AED</name></wpt><rte>'
               '<rtept lat="52.3" lon="21.1"><name>zakręt</name></rtept></rte></gpx>').encode()
        a = analyze(gpx, "a.gpx")
        self.assertEqual((a["wiersze"], "tras" in " ".join(a["uwagi"])), (1, True))

    def test_gml_point_with_srs_name(self):
        # Przemyśl has no srsName, so it never produced "SRID=…;a b". Explicit systems, GML 3 axis order:
        for srs, pos in (("EPSG:4326", "52.2086 21.0149"), ("urn:ogc:def:crs:EPSG::2180", "484418.36 637629.99")):
            gml = ('<gml:FeatureCollection xmlns:gml="http://www.opengis.net/gml"><gml:featureMember><gml:name>Urząd'
                   '</gml:name><gml:Point srsName="%s"><gml:pos>%s</gml:pos></gml:Point></gml:featureMember>'
                   '</gml:FeatureCollection>' % (srs, pos)).encode()
            records = auto(gml, "a.gml", {"miejscowosc": "Warszawa"})[3][0]
            self.assertEqual(len(records), 1, srs)
            self.assertLess(haversine_m(float(records[0]["szerokosc_geograficzna"]), float(records[0]["dlugosc_geograficzna"]),
                                        52.2086, 21.0149), 5, srs)

    def test_ods_repeated_rows_are_checked_before_expanding(self):
        with self.assertRaises(ConverterError) as ctx:
            analyze(ods(ODS_HEADER + ODS_ROW % 60000), "a.ods")
        self.assertIn("powtórzeń wiersza", str(ctx.exception))
        empty_tail = '<table:table-row table:number-rows-repeated="1048570"><table:table-cell/></table:table-row>'
        self.assertEqual(analyze(ods(ODS_HEADER + ODS_ROW % 2 + empty_tail), "a.ods")["wiersze"], 2)

    def test_malformed_files_are_polish_errors(self):
        for data in MALFORMED:
            with self.assertRaises(ConverterError, msg=data[:60]):
                analyze(data, "plik.json")


MALFORMED = (
    b'{"features": [{"attributes": {"a": 1}, "geometry": {"x": 1, "y": 2}}, null]}',
    b'{"features": [{"attributes": {"a": 1}}, {"attributes": "x"}]}',
    b'{"features": [{"attributes": {"a": 1}, "geometry": [1, 2]}]}',
    b"[" * 100000,
    b'{"type": "FeatureCollection", "features": []}',
    b'{"data": "nic"}',
    b'<kml xmlns="http://www.opengis.net/kml/2.2"><Document/></kml>',
    b'<kml><Placemark><Point><coordinates>   </coordinates></Point></Placemark>',
    b"   ",
    b"nazwa;lat;lon\n",
    b"PK\x03\x04" + b"\0" * 40,
)


if __name__ == "__main__":
    unittest.main()
