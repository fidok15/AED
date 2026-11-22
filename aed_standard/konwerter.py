"""Converter: a provider's own AED file (any column layout, CSV or GeoJSON) -> a list (wykaz) in the standard.

Two steps, both in memory (nothing is stored):
    analyze(data, filename)                       -> columns, sample rows, proposed mapping column -> target
    convert(data, filename, mapping, constants)   -> CSV text in the standard + Polish validation report

The mapping is turned into a registry entry like those in sources.json and run through the same generic
mapper (sources.map_rows) and the same check as the portal (wykaz.read_wykaz). Pure Python 3.8.
"""
import codecs
import csv
import json
import re
from collections import Counter

from . import schema as S
from .build import publication_reasons, to_csv
from .registry import REGISTRY_PATH, load_registry
from .sources import map_rows, parse_csv, parse_geojson
from .validate import EMAIL_RE, LAT, LON, WARNING, issue
from .wykaz import read_wykaz

ADDRESS = "_adres"        # target: whole address in one column, split by sources.parse_address
GEOM_LAT, GEOM_LON = "geometria: szerokość", "geometria: długość"   # pseudo-columns of a GeoJSON point
# zrodlo_id is the provider's own row id; the other system fields are filled by the portal (wykaz.read_wykaz).
TARGETS = [ADDRESS, "zrodlo_id"] + [f["name"] for f in S.FIELDS if f.get("wypelnia") != "system"] + ["data_weryfikacji"]
CONSTANT_TARGETS = [t for t in TARGETS if t not in (ADDRESS, "zrodlo_id", LAT, LON)]
TARGET_TITLES = dict({ADDRESS: "Adres w jednym polu (ulica, numer, kod, miejscowość)",
                      "zrodlo_id": "Identyfikator w Twoim pliku"},
                     **{f["name"]: f["title"] for f in S.FIELDS})

# Header words not found in schema.json or sources.json. Normalised as in _norm().
SYNONYMS = {
    "lat": LAT, "latitude": LAT, "szerokosc": LAT, "y": LAT,
    "lon": LON, "lng": LON, "long": LON, "longitude": LON, "dlugosc": LON, "x": LON,
    "miasto": "miejscowosc", "gmina": "miejscowosc", "city": "miejscowosc",
    "ulica": "nazwa_ulicy", "street": "nazwa_ulicy", "numer domu": "nr_budynku", "nr domu": "nr_budynku",
    "kod": "kod_pocztowy", "postcode": "kod_pocztowy", "adres": ADDRESS, "address": ADDRESS,
    "id": "zrodlo_id", "lp": "zrodlo_id", "numer id": "zrodlo_id",
    "email": "dysponent_email", "e mail": "dysponent_email", "telefon": "dysponent_telefon", "phone": "dysponent_telefon",
    "nazwa obiektu": "nazwa", "obiekt": "nazwa", "miejsce": "nazwa", "name": "nazwa",
    "godziny": "godziny_dostepu", "godziny otwarcia": "godziny_dostepu", "opis": "opis_lokalizacji",
    "producent urzadzenia": "producent", "model urzadzenia": "model", "nr seryjny": "numer_seryjny",
}
PL = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
POSTCODE_RE = re.compile(r"^\d{2}-\d{3}$")
ADDRESS_HINT_RE = re.compile(r"\d{2}-\d{3}\s+\S")
FREE_MAIL = ("gmail.", "wp.pl", "o2.pl", "onet.", "interia.", "poczta.fm", "op.pl", "yahoo.", "outlook.", "hotmail.", "icloud.")
PERSON_WORDS = ("imie", "nazwisko", "osoba", "kontakt", "opiekun")
SAMPLES = 3


class ConverterError(ValueError):
    """File-level problem; the message is Polish and shown to the provider."""


def _norm(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text).translate(PL).casefold()).strip()


