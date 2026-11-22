# Wykaz AED w portalu – jak włączyć i pokazać

Instrukcja dla osoby z działającym lokalnym portalem (panel `http://localhost:8001`, API `http://localhost:8000` z `docker-compose.aed-ports.yml`, konto `admin@mcod.local` / `testadmin123!`). Opis mechanizmu i porównanie z wykazem DGA: `docs/wykaz-dga-analiza.md`.

## Co to robi

Dostawca (samorząd, instytucja, firma) publikuje w swoim zbiorze zasób CSV w strukturze standardu AED i zaznacza „Wykaz AED: TAK”. Portal sprawdza plik przy zapisie standardem `aed_standard` i pokazuje błędy po polsku. Zadanie Celery scala wszystkie wykazy AED w jeden zasób „Krajowy wykaz AED” w zbiorze ministerstwa; w harmonogramie jest ustawione na 03:45, ale sprawdzone tylko ręcznym uruchomieniem (rozdział „Nadal niesprawdzone”). Przy zapisie portal sprawdza plik CSV; wykaz XLSX i wykaz-link – dopiero przy scalaniu. Scalanie przechodzi przez walidację, deduplikację i profil `publikacja`, więc w wyniku nie ma danych OSM ani urządzeń prywatnych. Wynik i raport (które wykazy przyjęto, które odrzucono i dlaczego) są publiczne, bez logowania: `GET /aed-aggregated` oraz zwykły widok zbioru, tabeli i mapy. Raport publiczny jest jawnie zdefiniowany (`public_report` w `mcod/aed/aed_utils.py`): liczniki, dla każdego wykazu status i liczby wierszy, problemy jako wiersz, pole ze standardu, kod i stały opis kodu (`PROBLEM_DESCRIPTIONS` w `constants.py`) – bez komunikatów walidatora, które cytują wartości z pliku („Otrzymano: …”), bez adresów URL i bez pól wewnętrznych (`powiadomienie_oczekuje`). Pole `wykorzystane_zasoby` podaje dla każdego przyjętego wykazu instytucję, tytuł zbioru i zasobu, trwały link do zasobu w portalu i licencję (uznanie autorstwa CC BY 4.0; opis zbioru zbiorczego odsyła do tej listy). Pełny raport zostaje w `AggregatedAEDInfo.report` dla panelu i e-maila. Endpoint zwraca 404, gdy zasób albo zbiór zbiorczy nie jest opublikowany.

## Włączenie

1. **Kod i standard w kontenerach.** `backend/docker-compose.local.yml` montuje `../aed_standard` w `/usr/src/mcod_backend/aed_standard` (wpis w obu kotwicach). Kontenery trzeba utworzyć od nowa:
   ```
   cd backend
   docker compose -f docker-compose.local.yml -f docker-compose.aed-ports.yml up -d --force-recreate mcod-local-admin mcod-local-api mcod-local-celery
   docker compose -f docker-compose.local.yml exec mcod-local-admin python -c "import aed_standard.wykaz; print('ok')"
   ```
2. **Migracje** (`resources.0076_resource_contains_aed_list` i `aed.0001_initial`):
   ```
   docker compose -f docker-compose.local.yml exec mcod-local-admin python manage.py migrate
   ```
3. **Instytucja ministerstwa.** W panelu: Instytucje → dodaj „Ministerstwo Cyfryzacji” (typ `state`) i odczytaj jej numer z adresu strony edycji. W `backend/.env` dopisz `MAIN_AED_DATASET_OWNER_ORGANIZATION_PK=<numer>` (w `env.sample` jest 2844 – numer, który zakłada `seed_aed_demo`) i powtórz krok 1 (`--force-recreate`, bo zwykły `restart` nie czyta `.env` od nowa). Ustawienie jest **wymagane** i nie przejmuje już numeru właściciela DGA: bez niego albo przy nieistniejącej instytucji zadanie kończy się błędem konfiguracji (`ImproperlyConfigured`) **przed** odczytem jakiegokolwiek wykazu, bez pliku i bez zasobu, a `seed_aed_demo` odmawia pracy z instrukcją.
4. **Kategoria „Zdrowie”** (opcjonalnie): jeśli istnieje, zbiór zbiorczy dostanie ją automatycznie; jeśli nie, zbiór powstanie bez kategorii.

## Ustawienia i zabezpieczenia scalania

Ustawienia w `backend/mcod/aed/constants.py` (zmienne środowiskowe `MAIN_AED_*`):

