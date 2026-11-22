# Wykaz DGA w portalu dane.gov.pl – jak działa i co z niego bierzemy dla AED

Analiza kodu forka `backend/` (mcod 2.63.0). Wszystko poniżej ustalono **czytaniem kodu**; portalu na tej maszynie nie uruchomiono. Odwołania `plik:linia` są względem `backend/` i stanu gałęzi `feat/zasilanie-xml-i-panel-portalu` (linie w `resources/forms.py` i `resources/admin.py` po dodaniu pola AED; dodane linie AED są wymienione osobno na końcu).

## Co to jest „wykaz” w portalu

W kodzie jest jeden mechanizm, który zbiera zasoby wielu dostawców i scala je w jedną listę: **wykaz zasobów chronionych danych (DGA, Data Governance Act)**. Każda instytucja publiczna publikuje we własnym zbiorze zasób-wykaz o ustalonych kolumnach, a portal raz dziennie skleja wszystkie wykazy w jeden zasób zbiorczy w zbiorze Ministerstwa Cyfryzacji.

Inne miejsca, w których pada słowo „wykaz”, nie scalają danych:

- „dane o wysokiej wartości z wykazu KE” to tylko flaga zasobu i zbioru (`resources/forms.py:235`, `datasets/forms.py:122`);
- katalog metadanych CSV/XML (`datasets/tasks.py:108`, `datasets/tasks.py:115`) agreguje metadane wszystkich zbiorów, nie treść zasobów;
- `resources/management/commands/dga_migrate.py` to jednorazowa migracja: szuka istniejących zasobów po nazwie („chronionych danych”, linia 23) i oznacza je jako wykaz DGA (linie 128–176).

## Mechanizm od końca do końca

### 1. Oznaczenie zasobu jako wykazu

- Pole modelu: `Resource.contains_protected_data = BooleanField(default=False)` – `resources/models.py:579`. Właściwość `is_dga` = flaga + opublikowany + nieusunięty – `resources/models.py:1380`.
- Formularz panelu: pole `contains_protected_data` jako wybór TAK/NIE z opisem po polsku – `resources/forms.py:253`; widoczne w zakładce ogólnej zasobu (`resources/admin.py:356`, zestaw pól przy dodawaniu – wpis `contains_protected_data` w `get_fieldsets`). Dla zasobów z harvestera pokazywana jest wersja tylko do odczytu `contains_protected_data_info` (`resources/admin.py:356`, `:853`).
- Ograniczenie typu instytucji: tylko `local` i `state` – `resources/dga_constants.py:40` (`ALLOWED_DGA_INSTITUTIONS`), sprawdzane w `resources/forms.py:422` i w harvesterze (`resources/dga_utils.py:887`).
- Wykluczenie innych flag: wykaz nie może być jednocześnie danymi dynamicznymi, badawczymi ani o wysokiej wartości – `resources/forms.py:408`, `resources/dga_utils.py:872`.
- **Jeden wykaz na instytucję.** `get_dga_resource_for_institution` (`resources/dga_utils.py:147–179`) szuka opublikowanych zasobów z flagą w zbiorach instytucji i zgłasza błąd przy więcej niż jednym. Przy zapisie nowego wykazu panel pokazuje stronę potwierdzenia „zastąpisz obecny wykaz” (`resources/admin.py:750–778`, `:780` i dalej; szablony `templates/admin/save_confirmation.html`, `deselect_dga_confirmation.html`, `dga_to_draft_confirmation.html`), a po potwierdzeniu formularz zdejmuje flagę ze starego zasobu (`resources/forms.py:489–511`). Plik wgrany przed potwierdzeniem czeka w katalogu tymczasowym (`resources/admin.py:741`, `resources/dga_utils.py:203`), który czyści zadanie `clean_dga_temp_directory` (`resources/tasks/dga.py:111–126`, harmonogram `celeryapp.py:83`). Zbiór zwraca tytuły swoich wykazów: `datasets/models.py:676`.
- Usuwanie wykazu: osobne ostrzeżenie w `templates/admin/delete_confirmation.html:48`.

