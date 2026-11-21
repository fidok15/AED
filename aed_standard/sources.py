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


def _krosno_marki_rows(raw_dir, rel, manifest, label, notes):
    """Krosno and Marki publish the same layout: lon, lat, 'Defibrylator', place, address, id."""
    entry = manifest[rel]
    dataset = entry["dataset_id"]
    with open(os.path.join(raw_dir, rel), encoding="utf-8-sig") as f:
        lines = f.read().splitlines()
    out = []
    repaired = 0
    swapped = []
    for line in lines[1:]:
        if not line.strip():
            continue
        if line.startswith('"') and line.endswith('"') and '""' in line:
            # Marki defect: the whole row is wrapped in one pair of quotes, inner quotes doubled.
            line = line[1:-1].replace('""', '"')
            repaired += 1
        vals = [v.strip() for v in next(csv.reader(io.StringIO(line)))]
        a, b = float(vals[0]), float(vals[1])
        lat, lon = b, a  # header order: longitude first
        if not _in_pl(lat, lon) and _in_pl(a, b):
            lat, lon = a, b
            swapped.append(vals[5])
        rec = _record("dane.gov.pl/%s" % dataset, vals[5], entry["license"], entry["data_date"],
                      nazwa=vals[3], **parse_address(vals[4]))
        rec[LAT], rec[LON] = _coord(lat), _coord(lon)
        out.append(rec)
    if repaired:
        notes.append("%s: %d wierszy było ujętych w jedną parę cudzysłowów – rozpakowano." % (label, repaired))
    if swapped:
        notes.append("%s, rekordy %s: szerokość i długość geograficzna były zamienione – poprawiono."
                     % (label, ", ".join(swapped)))
    drop_outliers(out, notes, label)
    note_shared_points(out, notes, label)
    return out


def krosno(raw_dir, manifest):
    notes = []
    return _krosno_marki_rows(raw_dir, "dane_gov_pl/krosno/resource_54632.csv", manifest, "Krosno", notes), notes


def marki(raw_dir, manifest):
    notes = []
    return _krosno_marki_rows(raw_dir, "dane_gov_pl/marki/resource_68353.csv", manifest, "Marki", notes), notes


def przemysl(raw_dir, manifest):
    # Five resources carry the same 21 points; the GeoJSON is the cleanest (typed coordinates,
    # separate address fields). The CSV uses ';' and embeds geometry as a JSON string.
    rel = "dane_gov_pl/przemysl/resource_62093.geojson"
    entry = manifest[rel]
    with open(os.path.join(raw_dir, rel), encoding="utf-8") as f:
        features = json.load(f)["features"]
    out = []
    for feat in features:
        p = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]
        rec = _record("dane.gov.pl/%s" % entry["dataset_id"], p["id"], entry["license"], entry["data_date"],
                      nazwa=p.get("name"), miejscowosc=p.get("city"), nazwa_ulicy=p.get("street"),
                      nr_budynku=p.get("home_number"), kod_pocztowy=p.get("postcode"),
                      dysponent_email=p.get("email"), dysponent_telefon=p.get("phone"))
        rec[LAT], rec[LON] = _coord(lat), _coord(lon)
        out.append(rec)
    notes = []
    drop_outliers(out, notes, "Przemyśl")
    return out, notes


def legionowo(raw_dir, manifest):
    # Column names are the standard's names (Legionowo is the reference subset).
    rel = "dane_gov_pl/legionowo/resource_2625221.csv"
    entry = manifest[rel]
    with open(os.path.join(raw_dir, rel), encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    out = []
    for i, row in enumerate(rows, start=1):
        # ponytail: the source has no ids; "<resource>/<row>" shifts if rows are inserted upstream.
        rec = _record("dane.gov.pl/%s" % entry["dataset_id"], "%s/%d" % (entry["resource_id"], i),
                      entry["license"], entry["data_date"], **row)
        out.append(rec)
    notes = []
    drop_outliers(out, notes, "Legionowo")
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


def warszawa(raw_dir, manifest):
    rel = "warszawa_api/defibrylatory.json"
    entry = manifest[rel]
    with open(os.path.join(raw_dir, rel), encoding="utf-8") as f:
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
        rec = _record(WARSAW, p["defibrillator_id"], entry["license"], snapshot,
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


def osm(raw_dir, manifest):
    rel = "openaedmap/PL.geojson"
    entry = manifest[rel]
    with open(os.path.join(raw_dir, rel), encoding="utf-8") as f:
        features = json.load(f)["features"]
    snapshot = entry["downloaded_at"][:10]
    out = []
    for feat in features:
        p = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]
        check = _clean(p.get("check_date"))
        check = check if re.match(r"^\d{4}-\d{2}-\d{2}$", check) else ""  # partial dates (2023-02) are dropped
        rec = _record(OSM, "%s/%s" % (p["@osm_type"], p["@osm_id"]), "ODbL 1.0", snapshot,
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


MAPPERS = [krosno, marki, przemysl, legionowo, warszawa, osm]


def load_all(raw_dir):
    """-> (records, notes) for all sources."""
    manifest = _manifest(raw_dir)
    records, notes = [], []
    for mapper in MAPPERS:
        recs, n = mapper(raw_dir, manifest)
        records.extend(recs)
        notes.extend(n)
    return records, notes
