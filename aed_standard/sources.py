"""Mappers from the raw sources in datasets/raw/ to standard records.

Each mapper returns (records, notes): records are dicts keyed by schema field names (all
values strings), notes are Polish descriptions of repairs made to the source data.
"""
import csv
import io
import json
import math
import os
import re

from . import schema as S
from .registry import REGISTRY_PATH, load_registry
from .validate import LAT, LON

OSM = "openstreetmap"
WARSAW = "um.warszawa.pl"
# Sources are compared on the coordinates, so only these keys need "_" meta fields:
# "_ref_warszawa" = Warsaw defibrillator_id that an OSM node points to (tag ref:api-um-warszawa-pl).


def _clean(value):
    """Collapse whitespace; None -> ''."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()


def _coord(value):
    return repr(round(float(value), 7))


def _manifest(raw_dir):
    with open(os.path.join(raw_dir, "manifest.json"), encoding="utf-8") as f:
        return {e["file"]: e for e in json.load(f)["files"]}


def _record(zrodlo, zrodlo_id, licencja, data_aktualizacji, **values):
    rec = S.blank_record()
    rec.update({k: _clean(v) for k, v in values.items() if k in rec})
    rec.update(zrodlo=zrodlo, zrodlo_id=_clean(zrodlo_id), licencja=licencja, data_aktualizacji=data_aktualizacji,
               wprowadzajacy_typ="import", status="niepotwierdzony")
    return rec


STREET_TYPES = {"ul": "ulica", "al": "aleja", "pl": "plac", "os": "osiedle"}
ADDRESS_RE = re.compile(
    r"^(?:(?P<cecha>ul|al|pl|os)\.+\s*)?(?P<ulica>[^,]*?)(?:\s+(?P<nr>\d+[A-Za-z]?(?:/\d+[A-Za-z]?)?))?"
    r"\s*,[\s,]*(?P<kod>\d{2}-\d{3})\s+(?P<miasto>[^,]+)$", re.IGNORECASE)


def parse_address(text):
    """'ul. Jasna 12, 38-400 Krosno' -> address fields; {} when the pattern is not unambiguous."""
    m = ADDRESS_RE.match(_clean(text))
    if not m:
        return {}
    cecha = (m.group("cecha") or "").lower()
    return {"cecha_ulicy": STREET_TYPES.get(cecha, ""), "nazwa_ulicy": m.group("ulica").strip(),
            "nr_budynku": m.group("nr") or "", "kod_pocztowy": m.group("kod"), "miejscowosc": m.group("miasto").strip()}


def drop_outliers(records, notes, label, max_km=20.0):
    """A municipal dataset covers one town: clear coordinates lying far from the median point."""
    pts = [(float(r[LAT]), float(r[LON])) for r in records if r[LAT] and r[LON]]
    if len(pts) < 3:
        return
    mlat = sorted(p[0] for p in pts)[len(pts) // 2]
    mlon = sorted(p[1] for p in pts)[len(pts) // 2]
    for r in records:
        if r[LAT] and r[LON]:
            km = haversine_m(float(r[LAT]), float(r[LON]), mlat, mlon) / 1000
            if km > max_km:
                notes.append("%s, rekord %s (%s): punkt %s, %s leży %.0f km od pozostałych punktów zbioru – współrzędne usunięte."
                             % (label, r["zrodlo_id"], r["nazwa"], r[LAT], r[LON], km))
                r[LAT] = r[LON] = ""


def note_shared_points(records, notes, label):
    """Report (not repair) different addresses that share identical coordinates within one source."""
    seen = {}
    for r in records:
        if r[LAT] and r[LON]:
            seen.setdefault((r[LAT], r[LON]), []).append(r)
    for (lat, lon), group in sorted(seen.items()):
        if len({(r["nazwa_ulicy"], r["nr_budynku"]) for r in group}) > 1:
            notes.append("%s, rekordy %s: różne adresy mają identyczne współrzędne %s, %s – do sprawdzenia u dostawcy (bez zmian)."
                         % (label, ", ".join(r["zrodlo_id"] for r in group), lat, lon))


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371008.8 * math.asin(math.sqrt(a))


def _in_pl(lat, lon):
    c1, c2 = S.BY_NAME[LAT]["constraints"], S.BY_NAME[LON]["constraints"]
    return c1["minimum"] <= lat <= c1["maximum"] and c2["minimum"] <= lon <= c2["maximum"]


def _unwrap(line):
    """Marki defect: a whole row wrapped in one pair of quotes, inner quotes doubled."""
    return line[1:-1].replace('""', '"')


def _read_csv(path, source, notes):
    """-> list of (row_number, {column: value}); column names and values stripped."""
    with open(path, encoding="utf-8-sig") as f:
        lines = [line for line in f.read().splitlines() if line.strip()]
    if not lines:
        return [], []
    unwrap = "unwrap_quoted_rows" in source["fixes"]
    header = lines[0]
    if unwrap and len(header) > 1 and header.startswith('"') and header.endswith('"'):
        header = _unwrap(header)
    columns = [c.strip() for c in next(csv.reader(io.StringIO(header)))]
    rows, repaired = [], 0
    for n, line in enumerate(lines[1:], start=1):
        if unwrap and line.startswith('"') and line.endswith('"') and '""' in line:
            line = _unwrap(line)
            repaired += 1
        vals = [v.strip() for v in next(csv.reader(io.StringIO(line)))]
        rows.append((n, dict(zip(columns, vals))))
    if repaired:
        notes.append("%s: %d wierszy było ujętych w jedną parę cudzysłowów – rozpakowano." % (source["label"], repaired))
    return rows, columns


def _read_geojson(path):
    with open(path, encoding="utf-8") as f:
        features = json.load(f)["features"]
    rows = [(n, dict(feat.get("properties") or {}), feat.get("geometry")) for n, feat in enumerate(features, start=1)]
    return rows, sorted({k for _, props, _ in rows for k in props})


def _needed_columns(source):
    rid = source["record_id"]
    cols = [rid.get("column") or rid.get("property")] if not rid.get("row_number") else []
    if isinstance(source.get("coordinates"), dict):
        cols += [source["coordinates"]["lat"], source["coordinates"]["lon"]]
    if source["fields"] != "*":
        cols += list(source["fields"].values())
    if source.get("address_text"):
        cols.append(source["address_text"])
    return cols


def map_source(raw_dir, entry, source, licence):
    """Generic mapper of a registry entry with "format" (csv | geojson) -> (records, notes)."""
    path = os.path.join(raw_dir, source["file"])
    notes = []
    if source["format"] == "csv":
        rows, columns = _read_csv(path, source, notes)
        rows = [(n, row, None) for n, row in rows]
    else:
        rows, columns = _read_geojson(path)
    missing = [c for c in _needed_columns(source) if c not in columns]
    if rows and missing:
        raise ValueError("w pliku brakuje kolumn: %s (są: %s)" % (", ".join(missing), ", ".join(columns)))
    rid, coords, swap = source["record_id"], source.get("coordinates"), "swap_lat_lon_outside_pl" in source["fixes"]
    out, swapped = [], []
    for n, row, geometry in rows:
        if rid.get("row_number"):
            zrodlo_id = "%s/%d" % (entry["resource_id"], n)
        else:
            zrodlo_id = row.get(rid.get("column") or rid.get("property"))
        if source["fields"] == "*":
            values = {k: v for k, v in row.items() if k in S.BY_NAME}
        else:
            values = {field: row.get(col) for field, col in source["fields"].items()}
        if source.get("address_text"):
            values.update(parse_address(row.get(source["address_text"])))
        rec = _record(source["zrodlo"], zrodlo_id, licence, entry.get("data_date"), **values)
        if coords == "geometry":
            lon, lat = geometry["coordinates"]
            rec[LAT], rec[LON] = _coord(lat), _coord(lon)
        elif coords:
            lat, lon = float(row[coords["lat"]]), float(row[coords["lon"]])
            if swap and not _in_pl(lat, lon) and _in_pl(lon, lat):
                lat, lon = lon, lat
                swapped.append(_clean(zrodlo_id))
            rec[LAT], rec[LON] = _coord(lat), _coord(lon)
        out.append(rec)
    if swapped:
        notes.append("%s, rekordy %s: szerokość i długość geograficzna były zamienione – poprawiono."
                     % (source["label"], ", ".join(swapped)))
    if "drop_outliers" in source["fixes"]:
        drop_outliers(out, notes, source["label"])
    if "note_shared_points" in source["fixes"]:
        note_shared_points(out, notes, source["label"])
    return out, notes


# Warsaw device_manufacturer mixes brand and model. Split only when the string starts with one of
# these brands (aliases incl. typos seen in the data); the rest of the string becomes the model.
BRANDS = [
    (("cu medical systems, inc.", "cu medical systems inc.", "cu medical systems", "cu medical system", "cu medical"), "CU Medical Systems"),
    (("philips medical systems", "philips", "phillips"), "Philips"),
    (("zoll medical corporation", "zoll"), "ZOLL"),
    (("heartsine",), "HeartSine"),
    (("medtronic",), "Medtronic"),
    (("physio-control", "physio control", "physio_control"), "Physio-Control"),
    (("primedic",), "Primedic"),
    (("schiller",), "Schiller"),
    (("welch allyn",), "Welch Allyn"),
    (("nihon kohden",), "Nihon Kohden"),
    (("mindray",), "Mindray"),
    (("aivia",), "Aivia"),
    (("defibtech",), "Defibtech"),
    (("bexen cardio",), "Bexen Cardio"),
]
NOT_A_VALUE = {".", "aed", "unknown", "brak danych", "brak informacji"}


def split_manufacturer(text):
    """-> (producent, model)."""
    text = _clean(text)
    if text.casefold() in NOT_A_VALUE:
        return "", ""
    low = text.casefold()
    for aliases, brand in BRANDS:
        for alias in aliases:
            if low.startswith(alias) and (len(low) == len(alias) or not low[len(alias)].isalnum()):
                model = re.sub(r"^[\s,.:;-]*(inc\.?|inc,)?[\s,.:;-]*(model:?)?\s*", "", text[len(alias):], flags=re.I)
                return brand, model.strip(" ,.;-")
    return text, ""


def warszawa(raw_dir, entry, source, licence):
    with open(os.path.join(raw_dir, source["file"]), encoding="utf-8") as f:
        data = json.load(f)
    snapshot = entry["downloaded_at"][:10]  # live API without per-record dates: date of the snapshot
    # device_public_access: Publiczny -> publiczny, Prywatny -> ograniczony. The 100 "Prywatny" records
    # are schools, pools and company receptions that the city lists with access hours, so the device
    # is reachable with staff help rather than hidden; "prywatny" in the standard means "not published".
    access = {"Publiczny": "publiczny", "Prywatny": "ograniczony"}
    out = []
    for feat in data:
        p = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"][0]
        producent, model = split_manufacturer(p.get("device_manufacturer"))
        loc = _clean(p.get("device_location"))
        # device_availability: API docs define it as "is the device available 24/7". Values: Tak (100),
        # Nie (511), Ograniczona (95), 2 free-text. Only "Tak" means 24/7; the rest gives no hours,
        # so godziny_dostepu stays empty and the description goes to godziny_dostepu_opis.
        avail = _clean(p.get("device_availability"))
        hours_text = _clean(p.get("device_access_description"))
        if avail not in ("Tak", "Nie", "Ograniczona") and not hours_text:
            hours_text = avail
        rec = _record(source["zrodlo"], p["defibrillator_id"], licence, snapshot,
                      nazwa=p.get("location_object_name"), miejscowosc=p.get("location_city"),
                      nazwa_ulicy=p.get("location_street"), nr_budynku=p.get("location_building"),
                      kod_pocztowy=p.get("location_postcode"), opis_lokalizacji=p.get("location_description"),
                      wewnatrz_budynku="tak" if loc.startswith("Wewnątrz") else "nie" if loc.startswith("Na zewnątrz") else "",
                      dostep=access.get(_clean(p.get("device_public_access")), ""),
                      godziny_dostepu="24/7" if avail == "Tak" else "",
                      godziny_dostepu_opis=hours_text, producent=producent, model=model)
        rec[LAT], rec[LON] = _coord(lat), _coord(lon)
        out.append(rec)
    return out, []


# OSM access tag -> dostep. permit ("only with permission") is treated as ograniczony;
# unknown and missing stay empty.
OSM_ACCESS = {"yes": "publiczny", "permissive": "publiczny", "customers": "ograniczony", "permit": "ograniczony",
              "private": "prywatny", "no": "prywatny"}


def osm(raw_dir, entry, source, licence):
    with open(os.path.join(raw_dir, source["file"]), encoding="utf-8") as f:
        features = json.load(f)["features"]
    snapshot = entry["downloaded_at"][:10]
    out = []
    for feat in features:
        p = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]
        check = _clean(p.get("check_date"))
        check = check if re.match(r"^\d{4}-\d{2}-\d{2}$", check) else ""  # partial dates (2023-02) are dropped
        rec = _record(source["zrodlo"], "%s/%s" % (p["@osm_type"], p["@osm_id"]), licence, snapshot,
                      nazwa=p.get("name") or p.get("operator"),  # description is free text, not a name
                      miejscowosc=p.get("addr:city"), nazwa_ulicy=p.get("addr:street"),
                      nr_budynku=p.get("addr:housenumber"), kod_pocztowy=p.get("addr:postcode"),
                      opis_lokalizacji=p.get("defibrillator:location:pl") or p.get("defibrillator:location"),
                      wewnatrz_budynku={"yes": "tak", "no": "nie"}.get(p.get("indoor"), ""),
                      dostep=OSM_ACCESS.get(p.get("access"), ""), godziny_dostepu=p.get("opening_hours"),
                      producent=p.get("manufacturer"), model=p.get("model"), dysponent_nazwa=p.get("operator"),
                      dysponent_email=p.get("email"), dysponent_telefon=p.get("phone"),
                      data_weryfikacji=check, sposob_weryfikacji="import" if check else "")
        rec[LAT], rec[LON] = _coord(lat), _coord(lon)
        if p.get("ref:api-um-warszawa-pl"):
            rec["_ref_warszawa"] = _clean(p["ref:api-um-warszawa-pl"])
        out.append(rec)
    return out, []


CODE_MAPPERS = {"warszawa": warszawa, "osm": osm}


def load_all(raw_dir, registry_path=None):
    """-> (records, notes, errors, skipped) for all sources in the registry.

    errors: Polish messages (broken registry entries, sources that could not be mapped); skipped: zrodlo values
    of registry entries that produced no records this run. Each record carries "_priority" and "_copy_values"
    from its registry entry (meta fields, dropped by deduplication)."""
    sources, licences, errors = load_registry(registry_path or REGISTRY_PATH)
    manifest = _manifest(raw_dir)
    records, notes, skipped = [], [], []
    allowed = S.enum("licencja")
    for source in sources:
        entry = manifest.get(source["file"])
        if entry is None:
            problem = "brak pliku %s w manifest.json (źródło nie zostało pobrane)" % source["file"]
        elif licences.get(entry.get("license")) not in allowed:
            problem = ("licencja „%s” nie jest obsługiwana; dopisz ją do „licences” w sources.json, jeśli wolno "
                       "ją publikować (dozwolone: %s)" % (entry.get("license"), ", ".join(allowed)))
        else:
            problem = None
        if problem is None:
            mapper = CODE_MAPPERS[source["mapper"]] if "mapper" in source else map_source
            try:
                recs, n = mapper(raw_dir, entry, source, licences[entry["license"]])
            except Exception as ex:  # a broken or changed source file must not stop the other sources
                problem = "nie udało się odczytać pliku %s (%s: %s)" % (source["file"], type(ex).__name__, ex)
        if problem is not None:
            errors.append("Źródło %s (%s) pominięte: %s." % (source["label"], source["zrodlo"], problem))
            skipped.append(source["zrodlo"])
            continue
        for r in recs:
            r["_priority"], r["_copy_values"] = source["priority"], source["copy_values_on_merge"]
        records.extend(recs)
        notes.extend(n)
    return records, notes, errors, skipped