### 2. Walidacja kolumn – kiedy i jak

- **Przy zapisie w panelu** (`ResourceForm.clean`, `resources/forms.py:298`): dla zasobu z flagą plik musi być XLS/XLSX/CSV (`resources/dga_constants.py:5`), a kolumny muszą mieć dokładnie te nazwy i tę kolejność: `Lp.`, `Zasób chronionych danych`, `Format danych`, `Rozmiar danych`, `Warunki ponownego wykorzystywania` (`resources/dga_constants.py:33`). Sprawdza to `validate_dga_file_columns` (`resources/dga_utils.py:124`, odczyt przez pandas z wykryciem kodowania i separatora: `:94–116`), wywołane z `resources/forms.py:437`. Link zamiast pliku jest odrzucany (`resources/forms.py:513`). Przy edycji istniejącego zasobu sprawdzany jest zapisany plik. Komunikaty są błędami formularza, przetłumaczonymi na polski.
- **Przy imporcie harvesterem XML** (`harvester/serializers.py:569–680`, pole `containsProtectedData` w XSD od 1.12: `data/harvester/xml_import_otwarte_dane_1_13.xsd:666`): typ instytucji, konflikt flag, czy adres pliku odpowiada, typ treści, kolumny, najwyżej jeden wykaz w pliku XML (`resources/dga_utils.py:893`) i czy instytucja nie ma już wykazu z innego źródła (`resources/models.py:1606`).
- **Przy imporcie z CKAN** (`harvester/models.py:810–1012`): te same reguły jako „częściowy import” – zbiór z błędnym wykazem jest odrzucany, reszta importu przechodzi; kody błędów i ich opisy po polsku w `harvester/ckan_utils.py:15–23` i `:116–290`. Raport importu trafia do panelu harvestera.
- **Przy scalaniu**: tylko zasoby, które przeszły wszystkie zadania walidacji portalu (`data_tasks_last_status`, `file_tasks_last_status`, `link_tasks_last_status` = `SUCCESS`, `resources/dga_utils.py:234–266`), a potem kontrola treści każdego wykazu (`:316–398`).

### 3. Co uruchamia scalanie

Wyłącznie harmonogram Celery Beat: `dga_main_resource_creation` codziennie o 03:30 (`celeryapp.py:88–92`), kolejka `resources` (`settings/base.py:972`). Nie ma sygnału po zapisie wykazu ani przycisku w panelu – scalanie „na żądanie” to wywołanie zadania z powłoki.

### 4. Zadanie scalające – `create_main_dga_resource_task` (`resources/tasks/dga.py:23–108`)