- **Tylko pliki z magazynu portalu.** `MAIN_AED_ALLOW_REMOTE_LISTS` domyślnie `false`: zasób-link oznaczony jako wykaz AED formularz odrzuca komunikatem „Wykaz AED musi być plikiem zapisanym w portalu…”, a scalanie (np. dla zasobu z harvestera) odrzuca go z tym samym komunikatem w raporcie. Worker nie pobiera więc adresów wskazanych przez dostawcę. Z `true`: pobieranie bez przekierowań (`allow_redirects=False`), do `MAX_LIST_BYTES`, najwyżej `REMOTE_TOTAL_TIMEOUT` = 30 s na całe pobranie.
- **Limity jednego wykazu** (`MAX_LIST_BYTES` = 20 MB, `MAX_LIST_ROWS` = 100 000), sprawdzane przed parsowaniem, w formularzu i w scalaniu. Wykaz ponad limit jest odrzucony z komunikatem, pozostałe scalają się dalej. Limitu par w deduplikacji (`aed_standard/dedup.py`) nie dodano – to pakiet `aed_standard`, poza tą łatką.
- **Tylko w zbiorze własnej instytucji.** Redaktor (nie superużytkownik) nie oznaczy zasobu jako wykazu AED w zbiorze innej instytucji: „Wykaz AED można oznaczyć tylko w zbiorze swojej instytucji.” (`ResourceAdmin.get_form` przekazuje użytkownika do formularza, sprawdzenie w `_validate_aed_list_file`). Sama możliwość dodania zasobu do cudzego zbioru to zachowanie oryginalnego portalu (pole `dataset` w `resources/admin.py` filtruje tylko `source__isnull=True`); sprawdzone 22.11 curl-em: konto jury dodało zwykły zasób do zbioru Legionowa (302). Tego nie zmieniamy – to zgłoszenie do opiekunów portalu.
- **Jeden przebieg naraz.** Blokada `main_aed_run_lock` w cache (`cache.add`, atomowe `SET NX` w Redis) na `RUN_TIMEOUT` = 1 h, właścicielem jest identyfikator zadania Celery (ponowienia go zachowują). Drugie uruchomienie w trakcie pierwszego kończy się od razu („Main AED merge already running…”, wynik `locked`) i niczego nie tworzy ani nie usuwa. Klucze stanu (`main_aed_file_path_to_clean:<id>`, `main_aed_to_clean:<id>`) i nazwa pliku roboczego są przypisane do przebiegu, oba wpisy mają ten sam czas życia co blokada. Sprzątanie po błędzie nigdy nie usuwa zasobu, na który wskazuje `AggregatedAEDInfo`. Znane ograniczenie odziedziczone ze wzorca DGA: stan przebiegu żyje w cache, nie w bazie; po wygaśnięciu (worker zabity na ponad godzinę) osierocony kandydat i plik nie są sprzątane automatycznie.
- **Pusty wynik po awarii źródeł.** Gdy scalanie daje zero rekordów, a co najmniej jeden wykaz nie dał się odczytać z przyczyny przejściowej (błąd odczytu pliku, sieć, kod 5xx – klasa `TransientError`), poprzedni wykaz krajowy zostaje, a raport dostaje `ostatnie_nieudane_scalanie`. Odrzucenie z reguły (link wyłączony, limit, plik niezgodny ze standardem, wycofany zasób) się nie liczy – wtedy pusty wykaz jest publikowany.
- **Kandydat publiczny przed walidacją** – zostawione: zasób zbiorczy powstaje od razu jako `published`, tak jak w DGA (`dga_utils.create_main_dga_resource_with_dataset`); zmiana na wersję roboczą i publikację po walidacji wymagałaby sprawdzenia, czy zadania przetwarzania pliku i indeksowania portalu zachowują się tak samo dla zasobu roboczego – tego nie sprawdzono.
- **Plik roboczy** leży w `MEDIA_ROOT/main_aed`, tak jak plik DGA w `MEDIA_ROOT/main_dga` (`MAIN_DGA_RESOURCE_XLSX_CREATION_ROOT`); wzorca nie zmieniamy. Wdrożenie domenowe nie serwuje tego katalogu (`docs/wdrozenie-serwer.md`).
- **Powiadomienia:** flaga ponowienia `powiadomienie_oczekuje` także przy `send() == 0` i – dla wszystkich należnych wpisów – przy błędzie utworzenia połączenia z serwerem poczty. Treść e-maila używa tych samych stałych opisów kodów co raport publiczny, bez wartości z pliku.

## Pokaz krok po kroku

