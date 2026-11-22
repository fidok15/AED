# Usługa AED (prototyp)

Samodzielne API (Falcon 4 + SQLite) realizujące kontrakt z `docs/api-aed.md`. Walidacja, mapper, deduplikacja i eksport pochodzą z `aed_standard`.

## Start

Z katalogu głównego repozytorium (wymaga `uv`; Python 3.13, bo Falcon nie ma jeszcze wsparcia dla 3.15):

```
uv run --python 3.13 --with-requirements aed_service/requirements.txt python -m aed_service
```

- adres: `http://localhost:8085/api/aed` (zmiana portu: `AED_PORT=9000`),
- pierwszy start zakłada konta demo i importuje rejestr krajowy z `datasets/raw` (ok. 19 tys. rekordów, kilka sekund),
- baza: `aed_service/aed_service.db` (plik ignorowany przez git; inna ścieżka: `AED_DB=/ścieżka/plik.db`),
- CORS: dozwolony `http://localhost:4200` (zmiana: `AED_CORS_ORIGINS=http://a,http://b`),
- adres frontendu w kodzie QR naklejki: `AED_BASE_URL` (domyślnie `http://localhost:4200`).

## Konta demo (dane fikcyjne)

| Rola | E-mail | Hasło | Podmiot |
|---|---|---|---|
| ministerstwo | `ministerstwo@aed.example` | `ministerstwo-demo` | Ministerstwo Cyfryzacji (konto demo), Warszawa |
| firma (producent) | `pulsar@aed.example` | `pulsar-demo` | Pulsar Medical Sp. z o.o., Gdańsk |
| firma (sprzedawca) | `serwis@aed.example` | `serwis-demo` | Serwis Rytm Sp. z o.o., Poznań |

## Proxy w Angularze

W `frontend/proxy.*.conf.json` (dev) skieruj `/api/aed` na usługę, przed regułą dla `/api` portalu:

```json
{ "/api/aed": { "target": "http://localhost:8085", "secure": false, "changeOrigin": true } }
```

Bez proxy też działa (CORS dla `localhost:4200`), wtedy wołaj `http://localhost:8085/api/aed/...`.

## Odznaka sprzedawcy

`odznaka = tak`, gdy firma ma co najmniej jedno urządzenie oraz jednocześnie:

- średnia kompletność jej urządzeń >= `BADGE_MIN_COMPLETENESS` = 70,
- udział urządzeń zweryfikowanych (status `zweryfikowany`) >= `BADGE_MIN_ACTIVE_SHARE` = 0,5.

Stałe są na górze `aed_service/app.py`; progi zwraca też `GET /api/aed/sprzedawcy` w polu `progi`.

## Reguły zadań cyklicznych

Stałe w `app.py`: prośba o potwierdzenie po 183 dniach bez weryfikacji, przypomnienie 60 dni przed końcem ważności baterii lub elektrod, `nieaktualny` po 365 dniach. Ten sam rodzaj wiadomości dla urządzenia nie jest powtarzany przez 30 dni (więc ponowne uruchomienie tego samego dnia niczego nie dubluje).

## Harmonogram zadań cyklicznych

Przy starcie (`python -m aed_service`) działa wątek-demon, który co `AED_CYCLE_HOURS` godzin (domyślnie 24, `0` wyłącza; w testach nie startuje) wykonuje cykl:

1. odświeżenie źródeł: `scripts/download_aed_data.py` jako podproces (o ile plik istnieje); brak sieci lub tokenu Warszawy nie przerywa cyklu, używana jest migawka z `datasets/raw`,
2. mapper (upsert rekordów z importu; rekordy ze zgłoszeń, potwierdzone przez zarządcę i scalone nie są ruszane),
3. przypomnienia.

Każde uruchomienie (także ręczne przyciski ministerstwa) trafia do historii: `GET /api/aed/zadania` (ministerstwo, 20 ostatnich, najnowsze pierwsze):

```json
{"dane": [{"id": 3, "start": "2026-11-21T18:00:00", "koniec": "2026-11-21T18:00:09",
  "wyzwalacz": "harmonogram", "rodzaj": "cykl", "odswiezono": "Pobrano źródła z sieci",
  "mapper": {"dodano": 0, "zmieniono": 2, "polaczono": 266, "do_przegladu": 195},
  "przypomnienia": {"nieaktualne": 0, "prosby_o_potwierdzenie": 1, "przypomnienia_terminow": 1},
  "bledy": ["Źródło niedostępne: ... Użyto zapisanej migawki."]}]}
```

Odświeżenie jest bezpieczne: wpisy starego `datasets/raw/manifest.json`, których skrypt nie pobrał ponownie, są zachowywane (ich pliki zostają na dysku), a po awarii skryptu manifest jest przywracany. `odswiezono` mówi, co faktycznie się udało, np. „Odświeżono 1 z 18 plików źródłowych; pozostałe z zapisanej migawki”, a `bledy` zawiera krótkie komunikaty bez szczegółów wyjątków. **Uwaga:** przy uruchomieniu lokalnym (poza Dockerem) odświeżenie nadpisuje pliki w `datasets/raw/`, które są śledzone przez git; `AED_CYCLE_HOURS=0` temu zapobiega.

`wyzwalacz`: `harmonogram` | `ministerstwo`; `rodzaj`: `cykl` | `mapper` | `przypomnienia`; `odswiezono` jest `null`, gdy nie pobierano źródeł; `mapper` lub `przypomnienia` jest `null`, gdy nie były częścią uruchomienia albo się nie udały (wtedy jest wpis w `bledy`). Jedno zadanie naraz: ręczne uruchomienie w trakcie innego zwraca 409 `zadanie_trwa`. `GET /api/aed/statystyki` ma też `ostatnie_uruchomienia: {"mapper": "<czas>"|null, "przypomnienia": "<czas>"|null}` (ostatnie udane).

