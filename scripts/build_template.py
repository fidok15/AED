"""Generate wzorzec/wzorzec-aed.xlsx and the example CSV files from aed_standard/schema.json.

    uv run --with openpyxl python scripts/build_template.py
"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from aed_standard import schema as S  # noqa: E402
from aed_standard.dedup import make_id  # noqa: E402

OUT = os.path.join(ROOT, "wzorzec")

# Fictional seller data: company, devices and buyers do not exist.
SELLER = {"wprowadzajacy_typ": "sprzedawca", "wprowadzajacy_nazwa": "Fikcyjny Sprzedawca AED Sp. z o.o."}
BUYERS = [
    ("Przychodnia Przykładowa w Przykładowie", "aed@przychodnia.przyklad.example", "+48 00 000 00 01"),
    ("Szkoła Podstawowa nr 0 w Fikcyjnowie", "sekretariat@sp0.fikcyjnowo.example", "+48 00 000 00 02"),
    ("Hala Sportowa Demonstracyjna", "biuro@hala-demo.example", "+48 00 000 00 03"),
]


def seller_rows():
    rows = []
    for i in range(1, 11):
        name, email, phone = BUYERS[i % len(BUYERS)]
        rows.append(dict(SELLER, producent="FikcjaMed", model="DemoAED %d00" % (1 + i % 3),
                         numer_seryjny="DEMO-%05d" % i, data_produkcji="2025-%02d-15" % i,
                         data_waznosci_elektrod="2028-%02d-28" % i,
                         # every other battery date as on the label: month only (valid to the end of the month)
                         data_waznosci_baterii="2030-%02d" % i if i % 2 else "2030-%02d-28" % i,
                         dysponent_nazwa=name, dysponent_email=email, dysponent_telefon=phone))
    return rows


def seller_error_rows():
    rows = seller_rows()
    rows[0]["numer_seryjny"] = ""                                  # brak_wymaganego
    rows[1]["data_produkcji"] = "15.03.2024"                       # format_daty (with hint)
    rows[2]["data_waznosci_elektrod"] = "2024-01-31"               # termin_minal (warning)
    rows[3]["data_produkcji"] = "2099-01-01"                       # data_z_przyszlosci
    rows[4].update(dostep="otwarty")                               # spoza_slownika
    rows[5].update(szerokosc_geograficzna="21.012229", dlugosc_geograficzna="52.229676")  # wspolrzedne_zamienione
    rows[6]["numer_seryjny"] = rows[7]["numer_seryjny"]            # duplikat_numeru_seryjnego (row 8)
    rows[8]["dysponent_email"] = "sekretariat(at)sp0"              # format_email
    rows[9].update(szerokosc_geograficzna="52,229676", dlugosc_geograficzna="21.012229")  # przecinek_dziesietny
    return rows


PLACES = [  # fictional places, coordinates inside Poland
    ("Hala Sportowa Demonstracyjna", "Fikcyjnowo", "Przykładowa", "1", "00-001", "52.100000", "19.400000", "24/7", "nie"),
    ("Przychodnia Przykładowa", "Przykładowo", "Testowa", "12A", "00-002", "51.500000", "18.900000", "Mo-Fr 08:00-18:00", "tak"),
    ("Szkoła Podstawowa nr 0 w Fikcyjnowie", "Fikcyjnowo", "Szkolna", "7", "00-001", "52.101500", "19.402500", "Mo-Fr 07:30-16:00", "tak"),
]


def publication_rows():
    rows = []
    for i, (nazwa, city, street, nr, kod, lat, lon, hours, inside) in enumerate(PLACES, start=1):
        rec = S.blank_record()
        rec.update(seller_rows()[i - 1])
        rec.update(id_aed=make_id("zgloszenie", "DEMO-%05d" % i), nazwa=nazwa, miejscowosc=city, cecha_ulicy="ulica",
                   nazwa_ulicy=street, nr_budynku=nr, kod_pocztowy=kod, szerokosc_geograficzna=lat,
                   dlugosc_geograficzna=lon, opis_lokalizacji="Hol przy wejściu głównym", wewnatrz_budynku=inside,
                   dostep="publiczny", godziny_dostepu=hours, status="zweryfikowany", data_weryfikacji="2026-11-15",
                   pietro=str(i - 1), sposob_ustalenia_polozenia="pomiar_przy_urzadzeniu", stan_urzadzenia="gotowy",
                   data_stanu="2026-11-15",
                   sposob_weryfikacji="qr", data_aktualizacji="2026-11-15", zrodlo="zgloszenie",
                   zrodlo_id="%012x" % (0xdec0de000000 + i), licencja="CC0 1.0")  # opaque, as in aed_service
        rows.append(rec)
    return rows


PUBLIC_SHEET = "Dane otwarte (publikacja)"
PUBLIC_FIELDS = S.public_fields()


def public_rows():
    """Publication rows as the open export writes them (aed_standard.build.to_public), restricted to its columns."""
    from aed_standard.build import to_public
    return [{k: v for k, v in to_public(r).items() if k in PUBLIC_FIELDS} for r in publication_rows()]


def public_note():
    hidden = ", ".join("%s (%s)" % (S.BY_NAME[n]["title"], n) for n in S.hidden_fields())
    status_req = "; ".join("dla statusu „%s”: %s" % (st, ", ".join(names))
                           for st, names in sorted(S.SCHEMA["wymagane_dla_statusu"].items()))
    return [
        "Widok publikacyjny: tylko kolumny, które trafiają do zbioru krajowego na dane.gov.pl (jeden wiersz = jedno urządzenie).",
        "Zbierane, ale niepublikowane: %s. Kontakt dysponenta służy wyłącznie do próśb o potwierdzenie danych "
        "i przypomnień o terminach baterii i elektrod; numer seryjny zostaje w rejestrze ministerstwa do deduplikacji "
        "i obsługi wezwań producenta. Te kolumny są w eksporcie puste, a w tym arkuszu ich nie ma." % hidden,
        "Wiersz „wymagane” nad nagłówkiem: „tak” – pole wymagane w profilu „publikacja”; "
        "„przy statusie” – wymagane dopiero dla statusu (%s)." % status_req,
        "",
    ]


def write_csv(name, rows, columns):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def constraints_text(f):
    c = f.get("constraints", {})
    parts = []
    if f["name"] in S.MONTH_DATE_FIELDS:
        parts.append("data RRRR-MM-DD albo miesiąc RRRR-MM (ważne do końca miesiąca)")
        c = {k: v for k, v in c.items() if k != "pattern"}   # the pattern only spells out the two forms
    elif f.get("type") == "date":
        parts.append("data RRRR-MM-DD")
    if f.get("type") == "boolean":
        parts.append("tak / nie")
    if "enum" in c:
        parts.append("słownik: " + ", ".join(c["enum"]))
    if "pattern" in c:
        parts.append("wzorzec: " + c["pattern"])
    if "minimum" in c or "maximum" in c:
        parts.append("zakres: %s–%s" % (c.get("minimum", ""), c.get("maximum", "")))
    if f.get("format") == "email":
        parts.append("adres e-mail")
    return "; ".join(parts)


def weight_text(f):
    by_status = "; ".join("%s dla statusu „%s”" % (w, st) for st, w in sorted(f.get("waga_dla_statusu", {}).items()))
    return "%s (%s)" % (f.get("waga", 0), by_status) if by_status else f.get("waga", 0)


def enum_meaning(f, value):
    """Meaning of an enum value, taken from the field description: 'value (meaning)'."""
    m = re.search(r"\b%s \(((?:[^()]|\([^()]*\))*)\)" % re.escape(value), f["description"])
    return m.group(1) if m else f["description"]


INSTRUCTIONS = [
    "Wzorcowy zakres danych o defibrylatorach AED – instrukcja",
    "",
    "1. Jeden wiersz w arkuszu „Dane” to jedno urządzenie. Nie zmieniaj nazw kolumn w pierwszym wierszu.",
    "2. Wypełnij kolumny wymagane w Twoim profilu (arkusz „Słownik pól”). Pozostałe kolumny możesz zostawić puste albo usunąć.",
    "3. Profil „sprzedaz”: producent lub sprzedawca zgłasza urządzenie przy sprzedaży – dane urządzenia i nabywcy (dysponenta). Miejsce montażu nie jest jeszcze potrzebne.",
    "4. Profil „publikacja”: rekord gotowy do zbioru krajowego na dane.gov.pl – z nazwą miejsca, współrzędnymi i miejscowością.",
    "5. Daty wpisuj jako RRRR-MM-DD, np. 2026-03-01; datę produkcji i daty ważności baterii i elektrod możesz podać jako sam miesiąc RRRR-MM, np. 2030-01 (ważne do końca miesiąca). Liczby z kropką dziesiętną, np. 52.395198. Współrzędne w układzie WGS84.",
    "6. Wartości słownikowe wybieraj z listy rozwijanej (arkusz „Słowniki”). Pola logiczne: „tak” albo „nie”.",
    "7. Kontakt podawaj wyłącznie instytucjonalny. Nie wpisuj danych osobowych ani kodów do szafek.",
    "8. Zapis do CSV: Plik → Zapisz jako → „CSV UTF-8 (rozdzielany przecinkami)”. Jeden wiersz nagłówka, separator przecinek, bez cudzysłowu wokół całych wierszy.",
    "9. Usuń wiersz przykładowy przed wysłaniem.",
    "10. Arkusz „%s” pokazuje, które kolumny trafiają do zbioru otwartego na dane.gov.pl, a które zostają tylko w rejestrze ministerstwa." % PUBLIC_SHEET,
    "",
    "Co dzieje się po wysłaniu:",
    "– portal sprawdza plik i pokazuje raport: numer wiersza, pole i opis, co poprawić; wiersze z błędami nie są przyjmowane;",
    "– każde przyjęte urządzenie dostaje stały identyfikator id_aed i naklejkę z kodem QR (status „zgloszony”);",
    "– dysponent potwierdza miejsce i godziny dostępu po zeskanowaniu kodu QR – rekord staje się „zweryfikowany” i trafia do zbioru na dane.gov.pl;",
    "– przed końcem ważności baterii i elektrod dysponent dostaje przypomnienie, a raz na jakiś czas prośbę o potwierdzenie danych.",
]


def build_xlsx(path):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    bold = Font(bold=True)

    ws = wb.active
    ws.title = "Dane"
    ws.append(S.FIELD_NAMES)
    ws.append([f.get("przyklad", "") for f in S.FIELDS])
    for i, f in enumerate(S.FIELDS, start=1):
        col = get_column_letter(i)
        ws.cell(row=1, column=i).font = bold
        ws.column_dimensions[col].width = max(14, len(f["name"]) + 2)
        values = S.enum(f["name"]) or (f.get("trueValues", []) + f.get("falseValues", []) if f.get("type") == "boolean" else [])
        if values:
            dv = DataValidation(type="list", formula1='"%s"' % ",".join(values), allow_blank=True,
                                errorTitle="Wartość spoza słownika", error="Wybierz wartość z listy: " + ", ".join(values))
            ws.add_data_validation(dv)
            dv.add("%s2:%s5000" % (col, col))
    ws.freeze_panes = "A2"

    ws = wb.create_sheet(PUBLIC_SHEET)
    for line in public_note():
        ws.append([line])
    req_pub = set(S.required("publikacja"))
    req_status = {n for names in S.SCHEMA["wymagane_dla_statusu"].values() for n in names}
    ws.append(["tak" if n in req_pub else "przy statusie" if n in req_status else "" for n in PUBLIC_FIELDS])
    header_row = ws.max_row + 1
    ws.append(PUBLIC_FIELDS)
    example = public_rows()[0]
    ws.append([example[n] for n in PUBLIC_FIELDS])
    red = Font(bold=True, color="B00020")
    for i, n in enumerate(PUBLIC_FIELDS, start=1):
        ws.cell(row=header_row, column=i).font = red if n in req_pub else bold
        ws.column_dimensions[get_column_letter(i)].width = max(14, len(n) + 2)
    ws.cell(row=1, column=1).font = bold
    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)

    ws = wb.create_sheet("Słownik pól")
    ws.append(["pole", "nazwa", "typ", "wymagane – sprzedaz", "wymagane – publikacja", "ograniczenia",
               "waga w kompletności", "publiczne", "opis", "przykład"])
    req = {p: set(S.required(p)) for p in S.PROFILES}
    for f in S.FIELDS:
        ws.append([f["name"], f["title"], f.get("type", "string"), "tak" if f["name"] in req["sprzedaz"] else "",
                   "tak" if f["name"] in req["publikacja"] else "", constraints_text(f), weight_text(f),
                   "tak" if f["name"] in PUBLIC_FIELDS else "nie (tylko rejestr)", f["description"], f.get("przyklad", "")])

    ws = wb.create_sheet("Słowniki")
    ws.append(["pole", "wartość", "znaczenie"])
    for f in S.FIELDS:
        for v in S.enum(f["name"]):
            ws.append([f["name"], v, enum_meaning(f, v)])
        if f.get("type") == "boolean":
            for v in f.get("trueValues", [S.TRUE_VALUE]) + f.get("falseValues", [S.FALSE_VALUE]):
                ws.append([f["name"], v, f["description"]])

    ws = wb.create_sheet("Mapowanie źródeł")
    keys = []
    for f in S.FIELDS:
        keys.extend(k for k in f.get("zrodla", {}) if k not in keys)
    ws.append(["pole"] + keys)
    for f in S.FIELDS:
        ws.append([f["name"]] + [f.get("zrodla", {}).get(k, "") for k in keys])

    ws = wb.create_sheet("Instrukcja")
    for line in INSTRUCTIONS:
        ws.append([line])
    ws.column_dimensions["A"].width = 140

    for ws in wb.worksheets[2:5]:
        for cell in ws[1]:
            cell.font = bold
        ws.freeze_panes = "A2"
        for i in range(1, ws.max_column + 1):
            ws.column_dimensions[get_column_letter(i)].width = 60 if ws.cell(row=1, column=i).value in ("opis", "znaczenie") else 24
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    wb.save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    seller_cols = [n for n in S.FIELD_NAMES if n in set(S.required("sprzedaz")) | set(SELLER) | {"dysponent_telefon"}]
    write_csv("przyklad-sprzedawca.csv", seller_rows(), seller_cols)
    error_cols = seller_cols + [n for n in ("szerokosc_geograficzna", "dlugosc_geograficzna", "dostep")]
    error_cols = [n for n in S.FIELD_NAMES if n in error_cols]
    write_csv("przyklad-sprzedawca-bledy.csv", seller_error_rows(), error_cols)
    write_csv("przyklad-publikacja.csv", publication_rows(), S.FIELD_NAMES)
    write_csv("przyklad-dane-otwarte.csv", public_rows(), PUBLIC_FIELDS)
    build_xlsx(os.path.join(OUT, "wzorzec-aed.xlsx"))
    for name in sorted(os.listdir(OUT)):
        print(os.path.join(OUT, name))


if __name__ == "__main__":
    main()