1. **Wykaz poprawny.** Zaloguj się jako `admin@mcod.local`. Dodaj zbiór w instytucji „Pierwsza instytucja”, licencja CC0, status opublikowany. Dodaj do niego zasób: plik `datasets/raw/dane_gov_pl/legionowo/resource_2625221.csv` (prawdziwy zbiór Legionowa, podzbiór standardu), „Wykaz AED: TAK”, status opublikowany. Zapis przechodzi.
2. **Wykaz niezgodny.** W tym samym zbiorze dodaj zasób z plikiem `datasets/raw/dane_gov_pl/krosno/resource_54632.csv` i „Wykaz AED: TAK”. Formularz nie zapisze zasobu i przy polu „Wykaz AED” pokaże listę błędów, np. „Plik, pole Adres: Kolumna „Adres” nie występuje w standardzie…” oraz podpowiedź „Czy chodziło o „dlugosc_geograficzna”?”. Zapisz go z „Wykaz AED: NIE”, żeby pokazać, że zwykły zasób dalej działa.
3. **Wykaz ministerstwa.** W instytucji ministerstwa dodaj zbiór „Rejestr zgłoszeń AED” (licencja CC0) i zasób z plikiem `datasets/out/aed_dane_gov_pl.csv`, „Wykaz AED: TAK”. Wykaz właściciela zbioru zbiorczego ma pierwszeństwo przy łączeniu duplikatów. To samo działa dla eksportu z usługi `aed_service`.
4. **Podgląd scalania bez zapisu:**
   ```
   docker compose -f docker-compose.local.yml exec mcod-local-admin python manage.py create_main_aed_resource --dry-run
   ```
   Wypisuje raport JSON i pierwsze wiersze pliku krajowego. Dla dwóch wykazów z kroków 1 i 3 oczekujemy (liczby z testu `tests/test_wykaz.py` na tych samych plikach): 805 rekordów z wykazów, 24 połączenia, 781 rekordów w wykazie krajowym.
5. **Scalanie właściwe** (to samo zadanie, które uruchamia harmonogram; wymaga działającego `mcod-local-celery`):
   ```
   docker compose -f docker-compose.local.yml exec mcod-local-admin python manage.py create_main_aed_resource
   ```
   Zadanie tworzy zbiór „Krajowy wykaz defibrylatorów AED – wykaz zbiorczy” i zasób „Krajowy wykaz AED”, czeka na walidację pliku przez portal (do 5 prób co 20 s), zapisuje raport i usuwa poprzedni zasób zbiorczy. Postęp: `docker compose -f docker-compose.local.yml logs -f mcod-local-celery | grep -i aed`.
6. **Wynik publicznie, bez logowania:**
   - `curl http://localhost:8000/aed-aggregated` – identyfikatory zbioru i zasobu oraz raport;
   - `http://localhost:8000/resources/<resource_id>/data` – dane tabelaryczne przez API;
   - frontend: strona zbioru i zasobu zbiorczego – widok tabeli i zakładka mapy (współrzędne są oznaczone jako `b`/`l`, nazwa jako `label` już przy tworzeniu zasobu);
   - plik CSV do pobrania z karty zasobu.

## Zrzuty ekranu do prezentacji

1. Formularz zasobu w panelu z polem „Wykaz AED” i tekstem pomocy.
2. Błędy po polsku po wgraniu pliku z Krosna.
3. Wynik `create_main_aed_resource --dry-run` (raport: wykazy przyjęte i odrzucone).
4. Odpowiedź `GET /aed-aggregated` w przeglądarce.
5. Zbiór „Krajowy wykaz defibrylatorów AED – wykaz zbiorczy” na liście zbiorów ministerstwa.
6. Widok tabeli zasobu zbiorczego.
7. Mapa zasobu zbiorczego.
8. Ocena otwartości i API zasobu (`/resources/<id>/data`).

## Powiadomienie dostawcy o wyniku scalania

Wykaz XLSX i wykaz z linku portal sprawdza dopiero przy scalaniu, a wykaz zapisany wcześniej może przestać przechodzić (np. minął termin baterii). Dlatego po każdym scalaniu portal pisze do dostawcy (`backend/mcod/aed/notifications.py`, szablony `backend/mcod/aed/templates/mails/aed-list-result.{txt,html}` w stylu powiadomień portalu):

- **kiedy:** wykaz ma status `odrzucony` albo `czesciowo`, a wynik różni się od poprzedniego scalania (status, liczba odrzuconych wierszy, liczba lub treść problemów; porównanie z `AggregatedAEDInfo.report`). Gdy wykaz wcześniej odrzucony przechodzi w całości – jedna wiadomość „Wykaz AED przyjęty w całości”. Ten sam wynik przy codziennym scalaniu nie daje kolejnej wiadomości;
- **treść:** zasób i zbiór, ile wierszy przyjęto i odrzucono, do 10 pierwszych problemów (najpierw błędy; wiersz, pole ze standardu i stały opis kodu problemu, bez wartości z pliku), link do zasobu w panelu, link do zbioru i raportu `/aed-aggregated`; przy `czesciowo` zdanie, że poprawne wiersze trafiły do wykazu krajowego; link do wzorca i konwertera, jeśli ustawiono `MAIN_AED_LIST_HELP_URL` (np. `https://<domena>/pl/aed/!konwerter`), inaczej bez linku;
- **adresat:** wyłącznie kontakt instytucjonalny – „E-mail do powiadomień” zbioru (`update_notification_recipient_email`, to samo pole, którego portal używa do przypomnień o aktualizacji), a gdy go brak – adres e-mail instytucji. W odróżnieniu od przypomnienia portalu nie ma powrotu do adresu redaktora (`modified_by`). Bez żadnego adresu: wpis w logu, bez wysyłki;
- **błędy:** wysyłka idzie po zapisaniu wyniku scalania; wyjątek przy wysyłce jest logowany i nie cofa scalania ani nie blokuje wiadomości do innych dostawców;
- **przełącznik:** `MAIN_AED_NOTIFY_PROVIDERS` (domyślnie włączone; `false` wyłącza), stała w `mcod/aed/constants.py`.

