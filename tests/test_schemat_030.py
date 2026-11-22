"""Schema 0.3.0: additive changes. Files written for 0.2.0 (tests/dane/schemat-0.2.0, copied from the repository
before the change) are read as before; new fields, month dates, condition of the device, status zweryfikowany."""
import csv
import datetime
import io
import json
import os
import sqlite3
import tempfile
import unittest

import aed_standard as A
from aed_standard import schema as S
from aed_standard.build import publication_export
from aed_standard.konwerter import convert
from aed_standard.validate import check_record, looks_like_person, validate_csv
from aed_standard.wykaz import read_wykaz

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(HERE, "dane", "schemat-0.2.0")
LEGIONOWO = os.path.join(os.path.dirname(HERE), "datasets", "raw", "dane_gov_pl", "legionowo", "resource_2625221.csv")
TODAY = datetime.date(2026, 11, 22)
SOURCE = {"zrodlo": "dane.gov.pl/1", "zasob": 1, "tytul": "t", "instytucja": "i", "licencja": "CC0 1.0",
          "data_aktualizacji": "2026-11-22"}
# Accepted rows measured with the 0.2.0 code on the same files: (sprzedaz, publikacja, read_wykaz).
BEFORE = {"aed_dane_gov_pl.csv": (0, 781, 781), "przyklad-dane-otwarte.csv": (0, 3, 3),
          "przyklad-publikacja.csv": (3, 3, 3), "przyklad-sprzedawca-bledy.csv": (2, 0, 0),
          "przyklad-sprzedawca.csv": (10, 0, 0), LEGIONOWO: (0, 0, 24)}
NEW = {"pietro", "sposob_ustalenia_polozenia", "stan_urzadzenia", "data_stanu"}


def read(path):
    with open(path, "rb") as f:
        return f.read()


def codes(problems, level=None):
    return {p["kod"] for p in problems if level is None or p["poziom"] == level}


class BackwardCompatibilityTest(unittest.TestCase):
    def test_files_of_0_2_0_are_read_as_before(self):
        for name, (sale, pub, listed) in BEFORE.items():
            data = read(os.path.join(OLD, name))
            got = []
            for profile in ("sprzedaz", "publikacja"):
                _, rep = validate_csv(data, profile, TODAY)
                got.append(rep["podsumowanie"]["poprawne"])
                self.assertFalse({p["pole"] for p in rep["problemy"]} & NEW, name)  # no new column is demanded
            recs, rep = read_wykaz(data, SOURCE, TODAY)
            got.append(rep["przyjete"])
            self.assertEqual(tuple(got), (sale, pub, listed), name)

    def test_status_aktywny_of_0_2_0_comes_out_as_zweryfikowany(self):
        data = read(os.path.join(OLD, "przyklad-publikacja.csv"))
        self.assertIn(b",aktywny,", data)
        records, rep = validate_csv(data, "publikacja", TODAY)
        self.assertEqual({r["status"] for r in records}, {"zweryfikowany"})
        recs, _ = read_wykaz(data, SOURCE, TODAY)
        self.assertEqual({r["status"] for r in recs}, {"zweryfikowany"})
        out = list(csv.DictReader(io.StringIO(A.build.to_csv(publication_export(recs)))))
        self.assertEqual(({r["status"] for r in out}, {r["numer_seryjny"] for r in out}), ({"zweryfikowany"}, {""}))

    def test_converter_maps_the_old_status_and_reports_it(self):
        data = ("nazwa,lat,lon,miejscowosc,status,bateria\nUrząd,52.2,21.0,Warszawa,aktywny,2030/1\n").encode()
        mapping = {"nazwa": "nazwa", "lat": "szerokosc_geograficzna", "lon": "dlugosc_geograficzna",
                   "miejscowosc": "miejscowosc", "status": "", "bateria": "data_waznosci_baterii"}
        text, rep = convert(data, "a.csv", mapping, today=TODAY)
        self.assertEqual(next(csv.DictReader(io.StringIO(text)))["data_waznosci_baterii"], "2030-01")  # a month stays
        from aed_standard.konwerter import normalize_value
        self.assertEqual(normalize_value("status", "aktywny"), "zweryfikowany")


