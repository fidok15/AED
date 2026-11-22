"""Validation of AED records and CSV files against aed_standard/schema.json.

Report returned by validate_records() and validate_csv() (stable contract, consumed by
aed_service, the portal backend and the Angular frontend; also printed by `validate --json`):

    {
      "profil": "sprzedaz" | "publikacja",
      "poprawny": bool,                 # no issue with poziom == "blad"
      "podsumowanie": {
        "wiersze": int,                 # non-empty data rows (header excluded)
        "poprawne": int,                # data rows without any "blad" (0 when a file-level error exists)
        "bledy": int,                   # all "blad" issues, file-level included
        "ostrzezenia": int
      },
      "problemy": [
        {
          "wiersz": int | null,         # 1-based data row (first row after header = 1); null = whole file / header
          "pole": str | null,           # schema field name or column name from the header; null = whole row / file
          "poziom": "blad" | "ostrzezenie",
          "kod": str,                   # stable machine code, e.g. "format_daty", "brak_wymaganego"
          "komunikat": str              # Polish message telling how to fix it
        }
      ],
      "poprawne_wiersze": [int],        # 1-based numbers of data rows without errors
      "kompletnosc": [{"wiersz": int, "kompletnosc": int}]   # 0-100 per data row
    }

Row n is the n-th non-empty data row; validate_csv() returns records where records[n-1] is row n.
"""
import codecs
import csv
import datetime
import difflib
import io
import re

from . import schema as S

LAT, LON = "szerokosc_geograficzna", "dlugosc_geograficzna"
EXPIRY_DATES = ("data_waznosci_elektrod", "data_waznosci_baterii")
ACTIVE_REQUIRED = tuple(S.SCHEMA["wymagane_dla_statusu"]["aktywny"])
ERROR, WARNING = "blad", "ostrzezenie"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PL_DATE_RE = re.compile(r"^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$")
INT_RE = re.compile(r"^-?\d+$")
EMAIL_RE = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$")
# Hard rule 6: a cabinet code ("kod do szafki 1234", "PIN: 4590") in a free-text field; "kod pocztowy" is not one.
LOCK_CODE_RE = re.compile(r"\b(?:kod(?:u|em|y)?|pin(?:u|em)?|szyfr(?:u|em)?)\b(?!\s*pocztow)\D{0,20}?(?<!\d)\d{3,8}(?!\d)",
                          re.IGNORECASE)
LOCK_CODE_FIELDS = ("nazwa", "opis_lokalizacji", "godziny_dostepu_opis")


def issue(row, field, level, code, message):
    return {"wiersz": row, "pole": field, "poziom": level, "kod": code, "komunikat": message}


def serial_key(record):
    """Normalised (producent, numer_seryjny) or None when either is empty."""
    prod = re.sub(r"[\W_]+", "", (record.get("producent") or "").casefold())
    serial = re.sub(r"[\W_]+", "", (record.get("numer_seryjny") or "").casefold())
    return (prod, serial) if prod and serial else None