Pierwsze scalanie po wdrożeniu nie wyśle wiadomości o wykazach, które już były odrzucone w poprzednim raporcie (wynik się nie zmienił).

Sprawdzone 22.11 ok. 02:30 na lokalnym stosie: raport w `AggregatedAEDInfo` wyczyszczony w `manage.py shell` (stan „pierwsze scalanie”), `create_main_aed_resource` przez Celery → log „AED list notifications sent: 1 of 1.”, wiadomość „Wykaz AED odrzucony: Wykaz AED – Gmina Krosno” do `admin@mcod.local` w MailHog (`http://localhost:8025`, zrzut `docs/zrzuty/portal-12-mail-odrzucony-wykaz.png` – prawdziwy ekran skrzynki, część HTML). Drugie scalanie bez zmian → „sent: 0 of 0”. Zasób zbiorczy po teście: 781 rekordów. Testy: `mcod/aed/tests/test_notifications.py` (wysyłka przy odrzuceniu, brak powtórki, wiadomość po naprawie, błąd SMTP nie przerywa, przełącznik).

## Harvester XML: schemat 1.14 z `containsAedList`

Zasób z harvestera XML oznacza się jako wykaz AED sam, bez panelu: nowa wersja schematu `backend/data/harvester/xml_import_otwarte_dane_1_14.xsd` (kopia 1.13, przestrzeń nazw `urn:otwarte-dane:harvester:1.14` i jeden opcjonalny element zasobu `containsAedList` typu `xs:boolean`, bez wartości domyślnej). Importer wybiera wersję XSD z przestrzeni nazw korzenia (`mcod/harvester/utils.py`, `get_xml_schema_version`), więc nowa wersja to jeden wpis w `HARVESTER_XML_VERSION_TO_SCHEMA_PATH` (`mcod/settings/base.py`) i jedno pole `contains_aed_list = Bool(data_key="containsAedList")` w `XMLResourceSchema` (`mcod/harvester/serializers.py`). Importer zapisuje do zasobu wszystkie pola z serializera, więc bez migracji. Pole nie ma wartości domyślnej: plik 1.13 albo 1.14 bez elementu nie zmienia flagi ustawionej ręcznie w panelu. Wykaz z harvestera nie przechodzi walidacji formularza – sprawdza go scalanie (jak wykaz z linku), a o odrzuceniu dostawca dowie się e-mailem. Test: `mcod/aed/tests/test_harvester.py` (przykład 1.13 z testów harvestera przeniesiony do 1.14). Pełnego importu harvesterem w działającym stosie nie uruchamiano.

Znane ryzyko utrzymaniowe (z przeglądu opiekuna portalu): „ministerstwo musi utrzymywać dodatkową wersję kontraktu harvestera od pierwszego wdrożenia”, a test sprawdza deserializację bez pełnego cyklu zapisu. Decyzja zespołu: schemat 1.14 zostaje w łatce.

Usługa `aed_service` wystawia zasilanie w wersji 1.13 (`/api/aed/eksport/dane-gov-pl.xml`) i tak zostaje (decyzja 22.11: produkcyjny portal zna tylko 1.13). Żeby jej zasób oznaczał się w forku jako wykaz, trzeba by zmienić przestrzeń nazw na `urn:otwarte-dane:harvester:1.14` i dopisać w elemencie `resource` jedną linię `<containsAedList>true</containsAedList>`.

## Konto dla jury

`seed_aed_demo` zakłada (idempotentnie) instytucję „Gmina Demo (konto jury)” (pk 90003) z pustym zbiorem „Defibrylatory AED – Gmina Demo” i konto redaktora tej instytucji – nie superużytkownika: `is_staff`, stan `active`, przypisana instytucja, imię i nazwisko oraz telefon (bez nich panel przekierowuje redaktora na uzupełnienie profilu, `ComplementUserDataMiddleware`). Hasła demo są jawne decyzją zespołu; komenda wypisuje je na końcu. Ponowne uruchomienie nie zmienia hasła i nie wylogowuje.

- panel: `http://localhost:8001` (na serwerze `https://admin.<domena>`),
- login: `jury@aed.example`, hasło: `jury-demo-2026`.

Trzy kroki:

1. Zaloguj się i otwórz Zasoby → Dodaj zasób; jako zbiór wybierz „Defibrylatory AED – Gmina Demo”.
2. Wgraj plik Krosna (`datasets/raw/dane_gov_pl/krosno/resource_54632.csv`), zaznacz „Wykaz AED: TAK” i zapisz – formularz nie zapisze zasobu i pokaże przy polu „Wykaz AED” błędy po polsku.
3. Wgraj plik Legionowa (`datasets/raw/dane_gov_pl/legionowo/resource_2625221.csv`) z „Wykaz AED: TAK” – zasób się zapisze i trafi do następnego scalania.

