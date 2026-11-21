# Jak dodać źródło danych o AED

Wszystkie źródła, z których powstaje rejestr krajowy, są opisane w jednym pliku: `aed_standard/sources.json`. Z tego pliku korzystają downloader (`scripts/download_aed_data.py`), mapper (`aed_standard/sources.py`), deduplikacja i zadanie cykliczne usługi AED. Cztery z sześciu obecnych źródeł (Krosno, Marki, Przemyśl, Legionowo) są opisane wyłącznie wpisami w tym pliku, bez osobnego kodu.

Po dodaniu wpisu:

```
python3 scripts/download_aed_data.py      # pobranie (dla zbiorów z dane.gov.pl)
python3 -m aed_standard build             # rejestr krajowy i raport
```

W usłudze AED to samo robi zadanie cykliczne (domyślnie co 24 godziny) albo przycisk ręcznego uruchomienia w panelu ministerstwa.

## Przypadek 1. Gmina publikuje dane według naszego wzorca

Kolumny pliku mają nazwy pól standardu (`wzorzec/wzorzec-aed.xlsx`), tak jak zbiór Legionowa. Wystarczy wpis z identyfikatorem zbioru na dane.gov.pl i `"fields": "*"`:

```json
{
  "id": "nowa-gmina",
  "label": "Nowa Gmina",
  "zrodlo": "dane.gov.pl/12345",
  "priority": 1,
  "dane_gov_pl": {"dataset_id": 12345, "resources": [67890]},
  "file": "dane_gov_pl/nowa-gmina/resource_67890.csv",
  "format": "csv",
  "record_id": {"row_number": true},
  "fields": "*",
  "fixes": ["drop_outliers"]
}
```

Jeśli plik ma kolumnę z identyfikatorem urządzenia, użyj jej zamiast numeru wiersza (`"record_id": {"column": "id"}`). Numer wiersza przesuwa się, gdy gmina wstawi wiersz w środku pliku, a od identyfikatora zależy `id_aed` zapisany w naklejce QR.

## Przypadek 2. Gmina z własnymi nazwami kolumn

Mapowanie `pole_standardu: kolumna_źródła` w `fields`. Przykład na wzór Krosna:

```json
{
  "id": "krosno",
  "label": "Krosno",
  "zrodlo": "dane.gov.pl/3624",
  "priority": 1,
  "dane_gov_pl": {"dataset_id": 3624},
  "file": "dane_gov_pl/krosno/resource_54632.csv",
  "format": "csv",
  "record_id": {"column": "Numer Id"},
  "coordinates": {"lat": "Szerokość geograficzna", "lon": "Długość geograficzna"},
  "fields": {"nazwa": "Lokalizacja"},
  "address_text": "Adres",
  "fixes": ["swap_lat_lon_outside_pl", "drop_outliers", "note_shared_points"]
}
```

| Klucz | Znaczenie |
|---|---|
| `id` | krótka nazwa źródła; też katalog w `datasets/raw/dane_gov_pl/` |
| `label` | nazwa w komunikatach raportu |
| `zrodlo` | wartość pola `zrodlo` w rekordach; dla dane.gov.pl zawsze `dane.gov.pl/<id zbioru>`. **Nie zmieniaj jej po publikacji** - od niej zależy `id_aed` |
| `priority` | pierwszeństwo przy łączeniu duplikatów, mniejsza liczba wygrywa: 1 zbiory z dane.gov.pl, 2 API Warszawy, 3 OpenStreetMap (0 mają zgłoszenia firm i zarządców) |
| `dane_gov_pl` | zbiór do pobrania; `resources` ogranicza pobieranie do wskazanych zasobów |
| `file` | plik w `datasets/raw/`, który mapujemy |
| `format` | `csv` albo `geojson` |
| `record_id` | skąd identyfikator rekordu w źródle: `{"column": ...}` (CSV), `{"property": ...}` (GeoJSON) albo `{"row_number": true}` |
| `coordinates` | kolumny szerokości i długości albo `"geometry"` dla GeoJSON; bez tego klucza współrzędne biorą się z `fields` |
| `fields` | mapowanie kolumn na pola standardu albo `"*"` |
| `address_text` | kolumna z adresem w jednym tekście, np. `ul. Jasna 12, 38-400 Krosno`; rozbijana na ulicę, numer, kod i miejscowość |
| `fixes` | naprawy danych, opisane niżej |
| `copy_values_on_merge` | `false` dla źródeł, których wartości nie wolno przepisywać do rekordów innych źródeł (licencja ODbL) |

Naprawy (`fixes`), każda opisana w `raport.json` w `naprawy_danych`:

| Naprawa | Co robi |
|---|---|
| `unwrap_quoted_rows` | rozpakowuje wiersze ujęte w jedną parę cudzysłowów (błąd eksportu w zbiorze Marek) |
| `swap_lat_lon_outside_pl` | zamienia szerokość z długością, gdy punkt leży poza Polską, a po zamianie w Polsce |
| `drop_outliers` | usuwa współrzędne punktu położonego ponad 20 km od pozostałych punktów zbioru gminy |
| `note_shared_points` | tylko zgłasza różne adresy o identycznych współrzędnych, bez zmian w danych |

## Przypadek 3. Źródło niestandardowe

API albo plik, którego nie da się opisać mapowaniem kolumn (Warszawa, OpenStreetMap):

1. W `aed_standard/sources.py` dopisz funkcję `nazwa(raw_dir, entry, source, licence) -> (records, notes)` i dodaj ją do słownika `CODE_MAPPERS`.
2. Dopisz jej nazwę do `CODE_MAPPERS` w `aed_standard/registry.py`.
3. Dodaj wpis z kluczem `"mapper": "nazwa"` zamiast `format`, `record_id` i `fields`.
4. Jeśli źródło nie jest zbiorem z dane.gov.pl, dopisz jego pobieranie w `scripts/download_aed_data.py`.
5. Dodaj test na prawdziwym pliku źródła w `tests/test_aed_standard.py`.

## Licencje

Licencja źródła pochodzi z manifestu pobrania (dla dane.gov.pl z API portalu) i jest tłumaczona słownikiem `licences` w `sources.json` na jedną z licencji standardu: `CC0 1.0`, `CC BY 4.0`, `ODbL 1.0`. Źródło z licencją spoza słownika jest pomijane. Dopisanie nowej licencji (np. `CC BY-SA 4.0`) to decyzja prawna, nie techniczna: trzeba ustalić, czy dane na tej licencji mogą trafić do zbioru publikowanego przez ministerstwo, a potem dopisać ją do `licences` i do słownika pola `licencja` w `schema.json`.

## Gdy coś pójdzie nie tak

Błędny wpis, nieobsługiwana licencja, brak pliku albo plik, w którym zmieniły się nazwy kolumn, nie zatrzymują budowy. Źródło jest pomijane, a komunikat po polsku trafia:

- do `datasets/out/raport.json` (`bledy_zrodel`, `pominiete_zrodla`) i na ekran przy `python3 -m aed_standard build` (linie zaczynające się od `!`);
- do historii zadań w panelu ministerstwa.

Urządzenia z pominiętego źródła **nie są wycofywane** z rejestru. Zostają z danymi z poprzedniego udanego przebiegu i wracają do aktualizacji po naprawie wpisu.

Test `tests/test_aed_standard.py` (`NewSourceTest`) pokazuje cały przypadek 2 na fikcyjnej gminie oraz pomijanie źródła z błędem.
