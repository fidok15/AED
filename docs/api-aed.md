# API usługi AED – kontrakt

Kontrakt między frontendem (`frontend/`, moduł AED) a usługą `aed_service/`. Usługa jest samodzielna (plan B wobec pełnego stosu portalu), napisana we frameworku Falcon – tym samym, którego używa API dane.gov.pl – tak, żeby widoki dało się przenieść do aplikacji `mcod/aed` w forku portalu.

Zasady ogólne:

- prefiks: `/api/aed`; odpowiedzi w JSON, UTF-8; daty `RRRR-MM-DD`;
- pola urządzenia mają dokładnie nazwy z `aed_standard/schema.json`;
- błąd: `{"blad": {"kod": "...", "komunikat": "..."}}` z właściwym kodem HTTP;
- uwierzytelnienie: nagłówek `Authorization: Bearer <token>` z logowania; role: `firma`, `ministerstwo`;
- konta demonstracyjne są zakładane przy starcie usługi i wypisane w `aed_service/README.md`.

## Sesja

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `POST /api/aed/sesja` | każdy | `{email, haslo}` → `{token, konto: {id, nazwa, rola, typ_podmiotu}}` |
| `GET /api/aed/sesja` | zalogowany | dane bieżącego konta |

## Schemat

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `GET /api/aed/schemat` | każdy | zawartość `aed_standard/schema.json` – z niej frontend buduje formularze |

## Zgłoszenia firmy (producent, sprzedawca)

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `POST /api/aed/zgloszenia` | firma | `multipart/form-data`, pole `plik` (CSV). Walidacja profilem `sprzedaz`. Wiersze poprawne są przyjmowane, błędne odrzucane. |
| `POST /api/aed/zgloszenia/sprawdz` | firma | to samo, ale bez zapisu – podgląd raportu przed wysłaniem |
| `GET /api/aed/zgloszenia` | firma | historia zgłoszeń konta |
| `POST /api/aed/urzadzenia` | firma | jedno urządzenie jako JSON (formularz); ta sama walidacja |

Odpowiedź zgłoszenia:

```json
{
  "id": 12,
  "utworzono": "2026-11-21T19:04:11",
  "podsumowanie": {"wiersze": 10, "przyjete": 8, "odrzucone": 2, "bledy": 3, "ostrzezenia": 1, "duplikaty": 1},
  "problemy": [
    {"wiersz": 4, "pole": "data_produkcji", "poziom": "blad", "kod": "format_daty", "komunikat": "…"}
  ],
  "przyjete": [
    {"id_aed": "AED-7F3K9Q2M4XTB", "producent": "…", "model": "…", "numer_seryjny": "…",
     "naklejka_url": "/api/aed/urzadzenia/AED-7F3K9Q2M4XTB/naklejka.svg",
     "link_aktywacyjny": "/aed/qr/AED-7F3K9Q2M4XTB?t=<token zarządcy>"}
  ]
}
```

`duplikaty` to wiersze, których producent i numer seryjny są już w rejestrze – nie tworzą nowego rekordu.

## Urządzenie i naklejka QR

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `GET /api/aed/urzadzenia/{id_aed}` | każdy | rekord w zakresie publicznym (bez kontaktu, bez numeru seryjnego) |
| `GET /api/aed/urzadzenia/{id_aed}?t=<token>` | zarządca | pełny rekord do edycji |
| `GET /api/aed/urzadzenia/{id_aed}/naklejka.svg` | każdy | naklejka z kodem QR prowadzącym do `/aed/qr/{id_aed}` |
| `POST /api/aed/urzadzenia/{id_aed}/potwierdzenie` | zarządca (token `t`) | uzupełnienie i potwierdzenie danych; rekord przechodzi w `aktywny` |
| `POST /api/aed/urzadzenia/{id_aed}/sygnal` | każdy | zgłoszenie z miejsca bez uprawnień; nie zmienia danych, trafia do dysponenta |

