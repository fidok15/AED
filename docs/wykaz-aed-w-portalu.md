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

Uruchomione na tej maszynie:

- `python3.8 -m unittest tests.test_wykaz` – 6 testów na prawdziwych plikach z `datasets/raw/` (Legionowo przyjęty, Krosno odrzucony z komunikatami, wiersz OSM i wiersz z błędem pominięte, urządzenie prywatne poza wykazem krajowym, licencja spoza standardu, scalenie z rejestrem ministerstwa, plik krajowy jest poprawnym wykazem w standardzie);
- plik krajowy (781 wierszy) z naszym `tabular_data_schema` przechodzi walidację goodtables 2.1.4 / tableschema 1.21.0 / tabulator 1.53.5, czyli w wersjach z `backend/Pipfile.lock` i z tymi samymi opcjami co `resources/indexed_data.py:610`;
- `python3.8 -m py_compile` wszystkich nowych i zmienionych plików backendu oraz `flake8` z konfiguracją `backend/.flake8`.

Sprawdzone tylko czytaniem kodu (nieuruchomione, bo portal tu nie działa):

- migracje, rejestracja aplikacji `mcod.aed`, formularz i zestawy pól w panelu;
- zadanie Celery, ponowienia, sprzątanie, podmiana zasobu zbiorczego;
- widok `/aed-aggregated`;
- odczyt pliku zasobu (CSV, kopia CSV z XLSX, link);
- zachowanie mapy we frontendzie;
- testy Django w `backend/mcod/aed/tests/test_aed_utils.py`. Wymagają stosu testowego portalu: `docker compose -f docker-compose.local.yml --profile tests run --rm mcod-local-tests mcod/aed`. Wejście kontenera dokleja argumenty do `pytest` i wcześniej robi `makemigrations --check`, więc sprawdzi też, czy migracje zgadzają się z modelami.

Znane ograniczenia:

- harvester XML i CKAN nie przenoszą flagi wykazu AED. Zasób z harvestera redaktor oznacza ręcznie w panelu; przy kolejnych importach harvester nadpisuje tylko pola ze swojego serializera, więc flaga powinna zostać (wniosek, nie sprawdzono);
- plik XLSX jest sprawdzany dopiero przy scalaniu (na kopii CSV portalu), a nie w formularzu.