1. **Plik zbiorczy** – `create_main_dga_file` (`resources/dga_utils.py:509–532`): wszystkie wykazy posortowane po nazwie instytucji (`:234`), dla każdego DataFrame (`:371`: plik lokalny przez `resource.tabular_data`, zasób z CKAN – pobranie linku `:269–313`), dopisanie kolumny „Nazwa dysponenta zasobu” z nazwy instytucji, numeracja `Lp.`, stała „Warunki ponownego wykorzystywania” (`:401–459`), zapis XLSX z formatowaniem (`:462–506`) do `media/main_dga` (`settings/base.py:404`).
2. **Zasób zbiorczy** – `create_main_dga_resource_with_dataset` (`resources/dga_utils.py:700–783`): gdy nie ma zbioru zbiorczego, tworzy go (`:645–693`) w instytucji `MAIN_DGA_DATASET_OWNER_ORGANIZATION_PK` (domyślnie 333 – Ministerstwo Cyfryzacji, `settings/base.py:1714`), z tytułem, opisem, e-mailem do przypomnień, częstotliwością „daily”, kategorią „Rząd i sektor publiczny” i tagami z ustawień (`settings/base.py:1715–1750`, `resources/dga_utils.py:607–642`). Tworzy **nowy** zasób (tytuł i opis przejmuje ze starego) i `ResourceFile(is_main=True)`; zapis pliku uruchamia zwykłe zadania walidacji portalu przez sygnał `post_save`.
3. **Kontrola walidacji** – `check_all_resource_validations_status` (`resources/dga_utils.py:535–604`): gdy zadania portalu jeszcze trwają, rzuca `PendingValidationException` i zadanie ponawia się (5 razy co 20 s, `resources/tasks/dga.py:23–31`); błąd pliku lub linku kończy zadanie; pusty plik jest dopuszczony.
4. **Podmiana** – `update_or_create_aggr_dga_info_and_delete_old_main_dga` (`resources/dga_utils.py:786–817`): jedyny wiersz `AggregatedDGAInfo` (`resources/models.py:1630`, `save` blokuje drugi) wskazuje nowy zasób, stary zasób jest usuwany.
5. **Sprzątanie i blokady** – wyniki kroków 1 i 2 są zapamiętane w pamięci podręcznej (`cache_memoize`, klucze stałe, `resources/dga_utils.py:220`, `:696`), więc ponowienie zadania nie tworzy drugiego pliku ani zasobu. `clean_up_after_main_dga_resource_creation` (`:820–869`) po błędzie usuwa utworzony zasób i zbiór, a zawsze kasuje plik tymczasowy i klucze pamięci podręcznej. Nie ma blokady przed dwoma równoległymi uruchomieniami poza tymi kluczami (wniosek).

### 5. Obsługa błędów

Wykaz, którego nie da się odczytać, któremu brakuje kolumn albo który ma puste wartości wymagane, jest **pomijany, a scalanie trwa dalej** (`resources/dga_utils.py:408–433`). Informacja trafia tylko do logów i Sentry – dostawca nie dostaje powiadomienia ani publicznego raportu. Komunikat po polsku dostawca widzi tylko wcześniej: w formularzu panelu albo w raporcie harvestera.

### 6. Odczyt publiczny

- `GET /dga-aggregated` (bez logowania, `login_optional`): identyfikator i slug zbioru oraz zasobu zbiorczego – `resources/views.py:740–772`, `resources/serializers.py:692`, trasa `routes.py:150`, opis w dokumentacji API `core/api/utils/views.py:98`, `:122`.
- Frontend: `frontend/src/app/services/dga.service.ts:44` (adres w `frontend/src/app/services/api/api.config.ts:71`) – strona „Wykaz chronionych danych” w CMS (`cms/models/dga.py:103`) pobiera ten adres i pokazuje zasób zbiorczy w zwykłym widoku tabeli.
- Sam zasób zbiorczy jest zwykłym zasobem: widok, API danych tabelarycznych, pobranie pliku.

### 7. Ustalenie poboczne: znaczniki mapy a ponowna walidacja

`_resolve_tabular_data_schema` (`resources/tasks/process_resource_file_data.py:24`) wylicza schemat od nowa, gdy `missingValues` zapisanego schematu różni się od listy znaków specjalnych zasobu. Schemat wyliczony przez tableschema 1.21.0 (wersja z `Pipfile.lock`) ma `missingValues: [""]`, a zasób bez znaków specjalnych ma pustą listę. Sprawdziliśmy to, uruchamiając tableschema na naszym pliku krajowym. Wniosek, którego nie sprawdzono w działającym portalu: znaczniki mapy ustawione ręcznie w „Mapy i wykresy” mogą znikać przy ponownej walidacji pliku. Dla wykazu AED omijamy to (niżej).

## Odpowiedniki dla AED

