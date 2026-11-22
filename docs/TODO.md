# Do zrobienia

Stan na 22.11.2026, 05:35, `main` = PR #34. Testy: usługa 143 przechodzą (Python 3.13; jeden test sieciowy pomijany bez sieci), frontend AED 60, linter i build OK; portal w kontenerze: 28 testów AED, 4 widoków, regresja DGA/panelu/Celery 137 – wszystkie po ostatniej zmianie. Zbiór krajowy z mappera: 18 814 rekordów, eksport 781, 195 par do przeglądu; wykaz krajowy w lokalnym portalu: 782 (781 + urządzenie demonstracyjne `AED-PRIFSO7R4SNZ`).

Co działa i ma dowód:

- prototyp lekki (`docker compose up --build`, `http://localhost:8080/pl/aed`), ścieżki A–D i K przeklikane od zera na Dockerze;
- pełny fork portalu lokalnie: migracje, testy Django `mcod/aed` (8) i regresji DGA, panelu i Celery (148), scalanie przez Celery uruchomione ręcznie, zasób zbiorczy z tabelą i mapą, `/aed-aggregated`, e-mail do dostawcy o odrzuconym wykazie w MailHog (`docs/wykaz-aed-w-portalu.md`);
- nakładka domenowa uruchomiona lokalnie pod `aed.localhost` (`docs/wdrozenie-serwer.md`, rozdz. 11);
- XSD harvestera 1.14 z `containsAedList` w forku (test parsera i serializera); usługa wystawia 1.13;
- prezentacja `prezentacja-html/prezentacja.html` (17 slajdów, wersja zespołu); stara, wygenerowana prezentacja PPTX została usunięta z repozytorium;
- liczby zbioru: stan z `datasets/out/raport.json` (rejestr z mappera, eksport, pary do przeglądu) – nie przepisujemy ich tutaj.

Nakład: S – do godziny, M – kilka godzin, L – dzień albo więcej.

## Dla agenta