Kod QR na naklejce jest publiczny, więc sam skan nie daje prawa edycji. Zarządca dostaje prawo edycji przez link z tokenem wysłany na `dysponent_email` (pierwsza aktywacja oraz każde późniejsze potwierdzenie).

Potwierdzenie (żądanie):

```json
{
  "t": "<token zarządcy>",
  "nazwa": "Urząd Miasta Legionowo",
  "szerokosc_geograficzna": 52.395198, "dlugosc_geograficzna": 20.931382,
  "miejscowosc": "Legionowo", "nazwa_ulicy": "Piłsudskiego", "nr_budynku": "41", "kod_pocztowy": "05-120",
  "opis_lokalizacji": "Hol główny, przy portierni",
  "wewnatrz_budynku": "tak",
  "dostep": "publiczny",
  "godziny_dostepu": "Mo-Fr 08:00-16:00",
  "stan": "sprawny"
}
```

`stan`: `sprawny` albo `problem` (wtedy wymagane `uwagi`). Odpowiedź: zaktualizowany rekord z `status`, `data_weryfikacji`, `sposob_weryfikacji`, `kompletnosc`.

Sygnał (żądanie): `{"typ": "jest" | "brak" | "uszkodzony" | "zamkniety", "szerokosc_geograficzna": …, "dlugosc_geograficzna": …, "uwagi": "…"}`. Współrzędne są opcjonalne.

## Rejestr krajowy

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `GET /api/aed/urzadzenia` | każdy | lista stronicowana; parametry: `status`, `zrodlo`, `dostep`, `q` (nazwa, miejscowość), `strona`, `na_stronie` |
| `GET /api/aed/urzadzenia.geojson` | każdy | punkty do mapy: `id_aed`, `nazwa`, `status`, `dostep`, `godziny_dostepu`, `kompletnosc`, `zrodlo`; parametr `bbox=minLon,minLat,maxLon,maxLat` |
| `GET /api/aed/statystyki` | każdy | liczba rekordów wg statusu i źródła, średnia kompletność, liczba dostawców, liczba potwierdzonych w ostatnich 90 dniach |
| `GET /api/aed/sprzedawcy` | każdy | mapa i ranking firm: nazwa, miejscowość, współrzędne siedziby, liczba urządzeń, średnia kompletność, udział aktywnych, `odznaka` (tak/nie) |
| `GET /api/aed/eksport/dane-gov-pl.csv` | każdy | eksport publikacyjny (profil `publikacja`, bez ODbL i bez `dostep = prywatny`) |

Lista stronicowana: `{"dane": [...], "razem": 19000, "strona": 1, "na_stronie": 50}`.

## Panel ministerstwa

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `GET /api/aed/duplikaty` | ministerstwo | pary do ręcznego przeglądu: oba rekordy, odległość w metrach, podobieństwo |
| `POST /api/aed/duplikaty/{id}` | ministerstwo | `{"decyzja": "polacz" | "rozdziel"}` |
| `GET /api/aed/wiadomosci` | ministerstwo | skrzynka nadawcza: prośby o potwierdzenie i przypomnienia (odbiorca, temat, treść, link, data) |
| `POST /api/aed/przypomnienia/uruchom` | ministerstwo | ręczne uruchomienie zadania cyklicznego: prośby o potwierdzenie dla rekordów bez weryfikacji od 6 miesięcy, przypomnienia 60 dni przed końcem ważności baterii lub elektrod, oznaczenie `nieaktualny` po 12 miesiącach bez potwierdzenia |
| `POST /api/aed/mapper/uruchom` | ministerstwo | ręczne uruchomienie mappera źródeł; odpowiedź: ile rekordów przybyło, ile zmieniono, ile połączono |

Wiadomości w prototypie nie są wysyłane pocztą – trafiają do skrzynki nadawczej, którą widać w panelu.