| Element DGA | Odpowiednik „wykaz AED” | Użyte bez zmian | Skopiowane / uogólnione |
|---|---|---|---|
| `Resource.contains_protected_data` | `Resource.contains_aed_list` (`resources/models.py:581`, migracja `resources/migrations/0076_resource_contains_aed_list.py`) | – | nowe pole, ta sama konwencja |
| pole formularza TAK/NIE z opisem | `ResourceForm.contains_aed_list` (`resources/forms.py:267`), w obu zestawach pól panelu (`resources/admin.py:409`, `:540`) | widżet `CheckboxSelect` | tekst pomocy |
| `validate_dga_file_columns` (stała lista 5 kolumn) | `validate_aed_list_file` (`aed/aed_utils.py`) → `aed_standard.wykaz.read_wykaz`: kolumny i wartości według `aed_standard/schema.json`, komunikaty po polsku na poziomie wiersza i pola | – | logika w `aed_standard` (czysty Python) |
| tylko instytucje `local`/`state` | wszystkie typy instytucji (firmy też publikują) | – | świadomie pominięte |
| jeden wykaz na instytucję + strony potwierdzenia | wiele wykazów dozwolonych; każdy to osobne źródło w deduplikacji | – | pominięte (decyzja do potwierdzenia) |
| `get_all_dga_resources_sorted_by_organizations` | `get_all_aed_list_resources` | – | bez filtra statusów zadań: odrzucony wykaz jest opisany w raporcie |
| `create_main_dga_df` (sklejenie DataFrame) | `aed_standard.wykaz.merge_wykazy`: walidacja → uzupełnienie pól systemowych → deduplikacja regułami `aed_standard` → profil `publikacja` (bez OSM/ODbL, bez `dostep=prywatny`) | `dedup.deduplicate`, `build.publication_export`, `build.to_csv` | nowy moduł `aed_standard/wykaz.py` |
| `create_main_dga_file` (XLSX) | `create_main_aed_file` (CSV UTF-8, przecinek, kolumny standardu) | `cache_memoize` | skopiowane |
| `create_main_dga_dataset`, `create_main_dga_resource_with_dataset` | `create_main_aed_dataset`, `create_main_aed_resource_with_dataset`; od razu z `tabular_data_schema` ze znacznikami mapy `b`, `l`, `label` | `Resource`, `ResourceFile`, zadania walidacji portalu | skopiowane |
| `check_all_resource_validations_status`, wyjątki Pending/Failed | to samo | **importowane z `dga_utils` bez zmian** | – |
| `AggregatedDGAInfo` | `aed.AggregatedAEDInfo` + pole `report` (JSON) | – | skopiowane, rozszerzone o raport |
| `update_or_create_aggr_dga_info_and_delete_old_main_dga`, `clean_up_after_main_dga_resource_creation` | odpowiedniki `_aed_` | – | skopiowane |
| `create_main_dga_resource_task`, wpis Beat 03:30 | `create_main_aed_resource_task` (`aed/tasks.py`), wpis 03:45 (`celeryapp.py:93`), kolejka `resources` | `extended_shared_task` | skopiowane |
| brak uruchomienia ręcznego | `python manage.py create_main_aed_resource [--dry-run]` | – | nowe |
| `GET /dga-aggregated` | `GET /aed-aggregated` (`aed/views.py`, `routes.py:152`) – dodatkowo publiczny raport: które wykazy przyjęto, które odrzucono i dlaczego | `JsonAPIView`, `BaseHdlr`, `login_optional` | skopiowane |
| odczyt linku CKAN (`request_remote_dga`) | odczyt zasobu-linku | **importowane bez zmian** | – |
| `containsProtectedData` w XSD harvestera i walidacja CKAN | nie zrobione; flagę na zasobie z harvestera może ustawić redaktor w panelu | – | XML: `containsAedList` w XSD 1.14 jest w forku (test parsera i serializera, `mcod/aed/tests/test_harvester.py`); usługa wystawia 1.13; CKAN – do zrobienia |
| `dga_migrate` (oznaczenie istniejących zasobów po nazwie) | nie zrobione; odpowiednikiem jest rejestr źródeł `aed_standard/sources.json` | – | możliwy następny krok |
| strona CMS „Wykaz chronionych danych” + `dga.service.ts` | nie zrobione; wynik widać w zwykłym widoku zbioru i zasobu | – | możliwy następny krok we froncie |