def _aliases():
    """normalised header -> (target, score, reason). Score 3: schema name/title, 2: known source file, 1: synonym."""
    out = {}

    def add(alias, target, score, reason):
        key = _norm(alias)
        if key and (key not in out or out[key][1] < score):
            out[key] = (target, score, reason)

    for k, v in SYNONYMS.items():
        add(k, v, 1, "nazwa kolumny (synonim)")
    sources, _, _ = load_registry(REGISTRY_PATH)
    for s in sources:
        label = "nazwa kolumny jak w pliku: %s" % s["label"]
        for field, col in (s.get("fields") or {}).items() if isinstance(s.get("fields"), dict) else ():
            add(col, field, 2, label)
        if isinstance(s.get("coordinates"), dict):
            add(s["coordinates"]["lat"], LAT, 2, label)
            add(s["coordinates"]["lon"], LON, 2, label)
        rid = s.get("record_id") or {}
        if rid.get("column") or rid.get("property"):
            add(rid.get("column") or rid.get("property"), "zrodlo_id", 2, label)
        if s.get("address_text"):
            add(s["address_text"], ADDRESS, 2, label)
    for f in S.FIELDS:
        for col in f.get("zrodla", {}).values():
            if "(" not in col and "." not in col and "[" not in col:   # skip descriptions like "Adres (część)"
                for part in col.split("|"):
                    add(part, f["name"], 2, "nazwa kolumny jak w znanym źródle")
        add(f["name"], f["name"], 3, "nazwa pola w standardzie")
        add(f["title"], f["name"], 3, "nazwa pola w standardzie")
    return {k: v for k, v in out.items() if v[0] in TARGETS}


# ---------- reading ----------

def _decode(data):
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16"), "UTF-16"
    try:
        return data.decode("utf-8-sig"), "UTF-8"
    except UnicodeDecodeError:
        return data.decode("cp1250", errors="replace"), "Windows-1250"


def _point(value):
    """'{"type":"Point","coordinates":[lon,lat]}' in a CSV cell -> geometry dict or None."""
    if not (isinstance(value, str) and value.lstrip().startswith("{")):
        return None
    try:
        g = json.loads(value)
    except ValueError:
        return None
    return g if isinstance(g, dict) and g.get("type") == "Point" else None


def read_table(data, filename=""):
    """-> dict(format, kodowanie, separator, columns, rows=[(n, {col: value}, geometry)], notes)."""
    if not data.strip():
        raise ConverterError("Plik jest pusty.")
    text, encoding = _decode(data)
    notes = []
    stripped = text.lstrip()
    if filename.lower().endswith((".geojson", ".json")) or stripped.startswith("{"):
        try:
            obj = json.loads(stripped)
            rows, columns = parse_geojson(obj)
        except (ValueError, KeyError, TypeError, AttributeError):
            raise ConverterError("Pliku nie da się odczytać jako GeoJSON (FeatureCollection z listą „features”).")
        fmt, sep = "geojson", None
    else:
        first = stripped.splitlines()[0] if stripped else ""
        sep = max((",", ";", "\t"), key=first.count)
        source = {"label": "Plik", "fixes": []}
        try:
            rows, columns = parse_csv(text, source, notes, sep)
            if len(columns) == 1 and sep in columns[0]:   # every row wrapped in one pair of quotes (Marki)
                source["fixes"] = ["unwrap_quoted_rows"]
                rows, columns = parse_csv(text, source, notes, sep)
        except csv.Error as ex:
            raise ConverterError("Pliku nie da się odczytać jako CSV (%s)." % ex)
        rows = [(n, row, None) for n, row in rows]
        fmt = "csv"
        # A column holding GeoJSON points (Przemyśl CSV) becomes the row geometry.
        for col in columns:
            vals = [row.get(col) for _, row, _ in rows if row.get(col)]
            if vals and all(_point(v) for v in vals):
                rows = [(n, row, _point(row.get(col))) for n, row, _ in rows]
                notes.append("Kolumna „%s” zawiera punkty GeoJSON – współrzędne odczytano z niej." % col)
                break
    if not columns or not rows:
        raise ConverterError("Plik nie zawiera wiersza nagłówka i co najmniej jednego wiersza danych.")
    if len(set(columns)) != len(columns):
        dup = [c for c, k in Counter(columns).items() if k > 1]
        raise ConverterError("Kolumny %s występują w nagłówku więcej niż raz. Zostaw po jednej." % ", ".join(dup))
    if any(g for _, _, g in rows):
        columns = columns + [GEOM_LAT, GEOM_LON]
        rows = [(n, dict(row, **_geom_values(g)), g) for n, row, g in rows]
    return {"format": fmt, "kodowanie": encoding, "separator": sep, "columns": columns, "rows": rows, "notes": notes}


