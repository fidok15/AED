"""AED service: Falcon + SQLite implementation of docs/api-aed.md.

All validation and registry logic lives in aed_standard; this module only stores, authorises and routes.
"""
import csv
import datetime
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import threading
import traceback

import falcon
import segno

import aed_standard

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW_DIR = os.path.join(ROOT, "datasets", "raw")
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
RESEND_GAP_DAYS = 30       # do not repeat the same kind of message for a device within this gap

HIDDEN_PUBLIC = ("dysponent_email", "dysponent_telefon", "numer_seryjny")
CONFIRM_FIELDS = ("nazwa", "szerokosc_geograficzna", "dlugosc_geograficzna", "miejscowosc", "cecha_ulicy",
                  "nazwa_ulicy", "nr_budynku", "nr_lokalu", "kod_pocztowy", "opis_lokalizacji", "wewnatrz_budynku",
                  "dostep", "godziny_dostepu", "godziny_dostepu_opis")
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
                     "godziny=?,kompletnosc=?,data_weryfikacji=?,lat=?,lon=? WHERE id_aed=? AND origin='import'")


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
    token = secrets.token_urlsafe(24)
    db.execute("UPDATE devices SET token_hash=? WHERE id_aed=?", (sha(token), id_aed))
    return token


def manager_ok(row, token):
    return bool(token) and bool(row["token_hash"]) and hmac.compare_digest(row["token_hash"], sha(str(token)))


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
    added, changed, inserts, updates = 0, 0, [], []
    for rec in records:
        rec = clean(rec)
        if rec["id_aed"] not in origins:
            inserts.append(device_row(rec, "import"))
            added += 1
        elif rec["id_aed"] in old and old[rec["id_aed"]] != json.dumps(rec, ensure_ascii=False):
            r = device_row(rec, "import")
            updates.append(r[1:2] + r[7:] + (rec["id_aed"],))
            changed += 1
    db.executemany(INSERT_SQL, inserts)
    db.executemany(IMPORT_UPDATE_SQL, updates)
    known = set(origins) | {r[0] for r in inserts}
    for p in pairs:
        if p["id_aed_a"] in known and p["id_aed_b"] in known:
            db.execute("INSERT OR IGNORE INTO duplicates(id_a,id_b,odleglosc_m,podobienstwo) VALUES(?,?,?,?)",
                       (p["id_aed_a"], p["id_aed_b"], p.get("odleglosc_m"), p.get("podobienstwo")))
    merged = int(report["polaczenia"]["razem"])
    return {"dodano": added, "zmieniono": changed, "polaczono": merged, "do_przegladu": len(pairs)}


DEMO_ACCOUNTS = [  # email, password, name, role, type, city, lat, lon
    ("ministerstwo@aed.example", "ministerstwo-demo", "Ministerstwo Cyfryzacji (konto demo)", "ministerstwo",
     "ministerstwo", "Warszawa", 52.2297, 21.0122),
    ("pulsar@aed.example", "pulsar-demo", "Pulsar Medical Sp. z o.o. (firma fikcyjna)", "firma", "producent",
     "Gdańsk", 54.3520, 18.6466),
    ("serwis@aed.example", "serwis-demo", "Serwis Rytm Sp. z o.o. (firma fikcyjna)", "firma", "sprzedawca",
     "Poznań", 52.4064, 16.9252),
]


def seed(db, with_registry=True):
    if not db.execute("SELECT 1 FROM accounts LIMIT 1").fetchone():
        for email, pw, name, rola, typ, city, lat, lon in DEMO_ACCOUNTS:
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


