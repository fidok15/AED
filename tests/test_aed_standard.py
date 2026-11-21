"""Tests on the real raw files. Run: python3 -m unittest discover -s tests"""
import copy
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import aed_standard as A  # noqa: E402
from aed_standard import schema as S, sources as M  # noqa: E402
from aed_standard.dedup import deduplicate  # noqa: E402
from aed_standard.validate import check_record  # noqa: E402

RAW = os.path.join(ROOT, "datasets", "raw")
DGP = os.path.join(RAW, "dane_gov_pl")


def read(path):
    with open(path, "rb") as f:
        return f.read()


def codes(report):
    return {p["kod"] for p in report["problemy"]}


def rec(zrodlo, zrodlo_id, lat, lon, **kw):
    r = S.blank_record()
    r.update(zrodlo=zrodlo, zrodlo_id=zrodlo_id, szerokosc_geograficzna=str(lat), dlugosc_geograficzna=str(lon),
             licencja="ODbL 1.0" if zrodlo == M.OSM else "CC BY 4.0", status="niepotwierdzony", **kw)
    return r


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapped, cls.notes = M.load_all(RAW)
        cls.records, cls.pairs, cls.report = A.build_registry(RAW)

    def test_legionowo_is_subset_of_standard(self):
        records, report = A.validate_csv(read(os.path.join(DGP, "legionowo", "resource_2625221.csv")), "publikacja")
        self.assertEqual(len(records), 24)
        # Only system-assigned columns are missing; no unknown column, no row-level error.
        self.assertEqual({p["kod"] for p in report["problemy"]}, {"brak_kolumny"})
        self.assertEqual({p["pole"] for p in report["problemy"]}, {"id_aed", "status", "zrodlo", "licencja"})
        for r in (r for r in self.mapped if r["zrodlo"] == "dane.gov.pl/40593"):
            r = dict(r, id_aed=A.make_id(r["zrodlo"], r["zrodlo_id"]))
            self.assertEqual(check_record(r, "publikacja"), [])

    def test_marki_repair(self):
        marki = [r for r in self.mapped if r["zrodlo"] == "dane.gov.pl/4955"]
        self.assertEqual(len(marki), 8)
        for r in marki:
            if r["zrodlo_id"] == "7":  # coordinates copied from Krosno: cleared
                self.assertEqual(r["szerokosc_geograficzna"], "")
                continue
            lat, lon = float(r["szerokosc_geograficzna"]), float(r["dlugosc_geograficzna"])
            self.assertTrue(52.2 < lat < 52.4 and 21.0 < lon < 21.2, r)
            self.assertEqual([p for p in check_record(r, "publikacja") if p["pole"] == "szerokosc_geograficzna"], [])
        self.assertTrue(any("Marki" in n and "zamienione" in n for n in self.notes))

    def test_warsaw_count(self):
        self.assertEqual(sum(1 for r in self.mapped if r["zrodlo"] == M.WARSAW), 708)

    def test_broken_csv_detector_on_real_marki(self):
        _, report = A.validate_csv(read(os.path.join(DGP, "marki", "resource_68353.csv")), "publikacja")
        self.assertIn("wiersz_w_cudzyslowie", codes(report))
        self.assertEqual(report["poprawne_wiersze"], [])

    def test_file_level_checks(self):
        self.assertIn("separator", codes(A.validate_csv(read(os.path.join(DGP, "przemysl", "resource_62095.csv")), "sprzedaz")[1]))
        self.assertIn("pusty_plik", codes(A.validate_csv(b"", "sprzedaz")[1]))
        self.assertIn("kodowanie", codes(A.validate_csv("producent\nŁódź".encode("cp1250"), "sprzedaz")[1]))
        self.assertIn("brak_wierszy", codes(A.validate_csv(b"producent,model\n", "sprzedaz")[1]))
        _, rep = A.validate_csv(b"\xef\xbb\xbfproducent,numer_seryjy\nX,1\n", "sprzedaz")
        self.assertIn("Czy chodziło o „numer_seryjny”", " ".join(p["komunikat"] for p in rep["problemy"]))
        self.assertIn("brak_kolumny", codes(rep))

    def test_swapped_coordinates(self):
        r = rec("zgloszenie", "1", 21.01, 52.23)
        found = [p for p in check_record(r, "publikacja") if p["kod"] == "wspolrzedne_zamienione"]
        self.assertEqual(len(found), 1)
        self.assertIn("52.23", found[0]["komunikat"])
        self.assertIn("poza_polska", {p["kod"] for p in check_record(rec("zgloszenie", "1", 40.0, 2.0), "publikacja")})

    def test_serial_number_merge(self):
        a = rec("zgloszenie", "s1", 52.1, 21.0, producent="Philips", numer_seryjny="B21K-04127")
        b = rec("dane.gov.pl/1", "x", 50.0, 19.0, producent="PHILIPS", numer_seryjny="b21k 04127", nazwa="Szkoła")
        merged, _, _ = deduplicate([a, b])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["zrodlo"], "zgloszenie")
        self.assertEqual(merged[0]["nazwa"], "Szkoła")  # gap filled from non-OSM member
        self.assertEqual(merged[0]["powiazane_zrodla"], "dane.gov.pl/1:x")

    def test_same_source_never_merges(self):
        a = rec(M.WARSAW, "1", 52.2, 21.0, nazwa="Urząd")
        b = rec(M.WARSAW, "2", 52.2, 21.00001, nazwa="Urząd")
        o = rec(M.OSM, "node/1", 52.2, 21.00002, nazwa="Urząd")
        merged, pairs, _ = deduplicate([a, b, o])
        self.assertEqual(len(merged), 2)
        # The OSM node joins the closer Warsaw record; the other pair goes to review.
        joined = [m for m in merged if m["powiazane_zrodla"]]
        self.assertEqual([m["zrodlo_id"] for m in joined], ["2"])
        self.assertEqual([p["powod"] for p in pairs], ["konflikt_zrodel"])
        for m in self.records:
            members = [m["zrodlo"]] + [x.split(":", 1)[0] for x in m["powiazane_zrodla"].split(";") if x]
            self.assertEqual(len(members), len(set(members)), m)

    def test_osm_values_never_leak(self):
        w = rec(M.WARSAW, "1", 52.2, 21.0, nazwa="Urząd")
        o = rec(M.OSM, "node/1", 52.2, 21.00001, nazwa="Urząd", godziny_dostepu="24/7", dostep="publiczny")
        merged, _, _ = deduplicate([w, o])
        self.assertEqual(len(merged), 1)
        self.assertEqual((merged[0]["godziny_dostepu"], merged[0]["dostep"], merged[0]["licencja"]), ("", "", "CC BY 4.0"))
        # Real registry: every value of a non-OSM record comes from one of its non-OSM members.
        by_key = {(r["zrodlo"], r["zrodlo_id"]): r for r in self.mapped}
        for m in self.records:
            if m["zrodlo"] == M.OSM:
                continue
            self.assertNotEqual(m["licencja"], "ODbL 1.0")
            members = [by_key[(m["zrodlo"], m["zrodlo_id"])]] + [
                by_key[tuple(x.split(":", 1))] for x in m["powiazane_zrodla"].split(";") if x]
            sources = [r for r in members if r["zrodlo"] != M.OSM]
            for f in S.FIELD_NAMES:
                if m[f] and f not in ("id_aed", "kompletnosc", "powiazane_zrodla", "licencja"):
                    self.assertIn(m[f], [r[f] for r in sources], (f, m["id_aed"]))

    def test_id_stable_across_builds(self):
        again, _, _ = A.build_registry(RAW)
        ids = lambda recs: {(r["zrodlo"], r["zrodlo_id"]): r["id_aed"] for r in recs}
        self.assertEqual(ids(self.records), ids(again))
        self.assertEqual(len({r["id_aed"] for r in self.records}), len(self.records))
        self.assertEqual(A.make_id("um.warszawa.pl", "622"), A.make_id("um.warszawa.pl", "622"))
        self.assertRegex(A.make_id("x", "1"), r"^AED-[A-Z2-7]{12}$")

    def test_publication_export(self):
        export = A.publication_export(self.records)
        self.assertTrue(export)
        self.assertEqual(len(export), self.report["eksport_dane_gov_pl"]["rekordy"])
        for r in export:
            self.assertNotEqual(r["licencja"], "ODbL 1.0")
            self.assertNotEqual(r["dostep"], "prywatny")
            self.assertEqual([p for p in check_record(r, "publikacja") if p["poziom"] == "blad"], [])

    def test_example_seller_files(self):
        recs, ok = A.validate_csv(read(os.path.join(ROOT, "wzorzec", "przyklad-sprzedawca.csv")), "sprzedaz")
        self.assertTrue(ok["poprawny"])
        self.assertEqual(ok["podsumowanie"]["poprawne"], len(recs))
        self.assertGreaterEqual(len(recs), 10)
        _, bad = A.validate_csv(read(os.path.join(ROOT, "wzorzec", "przyklad-sprzedawca-bledy.csv")), "sprzedaz")
        self.assertFalse(bad["poprawny"])
        self.assertTrue({"brak_wymaganego", "format_daty", "termin_minal", "data_z_przyszlosci", "spoza_slownika",
                         "wspolrzedne_zamienione", "duplikat_numeru_seryjnego", "format_email",
                         "przecinek_dziesietny"} <= codes(bad))
        _, pub = A.validate_csv(read(os.path.join(ROOT, "wzorzec", "przyklad-publikacja.csv")), "publikacja")
        self.assertTrue(pub["poprawny"], pub["problemy"])

    def test_malformed_files_are_file_level_problems(self):
        cases = {
            b",,\n": "pusty_plik",
            b"producent\n\"" + b"x" * 200000 + b"\"\n": "pole_za_dlugie",
            b"producent,model,numer_seryjny\n": "brak_wierszy",
            b"  \n\n\r\n \t\n": "pusty_plik",
            b"producent,model\nab\x00c,d\n": "znak_nul",
            "producent,model\nX,Y\n".encode("utf-16"): "kodowanie",
        }
        for data, code in cases.items():
            records, report = A.validate_csv(data, "sprzedaz")
            self.assertEqual(records, [], data[:20])
            self.assertFalse(report["poprawny"])
            self.assertIn(code, codes(report), data[:20])
            for p in report["problemy"]:
                self.assertEqual((p["wiersz"], p["poziom"]), (None, "blad"))
                self.assertTrue(p["komunikat"])

    def test_different_serials_never_merge_spatially(self):
        a = rec("zgloszenie", "s1", 52.2, 21.0, producent="Philips", numer_seryjny="A-1", nazwa="Urząd")
        b = rec("dane.gov.pl/1", "x", 52.2, 21.00001, producent="Philips", numer_seryjny="A-2", nazwa="Urząd")
        o = rec(M.OSM, "node/1", 52.2, 21.000005, nazwa="Urząd")
        merged, pairs, _ = deduplicate([a, b, o])
        self.assertEqual(len(merged), 2)
        self.assertEqual(sorted(m["numer_seryjny"] for m in merged), ["A-1", "A-2"])
        self.assertEqual(sum(1 for m in merged if "openstreetmap:node/1" in m["powiazane_zrodla"]), 1)
        serial_pair = {A.make_id("zgloszenie", "s1"), A.make_id("dane.gov.pl/1", "x")}
        self.assertFalse([p for p in pairs if {p["id_aed_a"], p["id_aed_b"]} == serial_pair])
        self.assertEqual(A.find_candidates(a, [b]), [])

    def test_find_candidates_matches_batch(self):
        pair = next(p for p in self.pairs if p["powod"] == "kandydat")
        [c] = A.find_candidates(pair["rekord_a"], [pair["rekord_b"]])
        self.assertEqual((c["id_aed"], c["odleglosc_m"], c["podobienstwo"], c["powod"], c["auto"]),
                         (pair["rekord_b"]["id_aed"], pair["odleglosc_m"], pair["podobienstwo"], "kandydat", False))
        a = rec("zgloszenie", "s1", 52.2, 21.0, producent="Philips", numer_seryjny="A-1")
        near = rec(M.WARSAW, "9", 52.2, 21.0001)  # ~7 m
        far = rec(M.WARSAW, "10", 52.3, 21.0)
        self.assertEqual([(c["powod"], c["auto"]) for c in A.find_candidates(a, [near, far])], [("odleglosc", True)])

    def test_validate_records_does_not_mutate(self):
        rows = [{"producent": "X", "numer_seryjny": "1"}, {"producent": "x", "numer_seryjny": "1", "status": "aktywny"}]
        before = copy.deepcopy(rows)
        report = A.validate_records(rows, "sprzedaz")
        self.assertEqual(rows, before)
        self.assertIn("duplikat_numeru_seryjnego", codes(report))
        self.assertIn("wymagane_dla_aktywnego", codes(report))
        self.assertEqual(report["poprawne_wiersze"], [])
        self.assertEqual(A.completeness(S.blank_record()), 0)
        self.assertEqual(A.field_names(), [f["name"] for f in A.load_schema()["fields"]])


if __name__ == "__main__":
    unittest.main()