Sprawdzone 22.11 ok. 03:55 curl-em z sesją na lokalnym stosie: logowanie 302 → `/`; lista zbiorów pokazuje tylko zbiór instytucji jury; Legionowo do własnego zbioru – zapisane (302, `contains_aed_list=True`); Krosno – odrzucone z komunikatami („Kolumna „Adres” nie występuje w standardzie…”); Legionowo z „Wykaz AED: TAK” do zbioru Legionowa (cudza instytucja) – odrzucone „Wykaz AED można oznaczyć tylko w zbiorze swojej instytucji.”; `/constance/config/` (ustawienia portalu) – 403. Uwaga: ten sam plik bez flagi wykazu w zbiorze Legionowa zapisał się (302) – to zachowanie oryginalnego portalu (wyżej). Strony `/users/user/` i `/organizations/organization/` zwracają 200 (lista użytkowników pokazuje jeden wpis – własne konto; tak działa uprawnienie redaktora w portalu). Zasoby dodane w teście usunięto, wykaz krajowy wrócił do 3 wykazów / 781 rekordów.

## Co sprawdzono, a czego nie

Stan na 22.11, ok. 01:55. Portal uruchomiony na Macu (Apple Silicon, Docker Desktop 8 GB), w katalogu `backend/`.

### Jak powtórzyć

Przygotowanie (pliki lokalne, poza gitem): `cp env.sample .env`, w `.env` ustawić `DISCOURSE_FORUM_ENABLED=false`; `cp mcod/settings/local.py.sample mcod/settings/local.py`, a w `local.py` usunąć dwa wiersze `"timeout": 1,` (Elasticsearch 6 odrzuca to ustawienie indeksu, `search_index --rebuild` kończy się błędem `unknown setting [index.timeout]`) i ustawić `SESSION_COOKIE_DOMAIN = None` (logowanie do panelu pod `localhost`).

`docker-compose.aed-mac.yml` (nowy plik, tylko lokalnie): podsieć `172.30.18.0/24` zamiast `172.18.18.0/24` (kolidowała z inną siecią Dockera), sterta Elasticsearch 512 MB (przy 1 GB kontener w emulacji zajął 2,9 GB i został zabity przez OOM), panel, API i Celery z obrazu testowego (jeden obraz do zbudowania), montowanie `../datasets` dla komendy demo. Obrazy Pythona zostają `linux/amd64`: natywna budowa arm64 się nie udała (gevent nie ma koła arm64 dla Pythona 3.8, kompilacja ze źródeł pada).

```
cd backend
C="docker compose -f docker-compose.local.yml -f docker-compose.aed-mac.yml"
$C build mcod-db mcod-redis mcod-rabbitmq mcod-elasticsearch mcod-rdfdb      # ok. 8 min
$C --profile tests build mcod-local-tests                                     # ok. 10 min (emulacja amd64)
$C up -d mcod-db mcod-redis mcod-rabbitmq mcod-elasticsearch mcod-rdfdb mcod-smtp

# szczebel 1: migracje i testy (wejście testowe robi compilemessages i makemigrations --check)
$C --profile tests run --rm --no-deps mcod-local-tests -p no:cacheprovider -n2 mcod/aed
$C --profile tests run --rm --no-deps mcod-local-tests-api -p no:cacheprovider -n1 mcod/aed/tests/test_views.py
$C --profile tests run --rm --no-deps mcod-local-tests -p no:cacheprovider -n2 \
   mcod/resources/tests/test_main_dga.py mcod/resources/tests/test_dga_utils.py \
   mcod/resources/tests/test_dga_migrate.py mcod/resources/tests/test_admin/test_admin.py mcod/tests/test_celery.py
$C --profile tests run --rm --no-deps mcod-local-tests-api -p no:cacheprovider -n1 \
   mcod/resources/tests/test_api.py mcod/aed/tests/test_views.py -k "dga or aed"

# szczebel 2: baza deweloperska, dane demo, scalanie
$C run --rm --no-deps mcod-local-admin python manage.py init_mcod_db
$C run --rm --no-deps mcod-local-admin python manage.py search_index --rebuild -f
$C -f docker-compose.aed-ports.yml up -d --no-deps mcod-local-admin mcod-local-api mcod-local-celery
docker exec mcod-admin python manage.py seed_aed_demo     # ministerstwo (pk 2844), Legionowo, Krosno
docker exec mcod-admin python manage.py create_main_aed_resource --dry-run
docker exec mcod-admin python manage.py create_main_aed_resource
curl http://localhost:8000/aed-aggregated

# zatrzymanie
$C -f docker-compose.aed-ports.yml stop mcod-local-admin mcod-local-api mcod-local-celery \
   mcod-db mcod-redis mcod-rabbitmq mcod-elasticsearch mcod-rdfdb mcod-smtp
```