## Dane demonstracyjne

Przy pierwszym starcie (`AED_DEMO_SEED`, domyślnie włączone; `0` wyłącza) powstają fikcyjne urządzenia, tą samą ścieżką co prawdziwe zgłoszenia i potwierdzenia (walidacja `aed_standard`, tokeny, skrzynka):

- Pulsar Medical: 12 urządzeń, 10 potwierdzonych w różnych miastach (odznaka: tak), 2 w statusie `zgloszony` (czekają na aktywację, link jest w skrzynce ministerstwa); jedno ma baterię ważną jeszcze ok. 30 dni, jedno ostatnie potwierdzenie sprzed 200 dni, więc `POST /przypomnienia/uruchom` wygeneruje prawdziwe wiadomości,
- Serwis Rytm: 6 urządzeń, 2 potwierdzone, 4 `zgloszony` (odznaka: nie).

Nazwy, e-maile (`@demo.example`) i numery seryjne (`DEMO-PUL-001`, ...) są fikcyjne. Rekordy demo mają w bazie flagę `demo = 1`: są widoczne w rejestrze, na mapie i w statystykach, ale **nie trafiają do eksportu `eksport/dane-gov-pl.csv`**. Dane demo nie powstają, gdy baza ma już jakiekolwiek zgłoszenia firm.

## Naklejka QR

`GET /urzadzenia/{id}/naklejka.svg`: szerokość 360 jednostek (viewBox), tytuł, kod QR ze strefą ciszy 4 moduły, identyfikator (20 px, pogrubiony) i dwuwierszowy podpis. Na górze jest puste, oznaczone miejsce na logo kampanii (`<g id="miejsce-na-logo">`, 56 jednostek wysokości). Jeśli istnieje plik SVG z ścieżki `STICKER_LOGO_PATH` (domyślnie `aed_service/naklejka-logo.svg`, zmiana: `AED_STICKER_LOGO`), jest wstawiany w to miejsce. W repozytorium leży tam znak akcji „Opiekun AED” (lockup w kolorze, kopia `kampania/logo/svg/opiekun-aed-lockup-kolor.svg` z polem ochronnym 1X w pliku); miejsce ma 56 jednostek wysokości, więc na arkuszu A4 z trzema naklejkami w rzędzie znak ma ok. 37 mm szerokości bez pola ochronnego – powyżej minimum 35 mm z księgi znaku. Test pilnuje, by każdy wiersz tekstu spełniał regułę: liczba znaków x rozmiar czcionki x 0,75 <= szerokość - 40.

## Znacznik demo

Publiczny widok urządzenia, wiersze listy i `properties` w geojson mają pole `demo` (true dla fikcyjnych rekordów demo, patrz wyżej).

## Linki zarządcy, wycofywanie, Docker

- Każdy link zarządcy (aktywacja, prośby, przypomnienia) ma własny token ważny 90 dni (`TOKEN_DAYS`); wydanie nowego nie unieważnia poprzednich.
- Mapper wycofuje (`wycofany`) rekordy z importu, których nie ma już w jego wyniku; wracają, gdy się pojawią. Gdy wynik jest pusty lub mniejszy niż połowa rekordów z importu (`RETIRE_MIN_SHARE`), nic nie jest wycofywane, a w historii zadań jest wpis w `bledy`. Rekordy wycofane nie trafiają do eksportu.
- Po potwierdzeniu lokalizacji urządzenie ze zgłoszenia jest porównywane z rekordami z importu w promieniu `aed_standard.dedup.CANDIDATE_M`; pasujące pary trafiają do `/duplikaty` (zachowywany jest rekord ze zgłoszenia).
- Numer seryjny nie jest nigdzie publiczny: `zrodlo_id` zgłoszeń jest losowe, nowe `id_aed` też (stare zostają bez zmian).
- Katalog migawki źródeł: `AED_RAW_DIR` (domyślnie `datasets/raw`); skrypt pobierania zawsze zapisuje w `datasets/raw`, więc przy innym katalogu odświeżanie jest wyłączone z komunikatem w `bledy`. W Dockerze katalog `datasets` należy do użytkownika usługi.

## Starsza baza

Przy starcie schemat jest uzupełniany (`migrate`: kolumna `demo`, tabela `jobs`), więc baza z poprzedniej wersji działa bez resetu. Zmiany mapowania w `aed_standard` (np. Warszawa „Prywatny” -> `ograniczony`) trafią do starej bazy po uruchomieniu mappera.

## Reset bazy

Zatrzymaj usługę i usuń plik: `rm aed_service/aed_service.db` (kolejny start zasieje dane od nowa). Przykładowy plik `wzorzec/przyklad-sprzedawca.csv` można wgrać raz; powtórne wgranie zgłosi duplikaty.

## Testy

```
uv run --python 3.13 --with-requirements aed_service/requirements.txt python -m unittest
```

## Uwagi prototypu

- Wiadomości nie są wysyłane; trafiają do skrzynki (`GET /api/aed/wiadomosci`, konto ministerstwa). Zawierają link z tokenem zarządcy (w bazie tylko hash tokenu).
- Eksport (bez rekordów `prywatny` i demo) i widok publiczny nie zawierają `numer_seryjny`, `dysponent_email` i `dysponent_telefon`.
- Brak limitu prób logowania i serwer jednowątkowy (`wsgiref`) – do demonstracji, nie do produkcji.
