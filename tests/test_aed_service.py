"""End-to-end tests of aed_service on a temporary database (Falcon testing client, real aed_standard)."""
import csv
import datetime
import io
import json
import os
import tempfile
import unittest
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


def multipart(data, filename="zgloszenie.csv"):
    b = "XXBOUNDARYXX"
    body = ('--%s\r\nContent-Disposition: form-data; name="plik"; filename="%s"\r\nContent-Type: text/csv\r\n\r\n'
            % (b, filename)).encode() + data + ("\r\n--%s--\r\n" % b).encode()
    return {"body": body, "headers": {"Content-Type": "multipart/form-data; boundary=" + b}}


class ServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.client = testing.TestClient(svc.create_app(os.path.join(cls.tmp.name, "t.db"), with_registry=False))

    @classmethod
    def tearDownClass(cls):
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
        data = open(SAMPLE, "rb").read() if os.path.exists(SAMPLE) else seller_csv(["S-100", "S-101"], bad_row=True)
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
        open(logo, "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>')
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
        return testing.TestClient(svc.create_app(self.path, with_registry=False, **kw))

    def ministry(self, c):
        r = c.simulate_post("/api/aed/sesja", json={"email": "ministerstwo@aed.example", "haslo": "ministerstwo-demo"})
        return {"Authorization": "Bearer " + r.json["token"]}

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
                job = svc.run_job(sqlite_conn(self.path), "harmonogram", "cykl")
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
                mock.patch.object(svc, "refresh_sources", return_value=(None, [])):
            job = svc.run_job(sqlite_conn(self.path), "harmonogram", "cykl")
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
        original = json.load(open(manifest, encoding="utf-8"))
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
                    job = svc.run_job(sqlite_conn(self.path), "harmonogram", "cykl")
                on_disk = [e["file"] for e in json.load(open(manifest, encoding="utf-8"))["files"]]
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
        conn = sqlite_conn(self.path)
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
        conn = sqlite_conn(self.path)
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
        conn = sqlite_conn(self.path)
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
            open(manifest, "w").write("{}")

        c = self.client()
        os.chmod(manifest, 0o444)
        os.chmod(raw, 0o555)
        try:
            with mock.patch.object(svc, "RAW_DIR", raw), mock.patch.object(svc, "SCRIPT_RAW_DIR", raw), \
                    mock.patch.object(svc, "DOWNLOAD_SCRIPT", __file__), \
                    mock.patch.object(svc.subprocess, "run", side_effect=failing_download):
                job = svc.run_job(sqlite_conn(self.path), "harmonogram", "cykl")
        finally:
            os.chmod(raw, 0o755)
            os.chmod(manifest, 0o644)
        self.assertIsNotNone(job["mapper"])  # mapper still ran on the readable snapshot
        self.assertIsNotNone(job["przypomnienia"])
        self.assertTrue(any("przywrócić" in e or "odświeżyć" in e for e in job["bledy"]), job["bledy"])
        self.assertEqual(c.simulate_get("/api/aed/zadania", headers=self.ministry(c)).json["dane"][0]["id"], job["id"])


def sqlite_conn(path):
    import sqlite3
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":
    unittest.main()