Zrobione po uwagach właściciela z 22.11 ok. 04:20 (PR #30–#31):

- [x] Rejestr: mapa jako pierwszy element strony, przycisk „Moja lokalizacja" przy +/− na mapie, zwijane „Dodatkowe filtry" (dostęp, 24/7, tylko z godzinami, w budynku / na zewnątrz, producent, model, miejscowość, źródło), `GET /api/aed/filtry`.
- [x] Etykieta statusu „Aktywny" → „Zweryfikowany" w interfejsie, schemacie, wzorcu i komunikatach; wartość techniczna `aktywny` w danych i API bez zmian (decyzja do potwierdzenia niżej).
- [x] Przegląd formatów, w jakich polskie instytucje publikują AED (`docs/formaty-zbiorow-aed.md`, z listą „Skąd wziąć dane do testu"), próbki w `datasets/probki-formatow/`.
- [x] Konwerter czyta format po treści pliku: CSV, XLSX, ODS, JSON ogólny, GeoJSON, ArcGIS JSON, KML/KMZ, GPX, GML/WFS, tabela HTML, tabela DOCX; położenie w stopniach-minutach-sekundach, w jednej kolumnie, WKT oraz w układach PUWG 1992, PUWG 2000 i Web Mercator; wiersze z samym adresem zostają w pliku do uzupełnienia. PDF, XLS i DOC są odrzucane z instrukcją.
- [x] Wzorzec XLSX z arkuszem „Dane otwarte (publikacja)"; tabele błędów i duplikatów na wąskich ekranach.
- [x] Skan bezpieczeństwa całego systemu (`docs/ewaluacja-codex/skan-bezpieczenstwa.md`).

Nieobejrzane na ekranie po zmianach (tylko testy komponentów): panel firmy i panel ministerstwa na wąskim ekranie, tabela mapowania konwertera przy 320 px.

Zrobione 22.11 ok. 05:30 (PR #32–#34): geokodowanie adresów i kody TERYT przez państwową usługę GUGiK (opcja na żądanie); stały adres wykazu krajowego (`/aed-aggregated/resource`, `/aed-aggregated/file`); wykaz o identycznej treści w tej samej instytucji oznaczany jako „powtórzony"; harmonogram scalania potwierdzony uruchomieniem przez Celery Beat (pora w UTC: 03:45 UTC = 04:45 czasu polskiego zimą); jeden rekord od naklejki QR do wykazu krajowego w portalu; mapa w buildzie produkcyjnym frontendu; przegląd panelu administratora w przeglądarce na kontach jury i admina (poprawione: TAK i NIE dawały się zaznaczyć naraz; odnośnik do konwertera przy odrzuceniu); ósmy przegląd kodu Codexem (7 znalezisk, poprawione); ocena struktury danych (`docs/ewaluacja-codex/struktura-danych.md`).

Otwarte po przeglądzie formatów:

- [x] Geokodowanie wierszy z samym adresem danymi państwowymi (PRG/TERYT) – opisane w `docs/formaty-zbiorow-aed.md`, niezaimplementowane; dziś takie wiersze (np. lista Krakowa) nie wchodzą do wykazu.
- [ ] Portale otwartych danych Gdańska, Wrocławia, Poznania i Lublina nie odpowiedziały na zapytania – sprawdzić ręcznie, czy publikują AED.
- [ ] Zbiory Koszalina i Krakowa nie mają podanej licencji – przed dodaniem do źródeł potrzebna zgoda albo licencja.


- [x] **Widok publikacyjny w XLSX** (S): w `wzorzec-aed.xlsx` arkusz z polami dopuszczonymi do udostępnienia (bez kontaktu dysponenta i numeru seryjnego) i przykładowym wierszem; generator `scripts/build_template.py`.
- [x] **Jeden identyfikator od QR do portalu** (M): zgłoszenie → naklejka → potwierdzenie → eksport usługi → wykaz ministerstwa w forku → scalanie → ten sam `id_aed` w zasobie zbiorczym; zapis kroków i zrzut.
- [x] **Stały adres zasobu zbiorczego** (M): ponowne scalanie dziś tworzy nowy zasób, stary zwraca 404; zachować identyfikator zasobu albo stały adres do bieżącego wyniku; test po dwóch scaleniach.
- [x] **Ponowne wgranie identycznego wykazu zawyża wynik** (M): ten sam plik Legionowa jako drugi zasób dał 805 zamiast 781; wykrywać duplikat wykazu tego samego dostawcy po skrócie znormalizowanej treści (urządzenia z jednego budynku zostają osobno).
- [x] **Test Celery Beat** (S): w środowisku testowym ustawić porę scalania na najbliższą minutę, zachować log Beat, wykonanie przez worker i odczyt zaktualizowanego zasobu.
- [ ] **Pliki robocze zasobów serwowane z dysku** (M): Caddy podaje `/media/resources/` bez sprawdzenia stanu publikacji; przywrócić kontrolę (`X-Accel-Redirect` jak w nginx portalu) i sprawdzić anonimowy odczyt zasobu opublikowanego i roboczego. Do tego czasu nie wgrywać na serwer niczego, co nie ma być jawne.
- [x] Uwagi UI A6–A8 (S–M): tabele błędów, duplikatów i mapowania na wąskich ekranach.
- [x] Mapa w buildzie produkcyjnym frontendu (`build:aed`) w pełnym forku – sprawdzono tylko `ng serve --no-prebundle` (S).

## Dla człowieka

- [ ] **Adres publiczny dla jury** (L): serwer (amd64, min. 8 GB RAM), domena z rekordami `api.`, `admin.`, `cms.`, kroki `docs/wdrozenie-serwer.md` (rozdz. 5–6), dane demo zakładane na serwerze (`seed_aed_demo`), konto `jury@aed.example`; potem sprawdzić z zewnętrznej sieci zbiór, tabelę, mapę, CSV i `/aed-aggregated`, wpisać adres w sekcji 0 `docs/instrukcja-dla-jury.md`.
- [ ] **Przypomnienie dostarczone do skrzynki zarządcy** (M): dziś wiadomości zostają w skrzynce nadawczej usługi; pokazać wysyłkę do kontrolowanej skrzynki i ponowne potwierdzenie z linku z wiadomości.
- [ ] **Testy na telefonie** (M): QR z wydrukowanej naklejki (ok. 4 cm), geolokalizacja i odmowa geolokalizacji, rejestr przy 320 px; VoiceOver na ścieżce dysponenta i panelu firmy; prawdziwy zoom 200%.
- [ ] **Pilotaż spoza Warszawy** (L): wykaz potwierdzony przez dysponenta spoza Warszawy (dziś większość eksportu to API Warszawy, a cały rejestr z mappera jest `niepotwierdzony`); na slajdzie zasięg, data i udział rekordów zweryfikowanych.
- [ ] Porównać liczby i nazwy w `prezentacja-html/index.html` ze stanem po wejściu standardu 0.3.0 (średnie kompletności z `datasets/out/raport.json`, wartość statusu `zweryfikowany`, nowe ekrany rejestru) i przebudować: `python3 prezentacja-html/build.py`.
- [ ] Potwierdzić u organizatora godzinę i sposób oddania.

## Kampania – 25% oceny (zespół)

- [x] Nazwa i hasło akcji: **Opiekun AED** – „Dbasz o AED? Pokaż to w danych.” (sprawdzenie domeny i rejestrów znaków nadal otwarte, `kampania/nazwa-i-haslo.md`).
- [x] Logo w `kampania/logo/` (`svg`, `png`, `jpg`, `pdf`; układ pełny i sygnet; kolor, mono, negatyw).
- [ ] Zapisać znak jako `aed_service/naklejka-logo.svg` – usługa wstawi go na naklejkę QR.
- [x] Księga znaku: `kampania/opiekun-aed-ksiega-znaku.pdf`.
- [ ] Wstawić nazwę akcji i znak do interfejsu modułu AED oraz do tytułu w `docs/opis-projektu.md`.

## Decyzje

- [ ] **Struktura danych** (ocena własna i Codexa, zgodne): osobne pole stanu urządzenia (dziś `status` miesza weryfikację danych z gotowością urządzenia), piętro, sposób ustalenia położenia, terminy baterii i elektrod także jako `RRRR-MM`, `kompletnosc` liczona tylko z pól publikowanych, `kod_terc` 7 cyfr (usługa GUGiK zwraca 6), lista dozwolonych pól zamiast zakazanych. To zmiana standardu – czeka na zgodę. Na slajd „co dalej": osobne identyfikatory egzemplarza, punktu i instalacji; historia zmian w rejestrze.
- [ ] Ten sam wykaz opublikowany przez DWIE różne instytucje nadal liczy się podwójnie (powtórzenie wykrywane jest w obrębie jednej instytucji).
- [ ] Pliki robocze zasobów: host `api.` podaje cały katalog plików także w oryginalnym portalu; pełne zamknięcie wymaga odejścia od konfiguracji ministerstwa.
- [ ] Geokodowanie: przyjmować dopasowanie przy innym kodzie pocztowym (dziś tak, z adnotacją)? Podstawa prawna użycia danych adresowych PRG – do potwierdzenia przez prawnika.

- [ ] „Zweryfikowany" zmieniono jako słowo dla ludzi; w danych (kolumna `status` w CSV, API, baza, kod portalu) zostaje wartość `aktywny`. Czy zmienić także wartość w danych? To migracja danych i kontraktu z portalem.
- [ ] Bez wybranego statusu lista rejestru pokazuje także rekordy `wycofany`, a mapa nie – ujednolicić?

Podjęte 22.11 (wpisane w `CLAUDE.md`): hasła kont demo jawne na czas pokazu; konto `jury@aed.example` (redaktor instytucji demo) w panelu portalu; numer seryjny ukryty w danych publicznych; zasilanie XML z usługi w wersji 1.13; kto odpowiada za wykaz i ile wykazów na instytucję – odłożone do przepisów.

Otwarte:

- [ ] Czy wymagać `id_aed` albo `zrodlo_id` w wykazie (bez nich identyfikator zależy od kolejności wierszy)?
- [ ] Mapper ignoruje `id_aed` z plików źródłowych, a wykaz w portalu zachowuje identyfikator dostawcy – czy ta różnica ma zostać?
- [ ] Kto wystawia linki przejęcia punktu: dziś tylko ministerstwo; czy także firmy dla własnych urządzeń?
- [ ] Zgłoszenie „problem” dla punktu z OSM nie uruchamia przejęcia (rekord zostaje ODbL, poza eksportem) – czy ma?
- [ ] Zaproszenie z podanym e-mailem nie wpisuje go do pola „E-mail dysponenta” na ekranie QR – czy ma wpisywać?
- [ ] Harmonogram Celery na serwerze: scalanie samo o 03:45 (`AED_CELERY_OPTS`) czy ręcznie na pokazie?

Odłożone pomysły: kreator źródła w panelu ministerstwa; uzupełnianie `kod_terc` i `kod_simc` ze współrzędnych.
