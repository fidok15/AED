"""Converter: a provider's own AED file (any column layout; CSV, XLSX, ODS, JSON/GeoJSON/ArcGIS, KML/KMZ, GPX, GML,
an HTML or DOCX table; recognised by content in formaty.py) -> a list (wykaz) in the standard.

Two steps, both in memory (nothing is stored):
    analyze(data, filename)                       -> columns, sample rows, proposed mapping column -> target
    convert(data, filename, mapping, constants)   -> CSV text in the standard + Polish validation report

The mapping is turned into a registry entry like those in sources.json and run through the same generic
mapper (sources.map_rows) and the same check as the portal (wykaz.read_wykaz). Pure Python 3.8.
"""
import calendar
import codecs
import csv
import datetime
import io
import itertools
import json
import re
import zipfile
from collections import Counter

from . import schema as S
from . import formaty, uklady, xlsx
from .build import HIDDEN_PUBLIC, publication_reasons, to_csv
from .registry import REGISTRY_PATH, load_registry
from .sources import ODBL, OSM, _clean, map_rows, parse_csv
from .validate import EMAIL_RE, EXPIRY_DATES, LAT, LON, WARNING, issue
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
    # Seen in the format survey (docs/formaty-zbiorow-aed.md): ArcGIS copy of the Warsaw list, KML/GML exports.
    "object name": "nazwa", "manufacturer": "producent", "building no": "nr_budynku", "location desc": "opis_lokalizacji",
    "access desc": "godziny_dostepu_opis", "description": "opis_lokalizacji", "desc": "opis_lokalizacji", "polozenie": "opis_lokalizacji",
    "miejscowosc": "miejscowosc", "home number": "nr_budynku", "nr budynku": "nr_budynku", "adres aed": ADDRESS,
}
PL = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
POSTCODE_RE = re.compile(r"^\d{2}-\d{3}$")
ADDRESS_HINT_RE = re.compile(r"\d{2}-\d{3}\s+\S")
FREE_MAIL = ("gmail.", "wp.pl", "o2.pl", "onet.", "interia.", "poczta.fm", "op.pl", "yahoo.", "outlook.", "hotmail.", "icloud.")
PERSON_WORDS = ("imie", "nazwisko", "osoba", "kontakt", "opiekun")
SAMPLES = 3
XLSX_MAX_UNPACKED = 50 * 2 ** 20   # the upload is at most 5 MB; text XML packs ~10x
# Work budget of one file, checked before the column analysis (columns x rows scans). The largest real list
# (Warsaw API, 708 rows x ~30 columns) is far below; the public endpoint must not be blocked by a sparse file.
MAX_ROWS = 50000
MAX_CELLS = 10 ** 6       # rows x columns
MAX_CHARS = 20 * 2 ** 20  # characters of all values; only XLSX can expand (one shared string in many cells)
# Spreadsheet spellings of yes/no, mapped to the schema's trueValues/falseValues.
YES_WORDS = {"tak", "t", "1", "true", "prawda", "x", "yes", "y", "wewnatrz", "wewnatrzbudynku"}
NO_WORDS = {"nie", "n", "0", "false", "falsz", "no", "nazewnatrz", "nazewnatrzbudynku", "zewnatrz"}
YMD_RE = re.compile(r"^(\d{4})([./-])(\d{1,2})\2(\d{1,2})(?:[ T]00:00(?::00)?)?$")
DMY_RE = re.compile(r"^(\d{1,2})([./-])(\d{1,2})\2(\d{4})$")
YM_RE = re.compile(r"^(\d{4})[./-](\d{1,2})$")
POSTCODE_LOOSE_RE = re.compile(r"^(\d{2})\s*-?\s*(\d{3})$")


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
        try:
            return data.decode("utf-16"), "UTF-16"
        except UnicodeDecodeError:
            raise ConverterError("Plik ma znacznik kodowania UTF-16, ale jego treść jest uszkodzona lub ucięta. "
                                 "Zapisz go ponownie jako „CSV UTF-8”.")
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


