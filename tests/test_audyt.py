"""Service findings of docs/ewaluacja-codex/audyt-uslugi.md, each with a test that failed before its fix."""
import csv
import datetime
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from falcon import testing

from aed_service import app as svc
from tests.test_aed_service import NEXT_YEAR, multipart, seller_csv


class AuditServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "t.db")
        self.c = self.client()

    def client(self, **kw):
        self.db = svc.open_db(self.path, with_registry=False, **kw)
        self.addCleanup(self.db.close)
        return testing.TestClient(svc.build_app(self.db))

    def login(self, email, password, c=None):
        r = (c or self.c).simulate_post("/api/aed/sesja", json={"email": email, "haslo": password})
        self.assertEqual(r.status_code, 200, r.text)
        return {"Authorization": "Bearer " + r.json["token"]}

    def firma(self, email="pulsar@aed.example", pw="pulsar-demo"):
        return self.login(email, pw)

    def ministry(self):
        return self.login("ministerstwo@aed.example", "ministerstwo-demo")

    def submit(self, data, headers, path="/api/aed/zgloszenia"):
        m = multipart(data)
        return self.c.simulate_post(path, headers=dict(headers, **m["headers"]), body=m["body"])

    def one(self, headers, **kw):
        body = dict({"producent": "Pulsar", "model": "P-1", "numer_seryjny": "S-1", "data_produkcji": "2025-01-10",
                     "data_waznosci_elektrod": NEXT_YEAR, "data_waznosci_baterii": NEXT_YEAR,
                     "dysponent_nazwa": "Szkoła nr 1", "dysponent_email": "szkola@example.org"}, **kw)
        r = self.c.simulate_post("/api/aed/urzadzenia", headers=headers, json=body)
        self.assertEqual(r.status_code, 201, r.text)
        return r.json

    def export_ids(self):
        return [r["id_aed"] for r in csv.DictReader(io.StringIO(self.c.simulate_get("/api/aed/eksport/dane-gov-pl.csv").text))]

    def confirm(self, item, **kw):
        body = dict({"t": item["link_aktywacyjny"].split("t=")[1], "nazwa": "Szkoła nr 1", "szerokosc_geograficzna": 52.39,
                     "dlugosc_geograficzna": 20.93, "miejscowosc": "Legionowo", "dostep": "publiczny",
                     "godziny_dostepu": "Mo-Fr 08:00-16:00", "stan": "sprawny"}, **kw)
        return self.c.simulate_post("/api/aed/urzadzenia/%s/potwierdzenie" % item["id_aed"], json=body)

    # 1
    def test_separate_ministry_password_and_reset_signs_everyone_out(self):
        self.tmp.cleanup()
        os.makedirs(self.tmp.name)
        with mock.patch.dict(os.environ, {"AED_DEMO_PASSWORD": "firmowe", "AED_MINISTRY_PASSWORD": "ministerialne"}):
            c = self.client()
        self.login("pulsar@aed.example", "firmowe", c)
        old = self.login("ministerstwo@aed.example", "ministerialne", c)
        self.assertEqual(c.simulate_post("/api/aed/sesja", json={"email": "ministerstwo@aed.example", "haslo": "firmowe"}).status_code, 401)
        with mock.patch.dict(os.environ, {"AED_MINISTRY_PASSWORD": "nowe", "AED_RESET_PASSWORDS": "1"}):
            c = self.client()
        self.assertEqual(c.simulate_get("/api/aed/sesja", headers=old).status_code, 401)
        self.login("ministerstwo@aed.example", "nowe", c)
        self.login("pulsar@aed.example", "pulsar-demo", c)  # no AED_DEMO_PASSWORD now: back to the demo one
        self.assertFalse(c.simulate_get("/api/aed/statystyki").json["hasla_demo_domyslne"])

    # 6
    def test_submission_marked_as_osm_is_rejected(self):
        out = self.c.simulate_post("/api/aed/urzadzenia", headers=self.firma(), json={
            "producent": "Pulsar", "model": "P-1", "numer_seryjny": "OSM-1", "data_produkcji": "2025-01-10",
            "data_waznosci_elektrod": NEXT_YEAR, "data_waznosci_baterii": NEXT_YEAR, "dysponent_nazwa": "Szkoła",
            "dysponent_email": "s@example.org", "licencja": "ODbL 1.0"}).json
        self.assertEqual((out["podsumowanie"]["przyjete"], out["podsumowanie"]["odrzucone"]), (0, 1))
        self.assertIn("dane_osm", {p["kod"] for p in out["problemy"]})

    # 8
    def test_submission_with_location_is_published_only_after_confirmation(self):
        item = self.one(self.firma(), nazwa="Szkoła nr 1", miejscowosc="Legionowo", szerokosc_geograficzna="52.39",
                        dlugosc_geograficzna="20.93")["przyjete"][0]
        self.assertEqual(self.export_ids(), [])
        self.assertEqual(self.confirm(item).status_code, 200)
        self.assertEqual(self.export_ids(), [item["id_aed"]])

    # 9
    def test_failed_write_is_rolled_back(self):
        with mock.patch.object(svc, "new_token", side_effect=RuntimeError("disk")):
            r = self.c.simulate_post("/api/aed/urzadzenia", headers=self.firma(), json={"producent": "Pulsar", "model": "P",
                                     "numer_seryjny": "X-1", "data_produkcji": "2025-01-10", "data_waznosci_elektrod": NEXT_YEAR,
                                     "data_waznosci_baterii": NEXT_YEAR, "dysponent_nazwa": "S", "dysponent_email": "s@example.org"})
        self.assertEqual(r.status_code, 500)
        self.assertFalse(self.db.in_transaction)
        self.one(self.firma(), numer_seryjny="X-2")  # the next write commits only itself
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM zgloszenia WHERE odpowiedz=''").fetchone()[0], 0)
        self.assertEqual(self.c.simulate_get("/api/aed/zgloszenia", headers=self.firma()).status_code, 200)

    # 10
    def test_other_companys_serial_is_not_revealed(self):
        self.one(self.firma("serwis@aed.example", "serwis-demo"), numer_seryjny="TAJNY-1")
        data = seller_csv(["TAJNY-1"])
        dry = self.submit(data, self.firma(), "/api/aed/zgloszenia/sprawdz").json
        self.assertEqual((dry["podsumowanie"]["duplikaty"], dry["podsumowanie"]["przyjete"]), (0, 1))
        self.submit(data, self.firma())
        self.assertEqual(self.c.simulate_get("/api/aed/duplikaty", headers=self.ministry()).json["razem"], 1)
        # the account's own repeat is still a duplicate
        self.assertEqual(self.submit(data, self.firma(), "/api/aed/zgloszenia/sprawdz").json["podsumowanie"]["duplikaty"], 1)

    # 11
    def test_withdrawn_device_is_not_on_the_map(self):
        item = self.one(self.firma())["przyjete"][0]
        self.confirm(item, godziny_dostepu="24/7")
        self.db.execute("UPDATE devices SET status='wycofany' WHERE id_aed=?", (item["id_aed"],))
        self.db.commit()
        for q in ("", "?dostepny_teraz=true"):
            self.assertEqual(self.c.simulate_get("/api/aed/urzadzenia.geojson" + q).json["features"], [], q)
        self.assertEqual(len(self.c.simulate_get("/api/aed/urzadzenia.geojson?status=wycofany").json["features"]), 1)

    # 12
    def test_demo_flag_is_set_with_the_insert_and_repaired(self):
        c = self.client(demo=True)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM devices WHERE demo=0").fetchone()[0], 0)
        self.db.execute("UPDATE devices SET demo=0")  # as left by an older, interrupted seed
        self.db.commit()
        c = self.client(demo=True)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM devices WHERE demo=0").fetchone()[0], 0)
        self.assertEqual(len(list(csv.DictReader(io.StringIO(c.simulate_get("/api/aed/eksport/dane-gov-pl.csv").text)))), 0)

    # 13
    def test_stale_pair_cannot_retire_the_last_active_record(self):
        ids = [self.one(self.firma(), numer_seryjny="D-%d" % i)["przyjete"][0]["id_aed"] for i in range(3)]
        a, b, c = ids
        for x, y in ((a, b), (b, c)):
            svc.queue_pair(self.db, x, y, 5.0, 0.9)
        self.db.commit()
        m = self.ministry()
        pairs = {(p["rekord_a"]["id_aed"], p["rekord_b"]["id_aed"]): p["id"]
                 for p in self.c.simulate_get("/api/aed/duplikaty", headers=m).json["dane"]}
        self.assertEqual(self.c.simulate_post("/api/aed/duplikaty/%d" % pairs[(a, b)], headers=m, json={"decyzja": "polacz"}).status_code, 200)
        # B-C is replaced by A-C; the old pair can no longer be decided
        self.assertEqual(self.c.simulate_post("/api/aed/duplikaty/%d" % pairs[(b, c)], headers=m, json={"decyzja": "polacz"}).status_code, 409)
        left = self.c.simulate_get("/api/aed/duplikaty", headers=m).json["dane"]
        self.assertEqual([(p["rekord_a"]["id_aed"], p["rekord_b"]["id_aed"]) for p in left], [(a, c)])
        # A withdrawn independently: deciding A-C must not retire C
        self.db.execute("UPDATE devices SET status='wycofany' WHERE id_aed=?", (a,))
        self.db.commit()
        r = self.c.simulate_post("/api/aed/duplikaty/%d" % left[0]["id"], headers=m, json={"decyzja": "polacz"})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.db.execute("SELECT status FROM devices WHERE id_aed=?", (c,)).fetchone()[0], "zgloszony")

    # 14
    def test_problem_report_still_gets_periodic_requests(self):
        item = self.one(self.firma())["przyjete"][0]
        self.confirm(item)
        r = self.confirm(item, stan="problem", uwagi="Brak elektrod")
        # 0.3.0: the problem concerns the device; the confirmed data stay confirmed
        self.assertEqual((r.status_code, r.json["status"], r.json["stan_urzadzenia"]), (200, "zweryfikowany", "czasowo_niedostepny"))
        self.assertEqual(svc.reminders(self.db)["prosby_o_potwierdzenie"], 0)   # just reported
        old = (datetime.date.today() - datetime.timedelta(days=31)).isoformat()
        self.db.execute("UPDATE devices SET data=json_set(data,'$.data_stanu',?) WHERE id_aed=?", (old, item["id_aed"]))
        self.db.commit()
        self.assertEqual(svc.reminders(self.db)["prosby_o_potwierdzenie"], 1)   # a month later: one request, not two
        self.assertEqual(svc.reminders(self.db)["prosby_o_potwierdzenie"], 0)
        msg = self.db.execute("SELECT temat FROM messages WHERE rodzaj='prosba' AND id_aed=?", (item["id_aed"],)).fetchall()
        self.assertEqual([m[0] for m in msg], ["Zaktualizuj stan urządzenia AED %s" % item["id_aed"]])

    # owner decision: serial numbers only for the submitting company and the ministry
    def test_serial_visible_only_to_owner_and_ministry(self):
        own = self.firma()
        item = self.one(own, numer_seryjny="SN-777")["przyjete"][0]
        self.confirm(item)
        path = "/api/aed/urzadzenia/" + item["id_aed"]
        public = [self.c.simulate_get(path).text, self.c.simulate_get("/api/aed/urzadzenia").text,
                  self.c.simulate_get("/api/aed/urzadzenia.geojson").text,
                  self.c.simulate_get("/api/aed/eksport/dane-gov-pl.csv").text,
                  self.c.simulate_get(path, headers=self.firma("serwis@aed.example", "serwis-demo")).text]
        for text in public:
            self.assertNotIn("SN-777", text)
            self.assertNotIn("szkola@example.org", text)
        self.assertEqual(self.c.simulate_get(path, headers=own).json["numer_seryjny"], "SN-777")
        self.assertEqual(self.c.simulate_get(path, headers=self.ministry()).json["dysponent_email"], "szkola@example.org")
        self.assertIn("SN-777", json.dumps(self.c.simulate_get("/api/aed/zgloszenia", headers=own).json))


if __name__ == "__main__":
    unittest.main()


class HardeningTest(unittest.TestCase):
    def test_sticker_cannot_run_as_a_page_and_responses_are_not_sniffed(self):
        import aed_service.app as svc
        from falcon import testing
        tmp = tempfile.TemporaryDirectory()
        db = svc.open_db(os.path.join(tmp.name, "t.db"), with_registry=False)
        self.addCleanup(tmp.cleanup)
        self.addCleanup(db.close)
        client = testing.TestClient(svc.build_app(db))
        self.assertEqual(client.simulate_get("/api/aed/statystyki").headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(client.simulate_get("/api/aed/urzadzenia/%3Csvg%20onload%3D1%3E/naklejka.svg").status_code, 404)
