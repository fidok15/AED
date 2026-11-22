"""AED service: Falcon + SQLite implementation of docs/api-aed.md.

All validation and registry logic lives in aed_standard; this module only stores, authorises and routes.
"""
import base64
import csv
import datetime
import functools
import hashlib
import hmac
import io
import json
import math
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import threading
import traceback
import xml.etree.ElementTree as ET

import falcon
import segno

import aed_standard
from aed_standard import konwerter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT_RAW_DIR = os.path.join(ROOT, "datasets", "raw")  # where scripts/download_aed_data.py writes
RAW_DIR = os.environ.get("AED_RAW_DIR", SCRIPT_RAW_DIR)  # snapshot read by the mapper; must be writable for refresh
DEFAULT_DB = os.path.join(HERE, "aed_service.db")

MAX_UPLOAD = 5 * 1024 * 1024
SESSION_HOURS = 12
BASE_URL = os.environ.get("AED_BASE_URL", "http://localhost:4200")  # where /aed/qr/{id} is served (frontend)
CORS_ORIGINS = os.environ.get("AED_CORS_ORIGINS", "http://localhost:4200").split(",")

# Seller badge: both thresholds must hold and the company needs at least one device.
BADGE_MIN_COMPLETENESS = 70   # average completeness (0-100)
BADGE_MIN_ACTIVE_SHARE = 0.5  # share of devices with status "aktywny"

# Reminder rules (days).
REQUEST_AFTER_DAYS = 183   # ask the manager to confirm after ~6 months without verification
EXPIRY_WARNING_DAYS = 60   # battery / pads expiry warning window
STALE_AFTER_DAYS = 365     # status "nieaktualny" after 12 months without confirmation
RETIRE_MIN_SHARE = 0.5      # mapper output below this share of the current import set = broken run, retire nothing
TOKEN_DAYS = 90           # every manager link stays valid this long; several links per device are valid at once
RESEND_GAP_DAYS = 30       # do not repeat the same kind of message for a device within this gap

HIDDEN_PUBLIC = aed_standard.build.HIDDEN_PUBLIC  # one rule for every public export
CONFIRM_FIELDS = ("nazwa", "szerokosc_geograficzna", "dlugosc_geograficzna", "miejscowosc", "cecha_ulicy",
                  "nazwa_ulicy", "nr_budynku", "nr_lokalu", "kod_pocztowy", "opis_lokalizacji", "wewnatrz_budynku",
                  "dostep", "godziny_dostepu", "godziny_dostepu_opis", "data_waznosci_baterii", "data_waznosci_elektrod")