`seed_aed_demo` (nowa komenda, tylko demo) wymaga `MAIN_AED_DATASET_OWNER_ORGANIZATION_PK` (w `env.sample` 2844) i zakłada instytucje „Ministerstwo Cyfryzacji” (pod tym numerem), konto jury (sekcja „Konto dla jury”), „Gmina Miejska Legionowo” i „Gmina Krosno”, po jednym zbiorze i jednym zasobie z flagą „Wykaz AED” z prawdziwych plików: `datasets/out/aed_dane_gov_pl.csv`, `datasets/raw/dane_gov_pl/legionowo/resource_2625221.csv`, `datasets/raw/dane_gov_pl/krosno/resource_54632.csv` (Krosno zapisane z pominięciem formularza, żeby pokazać odrzucenie przy scalaniu).

### Uruchomione i zgodne z oczekiwaniem

- Migracje: `makemigrations --check` – „No changes detected”; `migrate` na czystej bazie stosuje `resources.0076_resource_contains_aed_list` i `aed.0001_initial` bez błędów.
- Testy `mcod/aed`: 6 passed (komponent admin) + 2 passed (komponent api, `test_views.py`). Wśród nich test na prawdziwych plikach Legionowa i Krosna, który przechodzi przez walidację pliku i danych tabelarycznych samego portalu (Celery w trybie eager, Elasticsearch): Legionowo przyjęte, Krosno odrzucone, zasób zbiorczy z `tabular_data_schema` ze znacznikami `b`/`l`/`label` po przetworzeniu przez portal; test formularza (błędy po polsku przy polu „Wykaz AED”); test `GET /aed-aggregated` (200 z raportem, 404 bez wykazu).
- Regresja DGA i panelu: `test_main_dga.py`, `test_dga_utils.py`, `test_dga_migrate.py`, `test_admin/test_admin.py`, `mcod/tests/test_celery.py` – 137 passed; testy API `-k "dga or aed"` – 11 passed.
- `create_main_aed_resource --dry-run`: 3 wykazy, 2 przyjęte (Legionowo 24/24, ministerstwo 781/781), Krosno odrzucone z 10 komunikatami po polsku; 805 rekordów z wykazów, 24 połączenia, 2 do przeglądu, 781 w wykazie krajowym, średnia kompletność 51,4 – zgodnie z `tests/test_wykaz.py`.
- `create_main_aed_resource` przez RabbitMQ i worker Celery: kroki 1–4, jedno ponowienie „Pending validation(s)” po 20 s, potem sukces. Powstał zbiór „Krajowy wykaz defibrylatorów AED – wykaz zbiorczy” (CC BY 4.0, codziennie, tagi AED/defibrylator/wykaz zbiorczy) w instytucji ministerstwa i zasób „Krajowy wykaz AED”: walidacja pliku, danych i linku SUCCESS, `openness_score` 3, `visualization_types` `["map", "table"]`, `/resources/<id>/data` i `/resources/<id>/geo` zwracają po 781 rekordów (punkty mapy z nazwą).
- Drugie uruchomienie zastępuje zasób zbiorczy: nowy zasób w tym samym zbiorze, stary zwraca 404, zbiór zbiorczy jest jeden.
- `GET http://localhost:8000/aed-aggregated` bez logowania: identyfikatory zbioru i zasobu oraz pełny raport.
- Panel (`http://localhost:8001`, logowanie `curl`em jako `admin@mcod.local`): formularz „Dodaj zasób” ma pole „Wykaz AED” z tekstem pomocy. Plik Krosna z „Wykaz AED: TAK” – zasób niezapisany (HTTP 200) i 10 komunikatów po polsku przy polu; ten sam plik z „NIE” – zapisany (302); plik Legionowa z „TAK” – zapisany (302) z `contains_aed_list=True`.
- Wykaz ministerstwa (`aed_dane_gov_pl.csv`) jako zwykły zasób dostawcy: walidacja danych tabelarycznych portalu kończy się FAILURE (typy zgadywane przez portal, opis w `docs/panel-portalu-krok-po-kroku.md`). Scalanie czyta plik bezpośrednio, więc mu to nie przeszkadza; zasób zbiorczy przechodzi, bo dostaje schemat tekstowy od razu.

### Sprawdzone w przeglądarce (22.11, ok. 01:45–01:55)

Frontend forka (`frontend/`, `ng serve`) podpięty do lokalnego API, panel pod `http://localhost:8001`. Klikane w przeglądarce (Chrome sterowany przez DevTools), okno 1440 px.

Uruchomienie frontendu na lokalnym API (plik proxy poza repozytorium, bo `proxy.aed-local.conf.json` kieruje `/media` na `https://127.0.0.1:443`, a `/api/aed` na usługę AED, której tu nie potrzeba):

