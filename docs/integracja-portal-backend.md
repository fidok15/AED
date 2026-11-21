# Integracja z backendem dane.gov.pl (mcod 2.63.0) – ustalenia z kodu

Wynik przeglądu `backend/` (tylko odczyt, nic nie uruchamiano – demon Dockera nie działał na maszynie, na której robiono przegląd). „Sprawdzone” znaczy przeczytane w kodzie; „wniosek” znaczy wywnioskowane, bez testu.

## Uruchomienie lokalne

1. `cp env.sample .env` oraz `cp mcod/settings/local.py.sample mcod/settings/local.py`.
2. W `.env` ustawić `DISCOURSE_FORUM_ENABLED=false` – obraz forum wymaga logowania do prywatnego rejestru.
3. W `/etc/hosts`: `127.0.0.1 mcod.local api.mcod.local admin.mcod.local cms.mcod.local forum.mcod.local mail.mcod.local`.
4. `docker compose -f docker-compose.local.yml build`
5. `docker compose -f docker-compose.local.yml run mcod-local-run python manage.py init_mcod_db` (migracje i dane startowe z `mcod/core/fixtures/basic_data.json`; plik `initial_data.json` w katalogu głównym jest pusty).
6. Indeksy wyszukiwarki: `python manage.py search_index --rebuild -f` (w README wiersz dla Dockera jest ucięty).
7. `docker compose -f docker-compose.local.yml up mcod-local-admin mcod-local-api mcod-local-celery`

Adresy: panel `https://admin.mcod.local/login/`, API `https://api.mcod.local` (dokumentacja pod `/doc`), poczta testowa `http://localhost:8025`. Frontend: `frontend/proxy.local.conf.json` wskazuje na `https://api.mcod.local`.

Konta z danych startowych: `admin@mcod.local` / `testadmin123!` (superużytkownik), `pelnomocnik@mcod.local` / `User123!` (redaktor i pełnomocnik instytucji 2838).

Ryzyka na Macu z procesorem Apple:

- obrazy aplikacji są przypięte do `linux/amd64`, więc działają w emulacji; pierwsza budowa może trwać bardzo długo;
- potrzeba ok. 10 kontenerów i 6–8 GB pamięci dla Dockera (szacunek);
- pliki tłumaczeń `.mo` nie są w repozytorium, a katalog `translations/` jest montowany na te z obrazu – panel może być po angielsku do czasu `compilemessages` (wniosek);
- zadania przetwarzania plików wymagają działającego Celery i RabbitMQ; bez nich wgrany plik nigdy się nie zwaliduje.

**Limit: 3 godziny.** Po jego przekroczeniu pokazujemy samodzielną usługę `aed_service/` i tę notatkę jako plan wdrożenia.

## Co portal już umie bez zmian w kodzie

Redaktor firmy prywatnej może dziś zalogować się i wgrać zasób CSV, jeśli superużytkownik założy instytucję i konto (`is_staff`, stan aktywny, przypisana instytucja). Brakuje: typu instytucji dla branży AED, walidacji standardem AED i rejestru urządzeń.

## Precedens „deweloper”

Typ `developer` nie ma specjalnej logiki cen mieszkań. Występuje w:

- `mcod/organizations/models.py:33,38` – stała i wybór;
- `mcod/harvester/models.py:123-139` – to samo pole z `max_length=9`, więc **klucz nowego typu może mieć najwyżej 9 znaków** (np. `aedvendor`);
- `mcod/resources/models.py:616` – dla deweloperów wyłączone przetwarzanie danych tabelarycznych; dla AED tego nie chcemy;
- wykluczenia z kontroli zepsutych linków oraz z flag danych o wysokiej wartości;
- `data/schemas/{en,pl}/katalog.xsd:278`, tłumaczenia `.po`, filtry we frontendzie (`frontend/src/app/services/list-view-filters.service.ts:302-308`, `frontend/src/assets/i18n/pl.json:924`).

Minimalna zmiana dla nowego typu: stała i wybór w `organizations/models.py`, dwie migracje (organizations po `0025`, harvester po `0019`), dwa wpisy w `katalog.xsd`, wpisy w tłumaczeniach, opcjonalnie filtr we frontendzie.

