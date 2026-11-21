"""Tests on the real raw files. Run: python3 -m unittest discover -s tests"""
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import aed_standard as A  # noqa: E402
from aed_standard import schema as S, sources as M  # noqa: E402
from aed_standard.build import publication_export, to_csv  # noqa: E402
from aed_standard.dedup import copies_values, deduplicate, priority  # noqa: E402
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


class RegistryBuildTest(unittest.TestCase):
    def test_committed_outputs_match_build(self):
        records, pairs, report = A.build_registry(RAW)
        with open(os.path.join(ROOT, "datasets", "out", "aed_dane_gov_pl.csv"), encoding="utf-8", newline="") as f:
            self.assertEqual(to_csv(publication_export(records)), f.read())
        with open(os.path.join(ROOT, "datasets", "out", "raport.json"), encoding="utf-8") as f:
            committed = json.load(f)
        for key in ("bledy_zrodel", "pominiete_zrodla"):  # source problems: none on the real data
            self.assertEqual(report.pop(key, []), [])
            committed.pop(key, None)
        self.assertEqual(report, committed)


class PriorityTest(unittest.TestCase):
    def test_unknown_source_in_dedup_is_loud(self):
        with self.assertRaisesRegex(ValueError, "nieznane-zrodlo"):
            priority(rec("nieznane-zrodlo", "1", 52.2, 21.0))

    def test_priority_from_registry_without_meta(self):
        # records built outside load_all (service, tests) fall back to the registry by zrodlo
        self.assertEqual(priority(rec("zgloszenie", "1", 52.2, 21.0))[0], 0)
        self.assertEqual(priority(rec("dane.gov.pl/3624", "1", 52.2, 21.0))[0], 1)
        self.assertEqual(priority(rec(M.WARSAW, "1", 52.2, 21.0))[0], 2)
        self.assertEqual(priority(rec(M.OSM, "n/1", 52.2, 21.0))[0], 3)
        self.assertFalse(copies_values(rec(M.OSM, "n/1", 52.2, 21.0)))
        self.assertTrue(copies_values(rec("zgloszenie", "1", 52.2, 21.0)))

    def test_meta_fields_win_over_registry(self):
        r = rec(M.OSM, "n/1", 52.2, 21.0)
        r.update(_priority=7, _copy_values=True)
        self.assertEqual(priority(r)[0], 7)
        self.assertTrue(copies_values(r))


NEW_ENTRY = {"id": "testowo", "label": "Testowo", "zrodlo": "dane.gov.pl/999999", "priority": 1,
             "file": "dane_gov_pl/testowo/resource_1.csv", "format": "csv", "record_id": {"column": "Id"},
             "coordinates": {"lat": "Lat", "lon": "Lon"}, "fields": {"nazwa": "Nazwa", "miejscowosc": "Miasto"}}