def _geom_values(g):
    c = g.get("coordinates") if isinstance(g, dict) else None
    if isinstance(c, list) and len(c) >= 2:
        return {GEOM_LAT: str(c[1]), GEOM_LON: str(c[0])}
    return {GEOM_LAT: "", GEOM_LON: ""}


def _values(rows, col):
    return [str(row.get(col)).strip() for _, row, _ in rows if row.get(col) not in (None, "") and str(row.get(col)).strip()]


def _share(values, test):
    return sum(1 for v in values if test(v)) / float(len(values)) if values else 0.0


def _in_range(field):
    c = S.BY_NAME[field]["constraints"]

    def test(v):
        try:
            return c["minimum"] <= float(v.replace(",", ".")) <= c["maximum"]
        except ValueError:
            return False
    return test


# ---------- step 1: analysis ----------

def propose(columns, rows):
    """-> {column: (target, reason)}. Values decide first (coordinates, postcode, address), then header names."""
    proposal, taken = {}, set()

    def take(col, target, reason):
        if col not in proposal and target not in taken:
            proposal[col] = (target, reason)
            taken.add(target)

    values = {c: _values(rows, c) for c in columns}
    for col in columns:   # coordinates by value: the ranges of Poland do not overlap, so a swapped header is caught
        for field in (LAT, LON):
            if _share(values[col], _in_range(field)) >= 0.8:
                take(col, field, "wartości: współrzędne w zakresie Polski")
    for col in columns:
        if _share(values[col], POSTCODE_RE.match) >= 0.8:
            take(col, "kod_pocztowy", "wartości: kody pocztowe")
        elif _share(values[col], ADDRESS_HINT_RE.search) >= 0.8:
            take(col, ADDRESS, "wartości: pełny adres z kodem pocztowym")
        elif _share(values[col], EMAIL_RE.match) >= 0.8:
            take(col, "dysponent_email", "wartości: adresy e-mail")
    aliases = _aliases()
    scored = []
    for i, col in enumerate(columns):
        hit = aliases.get(_norm(col))
        constant = len(rows) > 1 and len(set(values[col])) == 1 and len(values[col]) == len(rows)
        if hit:   # a column with the same value in every row (Krosno "Nazwa" = "Defibrylator") yields to others
            scored.append((constant, -hit[1], i, col, hit[0], hit[2]))
    for _, _, _, col, target, reason in sorted(scored):
        take(col, target, reason)
    return proposal


def privacy_warnings(columns, rows, mapping):
    """Rule 6 heuristics: personal data in contact columns. -> list of Polish messages."""
    out = []
    for col in columns:
        words = _norm(col)
        if any(w in words for w in PERSON_WORDS):
            out.append("Kolumna „%s” może zawierać dane osoby (imię, nazwisko). W wykazie podaj wyłącznie kontakt "
                       "instytucjonalny." % col)
    for col, target in mapping.items():
        if target != "dysponent_email":
            continue
        emails = _values(rows, col)
        personal = [e for e in emails if e.split("@")[-1].casefold().startswith(FREE_MAIL)
                    or re.match(r"^[a-ząćęłńóśźż]+\.[a-ząćęłńóśźż]+@", e.casefold())]
        if personal:
            out.append("Kolumna „%s”: %d adresów e-mail wygląda na prywatne lub imienne (np. %s). Podaj adres "
                       "instytucji, np. sekretariat@…" % (col, len(personal), personal[0]))
    if any(t in ("dysponent_email", "dysponent_telefon") for t in mapping.values()):
        out.append("Kontakt do dysponenta służy tylko do przypomnień; w zbiorze krajowym na dane.gov.pl kolumny "
                   "e-mail i telefon są puste.")
    return out


def analyze(data, filename=""):
    t = read_table(data, filename)
    columns, rows = t["columns"], t["rows"]
    proposal = propose(columns, rows)
    return {
        "plik": filename,
        "format": t["format"],
        "kodowanie": t["kodowanie"],
        "separator": {",": "przecinek", ";": "średnik", "\t": "tabulator"}.get(t["separator"]),
        "wiersze": len(rows),
        "kolumny": [{"kolumna": c, "przyklady": _values(rows, c)[:SAMPLES],
                     "pole": proposal.get(c, ("", ""))[0], "powod": proposal.get(c, ("", ""))[1]} for c in columns],
        "przyklad_wierszy": [[str(row.get(c, "")) for c in columns] for _, row, _ in rows[:5]],
        "pola": [{"pole": t_, "tytul": TARGET_TITLES[t_]} for t_ in TARGETS],
        "pola_stale": [{"pole": t_, "tytul": TARGET_TITLES[t_], "wartosci": S.enum(t_) or None} for t_ in CONSTANT_TARGETS],
        "uwagi": t["notes"],
        "ostrzezenia": privacy_warnings(columns, rows, {c: p[0] for c, p in proposal.items()}),
    }