def _separator(text):
    """Separator giving the widest header with the same width in the first rows, quotes respected
    ("Nazwa, opis";lat;lon -> ';'). When every candidate yields one column, count the characters of the first line."""
    def score(sep):
        try:
            sample = [r for r in itertools.islice(csv.reader(io.StringIO(text, newline=""), delimiter=sep), 20) if any(r)]
        except csv.Error:
            return (False, False, 0)
        width = len(sample[0]) if sample else 0
        # A parse into several columns beats a one-column parse even when a data row is short.
        return (width > 1, all(len(r) == width for r in sample), width)

    candidates = (",", ";", "\t")
    best = max(candidates, key=score)
    if score(best)[0]:
        return best
    first = text.splitlines()[0] if text else ""
    return max(candidates, key=first.count)


def _grid(lines, notes, what):
    """Rows of cells from a sheet or a table -> (csv_text, None, None) when every row is one CSV line in one cell
    (Marki), else (None, columns, rows). Title rows above the header (a document heading in one cell) are skipped."""
    lines = [[v.strip() for v in line] for line in lines if any(v.strip() for v in line)]
    if not lines:
        raise ConverterError("%s nie zawiera danych." % what)
    if len(lines[0]) == 1 and any(sep in lines[0][0] for sep in ",;\t"):
        notes.append("Każdy wiersz arkusza ma cały wiersz CSV w jednej komórce – odczytano go jako CSV.")
        return "\n".join(line[0] if line else "" for line in lines), None, None
    filled = [sum(1 for v in line if v) for line in lines]
    first = next(i for i, k in enumerate(filled) if k >= max(2, max(filled) // 2) or k == max(filled))
    if first:
        notes.append("Pominięto %d wiersz(e) tytułowe nad nagłówkiem (np. „%s”)." % (first, next(v for v in lines[0] if v)[:80]))
        lines = lines[first:]
    width = max(len(line) for line in lines)
    header = [h.strip() for h in lines[0]] + [""] * (width - len(lines[0]))
    keep = [i for i in range(width) if header[i] or any(i < len(line) and line[i].strip() for line in lines[1:])]
    columns = [header[i] or "Kolumna %d" % (i + 1) for i in keep]
    rows = [(n, {columns[k]: (line[i].strip() if i < len(line) else "") for k, i in enumerate(keep)})
            for n, line in enumerate(lines[1:], start=1)]
    return None, columns, rows


def read_table(data, filename=""):
    """-> dict(format, kodowanie, separator, columns, rows=[(n, {col: value}, geometry)], notes).
    Every format becomes the same table here; the analysis and the mapping below do not know the format."""
    if not data.strip():
        raise ConverterError("Plik jest pusty.")
    notes = []
    try:
        fmt = formaty.detect(data, filename)
        return _read(fmt, data, notes)
    except (formaty.FormatError, xlsx.XlsxError) as ex:
        raise ConverterError(str(ex))
    except (zipfile.BadZipFile, StopIteration):
        raise ConverterError("Pliku nie da się rozpakować – archiwum jest uszkodzone.")


def _read(fmt, data, notes):
    sep, text = None, None
    if fmt in ("xlsx", "zip?"):
        sheet, lines = xlsx.read_rows(data, XLSX_MAX_UNPACKED, MAX_CHARS)
        notes.append("Odczytano pierwszy arkusz pliku XLSX%s." % (" („%s”)" % sheet if sheet else ""))
        fmt, encoding = "xlsx", "nie dotyczy (XLSX)"
    elif fmt == "ods":
        sheet, lines = formaty.read_ods(data, xlsx.MAX_CELLS)
        notes.append("Odczytano pierwszy arkusz pliku ODS%s." % (" („%s”)" % sheet if sheet else ""))
        encoding = "nie dotyczy (ODS)"
    elif fmt == "docx":
        lines, more = formaty.read_docx(data)
        notes.extend(more)
        encoding = "nie dotyczy (DOCX)"
    elif fmt in ("kmz", "kml", "gpx", "gml"):
        columns, rows, more = formaty.read_xml_format(fmt, data)
        notes.extend(more)
        return _finish(fmt, "UTF-8 (XML)", None, columns, rows, notes)
    else:
        text, encoding = _decode(data)
        if fmt == "json":
            fmt, columns, rows, more = formaty.read_json(text.lstrip())
            notes.extend(more)
            return _finish(fmt, encoding, None, columns, rows, notes)
        if fmt == "html":
            lines, more = formaty.read_html(text)
            notes.extend(more)
    if fmt != "csv":   # a grid: sheet, table in HTML or DOCX
        text, columns, rows = _grid(lines, notes, "Plik")
        if text is None:
            return _finish(fmt, encoding, None, columns, [(n, row, None) for n, row in rows], notes)
    sep = _separator(text.lstrip())
    source = {"label": "Plik", "fixes": []}
    try:
        rows, columns = parse_csv(text, source, notes, sep)
        if len(columns) == 1 and sep in columns[0]:   # every row wrapped in one pair of quotes (Marki)
            source["fixes"] = ["unwrap_quoted_rows"]
            rows, columns = parse_csv(text, source, notes, sep)
    except csv.Error as ex:
        raise ConverterError("Pliku nie da się odczytać jako CSV (%s)." % ex)
    return _finish(fmt, encoding, sep, columns, [(n, row, None) for n, row in rows], notes)


def _check_budget(columns, rows):
    if len(columns) > xlsx.MAX_COLUMNS:
        raise ConverterError("Plik ma %d kolumn, a wykaz może mieć najwyżej %d. Usuń zbędne kolumny." % (len(columns), xlsx.MAX_COLUMNS))
    if len(rows) > MAX_ROWS:
        raise ConverterError("Plik ma %d wierszy, a konwerter przyjmuje najwyżej %d. Podziel plik na części." % (len(rows), MAX_ROWS))
    if len(rows) * len(columns) > MAX_CELLS:
        raise ConverterError("Plik ma %d wierszy i %d kolumn, czyli więcej niż %d komórek. Usuń zbędne kolumny albo "
                             "podziel plik." % (len(rows), len(columns), MAX_CELLS))


def _finish(fmt, encoding, sep, columns, rows, notes):
    _check_budget(columns, rows)
    chars = sum(len(str(v)) for _, row, _ in rows for v in row.values())
    if chars > MAX_CHARS:
        raise ConverterError("Komórki pliku zawierają razem więcej niż %d mln znaków. Podziel plik." % (MAX_CHARS // 10 ** 6))
    if not columns or not rows:
        raise ConverterError("Plik nie zawiera wiersza nagłówka i co najmniej jednego wiersza danych.")
    if not any(g for _, _, g in rows):
        rows = _positions(columns, rows, notes)
    if len(set(columns)) != len(columns):
        dup = [c for c, k in Counter(columns).items() if k > 1]
        raise ConverterError("Kolumny %s występują w nagłówku więcej niż raz. Zostaw po jednej." % ", ".join(dup))
    if any(g for _, _, g in rows):
        columns = columns + [GEOM_LAT, GEOM_LON]
        rows = [(n, dict(row, **_geom_values(g)), g) for n, row, g in rows]
    return {"format": fmt, "kodowanie": encoding, "separator": sep, "columns": columns, "rows": rows, "notes": notes}


NORTH_HINT = re.compile(r"szer|lat|north|polnoc|^n$")
EAST_HINT = re.compile(r"dlug|lon|lng|east|wschod|^e$")


def _planar_number(value):
    try:
        return abs(float(re.sub(r"\s+", "", value).replace(",", "."))) >= 1000
    except ValueError:
        return False


def _numbers(rows, col):
    out = []
    for _, row, _ in rows:
        try:
            out.append(float(re.sub(r"\s+", "", str(row.get(col) or "")).replace(",", ".")))
        except ValueError:
            out.append(None)
    return out


def _with_points(rows, points):
    return [(n, row, {"type": "Point", "coordinates": [p[1], p[0]]} if p else None)
            for (n, row, _), p in zip(rows, points)]


def _positions(columns, rows, notes):
    """Position written in another way than two WGS84 columns -> row geometry (same for every format):
    degrees-minutes-seconds in a column (rewritten in place), one column with a whole point (GeoJSON, WKT, "lat, lon",
    DMS pair), or two columns of planar coordinates (PUWG 1992 / 2000, Web Mercator)."""
    for col in columns:   # DMS in separate columns: 52°13'47"N -> 52.2297222
        vals = _values(rows, col)
        if vals and _share(vals, uklady.dms) >= 0.8:
            for _, row, _ in rows:
                p = uklady.dms(str(row.get(col) or ""))
                if p:
                    row[col] = repr(round(p[0], 7))
            notes.append("Kolumna „%s”: współrzędne w stopniach, minutach i sekundach zamieniono na stopnie dziesiętne." % col)
    for col in columns:   # one column with the whole point
        vals = _values(rows, col)
        if not vals:
            continue
        if all(_point(v) for v in vals):   # GeoJSON point in a cell (Przemyśl CSV)
            notes.append("Kolumna „%s” zawiera punkty GeoJSON – współrzędne odczytano z niej." % col)
            return [(n, row, _point(row.get(col))) for n, row, _ in rows]
        cells = [uklady.point(str(row.get(col) or "")) for _, row, _ in rows]
        found = [c for c in cells if c]
        if len(found) < 0.8 * len(vals):
            continue
        srid = re.match(r"\s*SRID=(\d+);", vals[0])
        system = uklady.EPSG.get(int(srid.group(1))) if srid else None
        if found[0][2] == "latlon":
            points = [(c[0], c[1]) if c else None for c in cells]
            label = "stopnie, minuty i sekundy"
        else:
            # WKT and ArcGIS give x (easting) first; a plain pair is usually written latitude first (and so is a GML
            # pos in EPSG:2180, whose axis order is northing, easting).
            x_first = found[0][2] == "xy"
            best = (system, not x_first) if system is not None else uklady.best_system([c[:2] for c in found], x_first)
            if best is None:
                continue
            system, swapped = best
            # a single row written the other way round (as in Krosno) is turned back, like swap_lat_lon_outside_pl
            points = [(uklady.convert(system, *((c[1], c[0]) if swapped else c[:2]))
                       or uklady.convert(system, *(c[:2] if swapped else (c[1], c[0])))) if c else None for c in cells]
            label = uklady.SYSTEMS[system][0]
        notes.append("Kolumna „%s” zawiera całe położenie (%s) – współrzędne odczytano z niej (%d z %d wierszy)."
                     % (col, label, sum(1 for p in points if p), len(rows)))
        return _with_points(rows, points)
    if any(_share(_values(rows, c), _in_range(f)) >= 0.8 for c in columns for f in (LAT, LON)):
        return rows   # degrees in two columns: the usual path
    numeric = [c for c in columns if _share(_values(rows, c), _planar_number) >= 0.8][:10]
    best = None
    for i, c1 in enumerate(numeric):   # planar coordinates in two columns
        for c2 in numeric[i + 1:]:
            n1, n2 = _norm(c1), _norm(c2)
            x_first = not (NORTH_HINT.search(n1) or EAST_HINT.search(n2))
            pairs = [(a, b) for a, b in zip(_numbers(rows, c1), _numbers(rows, c2)) if a is not None and b is not None]
            found = uklady.best_system(pairs, x_first)
            if found and found[0]:
                system, swapped = found
                points = [uklady.convert(system, *((b, a) if swapped else (a, b))) if a is not None and b is not None
                          else None for a, b in zip(_numbers(rows, c1), _numbers(rows, c2))]
                hits = sum(1 for p in points if p)
                if hits >= 0.8 * len(rows) and (best is None or hits > best[0]):
                    east, north = (c2, c1) if swapped else (c1, c2)
                    best = (hits, points, system, east, north)
    if best:
        hits, points, system, east, north = best
        notes.append("Kolumny „%s” (wschodnia, easting) i „%s” (północna, northing) mają współrzędne w układzie %s – "
                     "przeliczono je na WGS84 (%d z %d wierszy). Sprawdź kilka punktów na mapie: przy zamienionych "
                     "kolumnach X/Y punkty wypadną w innym miejscu Polski." % (east, north, uklady.SYSTEMS[system][0],
                                                                            hits, len(rows)))
        return _with_points(rows, points)
    return rows


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
        "format_opis": "Rozpoznano po treści pliku: %s." % formaty.TITLES.get(t["format"], t["format"]),
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

def _key(text):
    return _norm(text).replace(" ", "")


def _enum_value(field, value):
    """Dictionary value by key or label from schema.json, ignoring case, Polish letters, spaces and underscores;
    also when the first word is the key ("Ograniczony dostęp")."""
    f = S.BY_NAME[field]
    lookup = {}
    for k in S.enum(field):
        label = f.get("etykiety", {}).get(k, "")
        for alias in (k, label, label.split("–")[0]):
            if _key(alias):
                lookup.setdefault(_key(alias), k)
    words = _norm(value).split()
    return lookup.get(_key(value)) or (lookup.get(words[0]) if words and words[0] in S.enum(field) else None) or value


def _date_value(field, value):
    """D.M.RRRR, D-M-RRRR, D/M/RRRR, RRRR/M/D -> RRRR-MM-DD; RRRR-MM -> last day of the month for expiry dates.
    Ambiguous (3/4/2027: DD/MM or MM/DD) and impossible dates stay as they are, so the validator names them."""
    m = YMD_RE.match(value)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(3)), int(m.group(4))
    else:
        m = DMY_RE.match(value)
        if m:
            d, mo, y = int(m.group(1)), int(m.group(3)), int(m.group(4))
            if m.group(2) == "/" and d <= 12 and mo <= 12 and d != mo:
                return value
        else:
            m = YM_RE.match(value)
            if not (m and field in EXPIRY_DATES and 1 <= int(m.group(2)) <= 12):
                return value
            y, mo = int(m.group(1)), int(m.group(2))
            d = calendar.monthrange(y, mo)[1]
    try:
        return datetime.date(y, mo, d).isoformat()
    except ValueError:
        return value


def normalize_value(field, value):
    """One cell -> the spelling the standard expects; unchanged when there is no unambiguous one."""
    value = _clean(value)
    if re.match(r"^'[+\d]", value):   # leading apostrophe: a spreadsheet's "keep as text" marker
        value = value[1:]
    f = S.BY_NAME.get(field)
    if not f or not value:
        return value
    t = f.get("type", "string")
    if S.enum(field):
        return _enum_value(field, value)
    if t == "boolean":
        word = _key(value)
        return (f.get("trueValues") or [S.TRUE_VALUE])[0] if word in YES_WORDS else \
            (f.get("falseValues") or [S.FALSE_VALUE])[0] if word in NO_WORDS else value
    if t == "date":
        return _date_value(field, value)
    if t == "number":
        number = re.sub(r"\s+", "", value).replace(",", ".")
        try:
            float(number)
            return number
        except ValueError:
            return value
    if field == "kod_pocztowy":
        m = POSTCODE_LOOSE_RE.match(value)
        return "%s-%s" % m.groups() if m else value
    return value


def _cell(value):
    if isinstance(value, bool):   # GeoJSON properties may be true/false or numbers
        return "true" if value else "false"
    return "" if value is None else str(value)


def normalize_rows(rows, mapping):
    """Normalise mapped cells in place. -> [{kolumna, pole, liczba, z, na, komunikat}], one per changed column."""
    out = []
    for col, target in mapping.items():
        if target not in S.BY_NAME:
            continue
        changed, first = 0, None
        for _, row, _ in rows:
            before = _cell(row.get(col))
            after = normalize_value(target, before)
            if after != _clean(before):
                changed += 1
                first = first or (before, after)
            row[col] = after
        if changed:
            filled = sum(1 for _, row, _ in rows if row.get(col))
            out.append({"kolumna": col, "pole": target, "liczba": changed, "z": first[0], "na": first[1],
                        "komunikat": "Kolumna „%s” (%s): ujednolicono zapis %d z %d wartości, np. „%s” → „%s”."
                                     % (col, TARGET_TITLES[target], changed, filled, first[0], first[1])})
    return out

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


def _osm_rows(columns, rows):
    """Numbers of rows whose own source or licence column says OpenStreetMap / ODbL (a list exported from OSM)."""
    marks = {_key(S.BY_NAME[f]["name"]): f for f in ("zrodlo", "licencja")}
    marks.update({_key(S.BY_NAME[f]["title"]): f for f in ("zrodlo", "licencja")})
    marks.update({"source": "zrodlo", "license": "licencja", "licence": "licencja"})
    cols = [c for c in columns if _key(c) in marks]
    def marked(value):
        value = _key(value)
        return value == "osm" or _key(OSM) in value or "odbl" in value
    return {n for n, row, _ in rows if any(marked(_cell(row.get(c))) for c in cols)}


def convert(data, filename, mapping, constants=None, today=None):
    """-> (csv_text, report). mapping: {column: target or ""}; constants: {field: value} filled into empty cells."""
    t = read_table(data, filename)
    entry = _entry(t["columns"], mapping)
    constants = {k: str(v).strip() for k, v in (constants or {}).items() if str(v).strip()}
    bad = [k for k in constants if k not in CONSTANT_TARGETS]
    if bad:
        raise ConverterError("Wartości stałej nie można ustawić dla pól: %s." % ", ".join(bad))
    constants = {k: normalize_value(k, v) for k, v in constants.items()}
    normalized = normalize_rows(t["rows"], mapping)
    for col in (c for c, target in mapping.items() if target == ADDRESS):   # "ul. Jasna 12 38-400 Krosno": comma
        for _, row, _ in t["rows"]:                                         # before the postcode, as parse_address needs
            row[col] = re.sub(r"(\S)\s+(\d{2}-\d{3}\s)", r"\1, \2", _cell(row.get(col)))
    osm = _osm_rows(t["columns"], t["rows"])
    records, notes = map_rows(t["rows"], t["columns"], {"resource_id": "plik"}, entry, "")
    # Mapped columns and constants both count: a constant must not put a hidden value back into the public file.
    hidden = [f for f in HIDDEN_PUBLIC if constants.get(f) or any(r[f] for r in records)]
    for (n, _, _), rec in zip(t["rows"], records):
        # System columns stay empty: the portal fills them from the dataset when it reads the list. A row the file
        # itself marks as OpenStreetMap / ODbL keeps the mark, so the list check rejects it (CLAUDE.md, rule 3).
        rec.update(zrodlo=OSM if n in osm else "", licencja=ODBL if n in osm else "", status="", wprowadzajacy_typ="",
                   data_aktualizacji="")
        if "row_number" in entry["record_id"]:
            rec["zrodlo_id"] = ""
        for k, v in constants.items():
            rec[k] = rec[k] or v
        # The file is meant for dane.gov.pl: the same columns stay empty as in every public export.
        rec.update({f: "" for f in HIDDEN_PUBLIC})
    text = to_csv(records)
    # Address without a position: the row stays in the file to be completed, but the list check rejects it.
    no_position = sum(1 for r in records if not (r[LAT] and r[LON])
                      and any(r[f] for f in ("nazwa_ulicy", "miejscowosc", "kod_pocztowy")))
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
        "normalizacje": normalized,
        "bez_wspolrzednych": no_position,
        "bez_wspolrzednych_komunikat": ("%d wierszy ma adres bez współrzędnych – nie trafią do wykazu, dopóki nie "
                                        "uzupełnisz położenia. Pobrany plik zawiera je z pustymi kolumnami "
                                        "szerokosc_geograficzna i dlugosc_geograficzna do uzupełnienia (np. odczytem "
                                        "z mapy albo telefonu przy urządzeniu)." % no_position) if no_position else "",
        "ukryte_pola": hidden,
        "ukryte_komunikat": ("Kolumny %s są w pobranym pliku puste: kontakt i numer seryjny nie trafiają do pliku "
                             "publicznego. Przekaż je ministerstwu kanałem rejestru (konto firmy albo potwierdzenie "
                             "z naklejki QR)." % ", ".join(TARGET_TITLES[f] for f in hidden)) if hidden else "",
    }
    return text, report