class NewSourceTest(unittest.TestCase):
    """A municipality added with a registry entry only: a copy of the real raw snapshot plus one fictitious file."""

    def fixture(self, licence="CC0 1.0", header="Id,Nazwa,Miasto,Lat,Lon", in_manifest=True, rows=None, entry=None,
                build=True):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        raw = os.path.join(tmp, "raw")
        os.makedirs(os.path.join(raw, "dane_gov_pl", "testowo"))
        for name in os.listdir(RAW):  # symlinks: the real snapshot stays untouched and the copy is instant
            if name not in ("manifest.json", "dane_gov_pl"):
                os.symlink(os.path.join(RAW, name), os.path.join(raw, name))
        for name in os.listdir(DGP):
            os.symlink(os.path.join(DGP, name), os.path.join(raw, "dane_gov_pl", name))
        with open(os.path.join(raw, NEW_ENTRY["file"]), "w", encoding="utf-8") as f:
            body = rows if rows is not None else "1,Urząd Gminy Testowo,Testowo,52.1,19.1\n2,Szkoła Testowo,Testowo,52.2,19.2\n"
            f.write(header + "\n" + body)
        with open(os.path.join(RAW, "manifest.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        if in_manifest:
            manifest["files"].append({"file": NEW_ENTRY["file"], "source": "dane.gov.pl", "dataset_id": 999999,
                                      "resource_id": 1, "license": licence, "data_date": "2026-11-01"})
        with open(os.path.join(raw, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False)
        with open(os.path.join(ROOT, "aed_standard", "sources.json"), encoding="utf-8") as f:
            registry = json.load(f)
        registry["sources"].append(entry or NEW_ENTRY)
        reg = os.path.join(tmp, "sources.json")
        with open(reg, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False)
        return A.build_registry(raw, registry_path=reg) if build else M.load_all(raw, reg)

    def test_new_municipality_by_configuration_only(self):
        records, _, report = self.fixture()
        mine = [r for r in records if r["zrodlo"] == "dane.gov.pl/999999"]
        self.assertEqual(sorted(r["nazwa"] for r in mine), ["Szkoła Testowo", "Urząd Gminy Testowo"])
        self.assertEqual({r["licencja"] for r in mine}, {"CC0 1.0"})
        self.assertEqual({r["id_aed"] for r in mine},
                         {A.make_id("dane.gov.pl/999999", "1"), A.make_id("dane.gov.pl/999999", "2")})
        self.assertEqual((report["bledy_zrodel"], report["pominiete_zrodla"]), ([], []))
        self.assertEqual(report["rekordy_na_zrodlo"]["dane.gov.pl/999999"]["przed"], 2)

    def test_unknown_licence_skips_only_that_source(self):
        records, _, report = self.fixture(licence="CC BY-SA 4.0")
        self.assertNotIn("dane.gov.pl/999999", {r["zrodlo"] for r in records})
        self.assertEqual(report["pominiete_zrodla"], ["dane.gov.pl/999999"])
        self.assertIn("CC BY-SA 4.0", report["bledy_zrodel"][0])
        self.assertEqual(report["rejestr_rekordy"], 18814)

    def test_changed_header_skips_only_that_source(self):
        records, _, report = self.fixture(header="ID,Name,Town,Lat,Lon")
        self.assertEqual(report["pominiete_zrodla"], ["dane.gov.pl/999999"])
        self.assertIn("Testowo", report["bledy_zrodel"][0])
        self.assertIn("Nazwa", report["bledy_zrodel"][0])
        self.assertEqual(report["rejestr_rekordy"], 18814)

    def test_invalid_entry_is_not_listed_as_processed(self):
        # a typo in a key drops the entry at validation: its zrodlo must not be among the processed sources,
        # so the service never treats its devices as gone
        _, _, report = self.fixture(entry=dict(NEW_ENTRY, feilds={}))
        self.assertIn("feilds", report["bledy_zrodel"][0])
        self.assertNotIn("dane.gov.pl/999999", report["zrodla_przetworzone"])
        self.assertIn("dane.gov.pl/3624", report["zrodla_przetworzone"])

    def test_header_only_file_skips_source(self):
        _, _, report = self.fixture(rows="")
        self.assertEqual(report["pominiete_zrodla"], ["dane.gov.pl/999999"])
        self.assertNotIn("dane.gov.pl/999999", report["zrodla_przetworzone"])

    def test_odbl_source_never_copies_values_whatever_the_flag(self):
        records, _, _, _ = self.fixture(licence="ODbL 1.0 (© OpenStreetMap contributors)", build=False)
        mine = [r for r in records if r["zrodlo"] == "dane.gov.pl/999999"]
        self.assertEqual(len(mine), 2)
        self.assertEqual({r["_copy_values"] for r in mine}, {False})

    def test_bad_coordinates_blank_only_that_row(self):
        rows = '1,Urząd,Testowo,"52,1","19,1"\n2,Szkoła,Testowo,,19.2\n3,Przedszkole,Testowo,52.3,19.3\n'
        records, notes, errors, _ = self.fixture(rows=rows, build=False)
        mine = {r["zrodlo_id"]: r for r in records if r["zrodlo"] == "dane.gov.pl/999999"}
        self.assertEqual(errors, [])
        self.assertEqual((mine["1"]["szerokosc_geograficzna"], mine["1"]["dlugosc_geograficzna"]), ("52.1", "19.1"))
        self.assertEqual((mine["2"]["szerokosc_geograficzna"], mine["2"]["dlugosc_geograficzna"]), ("", ""))
        self.assertEqual(mine["3"]["szerokosc_geograficzna"], "52.3")
        self.assertTrue(any("Testowo, rekord 2" in n for n in notes), notes)

    def test_missing_file_skips_source(self):
        _, _, report = self.fixture(in_manifest=False)
        self.assertEqual(report["pominiete_zrodla"], ["dane.gov.pl/999999"])
        self.assertIn("manifest.json", report["bledy_zrodel"][0])


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapped, cls.notes, _, _ = M.load_all(RAW)
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
        b = rec("dane.gov.pl/3624", "x", 50.0, 19.0, producent="PHILIPS", numer_seryjny="b21k 04127", nazwa="Szkoła")
        merged, _, _ = deduplicate([a, b])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["zrodlo"], "zgloszenie")
        self.assertEqual(merged[0]["nazwa"], "Szkoła")  # gap filled from non-OSM member
        self.assertEqual(merged[0]["powiazane_zrodla"], "dane.gov.pl/3624:x")

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
        b = rec("dane.gov.pl/3624", "x", 52.2, 21.00001, producent="Philips", numer_seryjny="A-2", nazwa="Urząd")
        o = rec(M.OSM, "node/1", 52.2, 21.000005, nazwa="Urząd")
        merged, pairs, _ = deduplicate([a, b, o])
        self.assertEqual(len(merged), 2)
        self.assertEqual(sorted(m["numer_seryjny"] for m in merged), ["A-1", "A-2"])
        self.assertEqual(sum(1 for m in merged if "openstreetmap:node/1" in m["powiazane_zrodla"]), 1)
        serial_pair = {A.make_id("zgloszenie", "s1"), A.make_id("dane.gov.pl/3624", "x")}
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