# ---------- step 2: conversion ----------

def _entry(columns, mapping):
    """Mapping {column: target} -> registry entry for sources.map_rows."""
    unknown = [c for c in mapping if c not in columns]
    if unknown:
        raise ConverterError("W pliku nie ma kolumn: %s." % ", ".join(unknown))
    bad = [t for t in mapping.values() if t and t not in TARGETS]
    if bad:
        raise ConverterError("Nieznane pola standardu: %s." % ", ".join(bad))
    by_target = {}
    for col, target in mapping.items():
        if target:
            if target in by_target:
                raise ConverterError("Pole „%s” przypisano do dwóch kolumn: „%s” i „%s”. Wybierz jedną."
                                     % (TARGET_TITLES[target], by_target[target], col))
            by_target[target] = col
    if (LAT in by_target) != (LON in by_target):
        raise ConverterError("Wskaż obie kolumny współrzędnych: szerokość i długość geograficzną.")
    entry = {"label": "Plik", "zrodlo": "konwerter", "fixes": ["swap_lat_lon_outside_pl", "note_shared_points"],
             "record_id": {"column": by_target.pop("zrodlo_id")} if "zrodlo_id" in by_target else {"row_number": True}}
    lat, lon = by_target.pop(LAT, None), by_target.pop(LON, None)
    if lat == GEOM_LAT and lon == GEOM_LON:
        entry["coordinates"] = "geometry"
    elif lat:
        entry["coordinates"] = {"lat": lat, "lon": lon}
    if ADDRESS in by_target:
        entry["address_text"] = by_target.pop(ADDRESS)
    entry["fields"] = by_target
    return entry


def convert(data, filename, mapping, constants=None, today=None):
    """-> (csv_text, report). mapping: {column: target or ""}; constants: {field: value} filled into empty cells."""
    t = read_table(data, filename)
    entry = _entry(t["columns"], mapping)
    constants = {k: str(v).strip() for k, v in (constants or {}).items() if str(v).strip()}
    bad = [k for k in constants if k not in CONSTANT_TARGETS]
    if bad:
        raise ConverterError("Wartości stałej nie można ustawić dla pól: %s." % ", ".join(bad))
    records, notes = map_rows(t["rows"], t["columns"], {"resource_id": "plik"}, entry, "")
    for rec in records:
        # System columns stay empty: the portal fills them from the dataset when it reads the list.
        rec.update(zrodlo="", licencja="", status="", wprowadzajacy_typ="", data_aktualizacji="")
        if "row_number" in entry["record_id"]:
            rec["zrodlo_id"] = ""
        for k, v in constants.items():
            rec[k] = rec[k] or v
    text = to_csv(records)
    accepted, rep = read_wykaz(text.encode("utf-8"), {"zrodlo": "konwerter", "zasob": "plik", "tytul": filename,
                                                      "instytucja": "", "licencja": "CC0 1.0", "priority": 1}, today)
    not_national = sum(1 for r in accepted if publication_reasons(r))
    warnings = privacy_warnings(t["columns"], t["rows"], mapping)
    report = {
        "status": rep["status"],
        "wiersze": rep["wiersze"],
        "poprawne": rep["przyjete"],
        "odrzucone": rep["wiersze"] - rep["przyjete"],
        "poza_wykazem_krajowym": not_national,
        "kompletnosc_srednia": round(sum(int(r["kompletnosc"]) for r in accepted) / float(len(accepted)), 1) if accepted else 0,
        "problemy": rep["problemy"] + [issue(None, None, WARNING, "dane_osobowe", w) for w in warnings],
        "problemy_razem": rep["problemy_razem"] + len(warnings),
        "poprawki": t["notes"] + notes,
    }
    return text, report
