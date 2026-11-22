# Integracja z backendem dane.gov.pl (mcod 2.63.0) – ustalenia z kodu

Wynik przeglądu `backend/` (tylko odczyt, nic nie uruchamiano – demon Dockera nie działał na maszynie, na której robiono przegląd). „Sprawdzone” znaczy przeczytane w kodzie; „wniosek” znaczy wywnioskowane, bez testu. Późniejsze uruchomienie pełnego stosu na Macu (22.11) i jego wyniki: `docs/wykaz-aed-w-portalu.md`, „Co sprawdzono”.

## Uruchomienie lokalne

1. `cp env.sample .env` oraz `cp mcod/settings/local.py.sample mcod/settings/local.py`. W `local.py` usunąć dwa wiersze `"timeout": 1,` (Elasticsearch 6 odrzuca to ustawienie indeksu i `search_index --rebuild` kończy się błędem `unknown setting [index.timeout]`), a do logowania pod `localhost` ustawić `SESSION_COOKIE_DOMAIN = None` (sprawdzone 22.11).
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
- potrzeba ok. 10 kontenerów i 8 GB pamięci dla Dockera; zmierzone 22.11: Elasticsearch ok. 2,9 GB mimo sterty 512 MB (emulacja; przy stercie 1 GB kontener padł z braku pamięci), panel i API po ok. 0,6 GB, kontener testów do 2 GB;
- podsieć `172.18.18.0/24` z `docker-compose.local.yml` kolidowała z inną siecią Dockera – `docker-compose.aed-mac.yml` zmienia ją na `172.30.18.0/24`;
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

Stan na 22.11: krok 0 zrobiony (wolumen `../aed_standard` w obu kotwicach `docker-compose.local.yml`). Wykaz AED – zgłaszanie i scalanie wykazów jako zasobów portalu, wzorem wykazu DGA – jest w `mcod/aed/`; instrukcja: `docs/wykaz-aed-w-portalu.md`, analiza: `docs/wykaz-dga-analiza.md`. Kod Django nie był jeszcze uruchomiony w portalu. Uruchomienie pełnego forka na serwerze pod domeną (HTTPS, panel, API, usługa AED): `docs/wdrozenie-serwer.md`.

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
- **Mapa:** znaczniki w `Resource.tabular_data_schema["fields"][i]["geo"]`; dozwolone zestawy: `{label, b, l}`, `{label, uaddress}`, `{label, place, postal_code[, house_number[, street]]}`; `l` i `b` muszą być liczbowe (`resources/forms.py:83-168`). Automatycznego znakowania nie ma. Nasz CSV bez poprawki typów nie przechodzi walidacji danych (`nr_budynku`, `zrodlo_id`, `kod_terc`, `kod_simc` trzeba ustawić na tekst) – szczegóły i kroki: `docs/panel-portalu-krok-po-kroku.md`.
- **Harvester XML:** uruchamiany codziennie o 03:00; adres XML kończy się na `.xml` (może być `http`), suma leży pod tym adresem z `.xml` zamienionym na `.md5`, typ treści XML, zgodność z XSD (najnowszy: 1.13 w `data/harvester/`). HTTPS jest wymagany dla adresów **zasobów** w pliku (XSD 1.13 i `harvester/serializers.py:133-141`), certyfikat nie jest sprawdzany. `extIdent` (1–36 znaków) jest kluczem; obiekt, który zniknie z pliku, jest usuwany. Przykłady: `statics/harvester/otwarte_dane_sample_{min,max}.xml`. Usługa wystawia zasilanie pod `/api/aed/eksport/dane-gov-pl.xml` (`docs/api-aed.md`); konfiguracja źródła w panelu, obejście HTTPS lokalnie i ręczne uruchomienie importu: `docs/panel-portalu-krok-po-kroku.md`.
- **Poczta:** wzorzec przypomnień w `datasets/models.py:829-849` i `datasets/tasks.py:136`; szablony w `mcod/templates/mails/`.

## Licencja kodu

W `backend/` i `frontend/` nie ma pliku `LICENSE` ani nagłówków licencyjnych. Jedyna deklaracja to `"license": "MIT"` w `frontend/package.json`. Strona portalu z kodem źródłowym mówi o GPL v3 (ustalenie z researchu, nie z kodu). Do wyjaśnienia z organizatorem.
