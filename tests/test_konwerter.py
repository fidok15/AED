"""Converter of providers' own files to a list in the standard, on real raw files.
Run: python3 -m unittest tests.test_konwerter"""
import csv
import datetime
import io
import os
import sys
import unittest
import zipfile

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


def xlsx_file(sheet_rows, shared=(), styles="", extra=None):
    """Minimal .xlsx built with zipfile: sheet_rows is the inner XML of <sheetData>."""
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("xl/workbook.xml", '<workbook %s xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/'
                   'relationships"><sheets><sheet name="AED" sheetId="1" r:id="rId1"/></sheets></workbook>' % ns)
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
                   'relationships"><Relationship Id="rId1" Target="worksheets/arkusz.xml"/></Relationships>')
        z.writestr("xl/worksheets/arkusz.xml", "<worksheet %s><sheetData>%s</sheetData></worksheet>" % (ns, sheet_rows))
        if shared is not None:
            z.writestr("xl/sharedStrings.xml", "<sst %s>%s</sst>" % (ns, "".join("<si><t>%s</t></si>" % s for s in shared)))
        z.writestr("xl/styles.xml", "<styleSheet %s>%s</styleSheet>" % (ns, styles))
        for name, content in (extra or {}).items():
            z.writestr(name, content)
    return buf.getvalue()


class NormalizationTest(unittest.TestCase):
    def test_values_are_normalized_and_reported(self):
        data = ("Nazwa;Lat;Lon;Dostep;Wewnatrz;Bateria;Elektrody;Produkcja;Kod;Tel\n"
                "Urząd;52,2297;21,0122;Publiczny;TAK;31.01.2030;2029-05;2020/03/04;00950;'+48 22 123 45 67\n"
                "Szkoła;52.2300; 21.0130 ;Ograniczony dostęp;x;05-02-2030;2029-02;2020-03-04;00-951;+48 22 1\n"
                "Hala;52.23;21.01;publiczny ;0;03/04/2030;31.02.2030;01/13/2020;12-345;\n").encode("utf-8")
        mapping = {"Nazwa": "nazwa", "Lat": "szerokosc_geograficzna", "Lon": "dlugosc_geograficzna", "Dostep": "dostep",
                   "Wewnatrz": "wewnatrz_budynku", "Bateria": "data_waznosci_baterii", "Elektrody": "data_waznosci_elektrod",
                   "Produkcja": "data_produkcji", "Kod": "kod_pocztowy", "Tel": "dysponent_telefon"}
        text, rep = convert(data, "gmina.csv", mapping, {"miejscowosc": "Warszawa"}, today=datetime.date(2026, 11, 22))
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual([r["dostep"] for r in rows], ["publiczny", "ograniczony", "publiczny"])
        self.assertEqual([r["wewnatrz_budynku"] for r in rows], ["tak", "tak", "nie"])
        # 03/04/2030 is DD/MM or MM/DD: left as is; 31.02 does not exist: left as is. Both named by the validator.
        self.assertEqual([r["data_waznosci_baterii"] for r in rows], ["2030-01-31", "2030-02-05", "03/04/2030"])
        self.assertEqual([r["data_waznosci_elektrod"] for r in rows], ["2029-05-31", "2029-02-28", "31.02.2030"])
        self.assertEqual([r["data_produkcji"] for r in rows], ["2020-03-04", "2020-03-04", "01/13/2020"])
        self.assertEqual([r["kod_pocztowy"] for r in rows], ["00-950", "00-951", "12-345"])
        self.assertEqual(rows[0]["dysponent_telefon"], "+48 22 123 45 67")
        self.assertEqual((rows[0]["szerokosc_geograficzna"], rows[1]["dlugosc_geograficzna"]), ("52.2297", "21.013"))
        by_col = {n["kolumna"]: n for n in rep["normalizacje"]}
        self.assertEqual((by_col["Dostep"]["liczba"], by_col["Dostep"]["z"], by_col["Dostep"]["na"]), (2, "Publiczny", "publiczny"))
        self.assertIn("ujednolicono zapis 2 z 3 wartości", by_col["Dostep"]["komunikat"])
        self.assertNotIn("Nazwa", by_col)   # trimming spaces alone is not reported
        self.assertEqual((rep["poprawne"], rep["odrzucone"]), (2, 1))
        self.assertEqual({p["kod"] for p in rep["problemy"] if p["wiersz"] == 3}, {"format_daty"})


class XlsxTest(unittest.TestCase):
    def test_template_xlsx(self):
        a, (text, rep) = auto(os.path.join(ROOT, "wzorzec", "wzorzec-aed.xlsx"))
        self.assertEqual(a["format"], "xlsx")
        self.assertIn("Dane", " ".join(a["uwagi"]))
        self.assertEqual((rep["status"], rep["poprawne"]), ("przyjety", 1))

    def test_marki_xlsx_with_csv_lines_in_cells(self):
        # Marki publishes the same list as XLSX, each row a whole CSV line in column A.
        a, (text, rep) = auto(os.path.join(RAW, "marki", "resource_68355.xlsx"))
        self.assertEqual((rep["status"], rep["poprawne"]), ("przyjety", 8))
        self.assertEqual(text, auto(MARKI)[1][0])

    def test_shared_strings_numbers_and_dates(self):
        styles = ('<numFmts><numFmt numFmtId="164" formatCode="[$-415]dd\\.mm\\.yyyy"/></numFmts>'
                  '<cellXfs><xf numFmtId="0"/><xf numFmtId="14"/><xf numFmtId="164"/><xf numFmtId="2"/></cellXfs>')
        rows = ('<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1" t="s"><v>2</v></c>'
                '<c r="D1" t="inlineStr"><is><t>Bateria</t></is></c><c r="E1" t="s"><v>3</v></c></row>'
                '<row r="3"><c r="A3" t="s"><v>4</v></c><c r="B3"><v>52.229675999999998</v></c><c r="C3" s="3"><v>21.0122</v></c>'
                '<c r="D3" s="1"><v>47514</v></c><c r="E3" s="2"><v>43894</v></c></row>')
        data = xlsx_file(rows, ["Nazwa", "Lat", "Lon", "Produkcja", "Urząd &amp; Biblioteka"], styles)
        a = analyze(data, "gmina.xlsx")
        self.assertEqual([c["kolumna"] for c in a["kolumny"]], ["Nazwa", "Lat", "Lon", "Bateria", "Produkcja"])
        self.assertEqual(a["przyklad_wierszy"], [["Urząd & Biblioteka", "52.229676", "21.0122", "2030-01-31", "2020-03-04"]])

    def test_unsafe_or_broken_xlsx_is_refused(self):
        bomb = xlsx_file("<row><c><v>1</v></c></row>", shared=None, extra={"xl/sharedStrings.xml": "<sst>" + " " * (60 * 2 ** 20) + "</sst>"})
        self.assertLess(len(bomb), 5 * 2 ** 20)
        for data, words in ((bomb, "po rozpakowaniu"), (b"PK\x03\x04 not a zip", "XLSX"),
                            (xlsx_file('<row><c t="s"><v>0</v></c></row>', shared=None, extra={"xl/sharedStrings.xml": (
                                '<!DOCTYPE sst [<!ENTITY e SYSTEM "file:///etc/passwd">]><sst><si><t>&e;</t></si></sst>')}),
                             "DOCTYPE")):
            with self.assertRaises(ConverterError) as ctx:
                analyze(data, "plik.xlsx")
            self.assertIn(words, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