## Rekomendowany kształt integracji

Wszystko w nowej aplikacji `mcod/aed`, żeby zmianę dało się pokazać jako łatkę.

| Krok | Zmiana | Pliki | Szac. godz. |
|---|---|---|---|
| 0 | Udostępnić `aed_standard` w kontenerach: wolumen `../aed_standard:/usr/src/mcod_backend/aed_standard:ro` w obu kotwicach `docker-compose.local.yml` | `docker-compose.local.yml` | 0,25 |
| 1 | Uruchomić stos, sprawdzić logowanie, wgrać CSV przez panel | `.env`, `local.py` | do 3 |
| 2 | Nowy typ instytucji (klucz do 9 znaków) | `organizations/models.py`, migracje, `katalog.xsd`, `.po` | 1 |
| 3 | Szkielet aplikacji i rejestracja | `mcod/aed/`, `settings/base.py` (`INSTALLED_APPS`, menu SUIT) | 1 |
| 4 | Modele zgłoszenia i urządzenia | `mcod/aed/models.py` | 1,5 |
| 5 | `POST /aed/submissions` wzorem `mcod/submissions/views.py` (gotowy wzorzec wgrywania pliku) | `mcod/aed/views.py`, `mcod/routes.py` | 4 |
| 6 | `GET /aed/devices` wzorem `mcod/guides/views.py` | `mcod/aed/views.py` | 1,5 |
| 7 | Zadanie publikujące zbiór krajowy: CSV z rejestru → `ResourceFile.objects.create(resource=…, is_main=True, file=…)` na zbiorze instytucji „ministerstwo”; znaczniki mapy `l`, `b`, `label` w `tabular_data_schema` | `mcod/aed/tasks.py` | 3 |
| 8 | Zadania cykliczne: mapper i przypomnienia (wpisy w `mcod/celeryapp.py`, kolejka `periodic`) | `mcod/aed/tasks.py`, `celeryapp.py` | 5 |
| 9 | Szablony wiadomości | `mcod/templates/mails/aed-*.{txt,html}` | 1 |

Razem ok. 20 godzin dla osoby znającej Django – więcej, niż mamy. Dlatego kolejność jest taka: najpierw samodzielna usługa `aed_service/` (ten sam framework Falcon, kontrakt w `docs/api-aed.md`), a w forku portalu tylko kroki 0–2 i ewentualnie 7.

## Szczegóły przydatne przy implementacji

- **Uwierzytelnienie API:** `mcod/core/api/hooks.py:53` – `login_required` czyta `Authorization: Bearer <JWT>`; role `editor`, `admin`, `agent`, `official`. Logowanie: `POST /auth/login`.
- **Trasy API:** płaska lista w `mcod/routes.py`; aplikację rejestruje `mcod/api.py:106-117`.
- **Ścieżka pliku CSV:** `ResourceFile` → `process_created_file` (`resources/models.py:2019`) → walidacja typu pliku → walidacja tabelaryczna goodtables 2.1.4 (`indexed_data.py:610-641`: struktura, schemat, zero wierszy, limit 10 błędów) → ocena otwartości → indeks.
- **Mapa:** znaczniki w `Resource.tabular_data_schema["fields"][i]["geo"]`; dozwolone zestawy: `{label, b, l}`, `{label, uaddress}`, `{label, place, postal_code[, house_number[, street]]}`; `l` i `b` muszą być liczbowe (`resources/forms.py:83-168`). Automatycznego znakowania nie ma.
- **Harvester XML:** uruchamiany codziennie o 03:00; wymaga adresu HTTPS kończącego się na `.xml`, pliku `.md5` obok, typu treści XML i zgodności z XSD (najnowszy: 1.13 w `data/harvester/`). `extIdent` (1–36 znaków) jest kluczem; obiekt, który zniknie z pliku, jest usuwany. Przykłady: `statics/harvester/otwarte_dane_sample_{min,max}.xml`.
- **Poczta:** wzorzec przypomnień w `datasets/models.py:829-849` i `datasets/tasks.py:136`; szablony w `mcod/templates/mails/`.

