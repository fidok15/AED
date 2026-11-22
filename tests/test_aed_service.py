"""End-to-end tests of aed_service on a temporary database (Falcon testing client, real aed_standard)."""
import contextlib
import csv
import datetime
import gc
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
import warnings
import xml.etree.ElementTree as ET
from unittest import mock

import aed_standard
from falcon import testing

from aed_service import app as svc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "wzorzec", "przyklad-sprzedawca.csv")
NEXT_YEAR = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()


def seller_csv(serials, bad_row=False):
    """Small valid seller CSV built from schema field names (used when the sample file is absent)."""
    out = io.StringIO()
    cols = ["producent", "model", "numer_seryjny", "data_produkcji", "data_waznosci_elektrod",
            "data_waznosci_baterii", "dysponent_nazwa", "dysponent_email"]
    w = csv.writer(out)
    w.writerow(cols)
    for s in serials:
        w.writerow(["Pulsar", "P-1", s, "2025-01-10", NEXT_YEAR, NEXT_YEAR, "Szkoła Podstawowa nr 1", "szkola@example.org"])
    if bad_row:
        w.writerow(["Pulsar", "P-1", "BAD", "10.01.2025", NEXT_YEAR, NEXT_YEAR, "X", "nie-email"])
    return out.getvalue().encode("utf-8")


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def multipart(data, filename="zgloszenie.csv", fields=None):
    b = "XXBOUNDARYXX"
    body = b"".join(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (b, k, v)).encode()
                    for k, v in (fields or {}).items())
    body += ('--%s\r\nContent-Disposition: form-data; name="plik"; filename="%s"\r\nContent-Type: text/csv\r\n\r\n'
             % (b, filename)).encode() + data + ("\r\n--%s--\r\n" % b).encode()
    return {"body": body, "headers": {"Content-Type": "multipart/form-data; boundary=" + b}}


class DbLifecycleTest(unittest.TestCase):
    def test_closed_app_leaves_no_open_database(self):
        with tempfile.TemporaryDirectory() as tmp, warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            conn = svc.open_db(os.path.join(tmp, "t.db"), with_registry=False)
            testing.TestClient(svc.build_app(conn)).simulate_get("/api/aed/statystyki")
            conn.close()
            del conn
            gc.collect()
        self.assertEqual([str(w.message) for w in caught if issubclass(w.category, ResourceWarning)], [])


class ServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = svc.open_db(os.path.join(cls.tmp.name, "t.db"), with_registry=False)
        cls.client = testing.TestClient(svc.build_app(cls.db))

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.tmp.cleanup()

    def login(self, email, password):
        r = self.client.simulate_post("/api/aed/sesja", json={"email": email, "haslo": password})
        self.assertEqual(r.status_code, 200, r.text)
        return {"Authorization": "Bearer " + r.json["token"]}

    def firma(self):
        return self.login("pulsar@aed.example", "pulsar-demo")

    def ministry(self):
        return self.login("ministerstwo@aed.example", "ministerstwo-demo")

    def submit(self, data, path="/api/aed/zgloszenia", headers=None):
        return self.client.simulate_post(path, headers=dict(headers or self.firma(), **multipart(data)["headers"]),
                                         body=multipart(data)["body"])

    def confirm_body(self, token, **kw):
        return dict({"t": token, "nazwa": "Szkoła Podstawowa nr 1", "szerokosc_geograficzna": 52.395198,
                     "dlugosc_geograficzna": 20.931382, "miejscowosc": "Legionowo", "dostep": "publiczny",
                     "godziny_dostepu": "Mo-Fr 08:00-16:00", "stan": "sprawny"}, **kw)

    def test_full_path(self):
        c = self.client
        self.assertEqual(c.simulate_post("/api/aed/sesja", json={"email": "pulsar@aed.example", "haslo": "x"}).status_code, 401)
        h = self.firma()
        self.assertEqual(c.simulate_get("/api/aed/sesja", headers=h).json["rola"], "firma")
        data = read_bytes(SAMPLE) if os.path.exists(SAMPLE) else seller_csv(["S-100", "S-101"], bad_row=True)
        # dry run does not store anything
        dry = self.submit(data, "/api/aed/zgloszenia/sprawdz").json
        self.assertGreater(dry["podsumowanie"]["przyjete"], 0)
        self.assertEqual(c.simulate_get("/api/aed/zgloszenia", headers=h).json["dane"], [])
        r = self.submit(data)
        self.assertEqual(r.status_code, 201, r.text)
        out = r.json
        self.assertEqual(out["podsumowanie"]["przyjete"], dry["podsumowanie"]["przyjete"])
        self.assertEqual(len(c.simulate_get("/api/aed/zgloszenia", headers=h).json["dane"]), 1)
        dev = out["przyjete"][0]
        id_aed, token = dev["id_aed"], dev["link_aktywacyjny"].split("t=")[1]
        # sticker
        s = c.simulate_get(dev["naklejka_url"])
        self.assertEqual(s.status_code, 200)
        self.assertIn("svg", s.headers["content-type"])
        self.assertIn("<svg", s.text)
        # public view hides contact and serial number; manager view shows them
        pub = c.simulate_get("/api/aed/urzadzenia/" + id_aed).json
        for hidden in ("dysponent_email", "dysponent_telefon", "numer_seryjny"):
            self.assertNotIn(hidden, pub)
        self.assertEqual(pub["status"], "zgloszony")
        self.assertIs(pub["demo"], False)
        self.assertIn("numer_seryjny", c.simulate_get("/api/aed/urzadzenia/%s?t=%s" % (id_aed, token)).json)
        # activation mail in the outbox
        msgs = c.simulate_get("/api/aed/wiadomosci", headers=self.ministry()).json["dane"]
        self.assertTrue(any(m["id_aed"] == id_aed and token in m["link"] for m in msgs))
        # wrong token refused, record unchanged
        url = "/api/aed/urzadzenia/%s/potwierdzenie" % id_aed
        self.assertEqual(c.simulate_post(url, json=self.confirm_body("zly-token")).status_code, 403)
        self.assertEqual(c.simulate_get("/api/aed/urzadzenia/" + id_aed).json["status"], "zgloszony")
        # incomplete confirmation returns problems and is not saved
        r = c.simulate_post(url, json=self.confirm_body(token, nazwa=""))
        self.assertEqual(r.status_code, 422)
        self.assertTrue(r.json["blad"]["problemy"])
        self.assertEqual(c.simulate_get("/api/aed/urzadzenia/" + id_aed).json["status"], "zgloszony")
        # good token activates; record shows up in the publication export
        self.assertNotIn(id_aed, c.simulate_get("/api/aed/eksport/dane-gov-pl.csv").text)
        r = c.simulate_post(url, json=self.confirm_body(token))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual((r.json["status"], r.json["sposob_weryfikacji"]), ("aktywny", "qr"))
        exp = c.simulate_get("/api/aed/eksport/dane-gov-pl.csv")
        rows = list(csv.DictReader(io.StringIO(exp.text)))
        mine = [x for x in rows if x["id_aed"] == id_aed]
        self.assertEqual(len(mine), 1)
        self.assertEqual(mine[0]["numer_seryjny"], "")
        self.assertEqual(mine[0]["status"], "aktywny")
        gj = c.simulate_get("/api/aed/urzadzenia.geojson?bbox=20,52,21,53").json
        self.assertEqual([f["properties"]["id_aed"] for f in gj["features"]], [id_aed])
        # duplicate re-submission
        again = self.submit(data).json["podsumowanie"]
        self.assertEqual(again["przyjete"], 0)
        self.assertEqual(again["duplikaty"], out["podsumowanie"]["przyjete"])

    def test_converter_public_and_stateless(self):
        c = self.client
        krosno = read_bytes(os.path.join(ROOT, "datasets", "raw", "dane_gov_pl", "krosno", "resource_54632.csv"))
        before = self.db.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
        mp = multipart(krosno, "krosno.csv")
        a = c.simulate_post("/api/aed/konwerter/analiza", headers=mp["headers"], body=mp["body"])  # no login
        self.assertEqual(a.status_code, 200, a.text)
        mapping = {col["kolumna"]: col["pole"] for col in a.json["kolumny"]}
        self.assertEqual(mapping["Adres"], "_adres")
        mp = multipart(krosno, "krosno.csv", {"mapowanie": json.dumps(mapping), "stale": json.dumps({"dostep": "publiczny"})})
        r = c.simulate_post("/api/aed/konwerter/konwersja", headers=mp["headers"], body=mp["body"])
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual((r.json["raport"]["status"], r.json["nazwa_pliku"]), ("przyjety", "krosno-wykaz-aed.csv"))
        self.assertEqual(next(csv.reader(io.StringIO(r.json["plik_csv"]))), aed_standard.field_names())
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM devices").fetchone()[0], before)
        mp = multipart(krosno, "krosno.csv", {"mapowanie": json.dumps({"Nazwa": "nazwa", "Lokalizacja": "nazwa"})})
        bad = c.simulate_post("/api/aed/konwerter/konwersja", headers=mp["headers"], body=mp["body"])
        self.assertEqual((bad.status_code, bad.json["blad"]["kod"]), (422, "zle_mapowanie"))
        mp = multipart(b"x", "a.xls")
        self.assertEqual(c.simulate_post("/api/aed/konwerter/analiza", headers=mp["headers"], body=mp["body"]).status_code, 415)
        # XLSX is accepted; a file that is not a zip is a readable Polish 422, not a crash.
        mp = multipart(b"x", "a.xlsx")
        bad = c.simulate_post("/api/aed/konwerter/analiza", headers=mp["headers"], body=mp["body"])
        self.assertEqual((bad.status_code, bad.json["blad"]["kod"]), (422, "plik_nieczytelny"))
        template = read_bytes(os.path.join(ROOT, "wzorzec", "wzorzec-aed.xlsx"))
        mp = multipart(template, "wzorzec-aed.xlsx")
        a = c.simulate_post("/api/aed/konwerter/analiza", headers=mp["headers"], body=mp["body"])
        self.assertEqual((a.status_code, a.json["format"]), (200, "xlsx"), a.text)

    def test_sticker_text_fits_and_logo_placeholder(self):
        """Rule (rendering cannot be tested here): every text line needs chars * font-size * 0.75 <= width - 2 * 20,
        0.75 being a generous average glyph width of bold Arial capitals; the QR keeps a margin inside the viewBox."""
        import xml.etree.ElementTree as ET
        c, ns = self.client, "{http://www.w3.org/2000/svg}"
        id_aed = self.submit(seller_csv(["STICKER-1"])).json["przyjete"][0]["id_aed"]
        url = "/api/aed/urzadzenia/%s/naklejka.svg" % id_aed
        root = ET.fromstring(c.simulate_get(url).text)
        _, _, w, h = [float(v) for v in root.get("viewBox").split()]
        texts = [(t.text, float(t.get("font-size"))) for t in root.iter(ns + "text")]
        self.assertIn(id_aed, [t for t, _ in texts])
        self.assertGreaterEqual(len(texts), 4)  # title, id, two caption lines
        for text, size in texts:
            self.assertLessEqual(len(text) * size * 0.75, w - 2 * svc.STICKER_MARGIN, text)
        self.assertGreaterEqual(min(size for _, size in texts), 15)
        qr = [e for e in root.iter(ns + "svg") if e is not root][0]
        self.assertGreaterEqual(float(qr.get("x")), 10)
        self.assertLessEqual(float(qr.get("x")) + float(qr.get("width")), w - 10)
        self.assertLessEqual(float(qr.get("y")) + float(qr.get("height")), h)
        # empty logo placeholder, filled when the logo file exists
        slot = [g for g in root.iter(ns + "g") if g.get("id") == "miejsce-na-logo"][0]
        self.assertEqual(len(slot), 0)
        logo = os.path.join(self.tmp.name, "logo.svg")
        with open(logo, "w") as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>')
        with mock.patch.object(svc, "STICKER_LOGO_PATH", logo):
            root = ET.fromstring(c.simulate_get(url).text)
        slot = [g for g in root.iter(ns + "g") if g.get("id") == "miejsce-na-logo"][0]
        self.assertEqual([e.tag for e in slot], [ns + "image"])

    def test_roles_and_upload_limits(self):
        c = self.client
        self.assertEqual(c.simulate_post("/api/aed/urzadzenia", json={}).status_code, 401)
        self.assertEqual(c.simulate_post("/api/aed/zgloszenia", **multipart(b"x")).status_code, 401)
        firma = self.firma()
        for method, path in (("get", "/api/aed/duplikaty"), ("get", "/api/aed/wiadomosci"),
                             ("post", "/api/aed/przypomnienia/uruchom"), ("post", "/api/aed/mapper/uruchom")):
            self.assertEqual(c.simulate_request(method.upper(), path, headers=firma).status_code, 403, path)
            self.assertEqual(c.simulate_request(method.upper(), path).status_code, 401, path)
        self.assertEqual(self.submit(b"x", headers=self.ministry()).status_code, 403)
        self.assertEqual(self.submit(b"a,b", headers=firma).status_code, 201)  # reported as errors, not a crash
        bad_ext = c.simulate_post("/api/aed/zgloszenia", headers=dict(firma, **multipart(b"x", "a.xlsx")["headers"]),
                                  body=multipart(b"x", "a.xlsx")["body"])
        self.assertEqual(bad_ext.status_code, 415)
        big = self.submit(b"x" * (svc.MAX_UPLOAD + 10), headers=firma)
        self.assertEqual(big.status_code, 413)
        self.assertNotIn("Traceback", big.text)

    def test_single_device_and_seller_ranking(self):
        h = self.login("serwis@aed.example", "serwis-demo")
        rec = {"producent": "Rytm", "model": "R2", "numer_seryjny": "R-1", "data_produkcji": "2025-02-01",
               "data_waznosci_elektrod": NEXT_YEAR, "data_waznosci_baterii": NEXT_YEAR,
               "dysponent_nazwa": "Gmina Test", "dysponent_email": "gmina@example.org"}
        r = self.client.simulate_post("/api/aed/urzadzenia", json=rec, headers=h)
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json["podsumowanie"]["przyjete"], 1)
        bad = self.client.simulate_post("/api/aed/urzadzenia", json=dict(rec, numer_seryjny="R-2", data_produkcji="x"), headers=h)
        self.assertEqual(bad.json["podsumowanie"]["odrzucone"], 1)
        sel = {s["nazwa"]: s for s in self.client.simulate_get("/api/aed/sprzedawcy").json["dane"]}
        mine = [s for n, s in sel.items() if n.startswith("Serwis")][0]
        self.assertGreaterEqual(mine["liczba_urzadzen"], 1)
        self.assertEqual(mine["odznaka"], "nie")

    def test_signal_does_not_change_record(self):
        h = self.login("serwis@aed.example", "serwis-demo")
        rec = {"producent": "Rytm", "model": "R2", "numer_seryjny": "SIG-1", "data_produkcji": "2025-02-01",
               "data_waznosci_elektrod": NEXT_YEAR, "data_waznosci_baterii": NEXT_YEAR,
               "dysponent_nazwa": "Gmina Test", "dysponent_email": "gmina@example.org"}
        item = self.client.simulate_post("/api/aed/urzadzenia", json=rec, headers=h).json["przyjete"][0]
        url = "/api/aed/urzadzenia/%s" % item["id_aed"]
        full = "%s?t=%s" % (url, item["link_aktywacyjny"].split("t=")[1])
        before = self.client.simulate_get(full).json
        r = self.client.simulate_post(url + "/sygnal", json={"typ": "brak", "uwagi": "Szafka jest pusta"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client.simulate_post(url + "/sygnal", json={"typ": "xx"}).status_code, 422)
        self.assertEqual(self.client.simulate_get(full).json, before)
        msgs = self.client.simulate_get("/api/aed/wiadomosci", headers=self.ministry()).json["dane"]
        self.assertTrue(any(m["rodzaj"] == "sygnal" and m["id_aed"] == item["id_aed"] for m in msgs))

    def test_reminders_idempotent_and_stale(self):
        h = self.login("serwis@aed.example", "serwis-demo")
        soon = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
        rec = {"producent": "Rytm", "model": "R2", "numer_seryjny": "REM-1", "data_produkcji": "2025-02-01",
               "data_waznosci_elektrod": NEXT_YEAR, "data_waznosci_baterii": soon,
               "dysponent_nazwa": "Gmina Test", "dysponent_email": "gmina@example.org"}
        item = self.client.simulate_post("/api/aed/urzadzenia", json=rec, headers=h).json["przyjete"][0]
        m = self.ministry()
        first = self.client.simulate_post("/api/aed/przypomnienia/uruchom", headers=m).json
        self.assertGreaterEqual(first["przypomnienia_terminow"], 1)
        n1 = self.client.simulate_get("/api/aed/wiadomosci", headers=m).json["razem"]
        second = self.client.simulate_post("/api/aed/przypomnienia/uruchom", headers=m).json
        self.assertEqual((second["przypomnienia_terminow"], second["prosby_o_potwierdzenie"]), (0, 0))
        self.assertEqual(self.client.simulate_get("/api/aed/wiadomosci", headers=m).json["razem"], n1)
        # 13 months later: requests go out, confirmed devices become nieaktualny
        token = self.client.simulate_get("/api/aed/wiadomosci", headers=m).json["dane"][0]["link"].split("t=")[1]
        self.client.simulate_post("/api/aed/urzadzenia/%s/potwierdzenie" % item["id_aed"],
                                  json={"t": token, "nazwa": "SP 1", "szerokosc_geograficzna": 52.2, "dlugosc_geograficzna": 21.0,
                                        "miejscowosc": "Warszawa", "dostep": "publiczny", "godziny_dostepu": "24/7", "stan": "sprawny"})
        later = datetime.date.today() + datetime.timedelta(days=400)
        with mock.patch.object(svc, "today", lambda: later):
            r = self.client.simulate_post("/api/aed/przypomnienia/uruchom", headers=m).json
        self.assertGreaterEqual(r["nieaktualne"], 1)
        self.assertEqual(self.client.simulate_get("/api/aed/urzadzenia/" + item["id_aed"]).json["status"], "nieaktualny")

    def test_mapper_private_and_duplicates(self):
        def rec(i, **kw):
            base = {n: "" for n in aed_standard.field_names()}
            base.update(id_aed="AED-MAPTEST%04d" % i, nazwa="Punkt %d" % i, szerokosc_geograficzna="52.1",
                       dlugosc_geograficzna="21.0", miejscowosc="Warszawa", status="niepotwierdzony", zrodlo="test",
                       zrodlo_id=str(i), licencja="CC BY 4.0", dostep="publiczny", kompletnosc="40")
            base.update(kw)
            return base
        m = self.ministry()
        a, b, priv = rec(1), rec(2), rec(3, dostep="prywatny", nazwa="Prywatny sekret")
        pair = {"id_aed_a": a["id_aed"], "id_aed_b": b["id_aed"], "odleglosc_m": 5.0, "podobienstwo": 0.9}
        run = lambda recs, pairs=(): mock.patch.object(  # noqa: E731
            aed_standard, "build_registry", return_value=(recs, list(pairs), {"polaczenia": {"razem": 7}}))
        with run([a, b, priv], [pair]):
            r = self.client.simulate_post("/api/aed/mapper/uruchom", headers=m).json
        self.assertEqual((r["dodano"], r["zmieniono"], r["polaczono"]), (3, 0, 7))
        with run([dict(a, nazwa="Zmieniony"), b, priv], [pair]):
            r = self.client.simulate_post("/api/aed/mapper/uruchom", headers=m).json
        self.assertEqual((r["dodano"], r["zmieniono"]), (0, 1))
        # private record: absent from every public output
        for path in ("/api/aed/urzadzenia?q=sekret", "/api/aed/urzadzenia.geojson", "/api/aed/eksport/dane-gov-pl.csv"):
            self.assertNotIn(priv["id_aed"], self.client.simulate_get(path).text, path)
        self.assertEqual(self.client.simulate_get("/api/aed/urzadzenia/" + priv["id_aed"]).status_code, 404)
        self.assertEqual(self.client.simulate_post("/api/aed/urzadzenia/%s/sygnal" % priv["id_aed"], json={"typ": "jest"}).status_code, 404)
        self.assertIn(a["id_aed"], self.client.simulate_get("/api/aed/eksport/dane-gov-pl.csv").text)
        # merged records are not overwritten by the mapper and decided pairs are not re-queued
        dups = self.client.simulate_get("/api/aed/duplikaty", headers=m).json["dane"]
        self.assertEqual(len(dups), 1)
        self.assertEqual(self.client.simulate_post("/api/aed/duplikaty/%d" % dups[0]["id"], json={"decyzja": "polacz"}, headers=m).status_code, 200)
        self.assertEqual(self.client.simulate_get("/api/aed/urzadzenia/" + b["id_aed"]).json["status"], "wycofany")
        with run([a, dict(b, nazwa="Nadpisany"), priv], [pair]):  # merged record b stays untouched, pair not re-queued
            r = self.client.simulate_post("/api/aed/mapper/uruchom", headers=m).json
        self.assertEqual(self.client.simulate_get("/api/aed/urzadzenia/" + b["id_aed"]).json["nazwa"], "Punkt 2")
        self.assertEqual(self.client.simulate_get("/api/aed/duplikaty", headers=m).json["razem"], 0)

    def test_open_now_filter(self):
        def rec(i, hours, **kw):
            base = {n: "" for n in aed_standard.field_names()}
            base.update(id_aed="AED-OPENTEST%04d" % i, nazwa="Punkt %d" % i, szerokosc_geograficzna="50.1",
                        dlugosc_geograficzna="20.1", miejscowosc="Kraków", status="niepotwierdzony", zrodlo="godziny",
                        zrodlo_id=str(i), licencja="CC BY 4.0", dostep="publiczny", kompletnosc="40",
                        godziny_dostepu=hours)
            base.update(kw)
            return base
        recs = [rec(1, "24/7"), rec(2, "Mo-Fr 08:00-16:00"), rec(3, "Sa 09:00-13:00"), rec(4, ""),
                rec(5, "sunrise-sunset"), rec(6, "24/7", dostep="prywatny")]
        with mock.patch.object(aed_standard, "build_registry", return_value=(recs, [], {"polaczenia": {"razem": 0}})):
            self.client.simulate_post("/api/aed/mapper/uruchom", headers=self.ministry())

        def ids(at, path="/api/aed/urzadzenia?zrodlo=godziny&dostepny_teraz=1"):
            with mock.patch.object(aed_standard, "warsaw_now", return_value=at):
                return self.client.simulate_get(path).json
        tuesday = ids(datetime.datetime(2026, 11, 24, 10, 0))
        self.assertEqual([r["id_aed"] for r in tuesday["dane"]], ["AED-OPENTEST0001", "AED-OPENTEST0002"])
        self.assertEqual((tuesday["razem"], tuesday["bez_godzin"]), (2, 2))
        saturday = ids(datetime.datetime(2026, 11, 28, 10, 0))
        self.assertEqual([r["id_aed"] for r in saturday["dane"]], ["AED-OPENTEST0001", "AED-OPENTEST0003"])
        night = ids(datetime.datetime(2026, 11, 28, 23, 0), "/api/aed/urzadzenia?zrodlo=godziny&dostepny_teraz=1&na_stronie=1&strona=1")
        self.assertEqual((night["razem"], len(night["dane"])), (1, 1))  # only 24/7, paged after the filter
        plain = self.client.simulate_get("/api/aed/urzadzenia?zrodlo=godziny").json
        self.assertEqual(plain["razem"], 5)  # without the parameter: no filter, no extra field
        self.assertNotIn("bez_godzin", plain)
        geo = ids(datetime.datetime(2026, 11, 24, 10, 0), "/api/aed/urzadzenia.geojson?dostepny_teraz=1&bbox=20,50,20.2,50.2")
        self.assertEqual(sorted(f["properties"]["id_aed"] for f in geo["features"] if f["properties"]["zrodlo"] == "godziny"),
                         ["AED-OPENTEST0001", "AED-OPENTEST0002"])

    def test_duplicate_decisions_survive_mapper_runs(self):
        def rec(i, **kw):
            base = {n: "" for n in aed_standard.field_names()}
            base.update(id_aed="AED-DECTEST%04d" % i, nazwa="Punkt %d" % i, szerokosc_geograficzna="50.5",
                       dlugosc_geograficzna="19.5", miejscowosc="Warszawa", status="niepotwierdzony", zrodlo="test",
                       zrodlo_id=str(i), licencja="CC BY 4.0", dostep="publiczny", kompletnosc="40")
            base.update(kw)
            return base
        m = self.ministry()
        a, b, c, d = rec(1), rec(2), rec(3), rec(4)
        merge = {"id_aed_a": a["id_aed"], "id_aed_b": b["id_aed"], "odleglosc_m": 3.0, "podobienstwo": 0.9}
        split = {"id_aed_a": c["id_aed"], "id_aed_b": d["id_aed"], "odleglosc_m": 4.0, "podobienstwo": 0.8}
        report = {"polaczenia": {"razem": 0}}

        def mapper(recs, pairs):
            with mock.patch.object(aed_standard, "build_registry", return_value=(recs, pairs, report)):
                self.assertEqual(self.client.simulate_post("/api/aed/mapper/uruchom", headers=m).status_code, 200)

        def queue():
            ids = {a["id_aed"], b["id_aed"], c["id_aed"], d["id_aed"]}
            return [x for x in self.client.simulate_get("/api/aed/duplikaty", headers=m).json["dane"]
                    if x["rekord_a"]["id_aed"] in ids]

        def get(r):
            return self.client.simulate_get("/api/aed/urzadzenia/" + r["id_aed"]).json

        mapper([a, b, c, d], [merge, split])
        by_a = {x["rekord_a"]["id_aed"]: x["id"] for x in queue()}
        self.assertEqual(len(by_a), 2)
        for pair_id, decision in ((by_a[a["id_aed"]], "polacz"), (by_a[c["id_aed"]], "rozdziel")):
            r = self.client.simulate_post("/api/aed/duplikaty/%d" % pair_id, json={"decyzja": decision}, headers=m)
            self.assertEqual(r.status_code, 200)
        swapped = dict(split, id_aed_a=d["id_aed"], id_aed_b=c["id_aed"])
        for run in range(2):  # twice, second time with the split pair listed in the other order and source data changed
            mapper([dict(a, nazwa="Źródło %d" % run), b, c, d], [merge, swapped if run else split])
            self.assertEqual(queue(), [], run)  # nothing back in the review queue
            ga = get(a)
            self.assertIn(b["id_aed"], ga["powiazane_zrodla"].split(";"), run)  # link on the kept record survives
            self.assertEqual(ga["powiazane_zrodla"].split(";").count(b["id_aed"]), 1)
            self.assertEqual(ga["nazwa"], "Źródło %d" % run)  # imported fields still refresh
            self.assertEqual(get(b)["status"], "wycofany", run)  # withdrawn record is not resurrected
            self.assertEqual((get(c)["status"], get(d)["status"]), ("niepotwierdzony", "niepotwierdzony"))


class JobsAndDemoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "t.db")

    def tearDown(self):
        self.tmp.cleanup()

    def client(self, **kw):
        db = svc.open_db(self.path, with_registry=False, **kw)
        self.addCleanup(db.close)
        return testing.TestClient(svc.build_app(db))

    def ministry(self, c):
        r = c.simulate_post("/api/aed/sesja", json={"email": "ministerstwo@aed.example", "haslo": "ministerstwo-demo"})
        return {"Authorization": "Bearer " + r.json["token"]}

    def test_stats_tell_whether_demo_passwords_are_the_default_ones(self):
        self.assertTrue(self.client().simulate_get("/api/aed/statystyki").json["hasla_demo_domyslne"])
        self.tmp.cleanup()
        os.makedirs(self.tmp.name)
        with mock.patch.dict(os.environ, {"AED_DEMO_PASSWORD": "inne-haslo-serwera"}):
            c = self.client()
        self.assertFalse(c.simulate_get("/api/aed/statystyki").json["hasla_demo_domyslne"])

    def test_job_history_and_failure_tolerance(self):
        c = self.client()
        m = self.ministry(c)
        self.assertEqual(c.simulate_get("/api/aed/zadania").status_code, 401)
        self.assertIsNone(c.simulate_get("/api/aed/statystyki").json["ostatnie_uruchomienia"]["mapper"])
        c.simulate_post("/api/aed/przypomnienia/uruchom", headers=m)
        empty = ([], [], {"polaczenia": {"razem": 0}})
        with mock.patch.object(aed_standard, "build_registry", return_value=empty):
            self.assertEqual(c.simulate_post("/api/aed/mapper/uruchom", headers=m).status_code, 200)
            # scheduled cycle: download fails, the cycle carries on with the snapshot on disk
            with mock.patch.object(svc, "refresh_sources", return_value=(None, ["Nie udało się pobrać źródeł (test)."])):
                job = svc.run_job(sqlite_conn(self, self.path), "harmonogram", "cykl")
        self.assertEqual((job["wyzwalacz"], job["rodzaj"]), ("harmonogram", "cykl"))
        self.assertEqual(job["bledy"], ["Nie udało się pobrać źródeł (test)."])
        self.assertIsNotNone(job["mapper"])
        self.assertIsNotNone(job["przypomnienia"])
        hist = c.simulate_get("/api/aed/zadania", headers=m).json["dane"]
        self.assertEqual([j["rodzaj"] for j in hist], ["cykl", "mapper", "przypomnienia"])
        self.assertEqual(hist[2]["wyzwalacz"], "ministerstwo")
        last = c.simulate_get("/api/aed/statystyki").json["ostatnie_uruchomienia"]
        self.assertTrue(last["mapper"] and last["przypomnienia"])
        # a mapper crash is recorded in Polish, not leaked
        with mock.patch.object(aed_standard, "build_registry", side_effect=RuntimeError("boom")), \
                mock.patch.object(svc, "refresh_sources", return_value=(None, [])), \
                contextlib.redirect_stderr(io.StringIO()) as log:  # the traceback goes to the log only
            job = svc.run_job(sqlite_conn(self, self.path), "harmonogram", "cykl")
        self.assertIn("boom", log.getvalue())
        self.assertIsNone(job["mapper"])
        self.assertIn("Mapper", job["bledy"][0])
        self.assertNotIn("boom", job["bledy"][0])

    def test_jobs_do_not_overlap(self):
        c = self.client()
        m = self.ministry(c)
        with svc.JOB_LOCK:
            r = c.simulate_post("/api/aed/mapper/uruchom", headers=m)
        self.assertEqual((r.status_code, r.json["blad"]["kod"]), (409, "zadanie_trwa"))

    def test_failed_refresh_keeps_snapshot_and_mapper_works(self):
        import shutil
        raw = os.path.join(self.tmp.name, "raw")  # temporary copy, never the real datasets/raw
        shutil.copytree(svc.RAW_DIR, raw)
        manifest = os.path.join(raw, "manifest.json")
        with open(manifest, encoding="utf-8") as f:
            original = json.load(f)
        files = [e["file"] for e in original["files"]]

        def fake_script(new_manifest):  # what a half-failed download leaves behind
            def run(*a, **kw):
                if isinstance(new_manifest, Exception):
                    raise new_manifest
                with open(manifest, "w", encoding="utf-8") as f:
                    f.write(new_manifest if isinstance(new_manifest, str) else json.dumps(new_manifest))
                return mock.Mock(returncode=0)
            return run

        subset = {"files": original["files"][:1], "errors": [
            "dane.gov.pl resource 1 (https://x): <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed>",
            "Warsaw API: WARSAW_API_TOKEN is not set"]}
        c = self.client()
        with mock.patch.object(svc, "RAW_DIR", raw), mock.patch.object(svc, "SCRIPT_RAW_DIR", raw), \
                mock.patch.object(svc, "DOWNLOAD_SCRIPT", __file__):
            for label, fake in (("subset", subset), ("crash", RuntimeError("secret detail")), ("garbage", "{not json")):
                with mock.patch.object(svc.subprocess, "run", side_effect=fake_script(fake)):
                    job = svc.run_job(sqlite_conn(self, self.path), "harmonogram", "cykl")
                with open(manifest, encoding="utf-8") as f:
                    on_disk = [e["file"] for e in json.load(f)["files"]]
                self.assertEqual(sorted(on_disk), sorted(files), label)
                self.assertIsNotNone(job["mapper"], (label, job["bledy"]))  # mapper step completed
                self.assertIsNotNone(job["przypomnienia"], label)
                self.assertNotIn("secret detail", json.dumps(job["bledy"]))
                self.assertNotIn("Traceback", json.dumps(job["bledy"]))
                if label == "subset":
                    self.assertTrue(job["odswiezono"].startswith("Odświeżono 1 z %d" % len(files)), job["odswiezono"])
                    self.assertIn("brak połączenia lub błąd certyfikatu", job["bledy"][0])
                    self.assertNotIn("CERTIFICATE", json.dumps(job["bledy"]))
                    self.assertIn("brak tokenu", job["bledy"][1])
                else:
                    self.assertIsNone(job["odswiezono"], label)
                    self.assertTrue(job["bledy"], label)

    def test_refresh_sources_survives_failures(self):
        with mock.patch.object(svc.subprocess, "run", side_effect=OSError("no network")):
            done, errors = svc.refresh_sources()
        self.assertIsNone(done)
        self.assertIn("migawki", errors[0])
        with mock.patch.object(svc.subprocess, "run", return_value=mock.Mock(returncode=1)):
            self.assertIn("kod 1", svc.refresh_sources()[1][0])
        self.assertIsNone(svc.start_scheduler(self.path, 0))

    def test_demo_seed_story(self):
        c = self.client(demo=True)
        m = self.ministry(c)
        sel = {s["typ_podmiotu"]: s for s in c.simulate_get("/api/aed/sprzedawcy").json["dane"]}
        self.assertEqual((sel["producent"]["liczba_urzadzen"], sel["producent"]["odznaka"]), (12, "tak"))
        self.assertEqual((sel["sprzedawca"]["liczba_urzadzen"], sel["sprzedawca"]["odznaka"]), (6, "nie"))
        dev = c.simulate_get("/api/aed/urzadzenia").json["dane"][0]
        self.assertIs(c.simulate_get("/api/aed/urzadzenia/" + dev["id_aed"]).json["demo"], True)
        self.assertTrue(all(r["demo"] is True for r in c.simulate_get("/api/aed/urzadzenia").json["dane"]))
        feats = c.simulate_get("/api/aed/urzadzenia.geojson").json["features"]
        self.assertTrue(feats and all(f["properties"]["demo"] is True for f in feats))
        # visible in the registry, absent from the publication export
        self.assertEqual(c.simulate_get("/api/aed/urzadzenia").json["razem"], 18)
        self.assertEqual(len(list(csv.DictReader(io.StringIO(c.simulate_get("/api/aed/eksport/dane-gov-pl.csv").text)))), 0)
        # waiting activation links and real reminders
        msgs = c.simulate_get("/api/aed/wiadomosci", headers=m).json["dane"]
        self.assertEqual(sum(1 for x in msgs if x["rodzaj"] == "aktywacja"), 18)
        out = c.simulate_post("/api/aed/przypomnienia/uruchom", headers=m).json
        self.assertGreaterEqual(out["przypomnienia_terminow"], 1)
        self.assertGreaterEqual(out["prosby_o_potwierdzenie"], 1)
        # restarting does not seed twice
        self.assertEqual(self.client(demo=True).simulate_get("/api/aed/urzadzenia").json["razem"], 18)

    def test_old_database_is_upgraded(self):
        self.client()
        conn = sqlite_conn(self, self.path)
        conn.execute("ALTER TABLE devices DROP COLUMN demo")
        conn.execute("DROP TABLE jobs")
        conn.commit()
        c = self.client()
        self.assertEqual(c.simulate_get("/api/aed/zadania", headers=self.ministry(c)).json["dane"], [])

    # ---- helpers for the review-round tests (fresh database per test) ----
    def seller(self, c):
        r = c.simulate_post("/api/aed/sesja", json={"email": "pulsar@aed.example", "haslo": "pulsar-demo"})
        return {"Authorization": "Bearer " + r.json["token"]}

    def add_device(self, c, serial, **kw):
        rec = dict({"producent": "Rytm", "model": "R2", "numer_seryjny": serial, "data_produkcji": "2025-02-01",
                    "data_waznosci_elektrod": NEXT_YEAR, "data_waznosci_baterii": NEXT_YEAR,
                    "dysponent_nazwa": "Gmina Test", "dysponent_email": "gmina@example.org"}, **kw)
        item = c.simulate_post("/api/aed/urzadzenia", json=rec, headers=self.seller(c)).json["przyjete"][0]
        item["t"] = item["link_aktywacyjny"].split("t=")[1]
        return item

    def confirm_body(self, item, **kw):
        return dict({"t": item["t"], "nazwa": "Punkt testowy", "szerokosc_geograficzna": 50.5, "dlugosc_geograficzna": 19.5,
                     "miejscowosc": "Kraków", "dostep": "publiczny", "godziny_dostepu": "24/7", "stan": "sprawny"}, **kw)

    def imported(self, i, **kw):
        base = {n: "" for n in aed_standard.field_names()}
        base.update(id_aed="AED-REVTEST%04d" % i, nazwa="Import %d" % i, szerokosc_geograficzna="50.5",
                   dlugosc_geograficzna="19.5", miejscowosc="Kraków", status="niepotwierdzony", zrodlo="test",
                   zrodlo_id=str(i), licencja="CC BY 4.0", dostep="publiczny", kompletnosc="40")
        base.update(kw)
        return base

    def mapper(self, c, recs, pairs=(), report=None):
        report = report or {"polaczenia": {"razem": 0}}
        with mock.patch.object(aed_standard, "build_registry", return_value=(recs, list(pairs), report)):
            return c.simulate_post("/api/aed/mapper/uruchom", headers=self.ministry(c))

    def test_typo_in_registry_entry_retires_nothing_end_to_end(self):
        """Real build_registry: a registry entry broken by a typo must not retire the devices of its source."""
        real = aed_standard.build_registry
        with open(os.path.join(ROOT, "aed_standard", "sources.json"), encoding="utf-8") as f:
            registry = json.load(f)
        registry["sources"] = [s for s in registry["sources"] if s["id"] in ("krosno", "legionowo")]
        good = os.path.join(self.tmp.name, "good.json")
        typo = os.path.join(self.tmp.name, "typo.json")
        with open(good, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False)
        registry["sources"][0]["feilds"] = registry["sources"][0].pop("fields")
        with open(typo, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False)
        c = self.client()
        m = self.ministry(c)

        def run(reg):
            with mock.patch.object(aed_standard, "build_registry", side_effect=lambda raw: real(raw, registry_path=reg)):
                r = c.simulate_post("/api/aed/mapper/uruchom", headers=m)
            self.assertEqual(r.status_code, 200)
            return r.json

        first = run(good)
        self.assertEqual(first["dodano"], 45)  # Krosno 21 + Legionowo 24
        broken = run(typo)
        self.assertEqual(broken["wycofano"], 0)
        jobs = c.simulate_get("/api/aed/zadania", headers=m).json["dane"]
        self.assertIn("feilds", " ".join(jobs[0]["bledy"]))
        krosno = c.simulate_get("/api/aed/urzadzenia", params={"zrodlo": "dane.gov.pl/3624", "na_stronie": 100}).json
        self.assertEqual(krosno["razem"], 21)
        self.assertEqual({d["status"] for d in krosno["dane"]}, {"niepotwierdzony"})
        fixed = run(good)
        self.assertEqual((fixed["dodano"], fixed["wycofano"]), (0, 0))

    def test_skipped_source_is_not_retired_and_error_is_in_job_history(self):
        c = self.client()
        recs = [self.imported(i) for i in range(1, 5)] + [self.imported(i, zrodlo="inne") for i in range(5, 9)]
        self.mapper(c, recs)
        report = {"polaczenia": {"razem": 0}, "pominiete_zrodla": ["test"],
                  "bledy_zrodel": ["Źródło Test (test) pominięte: licencja „CC BY-SA 4.0” nie jest obsługiwana."]}
        r = self.mapper(c, recs[4:], report=report).json
        self.assertEqual(r["wycofano"], 0)
        get = lambda x: c.simulate_get("/api/aed/urzadzenia/" + x["id_aed"]).json  # noqa: E731
        self.assertEqual({get(x)["status"] for x in recs}, {"niepotwierdzony"})
        jobs = c.simulate_get("/api/aed/zadania", headers=self.ministry(c)).json["dane"]
        self.assertIn("CC BY-SA 4.0", " ".join(jobs[0]["bledy"]))
        self.assertNotIn("bledy_zrodel", jobs[0]["mapper"])
        # once the source is back and a record really vanished from it, retirement works again
        self.assertEqual(self.mapper(c, recs[1:]).json["wycofano"], 1)

    def test_serial_never_in_public_output(self):
        c = self.client()
        serial = "LEAK-Serial-77x"
        item = self.add_device(c, serial)
        self.assertEqual(c.simulate_post("/api/aed/urzadzenia/%s/potwierdzenie" % item["id_aed"],
                                         json=self.confirm_body(item)).status_code, 200)
        c.simulate_post("/api/aed/urzadzenia/%s/sygnal" % item["id_aed"], json={"typ": "jest"})
        outputs = [c.simulate_get(u).text for u in (
            "/api/aed/urzadzenia/" + item["id_aed"], "/api/aed/urzadzenia", "/api/aed/urzadzenia.geojson",
            "/api/aed/eksport/dane-gov-pl.csv", "/api/aed/sprzedawcy", "/api/aed/statystyki",
            "/api/aed/urzadzenia/%s/naklejka.svg" % item["id_aed"])]
        outputs.append(c.simulate_post("/api/aed/urzadzenia/%s/sygnal" % item["id_aed"], json={"typ": "brak"}).text)
        self.assertIn(item["id_aed"], outputs[3])  # the export really contains the device
        for text in outputs:
            low = text.lower()
            self.assertNotIn(serial.lower(), low)
            self.assertNotIn("leakserial77x", low)
        # the id is not derived from the serial any more
        self.assertNotEqual(item["id_aed"], aed_standard.make_id("zgloszenie", "rytm|leakserial77x"))

    def test_legacy_database_rows_are_migrated(self):
        c = self.client()
        item = self.add_device(c, "OLD-1")
        conn = sqlite_conn(self, self.path)
        row = conn.execute("SELECT data FROM devices WHERE id_aed=?", (item["id_aed"],)).fetchone()
        rec = json.loads(row[0])
        rec["zrodlo_id"] = "rytm|old1"  # what the previous version stored
        conn.execute("UPDATE devices SET data=?, token_hash=? WHERE id_aed=?",
                     (json.dumps(rec), svc.sha("legacy-token"), item["id_aed"]))
        conn.execute("DELETE FROM tokens")
        conn.commit()
        c = self.client()
        pub = c.simulate_get("/api/aed/urzadzenia/" + item["id_aed"]).json
        self.assertNotIn("|", pub["zrodlo_id"])
        self.assertNotIn("old1", json.dumps(pub).lower())
        self.assertEqual(pub["id_aed"], item["id_aed"])  # issued ids are kept
        self.assertEqual(c.simulate_get("/api/aed/urzadzenia/%s?t=legacy-token" % item["id_aed"]).status_code, 200)

    def test_manager_links_are_independent(self):
        c = self.client()
        soon = (datetime.date.today() + datetime.timedelta(days=20)).isoformat()
        item = self.add_device(c, "TOK-1", data_waznosci_baterii=soon, data_waznosci_elektrod=soon)
        m = self.ministry(c)
        self.assertEqual(c.simulate_post("/api/aed/przypomnienia/uruchom", headers=m).json["przypomnienia_terminow"], 2)
        links = [x["link"] for x in c.simulate_get("/api/aed/wiadomosci", headers=m).json["dane"] if x["id_aed"] == item["id_aed"]]
        self.assertEqual(len(links), 3)  # activation + two reminders
        for link in links:
            r = c.simulate_get("/api/aed/urzadzenia/%s?t=%s" % (item["id_aed"], link.split("t=")[1]))
            self.assertEqual(r.status_code, 200, link)
        self.assertIn(item["t"], "".join(links))  # the original activation link is among them and still works
        # an expired link stops working
        conn = sqlite_conn(self, self.path)
        conn.execute("UPDATE tokens SET wygasa='2000-01-01T00:00:00' WHERE hash=?", (svc.sha(item["t"]),))
        conn.commit()
        self.assertEqual(c.simulate_get("/api/aed/urzadzenia/%s?t=%s" % (item["id_aed"], item["t"])).status_code, 403)

    def test_manager_can_replace_battery_and_reminder_stops(self):
        c = self.client()
        soon = (datetime.date.today() + datetime.timedelta(days=20)).isoformat()
        item = self.add_device(c, "BAT-1", data_waznosci_baterii=soon)
        url = "/api/aed/urzadzenia/%s/potwierdzenie" % item["id_aed"]
        bad = c.simulate_post(url, json=self.confirm_body(item, data_waznosci_baterii="jutro"))
        self.assertEqual(bad.status_code, 422)
        new = (datetime.date.today() + datetime.timedelta(days=900)).isoformat()
        r = c.simulate_post(url, json=self.confirm_body(item, data_waznosci_baterii=new))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json["rekord"]["data_waznosci_baterii"], new)
        full = c.simulate_get("/api/aed/urzadzenia/%s?t=%s" % (item["id_aed"], item["t"])).json
        self.assertEqual(full["data_waznosci_baterii"], new)
        out = c.simulate_post("/api/aed/przypomnienia/uruchom", headers=self.ministry(c)).json
        self.assertEqual(out["przypomnienia_terminow"], 0)

    def test_problem_report_is_validated_but_may_be_incomplete(self):
        c = self.client()
        item = self.add_device(c, "PRB-1")
        url = "/api/aed/urzadzenia/%s/potwierdzenie" % item["id_aed"]
        for bad in ({"dostep": "PRIVATE"}, {"szerokosc_geograficzna": "abc", "dlugosc_geograficzna": 19.5},
                    {"szerokosc_geograficzna": 10, "dlugosc_geograficzna": 10}):
            r = c.simulate_post(url, json={"t": item["t"], "stan": "problem", "uwagi": "Brak elektrod", **bad})
            self.assertEqual(r.status_code, 422, bad)
            self.assertEqual(r.json["blad"]["kod"], "niepoprawne_dane")
            self.assertTrue(r.json["blad"]["problemy"])
        pub = c.simulate_get("/api/aed/urzadzenia/%s?t=%s" % (item["id_aed"], item["t"])).json
        self.assertEqual((pub["dostep"], pub["status"]), ("", "zgloszony"))  # nothing was saved
        ok = c.simulate_post(url, json={"t": item["t"], "stan": "problem", "uwagi": "Brak elektrod"})  # incomplete, valid
        self.assertEqual(ok.status_code, 200, ok.text)

    def test_confirmation_queues_spatial_match_with_imported_record(self):
        c = self.client()
        m = self.ministry(c)
        near = self.imported(1, nazwa="Punkt testowy")
        far = self.imported(2, szerokosc_geograficzna="50.6", dlugosc_geograficzna="19.6")
        self.mapper(c, [near, far])
        item = self.add_device(c, "SPA-1")
        url = "/api/aed/urzadzenia/%s/potwierdzenie" % item["id_aed"]
        self.assertEqual(c.simulate_post(url, json=self.confirm_body(item)).status_code, 200)
        self.assertEqual(c.simulate_post(url, json=self.confirm_body(item)).status_code, 200)  # again: no second pair
        queue = c.simulate_get("/api/aed/duplikaty", headers=m).json["dane"]
        self.assertEqual(len(queue), 1)
        pair = queue[0]
        self.assertEqual((pair["rekord_a"]["id_aed"], pair["rekord_b"]["id_aed"]), (item["id_aed"], near["id_aed"]))
        self.assertLessEqual(pair["odleglosc_m"], 1)
        self.assertGreater(pair["podobienstwo"], 0.9)
        self.assertEqual(c.simulate_post("/api/aed/duplikaty/%d" % pair["id"], json={"decyzja": "polacz"}, headers=m).status_code, 200)
        self.assertEqual(c.simulate_get("/api/aed/urzadzenia/" + near["id_aed"]).json["status"], "wycofany")
        kept = c.simulate_get("/api/aed/urzadzenia/" + item["id_aed"]).json
        self.assertEqual(kept["status"], "aktywny")
        self.assertIn(near["id_aed"], kept["powiazane_zrodla"])
        self.assertEqual(c.simulate_post(url, json=self.confirm_body(item)).status_code, 200)  # decided: not re-queued
        self.assertEqual(c.simulate_get("/api/aed/duplikaty", headers=m).json["razem"], 0)

    def test_new_import_next_to_confirmed_device_is_queued(self):
        c = self.client()
        m = self.ministry(c)
        item = self.add_device(c, "IMP-1")
        url = "/api/aed/urzadzenia/%s/potwierdzenie" % item["id_aed"]
        self.assertEqual(c.simulate_post(url, json=self.confirm_body(item)).status_code, 200)
        self.assertEqual(c.simulate_get("/api/aed/duplikaty", headers=m).json["razem"], 0)  # nothing imported yet
        near = self.imported(1, nazwa="Punkt testowy", szerokosc_geograficzna="50.5001")  # ~11 m away
        far = self.imported(2, szerokosc_geograficzna="50.6", dlugosc_geograficzna="19.6")
        self.mapper(c, [near, far])
        queue = c.simulate_get("/api/aed/duplikaty", headers=m).json["dane"]
        self.assertEqual([(p["rekord_a"]["id_aed"], p["rekord_b"]["id_aed"]) for p in queue], [(item["id_aed"], near["id_aed"])])
        self.assertAlmostEqual(queue[0]["odleglosc_m"], 11.1, delta=0.5)
        self.mapper(c, [dict(near, nazwa="Punkt testowy (zmiana)"), far])  # changed record: no second pair
        self.assertEqual(c.simulate_get("/api/aed/duplikaty", headers=m).json["razem"], 1)

    def test_manager_takes_over_osm_only_record(self):
        c = self.client()
        m = self.ministry(c)
        osm = self.imported(1, zrodlo="openstreetmap", zrodlo_id="node/42", licencja="ODbL 1.0", nazwa="Nazwa z OSM",
                            opis_lokalizacji="Opis z OSM", producent="Z OSM", dysponent_email="z-osm@example.org",
                            godziny_dostepu="24/7")
        self.mapper(c, [osm])
        export = lambda: c.simulate_get("/api/aed/eksport/dane-gov-pl.csv").text  # noqa: E731
        self.assertNotIn(osm["id_aed"], export())
        url = "/api/aed/urzadzenia/%s/link-aktywacyjny" % osm["id_aed"]
        self.assertEqual(c.simulate_post(url, json={}, headers=self.seller(c)).status_code, 403)
        self.assertEqual(c.simulate_post(url, json={"email": "nie-email"}, headers=m).status_code, 422)
        r = c.simulate_post(url, json={"email": "aed@gmina.example.org"}, headers=m)
        self.assertEqual(r.status_code, 201, r.text)
        token = r.json["link_aktywacyjny"].split("t=")[1]
        msgs = c.simulate_get("/api/aed/wiadomosci", headers=m).json["dane"]
        self.assertEqual([(x["rodzaj"], x["odbiorca"]) for x in msgs], [("przejecie", "aed@gmina.example.org")])
        confirm = "/api/aed/urzadzenia/%s/potwierdzenie" % osm["id_aed"]
        # the manager must state name and place himself: nothing is carried over from OSM
        r = c.simulate_post(confirm, json={"t": token, "dostep": "publiczny", "godziny_dostepu": "24/7", "stan": "sprawny"})
        self.assertEqual(r.status_code, 422, r.text)
        body = {"t": token, "nazwa": "Urząd Gminy", "szerokosc_geograficzna": 50.5, "dlugosc_geograficzna": 19.5,
                "miejscowosc": "Kraków", "dostep": "publiczny", "godziny_dostepu": "Mo-Fr 08:00-16:00",
                "dysponent_nazwa": "Gmina Test", "dysponent_email": "aed@gmina.example.org", "stan": "sprawny"}
        r = c.simulate_post(confirm, json=body)
        self.assertEqual(r.status_code, 200, r.text)
        rec = r.json["rekord"]
        self.assertEqual((rec["status"], rec["licencja"], rec["zrodlo"], rec["powiazane_zrodla"]),
                         ("aktywny", "CC0 1.0", "zgloszenie", "openstreetmap:node/42"))
        self.assertEqual((rec["opis_lokalizacji"], rec["producent"], rec["dysponent_email"]), ("", "", "aed@gmina.example.org"))
        self.assertNotIn("OSM", json.dumps(rec))
        self.assertIn(osm["id_aed"], export())
        # the next mapper run brings the same OSM record again: the manager's record stays as it is
        self.mapper(c, [osm])
        again = c.simulate_get("/api/aed/urzadzenia/" + osm["id_aed"]).json
        self.assertEqual((again["status"], again["licencja"], again["nazwa"]), ("aktywny", "CC0 1.0", "Urząd Gminy"))
        self.assertEqual(c.simulate_get("/api/aed/statystyki").json["razem"], 1)

    def test_old_link_cannot_confirm_withdrawn_record(self):
        c = self.client()
        recs = [self.imported(i) for i in range(1, 5)]
        self.mapper(c, recs)
        r = c.simulate_post("/api/aed/urzadzenia/%s/link-aktywacyjny" % recs[3]["id_aed"], json={}, headers=self.ministry(c))
        token = r.json["link_aktywacyjny"].split("t=")[1]
        self.assertEqual(self.mapper(c, recs[:3]).json["wycofano"], 1)   # withdrawn after the link was issued
        r = c.simulate_post("/api/aed/urzadzenia/%s/potwierdzenie" % recs[3]["id_aed"], json=self.confirm_body({"t": token}))
        self.assertEqual((r.status_code, r.json["blad"]["kod"]), (409, "wycofany"))
        self.assertEqual(c.simulate_get("/api/aed/urzadzenia/" + recs[3]["id_aed"]).json["status"], "wycofany")

    def test_manager_adds_contact_to_imported_record_without_one(self):
        c = self.client()
        rec = self.imported(1, nazwa="Szkoła z zbioru miejskiego", opis_lokalizacji="Hol")
        self.mapper(c, [rec])
        r = c.simulate_post("/api/aed/urzadzenia/%s/link-aktywacyjny" % rec["id_aed"], json={}, headers=self.ministry(c))
        token = r.json["link_aktywacyjny"].split("t=")[1]
        body = {"t": token, "dostep": "publiczny", "godziny_dostepu": "24/7", "stan": "sprawny",
                "dysponent_nazwa": "Gmina Test", "dysponent_email": "aed@gmina.example.org", "dysponent_telefon": "+48 12 000 00 00"}
        r = c.simulate_post("/api/aed/urzadzenia/%s/potwierdzenie" % rec["id_aed"], json=body)
        self.assertEqual(r.status_code, 200, r.text)
        out = r.json["rekord"]
        self.assertEqual((out["status"], out["dysponent_email"], out["dysponent_nazwa"]), ("aktywny", "aed@gmina.example.org", "Gmina Test"))
        self.assertEqual((out["nazwa"], out["opis_lokalizacji"], out["licencja"]), ("Szkoła z zbioru miejskiego", "Hol", "CC BY 4.0"))
        # a record that already has a contact keeps it
        item = self.add_device(c, "CON-1")
        r = c.simulate_post("/api/aed/urzadzenia/%s/potwierdzenie" % item["id_aed"],
                            json=self.confirm_body(item, dysponent_email="inny@example.org"))
        self.assertEqual(r.json["rekord"]["dysponent_email"], "gmina@example.org")

    def test_mapper_counts_review_entries_from_both_paths(self):
        c = self.client()
        item = self.add_device(c, "CNT-1")
        self.assertEqual(c.simulate_post("/api/aed/urzadzenia/%s/potwierdzenie" % item["id_aed"],
                                         json=self.confirm_body(item)).status_code, 200)
        near = self.imported(1, nazwa="Punkt testowy", szerokosc_geograficzna="50.5001")
        a, b = self.imported(2, szerokosc_geograficzna="50.6"), self.imported(3, zrodlo="inne", szerokosc_geograficzna="50.6002")
        pair = {"id_aed_a": a["id_aed"], "id_aed_b": b["id_aed"], "odleglosc_m": 22, "podobienstwo": 0.5}
        self.assertEqual(self.mapper(c, [near, a, b], [pair]).json["do_przegladu"], 2)   # one spatial match + one mapper pair
        self.assertEqual(self.mapper(c, [dict(near, nazwa="Zmiana"), a, b], [pair]).json["do_przegladu"], 0)   # both known

    def test_problem_report_lists_only_blocking_errors(self):
        c = self.client()
        item = self.add_device(c, "PRB-2")
        r = c.simulate_post("/api/aed/urzadzenia/%s/potwierdzenie" % item["id_aed"],
                            json={"t": item["t"], "stan": "problem", "uwagi": "Brak elektrod", "dostep": "PRIVATE"})
        self.assertEqual(r.status_code, 422)
        self.assertEqual([(p["pole"], p["kod"]) for p in r.json["blad"]["problemy"]], [("dostep", "spoza_slownika")])

    def test_mapper_retires_vanished_import_records_and_restores_them(self):
        c = self.client()
        recs = [self.imported(i) for i in range(1, 5)]
        item = self.add_device(c, "RET-1")  # a submission must never be retired
        self.assertEqual(self.mapper(c, recs).json["wycofano"], 0)
        self.assertEqual(self.mapper(c, recs[:3]).json["wycofano"], 1)
        get = lambda r: c.simulate_get("/api/aed/urzadzenia/" + r["id_aed"]).json  # noqa: E731
        self.assertEqual([get(r)["status"] for r in recs], ["niepotwierdzony"] * 3 + ["wycofany"])
        self.assertEqual(get({"id_aed": item["id_aed"]})["status"], "zgloszony")
        r = self.mapper(c, recs[:3]).json  # idempotent
        self.assertEqual((r["wycofano"], r["zmieniono"]), (0, 0))
        r = self.mapper(c, recs).json  # the record reappears
        self.assertEqual(get(recs[3])["status"], "niepotwierdzony")
        self.assertEqual(r["zmieniono"], 1)

    def test_mapper_does_not_retire_on_a_broken_run(self):
        c = self.client()
        recs = [self.imported(i) for i in range(1, 7)]
        self.mapper(c, recs)
        for broken in ([], recs[:2]):  # empty output, drastically smaller output
            r = self.mapper(c, broken)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json["wycofano"], 0)
        statuses = {x["status"] for x in c.simulate_get("/api/aed/urzadzenia").json["dane"]}
        self.assertEqual(statuses, {"niepotwierdzony"})
        jobs = c.simulate_get("/api/aed/zadania", headers=self.ministry(c)).json["dane"]
        self.assertIn("podejrzanie mało", jobs[0]["bledy"][0])
        self.assertNotIn("ostrzezenie", jobs[0]["mapper"])

    def test_read_only_snapshot_is_not_fatal(self):
        import shutil
        if os.geteuid() == 0:
            self.skipTest("root ignores file permissions")
        raw = os.path.join(self.tmp.name, "raw")
        shutil.copytree(svc.RAW_DIR, raw)
        manifest = os.path.join(raw, "manifest.json")

        def failing_download(*a, **kw):  # the script cannot write into the read-only snapshot
            with open(manifest, "w") as f:
                f.write("{}")

        c = self.client()
        os.chmod(manifest, 0o444)
        os.chmod(raw, 0o555)
        try:
            with mock.patch.object(svc, "RAW_DIR", raw), mock.patch.object(svc, "SCRIPT_RAW_DIR", raw), \
                    mock.patch.object(svc, "DOWNLOAD_SCRIPT", __file__), \
                    mock.patch.object(svc.subprocess, "run", side_effect=failing_download):
                job = svc.run_job(sqlite_conn(self, self.path), "harmonogram", "cykl")
        finally:
            os.chmod(raw, 0o755)
            os.chmod(manifest, 0o644)
        self.assertIsNotNone(job["mapper"])  # mapper still ran on the readable snapshot
        self.assertIsNotNone(job["przypomnienia"])
        self.assertTrue(any("przywrócić" in e or "odświeżyć" in e for e in job["bledy"]), job["bledy"])
        self.assertEqual(c.simulate_get("/api/aed/zadania", headers=self.ministry(c)).json["dane"][0]["id"], job["id"])