class NewFieldsTest(unittest.TestCase):
    def rec(self, **kw):
        r = S.blank_record()
        r.update(id_aed="AED-1", nazwa="Urząd", szerokosc_geograficzna="52.2", dlugosc_geograficzna="21.0",
                 miejscowosc="Warszawa", status="niepotwierdzony", zrodlo="test", licencja="CC0 1.0")
        r.update(kw)
        return r

    def issues(self, **kw):
        return check_record(self.rec(**kw), "publikacja", today=TODAY)

    def test_month_dates(self):
        self.assertEqual(A.valid_until("2028-02"), datetime.date(2028, 2, 29))
        self.assertEqual(A.valid_until("2028-02-03"), datetime.date(2028, 2, 3))
        self.assertEqual(codes(self.issues(data_waznosci_baterii="2030-01", data_produkcji="2024-03")), set())
        self.assertEqual(codes(self.issues(data_waznosci_baterii="2030-13")), {"format_daty"})
        self.assertEqual(codes(self.issues(data_waznosci_elektrod="2026-11")), set())       # valid to 30 November
        self.assertEqual(codes(self.issues(data_waznosci_elektrod="2026-10")), {"termin_minal"})
        self.assertEqual(codes(self.issues(data_produkcji="2026-11")), set())
        self.assertEqual(codes(self.issues(data_produkcji="2026-12")), {"data_z_przyszlosci"})
        self.assertEqual(codes(self.issues(data_weryfikacji="2026-11")), {"format_daty"})    # day precision only
        self.assertEqual(S.BY_NAME["data_waznosci_baterii"]["type"], "string")   # a mixed column is text

    def test_terc_six_digits_is_a_warning(self):
        self.assertEqual(codes(self.issues(kod_terc="1408011")), set())
        self.assertEqual(codes(self.issues(kod_terc="140801"), "ostrzezenie"), {"terc_bez_rodzaju"})
        self.assertEqual(codes(self.issues(kod_terc="140801"), "blad"), set())
        self.assertEqual(codes(self.issues(kod_terc="14080"), "blad"), {"format_pola"})

    def test_hours_of_a_verified_record_must_be_readable(self):
        ok = dict(status="zweryfikowany", dostep="publiczny", data_weryfikacji="2026-11-01")
        self.assertEqual(codes(self.issues(godziny_dostepu="Mo-Fr 08:00-16:00", **ok)), set())
        self.assertEqual(codes(self.issues(godziny_dostepu="w godzinach pracy urzędu", **ok)), {"godziny_nieczytelne"})
        self.assertEqual(codes(self.issues(godziny_dostepu="Sa 22:00-02:00", **ok)), {"godziny_nieczytelne"})
        self.assertEqual(codes(self.issues(godziny_dostepu="w godzinach pracy urzędu")), set())   # only verified ones

    def test_floor_and_dictionaries(self):
        self.assertEqual(codes(self.issues(pietro="-1", stan_urzadzenia="gotowy", data_stanu="2026-11-20",
                                           sposob_ustalenia_polozenia="pomiar_przy_urzadzeniu")), set())
        self.assertEqual(codes(self.issues(pietro="61")), {"poza_zakresem"})
        self.assertEqual(codes(self.issues(pietro="1.5")), {"format_liczby_calkowitej"})
        self.assertEqual(codes(self.issues(stan_urzadzenia="zepsuty")), {"spoza_slownika"})

    def test_person_as_owner_is_a_warning(self):
        for name in ("Jan Kowalski", "Anna Maria Nowak-Kowalska"):
            self.assertTrue(looks_like_person(name), name)
            self.assertEqual(codes(self.issues(dysponent_nazwa=name), "ostrzezenie"), {"dysponent_osoba"})
        for name in ("Urząd Miasta Legionowo", "Szkoła Podstawowa nr 3", "OSP Wola", "„Kowalski” Sp. z o.o.",
                     "MOSiR Krosno", "Apteka Zdrowie", "Jan"):
            self.assertFalse(looks_like_person(name), name)

    def test_public_fields_and_completeness(self):
        self.assertEqual(A.hidden_fields(), ["numer_seryjny", "dysponent_email", "dysponent_telefon"])
        self.assertEqual(A.build.HIDDEN_PUBLIC, tuple(A.hidden_fields()))
        r = self.rec(numer_seryjny="SN-1", dysponent_email="a@b.pl", dysponent_telefon="+48 1")
        out = publication_export([r])[0]
        self.assertEqual((out["numer_seryjny"], out["dysponent_email"]), ("", ""))
        self.assertEqual(out["kompletnosc"], str(A.public_completeness(r)))
        self.assertGreater(A.public_completeness(r), A.completeness(dict(r, numer_seryjny="", dysponent_email="",
                                                                          dysponent_telefon="")))
        # the condition counts for a verified record only; "nieznany" is no answer
        self.assertEqual(A.completeness(self.rec(stan_urzadzenia="gotowy")), A.completeness(self.rec()))
        v = self.rec(status="zweryfikowany")
        self.assertGreater(A.completeness(dict(v, stan_urzadzenia="gotowy")), A.completeness(v))
        self.assertEqual(A.completeness(dict(v, stan_urzadzenia="nieznany")), A.completeness(v))

    def test_registry_build_marks_imported_positions(self):
        with open(os.path.join(os.path.dirname(HERE), "datasets", "out", "aed_dane_gov_pl.csv"), encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual({r["sposob_ustalenia_polozenia"] for r in rows}, {"import"})
        self.assertEqual({r["kompletnosc"] for r in rows if not r["kompletnosc"]}, set())


class ServiceTest(unittest.TestCase):
    """Path seller -> sticker -> ready -> problem -> not in "available now" -> export; and the 0.2.0 migration."""

    def setUp(self):
        from falcon import testing
        from aed_service import app as svc
        from tests.test_aed_service import NEXT_YEAR
        self.svc, self.next_year = svc, NEXT_YEAR
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "t.db")
        self.db = svc.open_db(self.path, with_registry=False)
        self.addCleanup(self.db.close)
        self.c = testing.TestClient(svc.build_app(self.db))

    def test_condition_of_the_device(self):
        r = self.c.simulate_post("/api/aed/sesja", json={"email": "pulsar@aed.example", "haslo": "pulsar-demo"})
        h = {"Authorization": "Bearer " + r.json["token"]}
        r = self.c.simulate_post("/api/aed/urzadzenia", headers=h, json={
            "producent": "Pulsar", "model": "P-1", "numer_seryjny": "S-1", "data_produkcji": "2025-01",
            "data_waznosci_elektrod": self.next_year, "data_waznosci_baterii": self.next_year[:7],
            "dysponent_nazwa": "Szkoła nr 1", "dysponent_email": "szkola@example.org", "stan_urzadzenia": "gotowy"})
        self.assertEqual(r.status_code, 201, r.text)
        item = r.json["przyjete"][0]
        dev = "/api/aed/urzadzenia/" + item["id_aed"]
        t = item["link_aktywacyjny"].split("t=")[1]
        got = self.c.simulate_get(dev).json
        self.assertEqual(got["stan_urzadzenia"], "")   # the seller does not decide the condition
        self.assertEqual(got["waznosc_do"]["data_waznosci_baterii"], str(A.valid_until(self.next_year[:7])))
        base = {"t": t, "nazwa": "Szkoła nr 1", "szerokosc_geograficzna": 52.39, "dlugosc_geograficzna": 20.93,
                "miejscowosc": "Legionowo", "dostep": "publiczny", "godziny_dostepu": "24/7", "pietro": "0"}
        r = self.c.simulate_post(dev + "/potwierdzenie", json=dict(base, stan="sprawny",
                                                                   sposob_ustalenia_polozenia="pomiar_przy_urzadzeniu"))
        today = datetime.date.today().isoformat()
        self.assertEqual((r.json["status"], r.json["stan_urzadzenia"], r.json["data_stanu"]), ("zweryfikowany", "gotowy", today))
        self.assertEqual(r.json["rekord"]["sposob_ustalenia_polozenia"], "pomiar_przy_urzadzeniu")
        near = "lat=52.39&lon=20.93"
        self.assertEqual(self.c.simulate_get("/api/aed/urzadzenia", query_string="dostepny_teraz=1").json["razem"], 1)
        r = self.c.simulate_post(dev + "/potwierdzenie", json={"t": t, "stan": "problem", "uwagi": "Wymiana baterii"})
        self.assertEqual((r.json["status"], r.json["stan_urzadzenia"]), ("zweryfikowany", "czasowo_niedostepny"))
        for q in ("dostepny_teraz=1", near):
            self.assertEqual(self.c.simulate_get("/api/aed/urzadzenia", query_string=q).json["razem"], 0, q)
        self.assertEqual(self.c.simulate_get("/api/aed/urzadzenia", query_string="stan_urzadzenia=czasowo_niedostepny").json["razem"], 1)
        self.assertEqual(self.c.simulate_get("/api/aed/urzadzenia", query_string="status=aktywny").json["razem"], 1)  # alias
        self.assertEqual(self.c.simulate_get("/api/aed/filtry").json["stan_urzadzenia"]["czasowo_niedostepny"], 1)
        feat = self.c.simulate_get("/api/aed/urzadzenia.geojson").json["features"][0]["properties"]
        self.assertEqual((feat["status"], feat["stan_urzadzenia"]), ("zweryfikowany", "czasowo_niedostepny"))
        # a bystander's signal never changes the condition (hard rule 2)
        self.c.simulate_post(dev + "/sygnal", json={"typ": "jest"})
        self.assertEqual(self.c.simulate_get(dev).json["stan_urzadzenia"], "czasowo_niedostepny")
        text = self.c.simulate_get("/api/aed/eksport/dane-gov-pl.csv").text
        row = next(csv.DictReader(io.StringIO(text)))
        self.assertTrue(NEW <= set(row))
        self.assertEqual((row["status"], row["stan_urzadzenia"], row["pietro"], row["numer_seryjny"]),
                         ("zweryfikowany", "czasowo_niedostepny", "0", ""))
        self.assertEqual(row["kompletnosc"], str(A.public_completeness(row)))
        # moving the point without saying how clears the old method
        r = self.c.simulate_post(dev + "/potwierdzenie", json=dict(base, stan="sprawny", szerokosc_geograficzna=52.391))
        self.assertEqual((r.json["rekord"]["sposob_ustalenia_polozenia"], r.json["stan_urzadzenia"]), ("", "gotowy"))
        s = self.c.simulate_get("/api/aed/sprzedawcy").json["dane"][0]
        self.assertEqual(s["udzial_zweryfikowanych"], s["udzial_aktywnych"])

    def test_migration_of_a_0_2_0_database(self):
        def old(id_aed, origin, uwagi=None, **kw):
            rec = {k: "" for k in A.field_names() if k not in NEW}
            rec.update(id_aed=id_aed, nazwa="X", szerokosc_geograficzna="52.1", dlugosc_geograficzna="21.1",
                       miejscowosc="W", zrodlo="test", licencja="CC0 1.0", **kw)
            self.db.execute("INSERT INTO devices(id_aed,data,origin,uwagi_zarzadcy,status) VALUES(?,?,?,?,?)",
                            (id_aed, json.dumps(rec), origin, uwagi, rec["status"]))
        qr = dict(sposob_weryfikacji="qr", data_weryfikacji="2026-10-01", data_aktualizacji="2026-10-05")
        old("AED-READY", "zarzadca", status="aktywny", **qr)
        old("AED-PROBLEM", "zarzadca", "Brak elektrod", status="niepotwierdzony", **qr)
        old("AED-NEW", "zgloszenie", status="zgloszony")
        old("AED-IMPORT", "import", status="aktywny")        # a provider's list said so: no proof of a QR answer
        self.db.commit()
        self.db.close()
        db = self.svc.open_db(self.path, with_registry=False)
        self.addCleanup(db.close)
        got = {r[0]: (json.loads(r[1]), r[2]) for r in db.execute("SELECT id_aed, data, status FROM devices")}
        view = {k: (v[1], v[0]["status"], v[0]["stan_urzadzenia"], v[0]["data_stanu"], v[0]["sposob_ustalenia_polozenia"])
                for k, v in got.items()}
        self.assertEqual(view["AED-READY"], ("zweryfikowany", "zweryfikowany", "gotowy", "2026-10-01", ""))
        self.assertEqual(view["AED-PROBLEM"], ("zweryfikowany", "zweryfikowany", "czasowo_niedostepny", "2026-10-05", ""))
        self.assertEqual(view["AED-NEW"], ("zgloszony", "zgloszony", "", "", ""))
        self.assertEqual(view["AED-IMPORT"], ("zweryfikowany", "zweryfikowany", "", "", "import"))
        self.svc.migrate(db)   # once only: a second start changes nothing
        self.assertEqual(got, {r[0]: (json.loads(r[1]), r[2]) for r in db.execute("SELECT id_aed, data, status FROM devices")})


if __name__ == "__main__":
    unittest.main()