## Zasilanie XML przez harwester (DATA SOURCES) – wdrożone i sprawdzone lokalnie

Rejestr ministerstwa publikuje zbiór mechanizmem portalu dla dostawców z własnym systemem, bez zmian w kodzie portalu. Rejestr wystawia `zasilanie.xml` (XSD 1.13), `zasilanie.md5` i plik CSV, a harwester portalu codziennie o 03:00 pobiera XML i sam aktualizuje zbiór. Metadane zbioru (tytuł, opis, kategoria `HEAL`, tagi, częstotliwość, flagi) są w `aed_standard/schema.json` pod kluczem `zbior_dane_gov_pl`. Generator: `aed_standard/feed.py`, zapis plików: `aed_service/feed.py`.

Ustalenia z kodu, które wyznaczają kształt pliku:

- `url` zasobu musi być `https://` (`harvester/serializers.py:136`); obok XML musi leżeć `.md5` (`harvester/utils.py:168`).
- Kluczem zbioru i zasobu jest `extIdent`. Nasze identyfikatory są stałe (`aed-polska`, `aed-polska-csv`), bo obiekt, którego zabraknie w pliku, harwester usuwa na stałe (`harvester/models.py:369-388`).
- Portal pobiera plik zasobu ponownie tylko po zmianie `link` (`resources/models.py:1285`). Dlatego każda wersja CSV ma nazwę z hashem treści (`aed_dane_gov_pl-<hash>.csv`), a stare wersje zostają w katalogu.
- Flagi (`hasDynamicData` itd.) są w XSD opcjonalne, ale w formularzu zbioru obowiązkowe – w pliku są podane jawnie.

Kroki lokalnie (portal z `docker-compose.aed-ports.yml`):

1. `uv run --python 3.13 --with-requirements aed_service/requirements.txt python -m aed_service.feed --out backend/statics/aed --url https://api.mcod.local/static/aed` – nginx serwuje `backend/statics` pod `https://api.mcod.local/static/`, skąd czyta też kontener Celery.
2. Panel `http://localhost:8001`: instytucja „Ministerstwo Cyfryzacji” (typ: państwowa), potem źródło danych: typ XML, adres `https://api.mcod.local/static/aed/zasilanie.xml`, częstotliwość codziennie, kategoria Zdrowie, status aktywne. Zapis ze statusem aktywnym od razu uruchamia import (`harvester/admin.py:233`).
3. Raport importu przy źródle danych: status OK, 1 zbiór, 1 zasób.
4. Redaktor w zasobie, zakładka danych tabelarycznych: typ `string` dla `nr_budynku`, `kod_terc`, `kod_simc`, `zrodlo_id` oraz znaczniki mapy `b` = `szerokosc_geograficzna`, `l` = `dlugosc_geograficzna`, `label` = `nazwa`. Portal sam wnioskuje typ `integer` dla tych kolumn, a schemat ma `missingValues: []`, więc puste pole jest błędem walidacji, a kody TERC/SIMC tracą zera wiodące. Ustawienia zostają przy kolejnych wersjach pliku (sprawdzone).

Sprawdzone 21.11 na lokalnym portalu: import utworzył zbiór i zasób; nowa wersja CSV zaktualizowała ten sam zasób (nowy link, nowy plik, 780 rekordów w indeksie), typy kolumn i mapa zostały; powrót do pełnej wersji przywrócił 781 rekordów. API zasobu przez chwilę zwraca liczbę z pamięci podręcznej.

Automatyzacja po stronie rejestru: zmienne `AED_FEED_DIR` i `AED_FEED_URL` usługi – po każdym cyklu harmonogramu pliki są zapisywane od nowa (`aed_service/__main__.py`).

## Licencja kodu

W `backend/` i `frontend/` nie ma pliku `LICENSE` ani nagłówków licencyjnych. Jedyna deklaracja to `"license": "MIT"` w `frontend/package.json`. Strona portalu z kodem źródłowym mówi o GPL v3 (ustalenie z researchu, nie z kodu). Do wyjaśnienia z organizatorem.