def read_upload(req):
    length = req.content_length
    if length is not None and length > MAX_UPLOAD + 4096:
        raise ApiError(413, "plik_za_duzy", "Plik jest większy niż %d MB." % (MAX_UPLOAD // 2 ** 20))
    ctype = req.content_type or ""
    if not ctype.startswith("multipart/form-data"):
        raise ApiError(415, "zly_typ", "Wyślij plik CSV jako multipart/form-data w polu „plik”.")
    try:
        for part in req.get_media():
            if part.name == "plik":
                name = part.filename or ""
                if not name.lower().endswith(".csv"):
                    raise ApiError(415, "tylko_csv", "Przyjmujemy wyłącznie pliki CSV (UTF-8).")
                data = part.get_data()
                if len(data) > MAX_UPLOAD:
                    raise ApiError(413, "plik_za_duzy", "Plik jest większy niż %d MB." % (MAX_UPLOAD // 2 ** 20))
                return name, data
    except falcon.MediaMalformedError:
        raise ApiError(413, "plik_za_duzy", "Plik jest większy niż %d MB lub żądanie jest uszkodzone." % (MAX_UPLOAD // 2 ** 20))
    raise ApiError(400, "brak_pliku", "Brakuje pola „plik” z plikiem CSV.")


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
        rec_id = aed_standard.make_id("zgloszenie", key)
        rec.update(id_aed=rec_id, status="zgloszony", zrodlo="zgloszenie", zrodlo_id=key, licencja="CC0 1.0",
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
    if manager_ok(row, req.get_param("t")):
        resp.media = rec
    elif req.get_param("t"):
        raise ApiError(403, "zly_token", "Link jest niepoprawny lub wygasł. Poproś o nowy.")
    elif row["dostep"] == "prywatny":
        raise ApiError(404, "nie_znaleziono", "Nie ma urządzenia o identyfikatorze %s." % id_aed)
    else:
        resp.media = public(rec)


def sticker(req, resp, id_aed):
    get_device(req.context.db, id_aed)
    qr = segno.make("%s/aed/qr/%s" % (BASE_URL.rstrip("/"), id_aed), error="m")
    inner = qr.svg_inline(scale=8, border=2, dark="#000000", light="#ffffff").replace("<svg ", '<svg x="20" y="70" ', 1)
    w = (qr.symbol_size(scale=8, border=2)[0])
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" '
           'aria-label="Naklejka AED %s">'
           '<rect width="100%%" height="100%%" rx="16" fill="#fff" stroke="#c8102e" stroke-width="6"/>'
           '<text x="50%%" y="44" text-anchor="middle" font-family="Arial,sans-serif" font-size="28" font-weight="700" '
           'fill="#c8102e">DEFIBRYLATOR AED</text>%s'
           '<text x="50%%" y="%d" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" fill="#000">%s</text>'
           '<text x="50%%" y="%d" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" fill="#333">'
           'Zeskanuj kod, aby sprawdzić lub zgłosić stan urządzenia</text></svg>'
           % (w + 40, w + 150, w + 40, w + 150, id_aed, inner, w + 108, id_aed, w + 134))
    resp.content_type = "image/svg+xml"
    resp.text = svg


def apply_confirmation(db, id_aed, data, on=None):
    """Manager confirmation (shared by the endpoint and the demo seed). `on` = date of the confirmation."""
    on = (on or today()).isoformat()
    row = get_device(db, id_aed)
    if not manager_ok(row, data.get("t")):
        raise ApiError(403, "zly_token", "Link jest niepoprawny lub wygasł. Poproś o nowy na adres e-mail dysponenta.")
    stan = data.get("stan")
    if stan not in ("sprawny", "problem"):
        raise ApiError(422, "zly_stan", "Pole „stan” musi mieć wartość „sprawny” albo „problem”.")
    uwagi = str(data.get("uwagi") or "").strip()[:2000]
    if stan == "problem" and not uwagi:
        raise ApiError(422, "brak_uwag", "Przy stanie „problem” opisz problem w polu „uwagi”.")
    rec = json.loads(row["data"])
    rec.update({k: v for k, v in clean(data).items() if k in CONFIRM_FIELDS and k in data})
    rec["data_aktualizacji"] = on
    if stan == "sprawny":
        rec.update(status="aktywny", data_weryfikacji=on, sposob_weryfikacji="qr")
    elif rec["status"] == "aktywny":
        rec["status"] = "niepotwierdzony"
    rec["kompletnosc"] = str(aed_standard.completeness(rec))
    if stan == "sprawny":
        report = aed_standard.validate_records([rec], "publikacja")
        errors = [p for p in report["problemy"] if p["poziom"] == "blad"]
        if errors:
            raise ApiError(422, "niepoprawne_dane", "Uzupełnij dane, zanim potwierdzisz urządzenie.",
                           {"problemy": report["problemy"]})
    save_device(db, rec, origin="zarzadca", uwagi_zarzadcy=uwagi if stan == "problem" else None)
    db.commit()
    return rec


def confirm(req, resp, id_aed):
    rec = apply_confirmation(req.context.db, id_aed, body(req))
    resp.media = {k: rec[k] for k in ("id_aed", "status", "data_weryfikacji", "sposob_weryfikacji", "kompletnosc")} | {
        "rekord": rec}


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
    rows = db.execute("SELECT data FROM devices WHERE %s ORDER BY id_aed LIMIT ? OFFSET ?" % cond,
                      args + [size, (page - 1) * size]).fetchall()
    resp.media = {"dane": [public(json.loads(r[0])) for r in rows], "razem": total, "strona": page, "na_stronie": size}


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
        "SELECT id_aed,nazwa,status,dostep,godziny,kompletnosc,zrodlo,lon,lat FROM devices WHERE " + " AND ".join(where), args)
    feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [r[7], r[8]]},
              "properties": {"id_aed": r[0], "nazwa": r[1], "status": r[2], "dostep": r[3], "godziny_dostepu": r[4],
                             "kompletnosc": r[5], "zrodlo": r[6]}} for r in rows]
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


def export_csv(req, resp):
    # Private and fictional demo devices are dropped here; ODbL, validation and the rest are aed_standard's job.
    rows = req.context.db.execute("SELECT data FROM devices WHERE dostep != 'prywatny' AND demo=0")
    exported = aed_standard.publication_export([json.loads(r[0]) for r in rows])
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=aed_standard.field_names(), extrasaction="ignore", lineterminator="\r\n")
    w.writeheader()
    w.writerows(dict(r, **{k: "" for k in HIDDEN_PUBLIC}) for r in exported if r.get("dostep") != "prywatny")
    resp.content_type = "text/csv; charset=utf-8"
    resp.set_header("Content-Disposition", 'attachment; filename="aed_dane_gov_pl.csv"')
    resp.data = out.getvalue().encode("utf-8")


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
    path = os.path.join(RAW_DIR, "manifest.json")
    try:
        with open(path, "rb") as f:
            old_bytes = f.read()
        old = json.loads(old_bytes)["files"]
    except (OSError, ValueError, KeyError):
        old_bytes, old = None, []

    def restore():
        if old_bytes is not None:
            with open(path, "wb") as f:
                f.write(old_bytes)

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
        restore()
        return None, ["Nie udało się odświeżyć źródeł (%s). Użyto zapisanej migawki." % type(ex).__name__]
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
            refreshed, errors = refresh_sources()
        for name, fn, label in (("mapper", lambda: import_registry(db), "Mapper"), ("przypomnienia", lambda: reminders(db), "Przypomnienia")):
            if kind not in ("cykl", name):
                continue
            try:
                result = fn()
                db.commit()
                mapper, remind = (result, remind) if name == "mapper" else (mapper, result)
            except Exception as ex:
                db.rollback()
                traceback.print_exception(ex, file=sys.stderr)
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
                traceback.print_exception(ex, file=sys.stderr)

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


def create_app(db_path=None, with_registry=True, demo=False):
    conn = sqlite3.connect(db_file(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    migrate(conn)
    seed(conn, with_registry)
    if demo:
        demo_seed(conn)

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
        traceback.print_exception(ex, file=sys.stderr)  # details go to the log, never to the client
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
    route(app, "/statystyki", get=stats)
    route(app, "/sprzedawcy", get=sellers)
    route(app, "/eksport/dane-gov-pl.csv", get=export_csv)
    route(app, "/duplikaty", get=list_duplicates)
    route(app, "/duplikaty/{dup_id:int}", post=decide_duplicate)
    route(app, "/wiadomosci", get=list_messages)
    route(app, "/przypomnienia/uruchom", post=manual_job("przypomnienia"))
    route(app, "/mapper/uruchom", post=manual_job("mapper"))
    route(app, "/zadania", get=list_jobs)
    return app
