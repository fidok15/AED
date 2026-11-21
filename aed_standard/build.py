"""National registry: map all sources -> deduplicate -> ids -> completeness -> exports and report."""
import csv
import io
import json
import os
from collections import Counter, defaultdict

from . import schema as S
from .dedup import deduplicate, make_id
from .sources import load_all
from .validate import ERROR, LAT, LON, check_record, completeness


def publication_reasons(record):
    """Why a registry record is not in the dane.gov.pl export ([] = it is)."""
    reasons = []
    if record.get("licencja") == "ODbL 1.0":
        reasons.append("licencja ODbL 1.0 (dane OpenStreetMap)")
    if record.get("dostep") == "prywatny":
        reasons.append("dostep prywatny")
    codes = sorted({"%s: %s" % (p["kod"], p["pole"]) for p in check_record(record, "publikacja") if p["poziom"] == ERROR})
    return reasons + ["profil publikacja – " + c for c in codes]


def publication_export(records):
    return [r for r in records if not publication_reasons(r)]


def build_registry(raw_dir):
    """-> (records, review_pairs, report). Pure: reads raw_dir, writes nothing."""
    mapped, notes = load_all(raw_dir)
    for r in mapped:
        r["id_aed"] = r["id_aed"] or make_id(r["zrodlo"], r["zrodlo_id"])
        r["kompletnosc"] = str(completeness(r))
    ids = Counter(r["id_aed"] for r in mapped)
    assert max(ids.values()) == 1, "id_aed collision: %s" % ids.most_common(3)

    records, pairs, edges = deduplicate(mapped)
    for r in records:
        r["kompletnosc"] = str(completeness(r))

    per_source = defaultdict(list)
    for r in mapped:
        per_source[r["zrodlo"]].append(r)
    after = Counter(r["zrodlo"] for r in records)
    export = publication_export(records)
    excluded = Counter()
    for r in records:
        for reason in publication_reasons(r):
            excluded[reason] += 1
    report = {
        "rejestr_rekordy": len(records),
        "rekordy_na_zrodlo": {z: {"przed": len(v), "po": after.get(z, 0)} for z, v in sorted(per_source.items())},
        "polaczenia": {
            "razem": len(edges),
            "pary_zrodel": dict(sorted(Counter(" + ".join(sorted((a, b))) for a, b, _ in edges).items())),
            "reguly": dict(sorted(Counter(rule for _, _, rule in edges).items())),
        },
        "do_przegladu": {"razem": len(pairs), "powody": dict(sorted(Counter(p["powod"] for p in pairs).items()))},
        "statusy": dict(sorted(Counter(r["status"] for r in records).items())),
        "eksport_dane_gov_pl": {
            "rekordy": len(export),
            "wykluczone": len(records) - len(export),
            "powody_wykluczenia": dict(excluded.most_common()),  # one record can have several reasons
        },
        "kompletnosc_srednia": {
            "zrodla": {z: round(sum(int(r["kompletnosc"]) for r in v) / float(len(v)), 1) for z, v in sorted(per_source.items())},
            "rejestr": round(sum(int(r["kompletnosc"]) for r in records) / float(len(records)), 1),
            "eksport_dane_gov_pl": round(sum(int(r["kompletnosc"]) for r in export) / float(len(export)), 1) if export else 0,
        },
        "pokrycie_pol": {z: {f: round(sum(1 for r in v if r[f]) / float(len(v)), 3) for f in S.FIELD_NAMES}
                         for z, v in sorted(per_source.items())},
        "naprawy_danych": notes,
    }
    return records, pairs, report


def to_csv(records):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=S.FIELD_NAMES, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    w.writerows(records)
    return buf.getvalue()


def to_geojson(records):
    def typed(name, value):
        t = S.BY_NAME[name].get("type")
        if value == "":
            return None
        return float(value) if t == "number" else int(value) if t == "integer" else value

    feats = []
    for r in records:
        geom = {"type": "Point", "coordinates": [float(r[LON]), float(r[LAT])]} if r[LAT] and r[LON] else None
        feats.append({"type": "Feature", "geometry": geom, "properties": {f: typed(f, r[f]) for f in S.FIELD_NAMES}})
    return json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False)


REVIEW_COLUMNS = ["odleglosc_m", "podobienstwo", "powod"] + [
    "%s_%s" % (f, s) for s in ("a", "b")
    for f in ("id_aed", "zrodlo", "zrodlo_id", "nazwa", "nazwa_ulicy", "nr_budynku", "miejscowosc", LAT, LON)]


def review_csv(pairs):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=REVIEW_COLUMNS, lineterminator="\n")
    w.writeheader()
    for p in pairs:
        row = {"odleglosc_m": p["odleglosc_m"], "podobienstwo": p["podobienstwo"], "powod": p["powod"]}
        for s in ("a", "b"):
            rec = p["rekord_" + s]
            row["id_aed_" + s] = p["id_aed_" + s]
            for f in ("zrodlo", "zrodlo_id", "nazwa", "nazwa_ulicy", "nr_budynku", "miejscowosc", LAT, LON):
                row["%s_%s" % (f, s)] = rec[f]
        w.writerow(row)
    return buf.getvalue()


def write_outputs(out_dir, records, pairs, report):
    os.makedirs(out_dir, exist_ok=True)
    files = {
        "aed_rejestr.csv": to_csv(records),
        "aed_rejestr.geojson": to_geojson(records),
        "aed_dane_gov_pl.csv": to_csv(publication_export(records)),
        "duplikaty_do_przegladu.csv": review_csv(pairs),
        "raport.json": json.dumps(report, ensure_ascii=False, indent=2),
    }
    for name, content in files.items():
        with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="") as f:
            f.write(content)
    return sorted(files)