OWNER_FIELDS = ("dysponent_nazwa", "dysponent_email", "dysponent_telefon")  # set by the manager when the record has no contact
ODBL = "ODbL 1.0"
REQUIRED_CODES = ("brak_wymaganego", "wymagane_dla_aktywnego")  # not an error in an incomplete problem report
SIGNAL_TYPES = ("jest", "brak", "uszkodzony", "zamkniety")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS accounts(
  id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, nazwa TEXT NOT NULL, rola TEXT NOT NULL,
  typ_podmiotu TEXT NOT NULL, miejscowosc TEXT, lat REAL, lon REAL, salt BLOB NOT NULL, pass_hash BLOB NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(
  token_hash TEXT PRIMARY KEY, account_id INTEGER NOT NULL, expires TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS devices(
  id_aed TEXT PRIMARY KEY, data TEXT NOT NULL,            -- data: JSON with exactly the schema field names
  origin TEXT NOT NULL,                                   -- import | zgloszenie | zarzadca | scalony
  konto_id INTEGER, zgloszenie_id INTEGER, token_hash TEXT, uwagi_zarzadcy TEXT, utworzono TEXT,
  klucz TEXT,                                             -- normalised producent|numer_seryjny
  status TEXT, dostep TEXT, zrodlo TEXT, nazwa TEXT, miejscowosc TEXT, szukaj TEXT, godziny TEXT,
  kompletnosc INTEGER, data_weryfikacji TEXT, lat REAL, lon REAL);
CREATE INDEX IF NOT EXISTS devices_klucz ON devices(klucz);
CREATE INDEX IF NOT EXISTS devices_konto ON devices(konto_id);
CREATE TABLE IF NOT EXISTS zgloszenia(
  id INTEGER PRIMARY KEY, konto_id INTEGER NOT NULL, utworzono TEXT NOT NULL, plik TEXT, odpowiedz TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS messages(
  id INTEGER PRIMARY KEY, rodzaj TEXT NOT NULL, id_aed TEXT, odbiorca TEXT, temat TEXT, tresc TEXT, link TEXT, data TEXT);
CREATE TABLE IF NOT EXISTS signals(
  id INTEGER PRIMARY KEY, id_aed TEXT NOT NULL, typ TEXT NOT NULL, lat REAL, lon REAL, uwagi TEXT, data TEXT);
CREATE TABLE IF NOT EXISTS tokens(
  hash TEXT PRIMARY KEY, id_aed TEXT NOT NULL, utworzono TEXT NOT NULL, wygasa TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS jobs(
  id INTEGER PRIMARY KEY, start TEXT NOT NULL, koniec TEXT, wyzwalacz TEXT NOT NULL, rodzaj TEXT NOT NULL,
  odswiezono TEXT, mapper TEXT, przypomnienia TEXT, bledy TEXT NOT NULL DEFAULT '[]');
CREATE TABLE IF NOT EXISTS duplicates(
  id INTEGER PRIMARY KEY, id_a TEXT NOT NULL, id_b TEXT NOT NULL, odleglosc_m REAL, podobienstwo REAL,
  decyzja TEXT, UNIQUE(id_a, id_b));
"""


def migrate(db):
    """Bring a database created by an older version up to date (additive changes only)."""
    cols = {r[1] for r in db.execute("PRAGMA table_info(devices)")}
    if "demo" not in cols:  # demo = 1 marks fictional seed devices: visible in the registry, never exported
        db.execute("ALTER TABLE devices ADD COLUMN demo INTEGER NOT NULL DEFAULT 0")
    if "powod" not in cols:  # reason a record was withdrawn by the mapper
        db.execute("ALTER TABLE devices ADD COLUMN powod TEXT")
    # single-token era: move the one hash per device into the tokens table (once), then clear the old column
    exp = (datetime.datetime.now() + datetime.timedelta(days=TOKEN_DAYS)).replace(microsecond=0).isoformat()
    db.execute("INSERT OR IGNORE INTO tokens(hash,id_aed,utworzono,wygasa) SELECT token_hash,id_aed,?,? FROM devices"
               " WHERE token_hash IS NOT NULL", (now(), exp))
    db.execute("UPDATE devices SET token_hash=NULL WHERE token_hash IS NOT NULL")
    # zrodlo_id of submissions used to be "producent|serial": replace it with an opaque value (id_aed stays as issued)
    for id_aed, data in db.execute("SELECT id_aed, data FROM devices WHERE zrodlo='zgloszenie'").fetchall():
        rec = json.loads(data)
        if "|" in rec.get("zrodlo_id", ""):
            rec["zrodlo_id"] = secrets.token_hex(6)
            db.execute("UPDATE devices SET data=? WHERE id_aed=?", (json.dumps(rec, ensure_ascii=False), id_aed))
    db.commit()


def today():
    return datetime.date.today()


def now():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


class ApiError(Exception):
    def __init__(self, status, kod, komunikat, extra=None):
        self.status, self.kod, self.komunikat, self.extra = status, kod, komunikat, extra or {}


# ---------- crypto helpers ----------

def hash_password(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1)


def sha(token):
    return hashlib.sha256(token.encode()).hexdigest()


def norm_key(rec):
    """Lookup key of a physical device: producent + serial number, lower-case alphanumerics only."""
    p = re.sub(r"[\W_]+", "", (rec.get("producent") or "").casefold())
    s = re.sub(r"[\W_]+", "", (rec.get("numer_seryjny") or "").casefold())
    return "%s|%s" % (p, s) if p and s else None


# ---------- device storage ----------

def to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def clean(rec):
    """Keep schema fields only, all values as stripped strings."""
    out = {}
    for name in aed_standard.field_names():
        v = rec.get(name)
        if isinstance(v, bool):
            v = "tak" if v else "nie"
        out[name] = "" if v is None else str(v).strip()
    return out


def device_row(rec, origin, konto_id=None, zgloszenie_id=None, token_hash=None, utworzono=None):
    return (rec["id_aed"], json.dumps(rec, ensure_ascii=False), origin, konto_id, zgloszenie_id, token_hash,
            utworzono or now(), norm_key(rec), rec.get("status", ""), rec.get("dostep", ""), rec.get("zrodlo", ""),
            rec.get("nazwa", ""), rec.get("miejscowosc", ""),
            ("%s %s" % (rec.get("nazwa", ""), rec.get("miejscowosc", ""))).casefold(),
            rec.get("godziny_dostepu", ""), int(rec.get("kompletnosc") or 0), rec.get("data_weryfikacji", ""),
            to_float(rec.get("szerokosc_geograficzna")), to_float(rec.get("dlugosc_geograficzna")))


UPSERT_COLS = ("id_aed,data,origin,konto_id,zgloszenie_id,token_hash,utworzono,klucz,status,dostep,zrodlo,nazwa,"
               "miejscowosc,szukaj,godziny,kompletnosc,data_weryfikacji,lat,lon")
INSERT_SQL = "INSERT INTO devices(%s) VALUES(%s)" % (UPSERT_COLS, ",".join("?" * 19))
IMPORT_UPDATE_SQL = ("UPDATE devices SET data=?,klucz=?,status=?,dostep=?,zrodlo=?,nazwa=?,miejscowosc=?,szukaj=?,"
                     "godziny=?,kompletnosc=?,data_weryfikacji=?,lat=?,lon=?,powod=NULL WHERE id_aed=? AND origin='import'")


def save_device(db, rec, **kw):
    """Update the stored record (data and the denormalised columns) of an existing device."""
    r = device_row(rec, "")
    db.execute("UPDATE devices SET data=?,klucz=?,status=?,dostep=?,zrodlo=?,nazwa=?,miejscowosc=?,szukaj=?,godziny=?,"
               "kompletnosc=?,data_weryfikacji=?,lat=?,lon=? WHERE id_aed=?", r[1:2] + r[7:] + (rec["id_aed"],))
    for col, val in kw.items():  # column names come from code, never from the request
        db.execute("UPDATE devices SET %s=? WHERE id_aed=?" % col, (val, rec["id_aed"]))


def get_device(db, id_aed):
    row = db.execute("SELECT * FROM devices WHERE id_aed=?", (id_aed,)).fetchone()
    if not row:
        raise ApiError(404, "nie_znaleziono", "Nie ma urządzenia o identyfikatorze %s." % id_aed)
    return row


def public(rec):
    return {k: v for k, v in rec.items() if k not in HIDDEN_PUBLIC}


def new_token(db, id_aed):
    """Issue one more manager token; earlier tokens of the device stay valid until they expire (TOKEN_DAYS)."""
    token = secrets.token_urlsafe(24)
    expires = (datetime.datetime.now() + datetime.timedelta(days=TOKEN_DAYS)).replace(microsecond=0).isoformat()
    db.execute("INSERT INTO tokens(hash,id_aed,utworzono,wygasa) VALUES(?,?,?,?)", (sha(token), id_aed, now(), expires))
    return token


def manager_ok(db, id_aed, token):
    return bool(token) and db.execute("SELECT 1 FROM tokens WHERE hash=? AND id_aed=? AND wygasa>?",
                                      (sha(str(token)), id_aed, now())).fetchone() is not None


def queue_message(db, rodzaj, id_aed, odbiorca, temat, tresc, link=None):
    db.execute("INSERT INTO messages(rodzaj,id_aed,odbiorca,temat,tresc,link,data) VALUES(?,?,?,?,?,?,?)",
               (rodzaj, id_aed, odbiorca, temat, tresc, link, now()))


def activation_link(id_aed, token):
    return "/aed/qr/%s?t=%s" % (id_aed, token)


# ---------- seed ----------

def import_registry(db, result=None):
    """Upsert mapper output. Records from submissions or confirmed by a manager are never touched."""
    records, pairs, report = result or aed_standard.build_registry(RAW_DIR)
    origins = {r[0]: r[1] for r in db.execute("SELECT id_aed, origin FROM devices")}
    old = {r[0]: r[1] for r in db.execute("SELECT id_aed, data FROM devices WHERE origin='import'")}
    # Ministry decisions "polacz": the kept record (A) stays an import record so its source fields keep refreshing,
    # but the link to the withdrawn record (B) is re-applied on every run.
    linked = {}
    for a_id, b_id in db.execute("SELECT id_a, id_b FROM duplicates WHERE decyzja='polacz'"):
        linked.setdefault(a_id, []).append(b_id)
    added, changed, inserts, updates = 0, 0, [], []
    for rec in records:
        rec = clean(rec)
        have = [x for x in rec["powiazane_zrodla"].split(";") if x]
        rec["powiazane_zrodla"] = ";".join(have + [x for x in linked.get(rec["id_aed"], []) if x not in have])
        if rec["id_aed"] not in origins:
            inserts.append(device_row(rec, "import"))
            added += 1
        elif rec["id_aed"] in old and old[rec["id_aed"]] != json.dumps(rec, ensure_ascii=False):
            r = device_row(rec, "import")
            updates.append(r[1:2] + r[7:] + (rec["id_aed"],))
            changed += 1
    db.executemany(INSERT_SQL, inserts)
    db.executemany(IMPORT_UPDATE_SQL, updates)
    # A new or changed import record next to a device a seller submitted or a manager confirmed goes to the review
    # queue (the other direction is checked at confirmation time).
    fresh = {r[0] for r in inserts} | {u[-1] for u in updates}
    owned = [json.loads(r[0]) for r in db.execute("SELECT data FROM devices WHERE %s AND lat IS NOT NULL" % OWNED_SQL)]
    queued = 0
    if fresh and owned:
        queued += queue_matches(db, owned, [clean(r) for r in records if r["id_aed"] in fresh])
    known = set(origins) | {r[0] for r in inserts}
    for p in pairs:
        a_id, b_id = p["id_aed_a"], p["id_aed_b"]
        if a_id in known and b_id in known:  # a decided pair never returns, whichever order it is listed in
            queued += queue_pair(db, a_id, b_id, p.get("odleglosc_m"), p.get("podobienstwo"))
    merged = int(report["polaczenia"]["razem"])
    out = {"dodano": added, "zmieniono": changed, "polaczono": merged, "do_przegladu": queued, "wycofano": 0}
    if report.get("bledy_zrodel"):
        out["bledy_zrodel"] = list(report["bledy_zrodel"])
    # Retire imported records that are gone from the mapper output (merged elsewhere or removed at the source).
    # Never touches submissions, manager-confirmed or ministry-decided records (origin != import).
    # Only sources that produced records this run can have lost records. A source skipped this run (broken or
    # mistyped registry entry, unsupported licence, unreadable or empty file) keeps its records untouched.
    processed = report.get("zrodla_przetworzone")
    skipped = set(report.get("pominiete_zrodla", []))
    live = {r[0] for r in db.execute("SELECT id_aed, zrodlo FROM devices WHERE origin='import' AND status!='wycofany'")
            if (r[1] in processed if processed is not None else r[1] not in skipped)}
    gone = live - {r["id_aed"] for r in records}
    if gone and (not records or len(records) < RETIRE_MIN_SHARE * len(live)):
        out["ostrzezenie"] = ("Mapper zwrócił podejrzanie mało rekordów (%d, a w rejestrze jest %d z importu); "
                              "nie wycofano żadnych rekordów." % (len(records), len(live)))
    else:
        for id_aed in gone:
            rec = json.loads(db.execute("SELECT data FROM devices WHERE id_aed=?", (id_aed,)).fetchone()[0])
            rec["status"] = "wycofany"
            db.execute("UPDATE devices SET status='wycofany', data=?, powod=? WHERE id_aed=? AND origin='import'",
                       (json.dumps(rec, ensure_ascii=False), "Brak w wynikach mappera: scalony z innym rekordem lub usunięty ze źródła.", id_aed))
        out["wycofano"] = len(gone)
    return out


DEMO_ACCOUNTS = [  # email, password, name, role, type, city, lat, lon
    ("ministerstwo@aed.example", "ministerstwo-demo", "Ministerstwo Cyfryzacji (konto demo)", "ministerstwo",
     "ministerstwo", "Warszawa", 52.2297, 21.0122),
    ("pulsar@aed.example", "pulsar-demo", "Pulsar Medical Sp. z o.o. (firma fikcyjna)", "firma", "producent",
     "Gdańsk", 54.3520, 18.6466),
    ("serwis@aed.example", "serwis-demo", "Serwis Rytm Sp. z o.o. (firma fikcyjna)", "firma", "sprzedawca",
     "Poznań", 52.4064, 16.9252),
]


@functools.lru_cache(maxsize=8)
def _is_default_password(password, salt, pass_hash):
    return hmac.compare_digest(hash_password(password, salt), pass_hash)


def demo_passwords_default(db):
    """True when the demo accounts still use the passwords from DEMO_ACCOUNTS (the sign-in cards may show them)."""
    email, pw = DEMO_ACCOUNTS[0][:2]
    row = db.execute("SELECT salt, pass_hash FROM accounts WHERE email=?", (email,)).fetchone()
    return bool(row) and _is_default_password(pw, bytes(row["salt"]), bytes(row["pass_hash"]))


def seed(db, with_registry=True):
    if not db.execute("SELECT 1 FROM accounts LIMIT 1").fetchone():
        for email, pw, name, rola, typ, city, lat, lon in DEMO_ACCOUNTS:
            pw = os.environ.get("AED_DEMO_PASSWORD") or pw  # public deployments: do not expose the well-known passwords
            salt = secrets.token_bytes(16)
            db.execute("INSERT INTO accounts(email,nazwa,rola,typ_podmiotu,miejscowosc,lat,lon,salt,pass_hash)"
                       " VALUES(?,?,?,?,?,?,?,?,?)", (email, name, rola, typ, city, lat, lon, salt, hash_password(pw, salt)))
    if with_registry and not db.execute("SELECT 1 FROM devices LIMIT 1").fetchone():
        import_registry(db)
    db.commit()


DEMO_CITIES = [("Gdańsk", 54.3520, 18.6466, "80-001"), ("Poznań", 52.4064, 16.9252, "61-001"),
               ("Kraków", 50.0647, 19.9450, "30-001"), ("Wrocław", 51.1079, 17.0385, "50-001"),
               ("Łódź", 51.7592, 19.4560, "90-001"), ("Katowice", 50.2649, 19.0238, "40-001"),
               ("Lublin", 51.2465, 22.5684, "20-001"), ("Szczecin", 53.4285, 14.5528, "70-001"),
               ("Białystok", 53.1325, 23.1688, "15-001"), ("Rzeszów", 50.0412, 21.9991, "35-001"),
               ("Olsztyn", 53.7784, 20.4801, "10-001"), ("Toruń", 53.0138, 18.5984, "87-100")]
DEMO_PLACES = ["Szkoła Podstawowa nr 7", "Urząd Dzielnicy", "Hala Sportowa", "Centrum Handlowe", "Dworzec Autobusowy",
               "Biblioteka Miejska", "Pływalnia Miejska", "Przychodnia Rejonowa", "Dom Kultury", "Siłownia Plenerowa",
               "Stadion Miejski", "Urząd Gminy"]
# company email, brand, model, serial prefix, device count, confirmed count
DEMO_PLAN = [("pulsar@aed.example", "Pulsar", "P-100 Demo", "PUL", 12, 10),
             ("serwis@aed.example", "RytmCare", "R-2 Demo", "RYT", 6, 2)]


def demo_seed(db):
    """Fictional devices created through the real submission and confirmation code (see README). Runs once."""
    if db.execute("SELECT 1 FROM devices WHERE demo=1 OR konto_id IS NOT NULL").fetchone():
        return
    t, ids = today(), []
    for email, brand, model, prefix, count, confirmed in DEMO_PLAN:
        account = db.execute("SELECT * FROM accounts WHERE email=?", (email,)).fetchone()
        records = []
        for i in range(count):
            city, lat, lon, zipcode = DEMO_CITIES[(i * 5 + len(prefix)) % len(DEMO_CITIES)]
            place = "%s (DEMO, fikcyjne)" % DEMO_PLACES[(i + len(brand)) % len(DEMO_PLACES)]
            records.append({
                "producent": brand, "model": model, "numer_seryjny": "DEMO-%s-%03d" % (prefix, i + 1),
                "data_produkcji": (t - datetime.timedelta(days=500 + i)).isoformat(),
                "data_waznosci_elektrod": (t + datetime.timedelta(days=500)).isoformat(),
                # device 4 of the first company: battery expires within the 60-day reminder window
                "data_waznosci_baterii": (t + datetime.timedelta(days=30 if (prefix == "PUL" and i == 4) else 900)).isoformat(),
                "dysponent_nazwa": "Fikcyjny Dysponent nr %d (DEMO)" % (i + 1), "dysponent_telefon": "+48 000 000 %03d" % (i + 1),
                "dysponent_email": "dysponent-%s-%d@demo.example" % (prefix.lower(), i + 1),
                "_place": (place, city, lat + i * 0.004, lon + i * 0.004, zipcode)})
        clean_recs = [{k: v for k, v in r.items() if k != "_place"} for r in records]
        out = process_submission(db, account, clean_recs, aed_standard.validate_records(clean_recs, "sprzedaz"), "demo", False)
        for i, item in enumerate(out["przyjete"]):
            ids.append(item["id_aed"])
            if i >= confirmed:
                continue  # stays "zgloszony": waiting activation link in the outbox
            place, city, lat, lon, zipcode = records[i]["_place"]
            apply_confirmation(db, item["id_aed"], {
                "t": item["link_aktywacyjny"].split("t=")[1], "nazwa": place, "szerokosc_geograficzna": round(lat, 6),
                "dlugosc_geograficzna": round(lon, 6), "miejscowosc": city, "nazwa_ulicy": "Demonstracyjna",
                "nr_budynku": str(i + 1), "kod_pocztowy": zipcode, "opis_lokalizacji": "Przy wejściu głównym (dane demo)",
                "wewnatrz_budynku": "tak", "dostep": "publiczny", "godziny_dostepu": "Mo-Fr 08:00-18:00",
                "godziny_dostepu_opis": "Dni robocze, 8:00-18:00", "stan": "sprawny"},
                on=t - datetime.timedelta(days=200) if (prefix == "PUL" and i == 5) else t)  # device 5: stale verification
    db.executemany("UPDATE devices SET demo=1 WHERE id_aed=?", [(i,) for i in ids])
    db.commit()


# ---------- request helpers ----------

def need_account(req, role=None):
    auth = req.get_header("Authorization") or ""
    if not auth.startswith("Bearer "):
        raise ApiError(401, "brak_logowania", "Zaloguj się, aby wykonać tę operację.")
    row = req.context.db.execute(
        "SELECT a.* FROM sessions s JOIN accounts a ON a.id=s.account_id WHERE s.token_hash=? AND s.expires>?",
        (sha(auth[7:].strip()), now())).fetchone()
    if not row:
        raise ApiError(401, "sesja_wygasla", "Sesja wygasła lub token jest niepoprawny. Zaloguj się ponownie.")
    if role and row["rola"] != role:
        raise ApiError(403, "brak_uprawnien", "Konto nie ma uprawnień do tej operacji.")
    return row


def body(req):
    data = req.get_media()
    if not isinstance(data, dict):
        raise ApiError(400, "zly_format", "Oczekiwano obiektu JSON.")
    return data


def account_json(a):
    return {"id": a["id"], "nazwa": a["nazwa"], "rola": a["rola"], "typ_podmiotu": a["typ_podmiotu"]}


def read_upload(req, exts=(".csv",), form=None):
    """-> (filename, bytes) of the multipart field "plik". Text fields named in `form` (a dict) are filled in."""
    length = req.content_length
    if length is not None and length > MAX_UPLOAD + 4096:
        raise ApiError(413, "plik_za_duzy", "Plik jest większy niż %d MB." % (MAX_UPLOAD // 2 ** 20))
    ctype = req.content_type or ""
    if not ctype.startswith("multipart/form-data"):
        raise ApiError(415, "zly_typ", "Wyślij plik CSV jako multipart/form-data w polu „plik”.")
    found = None
    try:
        for part in req.get_media():
            if part.name == "plik" and found is None:
                name = part.filename or ""
                if not name.lower().endswith(exts):
                    raise ApiError(415, "tylko_csv", "Przyjmujemy wyłącznie pliki CSV (UTF-8)." if exts == (".csv",)
                                   else "Przyjmujemy pliki: %s." % ", ".join(exts))
                data = part.get_data()
                if len(data) > MAX_UPLOAD:
                    raise ApiError(413, "plik_za_duzy", "Plik jest większy niż %d MB." % (MAX_UPLOAD // 2 ** 20))
                found = (name, data)
                if form is None:
                    return found
            elif form is not None and part.name in form:
                form[part.name] = part.get_text()
    except falcon.MediaMalformedError:
        raise ApiError(413, "plik_za_duzy", "Plik jest większy niż %d MB lub żądanie jest uszkodzone." % (MAX_UPLOAD // 2 ** 20))
    if found is None:
        raise ApiError(400, "brak_pliku", "Brakuje pola „plik” z plikiem CSV.")
    return found


# ---------- converter (public, nothing stored) ----------

CONVERTER_FILES = (".csv", ".geojson", ".json")


def converter_analyze(req, resp):
    name, data = read_upload(req, CONVERTER_FILES)
    try:
        resp.media = konwerter.analyze(data, name)
    except konwerter.ConverterError as ex:
        raise ApiError(422, "plik_nieczytelny", str(ex))


def converter_convert(req, resp):
    form = {"mapowanie": None, "stale": None}
    name, data = read_upload(req, CONVERTER_FILES, form)
    try:
        mapping = json.loads(form["mapowanie"] or "null")
        constants = json.loads(form["stale"] or "{}")
    except ValueError:
        raise ApiError(400, "zly_format", "Pola „mapowanie” i „stale” muszą zawierać obiekty JSON.")
    if not isinstance(mapping, dict) or not isinstance(constants, dict) or not all(
            isinstance(v, str) for v in list(mapping.values()) + list(constants.values())):
        raise ApiError(400, "zly_format", "Pole „mapowanie” musi być obiektem {kolumna: pole}, a „stale” obiektem {pole: wartość}.")
    try:
        text, report = konwerter.convert(data, name, mapping, constants)
    except konwerter.ConverterError as ex:
        raise ApiError(422, "zle_mapowanie", str(ex))
    base = re.sub(r"[^A-Za-z0-9_-]+", "-", os.path.splitext(os.path.basename(name))[0]).strip("-") or "plik"
    resp.media = {"nazwa_pliku": "%s-wykaz-aed.csv" % base, "plik_csv": text, "raport": report}


# ---------- submissions ----------

def process_submission(db, account, records, report, filename, dry_run):
    problems = report["problemy"]
    good = set(report["poprawne_wiersze"])
    total = report["podsumowanie"]["wiersze"]
    zg_id = None
    if not dry_run:
        zg_id = db.execute("INSERT INTO zgloszenia(konto_id,utworzono,plik,odpowiedz) VALUES(?,?,?,'')",
                           (account["id"], now(), filename)).lastrowid
    accepted, duplicates, seen = [], 0, set()
    for n, rec in enumerate(records, start=1):
        if n not in good:
            continue
        rec = clean(rec)
        key = norm_key(rec)
        if key in seen or db.execute("SELECT 1 FROM devices WHERE klucz=?", (key,)).fetchone():
            duplicates += 1
            continue
        seen.add(key)
        # Opaque random source id: nothing derived from the serial number may appear in public data.
        opaque = secrets.token_hex(6)
        rec_id = aed_standard.make_id("zgloszenie", opaque)
        rec.update(id_aed=rec_id, status="zgloszony", zrodlo="zgloszenie", zrodlo_id=opaque, licencja="CC0 1.0",
                   wprowadzajacy_typ=account["typ_podmiotu"], wprowadzajacy_nazwa=account["nazwa"],
                   data_aktualizacji=today().isoformat(), data_weryfikacji="", sposob_weryfikacji="")
        rec["kompletnosc"] = str(aed_standard.completeness(rec))
        accepted.append(rec)
    przyjete = []
    for rec in accepted:
        item = {"id_aed": rec["id_aed"], "producent": rec["producent"], "model": rec["model"],
                "numer_seryjny": rec["numer_seryjny"]}
        if not dry_run:
            db.execute(INSERT_SQL, device_row(rec, "zgloszenie", account["id"], zg_id))
            token = new_token(db, rec["id_aed"])
            item["naklejka_url"] = "/api/aed/urzadzenia/%s/naklejka.svg" % rec["id_aed"]
            item["link_aktywacyjny"] = activation_link(rec["id_aed"], token)
            queue_message(db, "aktywacja", rec["id_aed"], rec["dysponent_email"],
                          "Aktywuj urządzenie AED %s" % rec["id_aed"],
                          "Producent lub sprzedawca (%s) zgłosił do rejestru AED urządzenie %s %s, którym Państwo "
                          "zarządzają. Uzupełnij lokalizację i godziny dostępu, korzystając z linku. Link jest "
                          "przeznaczony wyłącznie dla zarządcy urządzenia."
                          % (account["nazwa"], rec["producent"], rec["model"]), item["link_aktywacyjny"])
        przyjete.append(item)
    s = report["podsumowanie"]
    out = {"id": zg_id, "utworzono": now(), "sucha_proba": dry_run,
           "podsumowanie": {"wiersze": total, "przyjete": len(przyjete), "odrzucone": total - len(good),
                            "bledy": s["bledy"], "ostrzezenia": s["ostrzezenia"], "duplikaty": duplicates},
           "problemy": problems, "przyjete": przyjete}
    if not dry_run:
        db.execute("UPDATE zgloszenia SET odpowiedz=? WHERE id=?", (json.dumps(out, ensure_ascii=False), zg_id))
        db.commit()
    return out


def submit_csv(dry_run):
    def handler(req, resp):
        account = need_account(req, "firma")
        name, data = read_upload(req)
        records, report = aed_standard.validate_csv(data, "sprzedaz")
        resp.media = process_submission(req.context.db, account, records, report, name, dry_run)
        resp.status = falcon.HTTP_200 if dry_run else falcon.HTTP_201
    return handler


def submit_one(req, resp):
    account = need_account(req, "firma")
    records = [clean(body(req))]
    report = aed_standard.validate_records(records, "sprzedaz")
    resp.media = process_submission(req.context.db, account, records, report, "formularz", False)
    resp.status = falcon.HTTP_201


def list_submissions(req, resp):
    account = need_account(req, "firma")
    rows = req.context.db.execute("SELECT odpowiedz FROM zgloszenia WHERE konto_id=? ORDER BY id DESC", (account["id"],))
    resp.media = {"dane": [json.loads(r[0]) for r in rows]}


# ---------- session / schema ----------

def login(req, resp):
    data = body(req)
    db = req.context.db
    row = db.execute("SELECT * FROM accounts WHERE email=?", (str(data.get("email", "")).strip().lower(),)).fetchone()
    salt = row["salt"] if row else b"\0" * 16
    ok = hmac.compare_digest(hash_password(str(data.get("haslo", "")), salt), row["pass_hash"] if row else b"x")
    if not (row and ok):
        raise ApiError(401, "zle_dane_logowania", "Niepoprawny adres e-mail lub hasło.")
    token = secrets.token_urlsafe(32)
    expires = (datetime.datetime.now() + datetime.timedelta(hours=SESSION_HOURS)).replace(microsecond=0).isoformat()
    db.execute("DELETE FROM sessions WHERE expires<?", (now(),))
    db.execute("INSERT INTO sessions(token_hash,account_id,expires) VALUES(?,?,?)", (sha(token), row["id"], expires))
    db.commit()
    resp.media = {"token": token, "konto": account_json(row)}


def whoami(req, resp):
    resp.media = account_json(need_account(req))


def schema(req, resp):
    resp.media = aed_standard.load_schema()


# ---------- devices ----------

def device_get(req, resp, id_aed):
    row = get_device(req.context.db, id_aed)
    rec = json.loads(row["data"])
    if manager_ok(req.context.db, id_aed, req.get_param("t")):
        resp.media = dict(rec, demo=bool(row["demo"]))
    elif req.get_param("t"):
        raise ApiError(403, "zly_token", "Link jest niepoprawny lub wygasł. Poproś o nowy.")
    elif row["dostep"] == "prywatny":
        raise ApiError(404, "nie_znaleziono", "Nie ma urządzenia o identyfikatorze %s." % id_aed)
    else:
        resp.media = dict(public(rec), demo=bool(row["demo"]))


STICKER_W = 360                # sticker width in user units; widened only if a long URL needs a bigger QR
STICKER_MARGIN = 20            # text must stay this far from both edges
STICKER_LOGO_PATH = os.environ.get("AED_STICKER_LOGO", os.path.join(HERE, "naklejka-logo.svg"))  # optional campaign logo
STICKER_LOGO_H = 50
STICKER_CAPTION = ("Zeskanuj kod QR", "i sprawdź lub zgłoś stan AED")  # two short lines, see test for the width rule
FONT = 'font-family="Arial,sans-serif" text-anchor="middle"'


def sticker(req, resp, id_aed):
    get_device(req.context.db, id_aed)
    qr = segno.make("%s/aed/qr/%s" % (BASE_URL.rstrip("/"), id_aed), error="m")
    scale = 7
    qr_w = qr.symbol_size(scale=scale, border=4)[0]  # border=4 modules is the quiet zone the QR spec requires
    w = max(STICKER_W, qr_w + 24)
    cx = w / 2
    # PLACEHOLDER for the campaign logo: empty group; filled with an <image> when STICKER_LOGO_PATH exists.
    logo = ""
    if os.path.exists(STICKER_LOGO_PATH):
        with open(STICKER_LOGO_PATH, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        logo = ('<image href="data:image/svg+xml;base64,%s" x="%d" y="16" width="%d" height="%d" '
                'preserveAspectRatio="xMidYMid meet"/>' % (data, STICKER_MARGIN, w - 2 * STICKER_MARGIN, STICKER_LOGO_H))
    top = 16 + STICKER_LOGO_H
    qr_y = top + 44
    id_y = qr_y + qr_w + 28
    cap_y = id_y + 30
    h = cap_y + 20 * len(STICKER_CAPTION) + 4
    inner = qr.svg_inline(scale=scale, border=4, dark="#000000", light="#ffffff").replace(
        "<svg ", '<svg x="%s" y="%d" ' % (cx - qr_w / 2, qr_y), 1)
    caption = "".join('<text x="%s" y="%d" %s font-size="15" fill="#222">%s</text>' % (cx, cap_y + 20 * i, FONT, line)
                      for i, line in enumerate(STICKER_CAPTION))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" '
           'aria-label="Naklejka AED %s">'
           '<rect x="3" y="3" width="%d" height="%d" rx="16" fill="#fff" stroke="#c8102e" stroke-width="6"/>'
           '<g id="miejsce-na-logo">%s</g>'
           '<text x="%s" y="%d" %s font-size="24" font-weight="700" fill="#c8102e">DEFIBRYLATOR AED</text>%s'
           '<text x="%s" y="%d" %s font-size="20" font-weight="700" fill="#000">%s</text>%s</svg>'
           % (w, h, w, h, id_aed, w - 6, h - 6, logo, cx, top + 30, FONT, inner, cx, id_y, FONT, id_aed, caption))
    resp.content_type = "image/svg+xml"
    resp.text = svg


def queue_pair(db, a_id, b_id, distance, similarity):
    """Add a pair to the review queue unless the ministry (or the queue) already knows it, in either order."""
    """-> 1 when the pair was added, 0 when already known."""
    if db.execute("SELECT 1 FROM duplicates WHERE (id_a=? AND id_b=?) OR (id_a=? AND id_b=?)",
                  (a_id, b_id, b_id, a_id)).fetchone():
        return 0
    db.execute("INSERT INTO duplicates(id_a,id_b,odleglosc_m,podobienstwo) VALUES(?,?,?,?)",
               (a_id, b_id, distance, similarity))
    return 1


OWNED_SQL = "origin IN ('zgloszenie','zarzadca') AND status!='wycofany'"  # submitted by a seller or confirmed by a manager


def coords(rec):
    lat, lon = to_float(rec.get("szerokosc_geograficzna")), to_float(rec.get("dlugosc_geograficzna"))
    return None if lat is None or lon is None else (lat, lon)


def nearby_box(lat, lon):
    """(min_lat, max_lat, min_lon, max_lon) containing every point within aed_standard.CANDIDATE_M, with 10% margin."""
    dlat = aed_standard.CANDIDATE_M * 1.1 / 111000.0
    dlon = dlat / max(math.cos(math.radians(lat)), 0.1)
    return lat - dlat, lat + dlat, lon - dlon, lon + dlon


def queue_matches(db, owned, imported):
    """Candidate duplicates (aed_standard.find_candidates) between submitted/confirmed devices and imported records
    go to the review queue, the submitted device as record A (the one kept). Nothing is merged automatically.
    -> number of pairs added to the queue."""
    # ponytail: O(owned x imported) box filter, fine for thousands of owned devices; grid both sides if it grows
    pts = [(p, r) for p, r in ((coords(r), r) for r in imported) if p]
    added = 0
    for rec in owned:
        p = coords(rec)
        if not p:
            continue
        y1, y2, x1, x2 = nearby_box(*p)
        near = [r for (lat, lon), r in pts if y1 <= lat <= y2 and x1 <= lon <= x2]
        for c in aed_standard.find_candidates(rec, near):
            added += queue_pair(db, rec["id_aed"], c["id_aed"], c["odleglosc_m"], c["podobienstwo"])
    return added


def enqueue_matches(db, rec):
    """A device that just got coordinates is compared with imported records nearby."""
    p = coords(rec)
    if not p:
        return
    rows = db.execute("SELECT data FROM devices WHERE origin='import' AND status!='wycofany'"
                      " AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?", nearby_box(*p)).fetchall()
    queue_matches(db, [rec], [json.loads(r[0]) for r in rows])


def apply_confirmation(db, id_aed, data, on=None):
    """Manager confirmation (shared by the endpoint and the demo seed). `on` = date of the confirmation."""
    on = (on or today()).isoformat()
    row = get_device(db, id_aed)
    if not manager_ok(db, id_aed, data.get("t")):
        raise ApiError(403, "zly_token", "Link jest niepoprawny lub wygasł. Poproś o nowy na adres e-mail dysponenta.")
    if row["status"] == "wycofany":  # a link issued before the withdrawal must not bring the record back
        raise ApiError(409, "wycofany", "Urządzenie zostało wycofane z rejestru; nie można go potwierdzić.")
    stan = data.get("stan")
    if stan not in ("sprawny", "problem"):
        raise ApiError(422, "zly_stan", "Pole „stan” musi mieć wartość „sprawny” albo „problem”.")
    uwagi = str(data.get("uwagi") or "").strip()[:2000]
    if stan == "problem" and not uwagi:
        raise ApiError(422, "brak_uwag", "Przy stanie „problem” opisz problem w polu „uwagi”.")
    rec = json.loads(row["data"])
    fields = CONFIRM_FIELDS
    if stan == "sprawny" and rec.get("licencja") == ODBL:
        # Takeover of a record known only from OpenStreetMap (CLAUDE.md rule 3): the manager's record starts empty,
        # so every published value (name and coordinates included) is the manager's own; only the link to OSM stays.
        # The id is kept, so the mapper keeps skipping the OSM record (origin != import) and no duplicate appears.
        linked = [x for x in rec.get("powiazane_zrodla", "").split(";") if x]
        opaque = secrets.token_hex(6)
        rec = dict({k: "" for k in aed_standard.field_names()}, id_aed=id_aed, zrodlo="zgloszenie", zrodlo_id=opaque,
                   licencja="CC0 1.0", wprowadzajacy_typ="dysponent", status="niepotwierdzony",
                   powiazane_zrodla=";".join(["%s:%s" % (rec["zrodlo"], rec["zrodlo_id"])] + linked))
        fields = CONFIRM_FIELDS + OWNER_FIELDS
    elif not rec.get("dysponent_email"):
        # No contact yet (e.g. a city dataset): the manager may add one, otherwise reminders skip the device.
        fields = CONFIRM_FIELDS + OWNER_FIELDS
    rec.update({k: v for k, v in clean(data).items() if k in fields and k in data})
    rec["data_aktualizacji"] = on
    if stan == "sprawny":
        rec.update(status="aktywny", data_weryfikacji=on, sposob_weryfikacji="qr")
    elif rec["status"] == "aktywny":
        rec["status"] = "niepotwierdzony"
    rec["kompletnosc"] = str(aed_standard.completeness(rec))
    report = aed_standard.validate_records([rec], "publikacja")
    errors = [p for p in report["problemy"] if p["poziom"] == "blad"]
    if stan == "problem":  # incomplete is fine, invalid is not: only type/enum/range errors of the supplied fields count
        supplied = {k for k in fields if k in data}
        if supplied & {"szerokosc_geograficzna", "dlugosc_geograficzna"}:
            supplied |= {"szerokosc_geograficzna", "dlugosc_geograficzna"}
        errors = [p for p in errors if p["kod"] not in REQUIRED_CODES and p["pole"] in supplied]
    if errors:
        raise ApiError(422, "niepoprawne_dane", "Uzupełnij dane, zanim potwierdzisz urządzenie." if stan == "sprawny"
                       else "Popraw błędne wartości w zgłoszeniu.",
                       {"problemy": report["problemy"] if stan == "sprawny" else errors})
    save_device(db, rec, origin="zarzadca", uwagi_zarzadcy=uwagi if stan == "problem" else None)
    enqueue_matches(db, rec)
    db.commit()
    return rec


def confirm(req, resp, id_aed):
    rec = apply_confirmation(req.context.db, id_aed, body(req))
    resp.media = dict({k: rec[k] for k in ("id_aed", "status", "data_weryfikacji", "sposob_weryfikacji", "kompletnosc")},
                      rekord=rec)


def signal(req, resp, id_aed):
    db = req.context.db
    data = body(req)
    row = get_device(db, id_aed)
    if row["dostep"] == "prywatny":
        raise ApiError(404, "nie_znaleziono", "Nie ma urządzenia o identyfikatorze %s." % id_aed)
    if data.get("typ") not in SIGNAL_TYPES:
        raise ApiError(422, "zly_typ", "Pole „typ” musi mieć wartość: %s." % ", ".join(SIGNAL_TYPES))
    lat, lon = to_float(data.get("szerokosc_geograficzna")), to_float(data.get("dlugosc_geograficzna"))
    uwagi = str(data.get("uwagi") or "").strip()[:1000]
    db.execute("INSERT INTO signals(id_aed,typ,lat,lon,uwagi,data) VALUES(?,?,?,?,?,?)",
               (id_aed, data["typ"], lat, lon, uwagi, now()))
    email = json.loads(row["data"]).get("dysponent_email")
    if email:
        queue_message(db, "sygnal", id_aed, email, "Zgłoszenie dotyczące urządzenia AED %s" % id_aed,
                      "Osoba postronna zgłosiła: %s. %s Sprawdź urządzenie i potwierdź dane." % (data["typ"], uwagi))
    db.commit()
    resp.status = falcon.HTTP_201
    resp.media = {"przyjeto": True}


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def issue_link(req, resp, id_aed):
    """Ministry: a manager link for a record already in the registry (e.g. known only from OSM or a city dataset),
    so its manager can confirm it and take it over. The link goes to the e-mail the ministry gives (never to a contact
    copied from the source) and is returned to the ministry as well."""
    need_account(req, "ministerstwo")
    db = req.context.db
    row = get_device(db, id_aed)
    if row["status"] == "wycofany":
        raise ApiError(409, "wycofany", "Urządzenie zostało wycofane z rejestru; nie można wystawić linku.")
    data = req.get_media(default_when_empty={})
    email = str((data if isinstance(data, dict) else {}).get("email") or "").strip()
    if email and not EMAIL_RE.match(email):
        raise ApiError(422, "zly_email", "Pole „email” musi być adresem e-mail (instytucjonalnym) zarządcy.")
    link = activation_link(id_aed, new_token(db, id_aed))
    if email:
        queue_message(db, "przejecie", id_aed, email, "Potwierdź urządzenie AED %s" % id_aed,
                      "Urządzenie AED, którym Państwo zarządzają, jest w rejestrze krajowym, ale nikt odpowiedzialny go "
                      "nie potwierdził. Podaj nazwę miejsca, położenie, godziny dostępu i kontakt, korzystając z linku. "
                      "Link jest przeznaczony wyłącznie dla zarządcy urządzenia.", link)
    db.commit()
    resp.status = falcon.HTTP_201
    resp.media = {"id_aed": id_aed, "link_aktywacyjny": link, "waznosc_dni": TOKEN_DAYS, "wyslano_na": email or None}


# ---------- registry ----------

def list_devices(req, resp):
    where, args = ["dostep != 'prywatny'"], []
    for param in ("status", "zrodlo", "dostep"):
        if req.get_param(param):
            where.append("%s=?" % param)
            args.append(req.get_param(param))
    q = (req.get_param("q") or "").strip().casefold()
    if q:
        where.append("szukaj LIKE ? ESCAPE '\\'")
        args.append("%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    page = max(req.get_param_as_int("strona") or 1, 1)
    size = min(max(req.get_param_as_int("na_stronie") or 50, 1), 200)
    cond = " AND ".join(where)
    db = req.context.db
    total = db.execute("SELECT COUNT(*) FROM devices WHERE " + cond, args).fetchone()[0]
    rows = db.execute("SELECT data, demo FROM devices WHERE %s ORDER BY id_aed LIMIT ? OFFSET ?" % cond,
                      args + [size, (page - 1) * size]).fetchall()
    resp.media = {"dane": [dict(public(json.loads(r[0])), demo=bool(r[1])) for r in rows], "razem": total, "strona": page, "na_stronie": size}


def geojson(req, resp):
    where, args = ["dostep != 'prywatny'", "lat IS NOT NULL", "lon IS NOT NULL"], []
    bbox = req.get_param("bbox")
    if bbox:
        try:
            x1, y1, x2, y2 = [float(v) for v in bbox.split(",")]
        except ValueError:
            raise ApiError(400, "zly_bbox", "Parametr bbox ma postać minLon,minLat,maxLon,maxLat.")
        where.append("lon BETWEEN ? AND ? AND lat BETWEEN ? AND ?")
        args += [x1, x2, y1, y2]
    rows = req.context.db.execute(
        "SELECT id_aed,nazwa,status,dostep,godziny,kompletnosc,zrodlo,lon,lat,demo FROM devices WHERE " + " AND ".join(where), args)
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r[7], r[8]]},
              "properties": {"id_aed": r[0], "nazwa": r[1], "status": r[2], "dostep": r[3], "godziny_dostepu": r[4],
                             "kompletnosc": r[5], "zrodlo": r[6], "demo": bool(r[9])}} for r in rows]
    resp.content_type = "application/geo+json"
    resp.text = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":"))


def stats(req, resp):
    db = req.context.db
    pub = "dostep != 'prywatny'"
    since = (today() - datetime.timedelta(days=90)).isoformat()
    total, avg = db.execute("SELECT COUNT(*), AVG(kompletnosc) FROM devices WHERE " + pub).fetchone()
    resp.media = {
        "razem": total, "srednia_kompletnosc": round(avg or 0, 1),
        "wg_statusu": dict(db.execute("SELECT status, COUNT(*) FROM devices WHERE %s GROUP BY status" % pub).fetchall()),
        "wg_zrodla": dict(db.execute("SELECT zrodlo, COUNT(*) FROM devices WHERE %s GROUP BY zrodlo" % pub).fetchall()),
        "dostawcy": db.execute("SELECT COUNT(DISTINCT konto_id) FROM devices WHERE konto_id IS NOT NULL").fetchone()[0],
        "hasla_demo_domyslne": demo_passwords_default(db),
        "potwierdzone_90_dni": db.execute(
            "SELECT COUNT(*) FROM devices WHERE %s AND origin!='import' AND data_weryfikacji>=?" % pub, (since,)).fetchone()[0],
        "ostatnie_uruchomienia": {col: (db.execute("SELECT MAX(start) FROM jobs WHERE %s IS NOT NULL" % col).fetchone()[0])
                                  for col in ("mapper", "przypomnienia")}}


def sellers(req, resp):
    rows = req.context.db.execute(
        "SELECT a.nazwa, a.typ_podmiotu, a.miejscowosc, a.lat, a.lon, COUNT(d.id_aed) n, AVG(d.kompletnosc) avg_k,"
        " AVG(d.status='aktywny') share FROM accounts a LEFT JOIN devices d ON d.konto_id=a.id"
        " WHERE a.rola='firma' GROUP BY a.id ORDER BY avg_k DESC")
    out = []
    for r in rows:
        avg, share = round(r["avg_k"] or 0, 1), round(r["share"] or 0, 2)
        out.append({"nazwa": r["nazwa"], "typ_podmiotu": r["typ_podmiotu"], "miejscowosc": r["miejscowosc"],
                    "szerokosc_geograficzna": r["lat"], "dlugosc_geograficzna": r["lon"], "liczba_urzadzen": r["n"],
                    "srednia_kompletnosc": avg, "udzial_aktywnych": share,
                    "odznaka": "tak" if r["n"] > 0 and avg >= BADGE_MIN_COMPLETENESS and share >= BADGE_MIN_ACTIVE_SHARE else "nie"})
    resp.media = {"dane": out, "progi": {"srednia_kompletnosc": BADGE_MIN_COMPLETENESS,
                                         "udzial_aktywnych": BADGE_MIN_ACTIVE_SHARE}}


def publication_csv(db):
    """-> (CSV bytes, exported records). Deterministic: same registry, same bytes."""
    # Private and fictional demo devices are dropped here; ODbL, validation and the rest are aed_standard's job.
    rows = db.execute("SELECT data FROM devices WHERE dostep != 'prywatny' AND demo=0 AND status != 'wycofany' ORDER BY id_aed")
    exported = [r for r in aed_standard.publication_export([json.loads(r[0]) for r in rows]) if r.get("dostep") != "prywatny"]
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=aed_standard.field_names(), extrasaction="ignore", lineterminator="\r\n")
    w.writeheader()
    w.writerows(exported)  # contacts and serial numbers are already blanked by publication_export
    return out.getvalue().encode("utf-8"), exported


def export_csv(req, resp):
    resp.content_type = "text/csv; charset=utf-8"
    resp.set_header("Content-Disposition", 'attachment; filename="aed_dane_gov_pl.csv"')
    resp.data = publication_csv(req.context.db)[0]


# ---------- harvester feed for dane.gov.pl (backend/mcod/harvester, XSD 1.13) ----------

HARVESTER_NS = "urn:otwarte-dane:harvester:1.13"
FEED_DESCRIPTION = (
    "Ogólnopolski zbiór defibrylatorów AED prowadzony przez Ministerstwo Cyfryzacji. Rekordy pochodzą od producentów "
    "i sprzedawców (konta firm), od zarządców urządzeń (potwierdzenie przez kod QR na naklejce) oraz z otwartych zbiorów "
    "samorządów, po ujednoliceniu do jednego standardu i deduplikacji. Jeden wiersz to jedno urządzenie; współrzędne "
    "WGS84 w kolumnach szerokosc_geograficzna i dlugosc_geograficzna. Zbiór nie zawiera danych osobowych, numerów "
    "seryjnych, urządzeń prywatnych ani rekordów znanych tylko z OpenStreetMap.")
RESOURCE_DESCRIPTION = (
    "Plik CSV (UTF-8, separator przecinek, daty RRRR-MM-DD) z rekordami spełniającymi profil publikacji standardu AED. "
    "Kolumna status mówi, czy zarządca potwierdził urządzenie (aktywny), a kompletnosc - jak pełny jest rekord (0-100).")


def harvester_xml_bytes(db):
    """XML for the portal's XML harvester. Its only input is the publication CSV, so it changes only when that does."""
    data, exported = publication_csv(db)
    base = BASE_URL.rstrip("/")
    # The portal re-downloads a resource file only when its link changes (resources/models.py:1287-1295, 1966),
    # so the link carries the content version.
    link = "%s/api/aed/eksport/dane-gov-pl.csv?wersja=%s" % (base, hashlib.md5(data).hexdigest()[:12])
    changed = max([max(r.get("data_aktualizacji") or "", r.get("data_weryfikacji") or "") for r in exported] or [""])

    def sub(parent, tag, text=None, **attrs):
        el = ET.SubElement(parent, tag, attrs)
        el.text = text
        return el

    def texts(parent, tag, pl, en=None):
        el = sub(parent, tag)
        sub(el, "polish", pl)
        if en:
            sub(el, "english", en)

    root = ET.Element("{%s}datasets" % HARVESTER_NS)
    ds = sub(root, "dataset", status="published")
    sub(ds, "extIdent", "aed-krajowy-rejestr")  # stable: an extIdent missing from the feed is deleted by the portal
    texts(ds, "title", "Krajowy rejestr AED", "National register of AED defibrillators")
    texts(ds, "description", FEED_DESCRIPTION)
    sub(ds, "url", base + "/aed")
    sub(ds, "updateFrequency", "daily")
    sub(sub(ds, "categories"), "category", "HEAL")
    cond = sub(ds, "conditions")  # source/modification = CC BY 4.0 in the portal (datasets/models.py:568-583)
    sub(cond, "source", "true")
    sub(cond, "modification", "true")
    res = sub(sub(ds, "resources"), "resource", status="published")
    sub(res, "extIdent", "aed-krajowy-rejestr-csv")
    sub(res, "url", link)
    texts(res, "title", "Defibrylatory AED - zbiór krajowy (CSV)", "AED defibrillators - national dataset (CSV)")
    texts(res, "description", RESOURCE_DESCRIPTION)
    sub(res, "availability", "local")
    if changed:
        sub(res, "dataDate", changed)
        sub(res, "lastUpdateDate", changed + "T00:00:00")
        sub(ds, "lastUpdateDate", changed + "T00:00:00")
    tags = sub(ds, "tags")
    for lang, name in (("pl", "AED"), ("pl", "defibrylator"), ("pl", "pierwsza pomoc"), ("pl", "zdrowie"),
                       ("en", "AED"), ("en", "defibrillator")):
        sub(tags, "tag", name, lang=lang)
    ET.register_namespace("p", HARVESTER_NS)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def export_xml(req, resp):
    resp.content_type = "application/xml; charset=utf-8"  # harvester/utils.py:191-197 needs text/xml or application/xml
    resp.data = harvester_xml_bytes(req.context.db)


def export_xml_md5(req, resp):
    # harvester/utils.py:168-179: the sum lives at the XML address with .xml replaced by .md5, body = 32 hex digits
    resp.content_type = "text/plain; charset=utf-8"
    resp.text = hashlib.md5(harvester_xml_bytes(req.context.db)).hexdigest()


# ---------- ministry panel ----------

def list_duplicates(req, resp):
    need_account(req, "ministerstwo")
    db = req.context.db
    out = []
    for d in db.execute("SELECT * FROM duplicates WHERE decyzja IS NULL ORDER BY podobienstwo DESC, id"):
        a, b = (db.execute("SELECT data FROM devices WHERE id_aed=?", (d[k],)).fetchone() for k in ("id_a", "id_b"))
        out.append({"id": d["id"], "rekord_a": json.loads(a[0]), "rekord_b": json.loads(b[0]),
                    "odleglosc_m": d["odleglosc_m"], "podobienstwo": d["podobienstwo"]})
    resp.media = {"dane": out, "razem": len(out)}


def decide_duplicate(req, resp, dup_id):
    need_account(req, "ministerstwo")
    db = req.context.db
    decision = body(req).get("decyzja")
    if decision not in ("polacz", "rozdziel"):
        raise ApiError(422, "zla_decyzja", "Pole „decyzja” musi mieć wartość „polacz” albo „rozdziel”.")
    d = db.execute("SELECT * FROM duplicates WHERE id=?", (dup_id,)).fetchone()
    if not d:
        raise ApiError(404, "nie_znaleziono", "Nie ma takiej pary do przeglądu.")
    if d["decyzja"]:
        raise ApiError(409, "juz_rozstrzygniete", "Ta para została już rozstrzygnięta.")
    if decision == "polacz":  # keep record A, retire B and remember the link
        a = json.loads(get_device(db, d["id_a"])["data"])
        b = json.loads(get_device(db, d["id_b"])["data"])
        a["powiazane_zrodla"] = ";".join(x for x in (a.get("powiazane_zrodla"), d["id_b"]) if x)
        b["status"] = "wycofany"
        save_device(db, a)
        save_device(db, b, origin="scalony")
    db.execute("UPDATE duplicates SET decyzja=? WHERE id=?", (decision, dup_id))
    db.commit()
    resp.media = {"id": dup_id, "decyzja": decision}


def list_messages(req, resp):
    need_account(req, "ministerstwo")
    rows = req.context.db.execute("SELECT * FROM messages ORDER BY id DESC LIMIT ?",
                                  (min(req.get_param_as_int("limit") or 200, 1000),)).fetchall()
    resp.media = {"dane": [{"id": r["id"], "rodzaj": r["rodzaj"], "id_aed": r["id_aed"], "odbiorca": r["odbiorca"],
                            "temat": r["temat"], "tresc": r["tresc"], "link": r["link"], "data": r["data"]} for r in rows],
                  "razem": req.context.db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]}


def reminders(db):
    t = today()
    day = lambda n: (t + datetime.timedelta(days=n)).isoformat()  # noqa: E731
    counts = {"nieaktualne": 0, "prosby_o_potwierdzenie": 0, "przypomnienia_terminow": 0}
    db.execute("DELETE FROM tokens WHERE wygasa<?", (now(),))
    # 1) stale: active but not confirmed for 12 months
    counts["nieaktualne"] = db.execute(
        "UPDATE devices SET status='nieaktualny', data=json_set(data,'$.status','nieaktualny')"
        " WHERE status='aktywny' AND data_weryfikacji!='' AND data_weryfikacji<?", (day(-STALE_AFTER_DAYS),)).rowcount

    def sent_recently(kind, id_aed):
        return db.execute("SELECT 1 FROM messages WHERE rodzaj=? AND id_aed=? AND data>=?",
                          (kind, id_aed, day(-RESEND_GAP_DAYS))).fetchone()

    for row in db.execute("SELECT * FROM devices WHERE status IN ('aktywny','zgloszony','nieaktualny','niepotwierdzony')"
                          " AND dostep != 'prywatny'").fetchall():
        rec = json.loads(row["data"])
        email = rec.get("dysponent_email")
        if not email:
            continue
        last = rec.get("data_weryfikacji") or rec.get("data_aktualizacji") or ""
        if row["status"] != "niepotwierdzony" and last and last < day(-REQUEST_AFTER_DAYS) \
                and not sent_recently("prosba", row["id_aed"]):
            link = activation_link(row["id_aed"], new_token(db, row["id_aed"]))
            queue_message(db, "prosba", row["id_aed"], email, "Potwierdź dane urządzenia AED %s" % row["id_aed"],
                          "Od ponad 6 miesięcy nie potwierdzono danych urządzenia. Potwierdź lokalizację, godziny dostępu "
                          "i stan urządzenia, baterii oraz elektrod.", link)
            counts["prosby_o_potwierdzenie"] += 1
        for field, what in (("data_waznosci_baterii", "baterii"), ("data_waznosci_elektrod", "elektrod")):
            if rec.get(field) and rec[field] <= day(EXPIRY_WARNING_DAYS) and not sent_recently("termin_" + field, row["id_aed"]):
                link = activation_link(row["id_aed"], new_token(db, row["id_aed"]))
                queue_message(db, "termin_" + field, row["id_aed"], email,
                              "Zbliża się termin ważności %s w urządzeniu AED %s" % (what, row["id_aed"]),
                              "Termin ważności %s: %s. Wymień element i potwierdź dane." % (what, rec[field]), link)
                counts["przypomnienia_terminow"] += 1
    db.commit()
    return counts


# ---------- cyclic jobs ----------

JOB_LOCK = threading.Lock()  # one job at a time: a manual run and a scheduled run never overlap
DOWNLOAD_SCRIPT = os.path.join(ROOT, "scripts", "download_aed_data.py")
DOWNLOAD_TIMEOUT = 600


def _short_error(text):
    """Polish one-liner for a raw error text from the download script (no exception details)."""
    name = re.split(r"[ (:]", text.strip(), maxsplit=1)[0] or "źródło"
    low = text.lower()
    if any(k in low for k in ("certificate", "urlopen", "timed out", "name or service", "connection", "network")):
        why = "brak połączenia lub błąd certyfikatu"
    elif "token" in low:
        why = "brak tokenu dostępu"
    elif "html" in low:
        why = "adres wskazuje stronę WWW, nie dane"
    else:
        why = "błąd pobierania"
    return "Źródło %s: %s. Użyto zapisanej migawki." % (name, why)


def refresh_sources():
    """Run scripts/download_aed_data.py without ever losing the snapshot on disk.

    The script rewrites manifest.json with only the files it downloaded; entries of the old manifest that are
    missing there are kept (their data files are still on disk) and the merged manifest is written back.
    Returns (what was refreshed or None, [Polish error texts]); never raises.
    """
    if not os.path.exists(DOWNLOAD_SCRIPT):
        return None, []
    if os.path.realpath(RAW_DIR) != os.path.realpath(SCRIPT_RAW_DIR):
        return None, ["Odświeżanie źródeł wyłączone: skrypt pobierania zapisuje w datasets/raw, a AED_RAW_DIR wskazuje inny katalog."]
    path = os.path.join(RAW_DIR, "manifest.json")
    try:
        with open(path, "rb") as f:
            old_bytes = f.read()
        old = json.loads(old_bytes)["files"]
    except (OSError, ValueError, KeyError):
        old_bytes, old = None, []

    def restore():  # never raises: a read-only snapshot must not stop the cycle
        try:
            if old_bytes is not None:
                with open(path, "wb") as f:
                    f.write(old_bytes)
        except OSError:
            return False
        return True

    try:
        r = subprocess.run([sys.executable, DOWNLOAD_SCRIPT], cwd=ROOT, capture_output=True, text=True,
                           timeout=DOWNLOAD_TIMEOUT)
        if r.returncode != 0:
            restore()
            return None, ["Pobieranie źródeł zakończyło się błędem (kod %d). Użyto zapisanej migawki." % r.returncode]
        with open(path, encoding="utf-8") as f:
            new = json.load(f)
        fresh = {e["file"] for e in new["files"]}
        merged = new["files"] + [e for e in old if e["file"] not in fresh]
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dict(new, files=merged), f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception as ex:  # timeout, cannot start, unreadable manifest, ...
        msg = "Nie udało się odświeżyć źródeł (%s). Użyto zapisanej migawki." % type(ex).__name__
        if not restore():
            msg += " Nie udało się przywrócić manifestu (katalog tylko do odczytu?)."
        return None, [msg]
    errors = [_short_error(e) for e in new.get("errors", [])]
    if len(fresh) == len(merged):
        done = "Odświeżono wszystkie źródła (%d plików)" % len(merged)
    else:
        done = "Odświeżono %d z %d plików źródłowych; pozostałe z zapisanej migawki" % (len(fresh), len(merged))
    return done, errors


def run_job(db, trigger, kind, blocking=True):
    """kind: cykl (download + mapper + reminders) | mapper | przypomnienia. Records the run in `jobs`; returns the row dict."""
    if not JOB_LOCK.acquire(blocking):
        raise ApiError(409, "zadanie_trwa", "Inne zadanie jest właśnie wykonywane. Spróbuj za chwilę.")
    try:
        start, refreshed, mapper, remind, errors = now(), None, None, None, []
        if kind == "cykl":
            try:
                refreshed, errors = refresh_sources()
            except Exception as ex:  # refresh_sources should not raise; the cycle must survive anyway
                refreshed, errors = None, ["Odświeżanie źródeł nie powiodło się (%s). Użyto zapisanej migawki." % type(ex).__name__]
        for name, fn, label in (("mapper", lambda: import_registry(db), "Mapper"), ("przypomnienia", lambda: reminders(db), "Przypomnienia")):
            if kind not in ("cykl", name):
                continue
            try:
                result = fn()
                if isinstance(result, dict):
                    errors.extend(result.pop("bledy_zrodel", []))
                    if "ostrzezenie" in result:
                        errors.append(result.pop("ostrzezenie"))
                db.commit()
                mapper, remind = (result, remind) if name == "mapper" else (mapper, result)
            except Exception as ex:
                db.rollback()
                traceback.print_exception(type(ex), ex, ex.__traceback__, file=sys.stderr)
                errors.append("%s: nie udało się zakończyć zadania (%s)." % (label, type(ex).__name__))
        j = lambda v: None if v is None else json.dumps(v)  # noqa: E731
        job_id = db.execute("INSERT INTO jobs(start,koniec,wyzwalacz,rodzaj,odswiezono,mapper,przypomnienia,bledy)"
                            " VALUES(?,?,?,?,?,?,?,?)", (start, now(), trigger, kind, refreshed, j(mapper), j(remind),
                                                         json.dumps(errors, ensure_ascii=False))).lastrowid
        db.commit()
        return job_json(db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())
    finally:
        JOB_LOCK.release()


def job_json(r):
    load = lambda v: None if v is None else json.loads(v)  # noqa: E731
    return {"id": r["id"], "start": r["start"], "koniec": r["koniec"], "wyzwalacz": r["wyzwalacz"], "rodzaj": r["rodzaj"],
            "odswiezono": r["odswiezono"], "mapper": load(r["mapper"]), "przypomnienia": load(r["przypomnienia"]),
            "bledy": json.loads(r["bledy"])}


def manual_job(kind):
    def handler(req, resp):
        need_account(req, "ministerstwo")
        job = run_job(req.context.db, "ministerstwo", kind, blocking=False)
        result = job[kind]
        if result is None:
            raise ApiError(500, "zadanie_nieudane", job["bledy"][0])
        resp.media = result
    return handler


def list_jobs(req, resp):
    need_account(req, "ministerstwo")
    rows = req.context.db.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 20").fetchall()
    resp.media = {"dane": [job_json(r) for r in rows]}


def start_scheduler(db_path, hours):
    """Daemon thread running the full cycle every `hours` hours (0 = disabled). Uses its own connection."""
    if hours <= 0:
        return None

    def loop():
        db = sqlite3.connect(db_path, timeout=30)
        db.row_factory = sqlite3.Row
        while True:
            threading.Event().wait(hours * 3600)
            try:
                run_job(db, "harmonogram", "cykl")
            except Exception as ex:  # keep the thread alive whatever happens
                traceback.print_exception(type(ex), ex, ex.__traceback__, file=sys.stderr)

    t = threading.Thread(target=loop, name="aed-scheduler", daemon=True)
    t.start()
    return t


# ---------- app ----------

class Db:
    def __init__(self, conn):
        self.conn = conn

    def process_request(self, req, resp):
        req.context.db = self.conn


def route(app, path, **methods):
    res = type("Res", (), {"on_" + m: (lambda f: lambda self, req, resp, **kw: f(req, resp, **kw))(fn)
                           for m, fn in methods.items()})()
    app.add_route("/api/aed" + path, res)


def db_file(db_path=None):
    return db_path or os.environ.get("AED_DB", DEFAULT_DB)


def open_db(db_path=None, with_registry=True, demo=False):
    """Open, migrate and seed the database. The caller owns the connection and closes it."""
    conn = sqlite3.connect(db_file(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    migrate(conn)
    seed(conn, with_registry)
    if demo:
        demo_seed(conn)
    return conn


def create_app(db_path=None, with_registry=True, demo=False):
    return build_app(open_db(db_path, with_registry, demo))


def build_app(conn):
    app = falcon.App(middleware=[Db(conn), falcon.CORSMiddleware(allow_origins=CORS_ORIGINS)])
    parse = app.req_options.media_handlers[falcon.MEDIA_MULTIPART].parse_options
    parse.max_body_part_buffer_size = MAX_UPLOAD + 1

    def on_api_error(req, resp, ex, params):
        resp.status = ex.status
        resp.media = {"blad": dict({"kod": ex.kod, "komunikat": ex.komunikat}, **ex.extra)}

    def on_http_error(req, resp, ex, params):
        resp.status = ex.status
        resp.media = {"blad": {"kod": "http_%d" % ex.status_code, "komunikat": ex.title or "Błąd żądania."}}

    def on_crash(req, resp, ex, params):
        traceback.print_exception(type(ex), ex, ex.__traceback__, file=sys.stderr)  # details go to the log, never to the client
        resp.status = falcon.HTTP_500
        resp.media = {"blad": {"kod": "blad_serwera", "komunikat": "Wystąpił błąd serwera. Spróbuj ponownie później."}}

    app.add_error_handler(Exception, on_crash)  # later handlers take precedence over earlier ones
    app.add_error_handler(falcon.HTTPError, on_http_error)
    app.add_error_handler(ApiError, on_api_error)

    route(app, "/sesja", post=login, get=whoami)
    route(app, "/schemat", get=schema)
    route(app, "/zgloszenia", post=submit_csv(False), get=list_submissions)
    route(app, "/zgloszenia/sprawdz", post=submit_csv(True))
    route(app, "/urzadzenia", get=list_devices, post=submit_one)
    route(app, "/urzadzenia.geojson", get=geojson)
    route(app, "/urzadzenia/{id_aed}", get=device_get)
    route(app, "/urzadzenia/{id_aed}/naklejka.svg", get=sticker)
    route(app, "/urzadzenia/{id_aed}/potwierdzenie", post=confirm)
    route(app, "/urzadzenia/{id_aed}/sygnal", post=signal)
    route(app, "/urzadzenia/{id_aed}/link-aktywacyjny", post=issue_link)
    route(app, "/statystyki", get=stats)
    route(app, "/sprzedawcy", get=sellers)
    route(app, "/eksport/dane-gov-pl.csv", get=export_csv, head=export_csv)
    route(app, "/eksport/dane-gov-pl.xml", get=export_xml, head=export_xml)  # the harvester sends HEAD first
    route(app, "/eksport/dane-gov-pl.md5", get=export_xml_md5, head=export_xml_md5)
    route(app, "/duplikaty", get=list_duplicates)
    route(app, "/duplikaty/{dup_id:int}", post=decide_duplicate)
    route(app, "/wiadomosci", get=list_messages)
    route(app, "/przypomnienia/uruchom", post=manual_job("przypomnienia"))
    route(app, "/mapper/uruchom", post=manual_job("mapper"))
    route(app, "/zadania", get=list_jobs)
    route(app, "/konwerter/analiza", post=converter_analyze)
    route(app, "/konwerter/konwersja", post=converter_convert)
    return app