```
// proxy.portal-local.conf.json
{
  "/api/**":  { "target": "http://localhost:8000/1.4/", "pathRewrite": { "^/api": "" }, "changeOrigin": true, "secure": false },
  "/media":   { "target": "http://localhost:8000", "changeOrigin": true, "secure": false },
  "/flags":   { "target": "https://dane.gov.pl/", "changeOrigin": true, "secure": true },
  "/pn-apps": { "target": "http://localhost:8001", "changeOrigin": true, "secure": false, "ws": true }
}
```
```
cd frontend
npx ng serve --configuration dev --port 4300 --no-prebundle --proxy-config /ścieżka/do/proxy.portal-local.conf.json
# http://localhost:4300/pl/dataset/4214  (zbiór zbiorczy), .../resource/40211 (tabela), .../resource/40211/map (mapa)
```

`--no-prebundle` jest konieczne: bez niego zakładka „Mapa” jest pusta, a w konsoli jest `Dynamic require of "leaflet" is not supported`. Przyczyna leży w kodzie portalu, nie w naszym: `src/app/services/leflet.service.ts` ładuje Leaflet przez `require('leaflet')`, a serwer deweloperski Angulara (esbuild/Vite) wydziela zależności z `node_modules` do osobnych modułów ESM. Buildu produkcyjnego (`npm run build:aed`) pod tym kątem nie sprawdzano.

Wyniki:

- **Strona zbioru** `http://localhost:4300/pl/dataset/4214`: „Krajowy wykaz defibrylatorów AED – wykaz zbiorczy”, dostawca Ministerstwo Cyfryzacji, kategoria Zdrowie, częstotliwość „Codziennie”, słowa kluczowe, jeden zasób „Krajowy wykaz AED” (CSV 253 kB) z ikonami mapy i tabeli. Zrzut `portal-01`.
- **Strona zasobu** `.../resource/40211`: poziom otwartości 3 gwiazdki, przyciski „CSV (253kB)”, „JSON” i „Wyświetl dane poprzez API”. Zrzut `portal-08`.
- **Tabela**: kolumny standardu (`id_aed`, `nazwa`, `szerokosc_geograficzna`…), 20 wierszy na stronę, 40 stron (781 rekordów). Zrzut `portal-06`.
- **Mapa** (z `--no-prebundle`): punkty z `/resources/40211/geo` w klastrach 739 + 21 + 21 = 781. Zrzut `portal-07`.
- **Panel, dodanie zasobu z plikiem Krosna i „Wykaz AED: TAK”**: formularz nie zapisuje zasobu i pokazuje przy polu „Wykaz AED” 10 komunikatów po polsku (6 × nieznana kolumna, w tym podpowiedzi „Czy chodziło o „dlugosc_geograficzna”?”, 4 × brak kolumny wymaganej w profilu publikacja). Zrzuty `portal-02` (formularz z polem i tekstem pomocy) i `portal-03` (błędy).
- **Panel, edycja istniejącego zasobu**: zasób „Wykaz AED Krosno (test formularza)” (plik Krosna, zapisany wcześniej z „NIE”) przełączony na „TAK” – zapis odrzucony z tymi samymi 10 komunikatami, w bazie flaga dalej `false`. Zasób Legionowa przełączony „TAK” → „NIE” – zapisany; potem „NIE” → „TAK” – zapisany z komunikatem „Zasób … został pomyślnie zmieniony”. Walidacja przy edycji czyta plik już zapisany w zasobie.
- **Wykaz jako link**: panel przyjmuje tylko adresy `https://` („Wymagany format protokołu to https://”), więc lokalny serwer HTTP odpada. Zasób z linkiem `https://api.dane.gov.pl/media/resources/20260914/aed.csv` (publiczny plik Legionowa) i „Wykaz AED: TAK” zapisał się bez sprawdzania (zgodnie z opisem: linki sprawdza dopiero scalanie). `create_main_aed_resource --dry-run` przyjął go: 4 wykazy, 3 przyjęte, link Legionowa 24/24. Ten sam plik Legionowa w dwóch zasobach jednego zbioru nie został połączony automatycznie (oba mają źródło `dane.gov.pl/4212`, a dwa rekordy z jednego źródła nigdy nie są łączone automatycznie) – wynik 805 zamiast 781 rekordów, 27 par do przeglądu zamiast 2. Zasób testowy usunięto w panelu, scalania właściwego nie uruchamiano, więc zasób zbiorczy dalej ma 781 rekordów.
- **Wykaz ministerstwa jako zwykły zasób, typy kolumn**: zakładka „Walidacja danych” pokazywała FAILURE („Wartość "" w wierszu 2 i kolumnie 11 nie jest typem "integer"”). W zakładce „Zmiana typu” portal wykrył jako `integer` pięć kolumn: `nr_budynku` (8), `kod_terc` (11), `kod_simc` (12) i `zrodlo_id` (35) i `kompletnosc` (38). Zmiana wszystkich pięciu na „Dane tekstowe” i „Zmień typ” → „Zmieniono typ danych”, po ok. 20 s walidacja danych SUCCESS (dwa zadania). Ręczna zmiana typów naprawia problem. Zrzut `portal-11` (stan po wyborze typów, przed kliknięciem „Zmień typ”).
- **`GET http://localhost:8000/aed-aggregated`** w przeglądarce (widok „Pretty-print” Chrome): raport z wykazami przyjętymi i odrzuconymi, 781 rekordów. Zrzut `portal-10`.
- Lista zasobów w panelu nie ma kolumny ani filtra „Wykaz AED” – zrzutu `portal-09` nie zrobiono.

Uwagi z przeglądarki: na stronach frontendu otwiera się okno „Polityka prywatności i RODO” z pustą treścią (frontend pyta `/cms/…`, a CMS nie jest uruchomiony) – trzeba je zamknąć; odnośniki „Pobierz” i „Wyświetl dane poprzez API” prowadzą pod `https://api.mcod.local/…` (adres API z ustawień backendu), więc lokalnie nie działają bez wpisu w `/etc/hosts` i TLS. Zegar panelu pokazuje czas kontenera.

Zrzuty (`docs/zrzuty/`): `portal-01`, `-02`, `-03`, `-06`, `-07`, `-08`, `-10`, `-11` to ekrany przeglądarki z tego uruchomienia. `portal-04` (`--dry-run`) i `portal-05` (`/aed-aggregated` z `curl`) to nadal wyjście terminala wyrenderowane do PNG.

### Poprawki po uruchomieniu

- `backend/docker-compose.local.yml`: wolumen `../aed_standard` w kontenerze testów bez `:ro`. `tests-entrypoint.sh` usuwa `*.pyc` pod `set -e`, a na wolumenie tylko do odczytu kończył się błędem, zanim uruchomił testy.
- W kodzie `mcod/aed`, migracjach i zaczepach nie znaleziono błędów.

### Obraz produkcyjny: pakiet `aed_standard`

`aed_standard` trafia do kontenerów wyłącznie przez montowanie `../aed_standard` w `docker-compose.local.yml` (katalog leży poza kontekstem budowania `backend/`). Dockerfile ministerstwa (`backend/docker/app/Dockerfile`) nie jest zmieniany. Obraz produkcyjny potrzebuje jednej z dwóch rzeczy: (a) skopiowania pakietu do `/usr/src/mcod_backend/aed_standard` – kontekst budowania musi wtedy obejmować katalog nadrzędny albo pakiet trzeba przed budową skopiować do `backend/` (np. `cp -r ../aed_standard backend/` w potoku CI i `COPY aed_standard /usr/src/mcod_backend/aed_standard` obok kopiowania kodu `mcod`); albo (b) instalacji pakietu (`pip install` z repozytorium lub archiwum) w warstwie zależności. Pakiet jest czystym Pythonem bez zależności, zgodnym z 3.8. Sprawdzone 22.11 w działającym kontenerze: `docker exec mcod-admin python -c "import aed_standard, sys; print(aed_standard.__file__, sys.version)"` → `/usr/src/mcod_backend/aed_standard/__init__.py 3.8.20`.

### Nadal niesprawdzone

- harmonogram Celery beat o 03:45 (zadanie uruchamiano ręcznie; wpis w harmonogramie sprawdza tylko `test_celery.py`);
- pliki XLSX jako wykazy, pełny import harvesterem XML (sprawdzono tylko parser i serializer testem); zasób-link przeszedł tylko `--dry-run`, nie scalanie właściwe;
- mapa w buildzie produkcyjnym frontendu (`build:aed`) – sprawdzono tylko `ng serve --no-prebundle`;
- nazwa pliku zawiera datę i pierwsze 8 znaków identyfikatora przebiegu, więc dwa scalenia w jednym dniu nie kolidują;
- nakładka domenowa (`Caddyfile`, `web.conf.template`, sesja `HttpOnly`) – tylko `caddy validate`, bez uruchomienia pod domeną.

### Czas i zasoby

Obrazy: usługi ok. 8 min, obraz testowy ok. 10 min (emulacja amd64, pobieranie z snapshot.debian.org). `init_mcod_db` ok. 2 min, przebudowa indeksów kilkanaście sekund, start panelu i API ok. 15 s. Pamięć w trakcie pracy: Elasticsearch ok. 2,9 GB (mimo sterty 512 MB, emulacja), panel i API po ok. 0,6 GB, kontener testów do 2 GB, reszta poniżej 0,5 GB. Na serwer: co najmniej 8 GB RAM, najlepiej natywny x86_64.

Znane ograniczenia:

- harvester CKAN nie przenosi flagi wykazu AED (XML – od schematu 1.14, sekcja wyżej). Zasób z CKAN albo z XML 1.13 redaktor oznacza ręcznie w panelu; przy kolejnych importach harvester nadpisuje tylko pola ze swojego serializera, więc flaga powinna zostać (wniosek, nie sprawdzono);
- plik XLSX jest sprawdzany dopiero przy scalaniu (na kopii CSV portalu), a nie w formularzu.
