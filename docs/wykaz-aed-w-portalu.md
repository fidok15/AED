# Wykaz AED w portalu – jak włączyć i pokazać

Instrukcja dla osoby z działającym lokalnym portalem (panel `http://localhost:8001`, API `http://localhost:8000` z `docker-compose.aed-ports.yml`, konto `admin@mcod.local` / `testadmin123!`). Opis mechanizmu i porównanie z wykazem DGA: `docs/wykaz-dga-analiza.md`.

## Co to robi

Dostawca (samorząd, instytucja, firma) publikuje w swoim zbiorze zasób CSV w strukturze standardu AED i zaznacza „Wykaz AED: TAK”. Portal sprawdza plik przy zapisie standardem `aed_standard` i pokazuje błędy po polsku. Codziennie o 03:45 portal scala wszystkie wykazy AED w jeden zasób „Krajowy wykaz AED” w zbiorze ministerstwa. Scalanie przechodzi przez walidację, deduplikację i profil `publikacja`, więc w wyniku nie ma danych OSM ani urządzeń prywatnych. Wynik i raport (które wykazy przyjęto, które odrzucono i dlaczego) są publiczne, bez logowania: `GET /aed-aggregated` oraz zwykły widok zbioru, tabeli i mapy.

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
3. **Instytucja ministerstwa.** W panelu: Instytucje → dodaj „Ministerstwo Cyfryzacji” (typ `state`) i odczytaj jej numer z adresu strony edycji. W `backend/.env` dopisz `MAIN_AED_DATASET_OWNER_ORGANIZATION_PK=<numer>` i powtórz krok 1. Bez tego wpisu właścicielem jest instytucja z `MAIN_DGA_DATASET_OWNER_ORGANIZATION_PK` (w `env.sample` 2844, w danych startowych jej nie ma), a zadanie skończy się błędem „Main AED Owner Institution not found”.
4. **Kategoria „Zdrowie”** (opcjonalnie): jeśli istnieje, zbiór zbiorczy dostanie ją automatycznie; jeśli nie, zbiór powstanie bez kategorii.

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

`seed_aed_demo` (nowa komenda, tylko demo) zakłada instytucje „Ministerstwo Cyfryzacji” (pk 2844, czyli domyślny `MAIN_DGA_DATASET_OWNER_ORGANIZATION_PK` z `env.sample`, więc dodatkowa zmienna nie jest potrzebna), „Gmina Miejska Legionowo” i „Gmina Krosno”, po jednym zbiorze i jednym zasobie z flagą „Wykaz AED” z prawdziwych plików: `datasets/out/aed_dane_gov_pl.csv`, `datasets/raw/dane_gov_pl/legionowo/resource_2625221.csv`, `datasets/raw/dane_gov_pl/krosno/resource_54632.csv` (Krosno zapisane z pominięciem formularza, żeby pokazać odrzucenie przy scalaniu).

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

### Nadal niesprawdzone

- harmonogram Celery beat o 03:45 (zadanie uruchamiano ręcznie; wpis w harmonogramie sprawdza tylko `test_celery.py`);
- pliki XLSX jako wykazy, harvester XML; zasób-link przeszedł tylko `--dry-run`, nie scalanie właściwe;
- mapa w buildzie produkcyjnym frontendu (`build:aed`) – sprawdzono tylko `ng serve --no-prebundle`;
- przy dwóch scaleniach w jednym dniu plik dostaje dopisek Django (`..._TiO6y0n.csv`), bo nazwa zawiera tylko datę; działa, ale nazwa jest mniej czytelna.

### Czas i zasoby

Obrazy: usługi ok. 8 min, obraz testowy ok. 10 min (emulacja amd64, pobieranie z snapshot.debian.org). `init_mcod_db` ok. 2 min, przebudowa indeksów kilkanaście sekund, start panelu i API ok. 15 s. Pamięć w trakcie pracy: Elasticsearch ok. 2,9 GB (mimo sterty 512 MB, emulacja), panel i API po ok. 0,6 GB, kontener testów do 2 GB, reszta poniżej 0,5 GB. Na serwer: co najmniej 8 GB RAM, najlepiej natywny x86_64.

Znane ograniczenia:

- harvester XML i CKAN nie przenoszą flagi wykazu AED. Zasób z harvestera redaktor oznacza ręcznie w panelu; przy kolejnych importach harvester nadpisuje tylko pola ze swojego serializera, więc flaga powinna zostać (wniosek, nie sprawdzono);
- plik XLSX jest sprawdzany dopiero przy scalaniu (na kopii CSV portalu), a nie w formularzu.