XSD = os.path.join(ROOT, "backend", "data", "harvester", "xml_import_otwarte_dane_1_13.xsd")
XMLLINT = "/usr/bin/xmllint"


class HarvesterFeedTest(unittest.TestCase):
    """XML feed for the dane.gov.pl harvester (backend/mcod/harvester/utils.py:validate_xml_url)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        db = svc.open_db(os.path.join(tmp.name, "t.db"), with_registry=False)
        self.addCleanup(db.close)
        self.client = testing.TestClient(svc.build_app(db))
        base = mock.patch.object(svc, "BASE_URL", "https://aed.example.gov.pl/")
        base.start()
        self.addCleanup(base.stop)

    def run_mapper(self, recs):
        r = self.client.simulate_post("/api/aed/sesja", json={"email": "ministerstwo@aed.example", "haslo": "ministerstwo-demo"})
        with mock.patch.object(aed_standard, "build_registry", return_value=(recs, [], {"polaczenia": {"razem": 0}})):
            out = self.client.simulate_post("/api/aed/mapper/uruchom", headers={"Authorization": "Bearer " + r.json["token"]})
        self.assertEqual(out.status_code, 200, out.text)

    def rec(self, i, **kw):
        base = {n: "" for n in aed_standard.field_names()}
        base.update(id_aed="AED-FEEDTEST%04d" % i, nazwa="Punkt %d" % i, szerokosc_geograficzna="52.1",
                    dlugosc_geograficzna="21.0", miejscowosc="Warszawa", status="niepotwierdzony", zrodlo="test",
                    zrodlo_id=str(i), licencja="CC BY 4.0", dostep="publiczny", kompletnosc="40",
                    data_aktualizacji="2026-11-0%d" % i)
        base.update(kw)
        return base

    def feed(self):
        xml = self.client.simulate_get("/api/aed/eksport/dane-gov-pl.xml")
        md5 = self.client.simulate_get("/api/aed/eksport/dane-gov-pl.md5")
        self.assertEqual((xml.status_code, md5.status_code), (200, 200))
        self.assertIn("application/xml", xml.headers["content-type"])
        self.assertEqual(md5.text, hashlib.md5(xml.content).hexdigest())
        return xml.content, md5.text

    def test_feed_valid_stable_and_versioned(self):
        osm = self.rec(3, licencja="ODbL 1.0", zrodlo="openstreetmap", nazwa="Tylko OSM")
        self.run_mapper([self.rec(1), self.rec(2), osm, self.rec(4, dostep="prywatny", nazwa="Prywatny")])
        head = self.client.simulate_head("/api/aed/eksport/dane-gov-pl.xml")
        self.assertEqual(head.status_code, 200)  # the harvester checks headers with HEAD first
        self.assertIn("application/xml", head.headers["content-type"])
        xml, md5 = self.feed()
        self.assertEqual(self.feed(), (xml, md5))  # unchanged registry -> identical bytes and sum

        root = ET.fromstring(xml)
        self.assertEqual(root.tag, "{urn:otwarte-dane:harvester:1.13}datasets")  # version read from the namespace
        self.assertEqual([e.text for e in root.iter("extIdent")], ["aed-krajowy-rejestr", "aed-krajowy-rejestr-csv"])
        self.assertEqual(root.find("dataset/lastUpdateDate").text, "2026-11-02T00:00:00")  # newest exported record
        link = root.find("dataset/resources/resource/url").text
        self.assertTrue(link.startswith("https://aed.example.gov.pl/api/aed/eksport/dane-gov-pl.csv?wersja="), link)
        csv_text = self.client.simulate_get(link.split("gov.pl", 1)[1].split("?")[0]).text
        self.assertIn("Punkt 1", csv_text)
        self.assertNotIn("Tylko OSM", csv_text)  # ODbL and private records never reach the linked file
        self.assertNotIn("Prywatny", csv_text)

        if os.path.exists(XMLLINT) and os.path.exists(XSD):
            path = os.path.join(self.tmp, "feed.xml")
            with open(path, "wb") as f:
                f.write(xml)
            check = subprocess.run([XMLLINT, "--noout", "--schema", XSD, path], capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)

        self.run_mapper([self.rec(1), self.rec(2, nazwa="Punkt 2 po zmianie"), osm])
        xml2, md5_2 = self.feed()
        self.assertNotEqual(md5_2, md5)
        self.assertNotEqual(ET.fromstring(xml2).find("dataset/resources/resource/url").text, link)  # new link -> re-download

    @unittest.skipUnless(os.path.exists(XMLLINT), "xmllint not available")
    def test_xsd_rejects_http_resource_link(self):
        """Why AED_BASE_URL must be https: XSD 1.13 restricts resource/url to https://.* (line 578-588)."""
        self.run_mapper([self.rec(1)])
        with mock.patch.object(svc, "BASE_URL", "http://localhost:8080"):
            xml = self.client.simulate_get("/api/aed/eksport/dane-gov-pl.xml").content
        path = os.path.join(self.tmp, "feed.xml")
        with open(path, "wb") as f:
            f.write(xml)
        self.assertNotEqual(subprocess.run([XMLLINT, "--noout", "--schema", XSD, path], capture_output=True).returncode, 0)


def sqlite_conn(test, path):
    """Direct connection to the service database, closed when the test ends."""
    import sqlite3
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    test.addCleanup(conn.close)
    return conn


if __name__ == "__main__":
    unittest.main()
