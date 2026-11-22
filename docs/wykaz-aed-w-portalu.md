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
   - `curl http://localhost:8000/aed-aggregated` – identyfikatory zbioru i zasobu oraz raport (z polem `stale_adresy`);
   - stałe adresy, które działają także po kolejnym scalaniu: `GET /aed-aggregated/resource` → 302 na bieżący zasób w API, `GET /aed-aggregated/file` → 302 na `/resources/<id>/file` (licznik pobrań portalu, potem plik CSV);
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
- Drugie uruchomienie zastępuje zasób zbiorczy: nowy zasób w tym samym zbiorze, stary zwraca 404, zbiór zbiorczy jest jeden. Dlatego od 22.11 są stałe adresy (rozdział „Stały adres zasobu zbiorczego”).
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

`--no-prebundle` jest konieczne: bez niego zakładka „Mapa” jest pusta, a w konsoli jest `Dynamic require of "leaflet" is not supported`. Przyczyna leży w kodzie portalu, nie w naszym: `src/app/services/leflet.service.ts` ładuje Leaflet przez `require('leaflet')`, a serwer deweloperski Angulara (esbuild/Vite) wydziela zależności z `node_modules` do osobnych modułów ESM. Build produkcyjny (`npm run build:aed`) tego problemu nie ma – sprawdzone 22.11 (rozdział „Mapa w buildzie produkcyjnym”).

Wyniki:

- **Strona zbioru** `http://localhost:4300/pl/dataset/4214`: „Krajowy wykaz defibrylatorów AED – wykaz zbiorczy”, dostawca Ministerstwo Cyfryzacji, kategoria Zdrowie, częstotliwość „Codziennie”, słowa kluczowe, jeden zasób „Krajowy wykaz AED” (CSV 253 kB) z ikonami mapy i tabeli. Zrzut `portal-01`.
- **Strona zasobu** `.../resource/40211`: poziom otwartości 3 gwiazdki, przyciski „CSV (253kB)”, „JSON” i „Wyświetl dane poprzez API”. Zrzut `portal-08`.
- **Tabela**: kolumny standardu (`id_aed`, `nazwa`, `szerokosc_geograficzna`…), 20 wierszy na stronę, 40 stron (781 rekordów). Zrzut `portal-06`.
- **Mapa** (z `--no-prebundle`): punkty z `/resources/40211/geo` w klastrach 739 + 21 + 21 = 781. Zrzut `portal-07`.
- **Panel, dodanie zasobu z plikiem Krosna i „Wykaz AED: TAK”**: formularz nie zapisuje zasobu i pokazuje przy polu „Wykaz AED” 10 komunikatów po polsku (6 × nieznana kolumna, w tym podpowiedzi „Czy chodziło o „dlugosc_geograficzna”?”, 4 × brak kolumny wymaganej w profilu publikacja). Zrzuty `portal-02` (formularz z polem i tekstem pomocy) i `portal-03` (błędy).
- **Panel, edycja istniejącego zasobu**: zasób „Wykaz AED Krosno (test formularza)” (plik Krosna, zapisany wcześniej z „NIE”) przełączony na „TAK” – zapis odrzucony z tymi samymi 10 komunikatami, w bazie flaga dalej `false`. Zasób Legionowa przełączony „TAK” → „NIE” – zapisany; potem „NIE” → „TAK” – zapisany z komunikatem „Zasób … został pomyślnie zmieniony”. Walidacja przy edycji czyta plik już zapisany w zasobie.
- **Wykaz jako link**: panel przyjmuje tylko adresy `https://` („Wymagany format protokołu to https://”), więc lokalny serwer HTTP odpada. Zasób z linkiem `https://api.dane.gov.pl/media/resources/20260914/aed.csv` (publiczny plik Legionowa) i „Wykaz AED: TAK” zapisał się bez sprawdzania (zgodnie z opisem: linki sprawdza dopiero scalanie). `create_main_aed_resource --dry-run` przyjął go: 4 wykazy, 3 przyjęte, link Legionowa 24/24. Ten sam plik Legionowa w dwóch zasobach jednego zbioru nie został połączony automatycznie (oba mają źródło `dane.gov.pl/4212`, a dwa rekordy z jednego źródła nigdy nie są łączone automatycznie) – wynik 805 zamiast 781 rekordów, 27 par do przeglądu zamiast 2. Poprawione 22.11 (rozdział „Powtórzony wykaz tej samej instytucji”). Zasób testowy usunięto w panelu, scalania właściwego nie uruchamiano, więc zasób zbiorczy dalej ma 781 rekordów.
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

- harmonogram Celery beat o pełnej porze 03:45 w działającym wdrożeniu (beat uruchomiono jednorazowo z porą przestawioną zmienną środowiskową – rozdział „Celery Beat”);
- pliki XLSX jako wykazy, pełny import harvesterem XML (sprawdzono tylko parser i serializer testem); zasób-link przeszedł tylko `--dry-run`, nie scalanie właściwe;
- nazwa pliku zawiera datę i pierwsze 8 znaków identyfikatora przebiegu, więc dwa scalenia w jednym dniu nie kolidują;
- nakładka domenowa (`Caddyfile`, `web.conf.template`, sesja `HttpOnly`) – tylko `caddy validate`, bez uruchomienia pod domeną.

### Czas i zasoby

Obrazy: usługi ok. 8 min, obraz testowy ok. 10 min (emulacja amd64, pobieranie z snapshot.debian.org). `init_mcod_db` ok. 2 min, przebudowa indeksów kilkanaście sekund, start panelu i API ok. 15 s. Pamięć w trakcie pracy: Elasticsearch ok. 2,9 GB (mimo sterty 512 MB, emulacja), panel i API po ok. 0,6 GB, kontener testów do 2 GB, reszta poniżej 0,5 GB. Na serwer: co najmniej 8 GB RAM, najlepiej natywny x86_64.

Znane ograniczenia:

- harvester CKAN nie przenosi flagi wykazu AED (XML – od schematu 1.14, sekcja wyżej). Zasób z CKAN albo z XML 1.13 redaktor oznacza ręcznie w panelu; przy kolejnych importach harvester nadpisuje tylko pola ze swojego serializera, więc flaga powinna zostać (wniosek, nie sprawdzono);
- plik XLSX jest sprawdzany dopiero przy scalaniu (na kopii CSV portalu), a nie w formularzu.

## Zmiany i sprawdzenia 22.11 (ok. 04:15–05:15)

Wszystko na lokalnym stosie z danymi demo (`seed_aed_demo`). Komendy z katalogu `backend/`, `C` to `docker compose -f docker-compose.local.yml -f docker-compose.aed-mac.yml -f docker-compose.aed-ports.yml` (w zsh jako funkcja: `C() { docker compose -f … "$@"; }`).

### Stały adres zasobu zbiorczego

Każde scalanie tworzy nowy zasób i usuwa poprzedni (wzorzec DGA), więc `/resources/<id>` sprzed scalania zwraca 404. DGA rozwiązuje to po stronie frontendu: strona punktu informacyjnego pyta `/dga-aggregated` o bieżący identyfikator (`frontend/src/app/services/dga.service.ts`, `getDgaAggregatedData`). Dla odnośników spoza portalu dodaliśmy w API dwa stałe adresy (`AggregatedAEDRedirectView` w `mcod/aed/views.py`, trasy w `mcod/routes.py`), zbudowane jak istniejące przekierowanie portalu `/resources/<id>/file` (`ResourceFileDownloadView`: `response.location` i `HTTP_302`):

- `GET /aed-aggregated/resource` → 302 na `API_URL/resources/<bieżący id>`,
- `GET /aed-aggregated/file` → 302 na `API_URL/resources/<bieżący id>/file` (to drugie przekierowanie portalu liczy pobranie i prowadzi do pliku CSV),
- 404, gdy zasób albo zbiór zbiorczy nie jest opublikowany (te same warunki co `/aed-aggregated`); `Cache-Control: no-cache`.

`/aed-aggregated` podaje oba adresy w `report.stale_adresy`, a opis zasobu zbiorczego (`RESOURCE_DESC`) – adres pliku. Zbiór zbiorczy ma stały identyfikator (4214 w danych demo) i nie wymaga przekierowania. Test: `test_aed_aggregated_permanent_addresses_follow_the_current_resource` (`tests/test_views.py`).

Sprawdzone w stosie: dwa scalenia z rzędu (`docker exec mcod-admin python manage.py create_main_aed_resource`):

```
merge 1: 40220 -> 40221   location: https://api.mcod.local/resources/40221   (…/file -> /resources/40221/file)   old /resources/40220: 404
merge 2: 40221 -> 40222   location: https://api.mcod.local/resources/40222   (…/file -> /resources/40222/file)   old /resources/40221: 404
curl -sI localhost:8000/resources/40222/file  ->  302 …/media/resources/20261122/Krajowy_wykaz_AED__…_4a45d9a7.csv  (782 wiersze z nagłówkiem)
```

Kolejny krok (oceniony, niewdrożony): zachować ten sam zasób i podmieniać tylko plik. Portal ma `ResourceFile` z `is_main`, a zapis pliku uruchamia walidację i indeksowanie, ale formularz panelu w ogóle nie pozwala wymienić pliku istniejącego zasobu (sprawdzone 22.11: edycja zasobu nie ma pola pliku), a DGA nigdy tego nie robi. Trzeba by sprawdzić, czy ponowne przetwarzanie pliku w tym samym zasobie czyści stary indeks danych i mapy (`resource-<id>` w Elasticsearch) i co widzi użytkownik w trakcie walidacji. To odejście od wzorca DGA – zostaje jako propozycja. Przy okazji: indeksy `resource-<id>` usuniętych zasobów zbiorczych zostają w Elasticsearch (np. `resource-40222` po usunięciu zasobu) – zachowanie portalu po usunięciu zasobu, nie naszej łatki; przy codziennym scalaniu trzeba to sprzątać (zgłoszenie do opiekunów).

### Powtórzony wykaz tej samej instytucji

`build_main_aed_list` (`mcod/aed/aed_utils.py`) liczy skrót SHA-256 treści każdego odczytanego wykazu po usunięciu BOM UTF-8, zamianie CRLF/CR na LF i obcięciu końcowych pustych linii (`list_digest`). Drugi i kolejny wykaz o tym samym skrócie **w tej samej instytucji** dostaje w raporcie status `powtorzony` i pole `powtorzenie_zasobu` (identyfikator pierwszego zasobu, czyli o najniższym numerze) i nie wchodzi do scalania ani do `wykorzystane_zasoby`; raport ma licznik `wykazy_powtorzone`. Wykazy pokrywające się częściowo scalają się jak dotąd. Ten sam plik w **innej** instytucji nie jest powtórzeniem – to dalej osobne źródło (do decyzji, czy też ma być wykrywany). Powiadomienia e-mail pomijają wpis `powtorzony` (wiadomość dostaje tylko pierwszy wykaz). Test: `test_identical_list_of_the_same_institution_is_not_merged_twice` (prawdziwy plik Legionowa, kopia bez BOM i z CRLF, wykaz bez ostatniego wiersza i ten sam plik w innej instytucji).

Dowód w stosie: kontem admina w panelu dodany zasób „Wykaz AED Legionowo – kopia (test powtórzenia)” (40224) z tym samym plikiem w zbiorze Legionowa, „Wykaz AED: TAK”:

```
docker exec mcod-admin python manage.py create_main_aed_resource --dry-run
{'wykazy_razem': 4, 'wykazy_przyjete': 2, 'wykazy_powtorzone': 1, 'rekordy_z_wykazow': 805, 'polaczenia': 24, 'do_przegladu': 1, 'rekordy_w_wykazie_krajowym': 781}
40224 powtorzony Wykaz AED Legionowo – kopia (test powtórzenia) 40208
```

Wcześniej ten sam przypadek dawał 805. Zasób 40224 usunięto w panelu; scalania właściwego z nim nie uruchamiano.

### Celery Beat

W lokalnym stosie worker działa bez `-B`. Beat uruchomiono jednorazowo w kontenerze `mcod-celery`, z porą zadania przestawioną istniejącą zmienną portalu `UPDATE_TASKS_CELERY_BEAT_TIME` (`mcod/celeryapp.py`, `update_beat_schedule`) – bez zmian w kodzie i bez trwałego harmonogramu w bazie (`PersistentScheduler` z plikiem w `/tmp` kontenera zamiast `DatabaseScheduler`):

```
M=$(date -u -v+2M +%M); H=$(date -u -v+2M +%H)
docker exec -e PYTHONUNBUFFERED=1 \
  -e UPDATE_TASKS_CELERY_BEAT_TIME="{\"aed_main_resource_creation\": {\"minute\": \"$M\", \"hour\": \"$H\"}}" \
  mcod-celery timeout 150 python -c "
import logging, sys
from celery.signals import beat_init
from mcod.celeryapp import app
@beat_init.connect
def enable_beat_log(**kw):
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter('[%(asctime)s: %(levelname)s/%(name)s] %(message)s'))
    lg = logging.getLogger('celery.beat'); lg.disabled = False; lg.setLevel('INFO'); lg.addHandler(h)
app.start(['beat', '-l', 'INFO', '--scheduler', 'celery.beat:PersistentScheduler', '-s', '/tmp/aed-beat-test-schedule'])
"
docker logs --since 5m mcod-celery | grep -i "Step\|AED lists\|retries"
curl -s http://localhost:8000/aed-aggregated
```

Wynik (zrzut `docs/zrzuty/portal-13-celery-beat.png` – log wyrenderowany do PNG): beat o 03:57 UTC „Scheduler: Sending due task aed_main_resource_creation (mcod.aed.tasks.create_main_aed_resource_task)”, worker kroki 1–4 z jednym ponowieniem „Pending validation(s)”, „No more retries - success”, `/aed-aggregated` → `resource_id` 40228, `updated_at` 2026-11-22T03:57:26Z, 781 rekordów. Wcześniej dwa przebiegi bez logu beat (03:47, 03:51) też uruchomiły scalanie.

Ustalenia:

- **Pora jest w UTC.** `celeryapp.py` ustawia `app.conf.timezone = UTC`, więc „03:45” to 04:45 czasu polskiego zimą i 05:45 latem (logi portalu są w `Europe/Warsaw`). Tak samo działają pozostałe zadania portalu, w tym DGA o 03:30.
- **Log beat jest wyciszony.** `LOGGING` portalu ma `disable_existing_loggers: True`, więc zwykłe `celery beat -l INFO` nie wypisuje „Sending due task” (sprawdzone dwa razy). Do dowodu włączono logger `celery.beat` sygnałem `beat_init` w poleceniu wyżej. W produkcji o wykonaniu świadczy log workera i `updated_at` w `/aed-aggregated`.

### Jeden rekord od naklejki do wykazu krajowego

Urządzenie demonstracyjne **`AED-PRIFSO7R4SNZ`** („Urządzenie demonstracyjne – ścieżka QR → portal”, Philips HeartStart FRx, numer seryjny `DEMO-QR-PORTAL-0001`, Warszawa 52.241, 21.011) zostaje w danych demo prototypu i portalu. Kroki (22.11, ok. 04:58–05:01; `B=http://localhost:8080/api/aed`):

1. Logowanie firmy: `curl -s -X POST $B/sesja -d '{"email":"pulsar@aed.example","haslo":"pulsar-demo"}'` → token.
2. Zgłoszenie (profil `sprzedaz`): `POST $B/urzadzenia` z polami producent, model, numer seryjny, daty, `dysponent_nazwa`, `dysponent_email` (`zarzadca.demo@aed.example`), `nazwa` → `podsumowanie.przyjete: 1`, `id_aed: AED-PRIFSO7R4SNZ`, `naklejka_url`, `link_aktywacyjny: /aed/qr/AED-PRIFSO7R4SNZ?t=…`.
3. Naklejka: `GET $B/urzadzenia/AED-PRIFSO7R4SNZ/naklejka.svg` → 200 `image/svg+xml`; strona QR `http://localhost:8080/aed/qr/AED-PRIFSO7R4SNZ?t=…` → 200.
4. Potwierdzenie zarządcy: `POST $B/urzadzenia/AED-PRIFSO7R4SNZ/potwierdzenie` z tokenem, nazwą, współrzędnymi, miejscowością, dostępem `publiczny`, godzinami `Mo-Fr 08:00-16:00`, `stan: sprawny` → `status: aktywny` (etykieta interfejsu „Zweryfikowany” według `aed-qr.component.spec.ts`; tego ekranu nie oglądano, potwierdzenie szło przez API), `sposob_weryfikacji: qr`, `kompletnosc: 87`.
5. Eksport: `GET $B/eksport/dane-gov-pl.csv` → 782 rekordy (781 z mappera + to urządzenie); `grep -c AED-PRIFSO7R4SNZ` → 1. Różnica identyfikatorów względem `datasets/out/aed_dane_gov_pl.csv`: tylko ten jeden.
6. Portal, kontem admina: nowy zasób „Wykaz AED – eksport rejestru usługi AED (22.11.2026)” (40229) w zbiorze ministerstwa „Rejestr zgłoszeń AED” z plikiem z kroku 5 i „Wykaz AED: TAK”; dotychczasowy wykaz ministerstwa (40207) przełączony na „Wykaz AED: NIE”. Wariant wybrany, bo nie zawyża wyniku: panel nie pozwala wymienić pliku istniejącego zasobu, a drugi wykaz tej samej instytucji z prawie tą samą treścią nie jest „powtórzony” (inny skrót) i podwoiłby 781 rekordów (rekordy jednego źródła nie są łączone automatycznie). `seed_aed_demo` nie doda starego wykazu z powrotem, bo zbiór ma już zasób z flagą.
7. Scalanie: `docker exec mcod-admin python manage.py create_main_aed_resource` → zasób zbiorczy 40228 → 40230; raport: 3 wykazy, 2 przyjęte (Legionowo 24, eksport usługi 782), Krosno odrzucone, 806 rekordów z wykazów, 24 połączenia, **782 w wykazie krajowym**.
8. Wynik: plik ze stałego adresu `/aed-aggregated/file` (→ `/resources/40230/file` → CSV) zawiera `AED-PRIFSO7R4SNZ` (`grep -c` → 1, 783 linie z nagłówkiem). `GET /resources/40230/data?q=AED-PRIFSO7R4SNZ` zwraca ten rekord jako pierwszy, ale `meta.count` = 782 – wyszukiwanie tabeli sortuje po trafności zamiast filtrować dokładnie (zachowanie portalu).

Harvestera XML na pliku z usługi (`/api/aed/eksport/dane-gov-pl.xml`) nie uruchamiano: limit czasu tej rundy; ograniczenia adresu opisuje `docs/panel-portalu-krok-po-kroku.md`.

### Mapa w buildzie produkcyjnym

`npm run build:aed` (= `ng build --configuration aed`, podmiana `environment.aed.ts`, `outputHashing: all`) w `frontend/` – 27 s, bez błędów (ostrzeżenia CSS z kodu portalu). Wynik `frontend/dist/frontend/browser` podany jednorazowym kontenerem `nginx:1.27-alpine` na porcie 8090 z konfiguracją poza repozytorium (`/api/` → `http://host.docker.internal:8000/1.4/`, `/media/` → `:8000`, `/flags/` → dane.gov.pl, reszta `try_files … /index.html`), potem zatrzymany. W przeglądarce (Playwright, 1440 px): strona zbioru 4214 („Krajowy wykaz defibrylatorów AED – wykaz zbiorczy”), tabela zasobu 40230 (kolumny standardu, 20 wierszy na stronę), **mapa: klastry 740 + 21 + 21 = 782** z `/resources/40230/geo?bbox=…` – zrzut `docs/zrzuty/portal-14-mapa-build-produkcyjny.png`. W buildzie produkcyjnym nie trzeba `--no-prebundle`. W konsoli nie ma błędów Leaflet; są błędy otoczenia: `/cms/api/pages` (CMS nie działa, „Http failure during parsing”) i 429 z `tile.openstreetmap.org` (serwer kafelków OSM ograniczył zautomatyzowaną przeglądarkę – stąd szare tło mapy na zrzucie). Na serwerze publicznym podkład z `tile.openstreetmap.org` podlega zasadom użycia OSM (ograniczenie do slajdu).

### Przegląd panelu (Playwright, konta jury i admin)

- Panel po polsku (`lang="pl"`, menu, komunikaty Django); `AggregatedAEDInfo` nie jest zarejestrowany w panelu (tak jak `AggregatedDGAInfo`).
- Konto jury widzi w zbiorach i zasobach tylko swoją instytucję. Lista zasobów nie ma kolumny ani filtra „Wykaz AED” – DGA też nie ma kolumny dla swojej flagi, więc nie dodawano. Zrzut `portal-15-panel-lista-zasobow-jury.png`.
- **Poprawione:** pole „Wykaz AED” zachowywało się jak dwa niezależne pola wyboru (TAK i NIE zaznaczone naraz; formularz zapisałby wtedy ostatnią wartość, czyli NIE). Pole DGA ma w `templates/admin/resources/change_form.html` skrypt wyłączności; dopisany identyczny dla `contains_aed_list` (4 linie). Sprawdzone w przeglądarce: kliknięcie TAK odznacza NIE i odwrotnie.
- **Poprawione:** tekst pomocy pola ma odnośnik „Wzorzec i konwerter wykazu AED”, gdy ustawiono `MAIN_AED_LIST_HELP_URL` (lokalnie w `.env`: `http://localhost:8080/pl/aed/!konwerter`, przykład zakomentowany w `env.sample`), a lista błędów kończy się zdaniem „Plik można przekształcić do standardu AED w konwerterze: <adres>” (test `test_form_messages_point_to_the_converter`). Zrzuty `portal-02`, `portal-03` podmienione (prawdziwe ekrany).
- Odrzucenie Krosna: na górze formularza ogólny komunikat Django „Proszę, popraw poniższy błąd.”, przy polu 10 komunikatów po polsku z instrukcją („Popraw nazwę zgodnie z arkuszem „Słownik pól” albo usuń kolumnę”, „Czy chodziło o „nazwa”?”, „Dodaj ją do nagłówka”). Po błędzie panel czyści pole pliku – zachowanie oryginalnego portalu.
- Legionowo w zbiorze jury – zapisane; przełączenie TAK → NIE → TAK – zapisane; Legionowo z TAK w zbiorze Legionowa (konto jury) – odmowa „Wykaz AED można oznaczyć tylko w zbiorze swojej instytucji.”. Zasoby testowe usunięte.
- Zbiór 4214: CC BY 4.0 z warunkami, kategoria Zdrowie, tagi AED / defibrylator / wykaz zbiorczy, „Codziennie”. Opisy zbioru i zasobu w bazie demo były starsze niż stałe w `constants.py` (scalanie przenosi opis poprzedniego zasobu, jak DGA – ręczna zmiana redaktora zostaje); w danych demo nadpisane bieżącym tekstem. Mapy i wykresy zasobu zbiorczego: `nazwa` = Etykieta, `szerokosc_geograficzna` = Szerokość, `dlugosc_geograficzna` = Długość geograficzna.