def parse_date(value):
    if not DATE_RE.match(value):
        return None
    try:
        return datetime.date(int(value[:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        return None


def to_float(value):
    try:
        return float(value)
    except ValueError:
        return None


def completeness(record):
    total = sum(S.WEIGHTS.values())
    got = sum(w for name, w in S.WEIGHTS.items() if (record.get(name) or "").strip())
    return int(round(100.0 * got / total)) if total else 0


def _label(name):
    return "„%s” (%s)" % (S.BY_NAME[name]["title"], name)


def check_value(name, value):
    """Type and constraint check of one non-empty value. Returns [(code, message)]."""
    f = S.BY_NAME[name]
    c = f.get("constraints", {})
    t = f.get("type", "string")
    example = f.get("przyklad") or ""
    if t == "number":
        if to_float(value) is None:
            if "," in value and to_float(value.replace(",", ".")) is not None:
                return [("przecinek_dziesietny", "Pole %s: użyj kropki jako separatora dziesiętnego, np. %s zamiast %s."
                         % (_label(name), value.replace(",", "."), value))]
            return [("format_liczby", "Pole %s musi być liczbą z kropką dziesiętną, np. %s. Otrzymano: „%s”."
                     % (_label(name), example, value))]
    elif t == "integer":
        if not INT_RE.match(value):
            return [("format_liczby_calkowitej", "Pole %s musi być liczbą całkowitą, np. %s. Otrzymano: „%s”."
                     % (_label(name), example, value))]
    elif t == "date":
        if parse_date(value) is None:
            m = PL_DATE_RE.match(value)
            hint = " Zamień na %s-%02d-%02d." % (m.group(3), int(m.group(2)), int(m.group(1))) if m else ""
            return [("format_daty", "Pole %s: wpisz istniejącą datę w formacie RRRR-MM-DD, np. %s. Otrzymano: „%s”.%s"
                     % (_label(name), example, value, hint))]
    elif t == "boolean":
        allowed = f.get("trueValues", [S.TRUE_VALUE]) + f.get("falseValues", [S.FALSE_VALUE])
        if value not in allowed:
            return [("wartosc_logiczna", "Pole %s: wpisz „%s”. Otrzymano: „%s”."
                     % (_label(name), "” albo „".join(allowed), value))]
    if "enum" in c and value not in c["enum"]:
        return [("spoza_slownika", "Pole %s: dozwolone wartości to %s. Otrzymano: „%s”."
                 % (_label(name), ", ".join(c["enum"]), value))]
    if "pattern" in c and not re.match(c["pattern"], value):
        return [("format_pola", "Pole %s ma niepoprawny format, np. %s. Otrzymano: „%s”."
                 % (_label(name), example or "zob. słownik pól", value))]
    if f.get("format") == "email" and not EMAIL_RE.match(value):
        return [("format_email", "Pole %s: podaj jeden poprawny adres e-mail instytucji, np. %s. Otrzymano: „%s”."
                 % (_label(name), example, value))]
    # Coordinate bounds are checked together in check_record (swap detection).
    if name not in (LAT, LON) and ("minimum" in c or "maximum" in c) and t in ("number", "integer"):
        v = float(value)
        if v < c.get("minimum", v) or v > c.get("maximum", v):
            return [("poza_zakresem", "Pole %s musi mieć wartość od %s do %s. Otrzymano: %s."
                     % (_label(name), c.get("minimum"), c.get("maximum"), value))]
    return []


def check_record(record, profile, row=None, today=None, columns=None):
    """Issues for one record (dict keyed by schema field names). Uniqueness is checked in validate_rows."""
    today = today or datetime.date.today()
    out = []
    val = {n: (record.get(n) or "").strip() for n in S.FIELD_NAMES}
    bad_type = set()
    for name in S.required(profile):
        if not val[name] and (columns is None or name in columns):
            out.append(issue(row, name, ERROR, "brak_wymaganego",
                             "Pole %s jest wymagane w profilu %s. Uzupełnij je." % (_label(name), profile)))
    for name in S.FIELD_NAMES:
        if val[name]:
            for code, msg in check_value(name, val[name]):
                bad_type.add(name)
                out.append(issue(row, name, ERROR, code, msg))

    if val["status"] == "aktywny":
        for name in ACTIVE_REQUIRED:
            if not val[name]:
                out.append(issue(row, name, ERROR, "wymagane_dla_aktywnego",
                                 "Rekord o statusie „aktywny” musi mieć wypełnione pole %s. Uzupełnij je albo zmień status."
                                 % _label(name)))

    if profile == "publikacja":
        for name in LOCK_CODE_FIELDS:
            if LOCK_CODE_RE.search(val[name]):
                out.append(issue(row, name, ERROR, "kod_do_szafki",
                                 "Pole %s wygląda na kod do szafki. Kod do szafki nie może trafić do danych otwartych – "
                                 "przekaż go kanałem dyspozytorskim." % _label(name)))

    if (val[LAT] or val[LON]) and not (val[LAT] and val[LON]):
        missing = LON if val[LAT] else LAT
        out.append(issue(row, missing, ERROR, "wspolrzedne_niepelne",
                         "Podano tylko jedną współrzędną. Uzupełnij pole %s albo usuń obie." % _label(missing)))
    elif val[LAT] and val[LON] and not ({LAT, LON} & bad_type):
        lat, lon = float(val[LAT]), float(val[LON])
        lat_min, lat_max = S.BY_NAME[LAT]["constraints"]["minimum"], S.BY_NAME[LAT]["constraints"]["maximum"]
        lon_min, lon_max = S.BY_NAME[LON]["constraints"]["minimum"], S.BY_NAME[LON]["constraints"]["maximum"]

        def inside(a, o):
            return lat_min <= a <= lat_max and lon_min <= o <= lon_max

        # ponytail: bounding box of Poland, not the border polygon; edge areas of neighbours pass.
        if not inside(lat, lon):
            if inside(lon, lat):
                out.append(issue(row, LAT, ERROR, "wspolrzedne_zamienione",
                                 "Szerokość i długość geograficzna są zamienione miejscami. Wpisz szerokość %s i długość %s."
                                 % (val[LON], val[LAT])))
            else:
                out.append(issue(row, LAT, ERROR, "poza_polska",
                                 "Punkt (%s, %s) leży poza Polską. Szerokość musi być od %s do %s, długość od %s do %s (WGS84, stopnie dziesiętne)."
                                 % (val[LAT], val[LON], lat_min, lat_max, lon_min, lon_max)))

    for name in S.FIELD_NAMES:
        if S.BY_NAME[name].get("type") != "date" or name in bad_type or not val[name]:
            continue
        d = parse_date(val[name])
        if name in EXPIRY_DATES:
            if d < today:
                out.append(issue(row, name, WARNING, "termin_minal",
                                 "Termin w polu %s minął (%s). Wymień element i wpisz nową datę ważności."
                                 % (_label(name), val[name])))
        elif d > today:
            out.append(issue(row, name, ERROR, "data_z_przyszlosci",
                             "Pole %s zawiera datę z przyszłości (%s). Sprawdź datę." % (_label(name), val[name])))
    return out


def validate_rows(rows, profile, today=None, columns=None, row_numbers=None):
    """Validate a list of records; adds the (producent, numer_seryjny) uniqueness rule."""
    issues = []
    seen = {}
    for i, rec in enumerate(rows):
        row = row_numbers[i] if row_numbers else i + 1
        issues.extend(check_record(rec, profile, row, today, columns))
        key = serial_key(rec)
        if key:
            if key in seen:
                issues.append(issue(row, "numer_seryjny", ERROR, "duplikat_numeru_seryjnego",
                                    "Urządzenie %s o numerze seryjnym %s występuje już w wierszu %d. Usuń powtórzony wiersz albo popraw numer."
                                    % (rec.get("producent", "").strip(), rec.get("numer_seryjny", "").strip(), seen[key])))
            else:
                seen[key] = row
    return issues


def make_report(issues, n_rows, profile, records=()):
    issues = sorted(issues, key=lambda p: (p["wiersz"] is not None, p["wiersz"] or 0))
    errors = sum(1 for p in issues if p["poziom"] == ERROR)
    file_error = any(p["poziom"] == ERROR and p["wiersz"] is None for p in issues)
    bad_rows = {p["wiersz"] for p in issues if p["poziom"] == ERROR and p["wiersz"] is not None}
    good = [] if file_error else [n for n in range(1, n_rows + 1) if n not in bad_rows]
    return {
        "profil": profile,
        "poprawny": errors == 0,
        "podsumowanie": {"wiersze": n_rows, "poprawne": len(good), "bledy": errors, "ostrzezenia": len(issues) - errors},
        "problemy": issues,
        "poprawne_wiersze": good,
        "kompletnosc": [{"wiersz": i + 1, "kompletnosc": completeness(r)} for i, r in enumerate(records)],
    }


def validate_records(records, profile, today=None):
    """Validate a list of record dicts (row n = records[n-1]). Does not mutate the input."""
    if profile not in S.PROFILES:
        raise ValueError("unknown profile: %s" % profile)
    return make_report(validate_rows(records, profile, today), len(records), profile, records)


def validate_csv(data, profile, today=None):
    """Validate a CSV file given as bytes. Returns (records, report).

    records[n-1] is data row n (empty data rows are skipped and not counted), keyed by the
    schema columns present in the header; empty list when the file cannot be read.
    See the module docstring for the report shape.
    """
    if profile not in S.PROFILES:
        raise ValueError("unknown profile: %s" % profile)
    def fail(code, message):
        return [], make_report([issue(None, None, ERROR, code, message)], 0, profile)

    save_as = "W arkuszu wybierz „Zapisz jako” → „CSV UTF-8 (rozdzielany przecinkami)”."
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return fail("kodowanie", "Plik jest zapisany w kodowaniu UTF-16, a standard wymaga UTF-8. " + save_as)
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return fail("kodowanie", "Plik nie jest zapisany w kodowaniu UTF-8. " + save_as)
    if "\x00" in text:
        return fail("znak_nul", "Plik zawiera znak NUL (bajt zerowy), więc nie jest zwykłym plikiem tekstowym CSV. " + save_as)
    try:
        raw = [r for r in csv.reader(io.StringIO(text, newline="")) if any(v.strip() for v in r)]
    except csv.Error as e:
        # Field-size policy: one value may have at most csv.field_size_limit() characters (131072 by
        # default). We do not raise it: the module runs inside the portal backend and the limit is
        # process-wide. No real AED field comes near it; a larger value is almost always a missing quote.
        if "field limit" in str(e):
            return fail("pole_za_dlugie", "Jedna z wartości ma więcej niż %d znaków. Sprawdź, czy nie brakuje zamykającego "
                                          "cudzysłowu – wtedy reszta pliku staje się jedną wartością." % csv.field_size_limit())
        return fail("format_csv", "Pliku nie da się odczytać jako CSV (%s). " % e + save_as)
    if not raw:
        return fail("pusty_plik", "Plik nie zawiera żadnych wartości. Dodaj wiersz nagłówka i co najmniej jeden wiersz danych.")
    issues = []
    header = [h.strip() for h in raw[0]]
    data_rows = raw[1:]
    first_line = text.lstrip().splitlines()[0]
    if len(header) == 1:
        if "," in header[0]:
            issues.append(issue(None, None, ERROR, "wiersz_w_cudzyslowie",
                                "Każdy wiersz pliku jest ujęty w jedną parę cudzysłowów, więc cały wiersz jest jedną wartością. "
                                "Zapisz plik ponownie jako CSV bez dodatkowego cudzysłowu wokół wierszy."))
            return [], make_report(issues, len(data_rows), profile)
        for sep, sep_name in ((";", "średnik"), ("\t", "tabulator"), ("|", "pionową kreskę")):
            if sep in first_line:
                issues.append(issue(None, None, ERROR, "separator",
                                    "Plik używa separatora: %s. Standard wymaga przecinka. Zapisz plik jako „CSV UTF-8 (rozdzielany przecinkami)”." % sep_name))
                return [], make_report(issues, len(data_rows), profile)

    known = set()
    seen_cols = set()
    for h in header:
        if not h:
            issues.append(issue(None, None, ERROR, "pusta_nazwa_kolumny",
                                "Nagłówek zawiera kolumnę bez nazwy. Usuń pustą kolumnę albo wpisz nazwę pola ze standardu."))
        elif h in seen_cols:
            issues.append(issue(None, h, ERROR, "powtorzona_kolumna", "Kolumna „%s” występuje w nagłówku więcej niż raz. Zostaw jedną." % h))
        elif h not in S.BY_NAME:
            close = difflib.get_close_matches(h, S.FIELD_NAMES, n=1, cutoff=0.75)
            hint = " Czy chodziło o „%s”?" % close[0] if close else ""
            issues.append(issue(None, h, ERROR, "nieznana_kolumna",
                                "Kolumna „%s” nie występuje w standardzie. Popraw nazwę zgodnie z arkuszem „Słownik pól” albo usuń kolumnę.%s" % (h, hint)))
        else:
            known.add(h)
        seen_cols.add(h)
    for name in S.required(profile):
        if name not in seen_cols:
            issues.append(issue(None, name, ERROR, "brak_kolumny",
                                "Brakuje kolumny „%s” wymaganej w profilu %s. Dodaj ją do nagłówka." % (name, profile)))
    if not data_rows:
        issues.append(issue(None, None, ERROR, "brak_wierszy", "Plik nie zawiera wierszy danych pod nagłówkiem."))

    header_words = set(S.FIELD_NAMES) | {f["title"].casefold() for f in S.FIELDS}
    records, checked, checked_rows = [], [], []
    for n, values in enumerate(data_rows, start=1):
        # Best-effort record even for broken rows, so records[n-1] is always row n.
        records.append({h: v for h, v in zip(header, values) if h in known})
        filled = [v.strip() for v in values if v.strip()]
        if len(values) == 1 and len(header) > 1 and "," in values[0]:
            issues.append(issue(n, None, ERROR, "wiersz_w_cudzyslowie",
                                "Cały wiersz jest ujęty w jedną parę cudzysłowów. Usuń cudzysłów otaczający wiersz."))
        elif sum(1 for v in filled if v in header_words or v.casefold() in header_words) * 2 >= len(filled):
            issues.append(issue(n, None, ERROR, "powtorzony_naglowek",
                                "Wiersz wygląda jak drugi wiersz nagłówka. Plik może mieć tylko jeden wiersz nagłówka – usuń ten wiersz."))
        elif len(values) != len(header):
            issues.append(issue(n, None, ERROR, "liczba_kolumn",
                                "Wiersz ma %d wartości, a nagłówek %d kolumn. Wartości zawierające przecinek ujmij w cudzysłów."
                                % (len(values), len(header))))
        else:
            checked.append(records[-1])
            checked_rows.append(n)
    issues.extend(validate_rows(checked, profile, today, known, checked_rows))
    return records, make_report(issues, len(data_rows), profile, records)


def format_report(result, name=""):
    """Human-readable Polish report."""
    s = result["podsumowanie"]
    lines = [
        "Raport walidacji%s – profil %s" % (" pliku " + name if name else "", result["profil"]),
        "Wiersze danych: %d, poprawne: %d, błędy: %d, ostrzeżenia: %d"
        % (s["wiersze"], s["poprawne"], s["bledy"], s["ostrzezenia"]),
        "Wynik: %s" % ("plik poprawny" if result["poprawny"] else "plik wymaga poprawek"),
        "",
    ]
    for p in result["problemy"]:
        where = "wiersz %d" % p["wiersz"] if p["wiersz"] is not None else "cały plik"
        if p["pole"]:
            where += ", pole %s" % p["pole"]
        lines.append("[%s] %s: %s (%s)" % ("BŁĄD" if p["poziom"] == ERROR else "OSTRZEŻENIE", where, p["komunikat"], p["kod"]))
    return "\n".join(lines)
