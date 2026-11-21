"""Registry of data sources: aed_standard/sources.json. Everything about a source comes from here.

Each entry says where the raw file is, how it maps to the standard (a generic CSV/GeoJSON mapping or a named
mapper in sources.py), its merge priority and whether its values may be copied into other sources' records.
A broken entry is skipped with a Polish message, so one typo never stops the national registry build.
"""
import json
import os

from . import schema as S

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources.json")

SUBMISSION = "zgloszenie"  # zrodlo of seller/manager submissions in aed_service; priority 0, not in the registry
KNOWN_FIXES = ("unwrap_quoted_rows", "swap_lat_lon_outside_pl", "drop_outliers", "note_shared_points")
CODE_MAPPERS = ("warszawa", "osm")
FORMATS = ("csv", "geojson")

REQUIRED = ("id", "zrodlo", "priority", "file")
OPTIONAL = ("label", "dane_gov_pl", "format", "mapper", "record_id", "coordinates", "fields", "address_text", "fixes",
            "copy_values_on_merge")


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _entry_problems(e):
    """-> list of Polish problem descriptions for one registry entry ([] = valid)."""
    if not isinstance(e, dict):
        return ["wpis musi być obiektem JSON"]
    out = ["brak wymaganego klucza „%s”" % k for k in REQUIRED if k not in e]
    out += ["nieznany klucz „%s”" % k for k in e if k not in REQUIRED + OPTIONAL]
    out += ["„%s” musi być niepustym tekstem" % k for k in ("id", "zrodlo", "file", "label")
            if k in e and not (isinstance(e[k], str) and e[k].strip())]
    if "priority" in e and not (_is_int(e["priority"]) and e["priority"] >= 1):
        out.append("„priority” musi być liczbą całkowitą od 1 (0 mają zgłoszenia firm i zarządców)")
    if e.get("zrodlo") == SUBMISSION:
        out.append("wartość zrodlo „%s” jest zarezerwowana dla zgłoszeń z usługi" % SUBMISSION)
    if ("format" in e) == ("mapper" in e):
        out.append("podaj dokładnie jeden z kluczy „format” (%s) albo „mapper” (%s)" % (", ".join(FORMATS), ", ".join(CODE_MAPPERS)))
    if "format" in e and e["format"] not in FORMATS:
        out.append("nieznany format „%s” (dozwolone: %s)" % (e["format"], ", ".join(FORMATS)))
    if "mapper" in e and e["mapper"] not in CODE_MAPPERS:
        out.append("nieznany mapper „%s” (dozwolone: %s)" % (e["mapper"], ", ".join(CODE_MAPPERS)))
    if "format" in e:
        rid = e.get("record_id")
        if not (isinstance(rid, dict) and len(rid) == 1 and (
                isinstance(rid.get("column"), str) or isinstance(rid.get("property"), str) or rid.get("row_number") is True)):
            out.append("„record_id” musi mieć dokładnie jeden klucz: „column”, „property” albo „row_number”: true")
        fields = e.get("fields")
        if fields != "*":
            if not isinstance(fields, dict):
                out.append("„fields” musi być \"*\" albo obiektem {pole_standardu: kolumna_źródła}")
            else:
                out += ["nieznane pole docelowe „%s” (dozwolone są pola z schema.json)" % k
                        for k in fields if k not in S.FIELD_NAMES]
    coords = e.get("coordinates")
    if coords is not None and coords != "geometry" and not (
            isinstance(coords, dict) and set(coords) == {"lat", "lon"} and all(isinstance(v, str) for v in coords.values())):
        out.append("„coordinates” musi być \"geometry\" albo obiektem {\"lat\": kolumna, \"lon\": kolumna}")
    out += ["nieznana naprawa „%s” (dozwolone: %s)" % (f, ", ".join(KNOWN_FIXES))
            for f in e.get("fixes", []) if f not in KNOWN_FIXES]
    if "copy_values_on_merge" in e and not isinstance(e["copy_values_on_merge"], bool):
        out.append("„copy_values_on_merge” musi być true albo false")
    dgp = e.get("dane_gov_pl")
    if dgp is not None and not (isinstance(dgp, dict) and _is_int(dgp.get("dataset_id")) and set(dgp) <= {"dataset_id", "resources"}
                                and all(_is_int(r) for r in dgp.get("resources", []))):
        out.append("„dane_gov_pl” musi mieć „dataset_id” (liczba) i opcjonalnie „resources” (lista liczb)")
    return out


def load_registry(path=REGISTRY_PATH):
    """-> (sources, licences, errors). Valid entries in file order (defaults filled in); broken entries are
    skipped with one Polish message each. Raises ValueError when the file itself is unusable."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as ex:
        raise ValueError("Plik %s nie jest poprawnym JSON-em: %s" % (path, ex))
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list) or not isinstance(data.get("licences"), dict):
        raise ValueError("Plik %s musi mieć klucze „licences” (obiekt) i „sources” (lista)." % path)
    sources, errors, ids, zrodla = [], [], set(), set()
    for n, e in enumerate(data["sources"], start=1):
        name = e["id"] if isinstance(e, dict) and isinstance(e.get("id"), str) and e["id"] else "nr %d" % n
        problems = _entry_problems(e)
        if not problems and e["id"] in ids:
            problems.append("identyfikator „%s” powtarza się" % e["id"])
        if not problems and e["zrodlo"] in zrodla:
            problems.append("wartość zrodlo „%s” powtarza się" % e["zrodlo"])
        if problems:
            errors.append("sources.json, źródło „%s” pominięte: %s." % (name, "; ".join(problems)))
            continue
        ids.add(e["id"])
        zrodla.add(e["zrodlo"])
        entry = dict(e)
        entry.setdefault("label", e["id"])
        entry.setdefault("fixes", [])
        entry.setdefault("copy_values_on_merge", True)
        sources.append(entry)
    return sources, dict(data["licences"]), errors
