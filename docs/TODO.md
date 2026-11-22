# Do zrobienia

Stan na 22.11.2026, 03:15, `main` = PR #25. Testy: 102 przechodzą (usługa, standard, wykaz, konwerter, godziny); frontend AED: 51 testów, linter i build OK; portal w kontenerze: 8 testów AED + 148 testów regresji. Zbiór krajowy: 18 814 rekordów, eksport 781, 195 par do przeglądu.

Plan i zasady: `CLAUDE.md` w katalogu głównym. Kontrakt API: `docs/api-aed.md`.

## 0. Noc 21/22.11 – co doszło i co z tego wynika

Zrobione na `feat/nocna-runda`: poprawki w `aed_standard` po przeglądzie kodu zespołu, przejęcie punktu z OSM (usługa + ekran), konwerter dowolnego pliku do standardu (`/pl/aed/konwerter`), dostosowanie frontendu do kontraktu, przejście ścieżek jury w przeglądarce z poprawkami, axe (0 naruszeń w module AED), plik prezentacji (`docs/prezentacja/`), opis projektu, wdrożenie pełnego forka pod domenę (`docs/wdrozenie-serwer.md`), dwa przeglądy Codexa z poprawkami (`docs/przeglad-codex.md`).

Doszło po 01:45 (PR #17–#23): wykaz AED uruchomiony w stosie portalu (migracje, testy, scalanie przez Celery, tabela i mapa we frontendzie forka – zrzuty `docs/zrzuty/portal-*.png`); konwerter z normalizacją wartości i XLSX; filtr „dostępny teraz" na liście; nowa mapa rejestru i „najbliższe urządzenia" z odległością i linkiem „Wyznacz trasę"; poprawki UI po ocenie Codexa (`docs/przeglad-ui-codex.md`); lekki prototyp zbudowany od zera i ścieżki jury przeklikane na Dockerze; próbne wdrożenie pod domeną lokalnie (`aed.localhost`) z trzema poprawkami; pięć przeglądów kodu Codexem, wszystkie znaleziska poprawione.

Stan lokalny na tej maszynie: prototyp `http://localhost:8080/pl/aed` (obrazy z kodu z 03:10); skrzynka testowa portalu `http://localhost:8025`; portal `http://localhost:8001` (panel, `admin@mcod.local`) i `http://localhost:8000/aed-aggregated`.

Po 03:00 (PR #24–#25): e-mail do dostawcy o odrzuconym albo częściowo przyjętym wykazie (z ponawianiem po błędzie wysyłki), schemat harvestera 1.14 z `containsAedList`, szósty przegląd Codexa z poprawkami. Prototyp w Dockerze przebudowany z aktualnego kodu. W portalu niesprawdzone w działającym stosie: wiadomość „przyjęty w całości" i pełny import harvesterem.

Niesprawdzone, wymaga człowieka albo serwera:

- [ ] Wdrożenie na serwerze: budowa obrazu `mcod-app:local`, `init_mcod_db` na nakładce domenowej, Let's Encrypt. Kroki: `docs/wdrozenie-serwer.md` (rozdz. 5 i 11). Nie przenosić bazy z laptopa – dane demo założyć na serwerze (`seed_aed_demo`).
- [ ] Geolokalizacja „Użyj mojej lokalizacji" na prawdziwym telefonie (testowana na podstawionej pozycji); rejestr przy 320 px po ustaleniu lokalizacji; axe na ekranie QR po zmianie kolejności kroków.
- [ ] Harmonogram scalania 03:45 (Celery beat) – scalanie uruchamiano ręcznie.
- [ ] Zrzut `wzorzec-slownik-pol.png` do prezentacji (karta „Słownik pól" z `wzorzec/wzorzec-aed.xlsx`) – jedyny brakujący.
- [ ] Pozostałe uwagi z przeglądu UI (A6–A8: tabele błędów, duplikatów i mapowania na wąskich ekranach) – niewdrożone.

Do zrobienia przez człowieka:

- [ ] Otworzyć `docs/prezentacja/misja-aed.pptx` w PowerPoincie albo Keynote i obejrzeć wszystkie slajdy (nie była renderowana). Tekst, nazwa akcji, hasło, logo: `docs/prezentacja/slajdy.json`, potem `uv run --with python-pptx python scripts/build_presentation.py`.
- [x] Dodać 9 brakujących zrzutów do `docs/zrzuty/` (8 z portalu `portal-01…08`, 1 z `wzorzec-aed.xlsx`: `wzorzec-slownik-pol.png`) i przebudować prezentację.
- [ ] Serwer: architektura (amd64/ARM), RAM, dysk, wolne porty 80/443; domena i rekordy `api.`, `admin.`, `cms.`; potem kroki z `docs/wdrozenie-serwer.md` (konfiguracja sprawdzona tylko składniowo).
- [ ] Konto dla jury w panelu portalu: redaktor jednej instytucji demo czy sam odczyt?

Interfejs – do poprawy (uwaga fidok15, 22.11 ok. 02:10):

- [x] Mapa rejestru jest nieczytelna, a pinezki brzydkie i nie pomagają w orientacji. Do przeprojektowania: znacznik czytelny z daleka i odróżniający stan (aktywny / niepotwierdzony / nieaktualny) kształtem i kolorem, grupowanie punktów przy oddaleniu, spokojniejszy podkład, legenda tekstem, wyraźne „jesteś tutaj". Pliki: `frontend/src/app/pages/aed/aed-map.component.ts`, `aed.scss`. Mapa ma zostać dodatkiem do dostępnej listy (zasada 7).
- [x] Przegląd UI/UX Codexem – oszczędnie: jedno uruchomienie, tylko na zrzutach `docs/zrzuty/01–09` i `frontend/aed-zrzuty/` (bez przeklikiwania aplikacji i bez czytania całego kodu), z poleceniem „najwyżej 10 znalezisk, od najważniejszego, każde z konkretną poprawką i plikiem", osobno mapa. Poprawki wdrażamy dopiero po wyborze przez człowieka.

Decyzje do podjęcia:

- [ ] Zasilanie XML z usługi zostaje w wersji 1.13. Przejście na 1.14 z `containsAedList` (jedna linia) sprawi, że zasób z usługi oznaczy się w forku sam jako wykaz AED, ale prawdziwy portal dane.gov.pl nie zna 1.14 i taki plik odrzuci.
- [ ] Kto wystawia linki przejęcia punktu: dziś tylko ministerstwo; czy także firmy dla własnych urządzeń?
- [ ] Mapper ignoruje `id_aed` z plików źródłowych, a wykaz w portalu zachowuje identyfikator dostawcy – czy ta różnica ma zostać?
- [ ] Zgłoszenie „problem" dla punktu z OSM nie uruchamia przejęcia (rekord zostaje ODbL, poza eksportem).
- [ ] Zaproszenie z podanym e-mailem nie wpisuje go do pola „E-mail dysponenta" na ekranie QR – czy ma wpisywać?
- [ ] Pliki zasobów w wersji roboczej są na serwerze demo publiczne (`/media/resources/`); nie wgrywać tam niczego, co nie ma być jawne.

## 1. Frontend – wstrzymane do sygnału

Agent frontendowy został przerwany limitem przed raportem; jego praca jest w commicie `6b7dcda` (`fix: frontend`), nieodebrana.

- [x] Sprawdzić znalezisko 12 z przeglądu Codexa: wyczyszczenie pola opcjonalnego na ekranie QR ma usuwać starą wartość (dziś niepotwierdzone).
- [x] Uruchomić testy i linter frontendu po commicie `6b7dcda` (`npm test`, `npm run lint`, `npm run build:aed`).
- [x] Przejść w przeglądarce trzy poprawki z przeglądu: skrzynka ministerstwa z wiadomością bez linku, ekran po zgłoszeniu problemu, krok „bateria i elektrody” – na usłudze z poprawkami z PR #14.
- [x] Dostosować frontend do zmian kontraktu z PR #14: licznik `wycofano` w wynikach mappera i historii zadań, błąd 422 także przy `stan = problem`, kilka ważnych linków dysponenta.
- [x] Pokazać w panelu ministerstwa źródła pominięte i błędy źródeł (dane dodane przez Jakuba w historii zadań i `raport.json`).
- [x] Filtr „dostępny teraz” na liście rejestru (dziś tylko na mapie) – lista jest stronicowana po stronie serwera, więc wymaga parametru w `GET /urzadzenia` i parsera godzin w Pythonie (dziś jest tylko w TypeScripcie).
- [x] Nowe zrzuty do prezentacji po zakończeniu poprawek (dopiero wtedy).

## 2. Docker i uruchomienie

- [x] Przebudować obrazy z aktualnego `main` (`docker compose up --build`) – działające kontenery mają obrazy sprzed poprawek po przeglądzie i sprzed zmian zespołu.
- [x] Sprawdzić, czy `backend/docker-compose.aed-ports.yml` i `frontend/proxy.aed-local.conf.json` (Hubert) nie kolidują z głównym `docker-compose.yml` (porty 8080, 8085).
- [x] Po przebudowie przejść trzy ścieżki z `docs/instrukcja-dla-jury.md` od zera na świeżym wolumenie.
- [ ] Decyzja: czy wystawić prototyp pod publicznym adresem dla jury (dziś tylko lokalnie).

## 3. Usługa i standard danych

- [x] Druga runda przeglądu Codexa po poprawkach (pierwsza: FAIL, 1 krytyczne + 11 poważnych; 9 naprawionych w PR #14, 3 frontendowe do potwierdzenia).
- [x] Przejrzeć zmiany zespołu w `aed_standard` (rejestr źródeł `sources.json`, `registry.py`, zmiany w `dedup.py`) pod kątem zgodności z poprawkami z PR #14 – testy przechodzą, przegląd kodu nie był robiony.
- [x] Zgodność `aed_service/app.py` z Pythonem 3.8 (operator `|` na słownikach, `traceback.print_exception` z jednym argumentem) – potrzebne tylko przy przenoszeniu do backendu portalu.
- [x] Usługa korzysta z funkcji `aed_standard` spoza publicznego API (`dedup.CANDIDATE_M`, `similarity`, `haversine_m`) – przepiąć na `find_candidates`.
- [x] Nowy rekord z importu obok już potwierdzonego urządzenia nie trafia do kolejki duplikatów (dopasowanie działa tylko w chwili potwierdzenia).
- [ ] Decyzja: czy numer seryjny jest publikowany w zbiorze otwartym (dziś kolumna w eksporcie jest pusta).

## 4. Portal dane.gov.pl (Jakub, Hubert)

- [x] Uruchomić portal lokalnie i wgrać `datasets/out/aed_dane_gov_pl.csv` jako zasób instytucji „ministerstwo”.
- [x] Ustawić mapę w zakładce „Mapy i wykresy” (kolumny `dlugosc_geograficzna`, `szerokosc_geograficzna`, `nazwa`).
- [x] Zrzuty: widok tabeli, mapa, API zasobu, poziom otwartości → do prezentacji i `docs/instrukcja-dla-jury.md`.
- [ ] Plan B, jeśli portal nie wstanie: `docs/integracja-portal-backend.md` jako plan wdrożenia i wpis w ograniczeniach.

Zrobione 22.11 (PR `feat/zasilanie-xml-i-panel-portalu`), **w portalu jeszcze nieuruchomione**:

- [x] Zasilanie XML dla harvestera: `/api/aed/eksport/dane-gov-pl.xml` i `.md5`, zgodne z XSD 1.13.
- [x] Wykaz AED w forku portalu wzorem wykazu DGA (`backend/mcod/aed/`, `aed_standard/wykaz.py`, pole `contains_aed_list`), publiczny odczyt `GET /aed-aggregated`.
- [x] Przegląd Codexem: 5 znalezisk, wszystkie poprawione (kontakty i numer seryjny wycinane z każdego eksportu, licencja CC BY 4.0 zbioru zbiorczego, unikalność identyfikatorów, weryfikacja certyfikatu przy pobieraniu wykazu, hasło kont demo z `AED_DEMO_PASSWORD`).
- [x] Wdrożenie pod domeną: `docker-compose.prod.yml` + `.env.example` (Caddy, automatyczny HTTPS).

Do zrobienia przez osobę z działającym portalem (`localhost:8001`, `admin@mcod.local`):

- [x] Migracje i przejście `docs/wykaz-aed-w-portalu.md`: oznaczyć zasoby jako wykaz AED, uruchomić `manage.py create_main_aed_resource`, sprawdzić `/aed-aggregated`, tabelę i mapę. Kod Django był tylko kompilowany.
- [x] Przejść `docs/panel-portalu-krok-po-kroku.md` (zasób CSV, typy kolumn, źródło harvestera) i zrobić zrzuty.
- [x] Testy Django `backend/mcod/aed/tests/` – nieuruchomione.

Decyzje do podjęcia:

- [ ] Wykaz AED: kilka wykazów na instytucję i każdy typ instytucji (dziś tak) czy jak DGA – jeden, tylko `local`/`state`?
- [ ] Czy wymagać `id_aed` albo `zrodlo_id` w wykazie (bez nich identyfikator zależy od kolejności wierszy)?
- [ ] Czy dodać `containsAedList` do XSD harvestera (wersja 1.14), żeby wykaz z harvestera oznaczał się sam?
- [ ] Hasło kont demo na serwerze publicznym: ustawić `AED_DEMO_PASSWORD` (jury dostaje hasło osobno) czy zostawić znane hasła demo?
- [ ] Wdrożenie pod domeną sprawdzone tylko jako poprawna konfiguracja compose – uruchomić na serwerze.

Odłożone – pomysły z przeglądu projektu (22.11), na razie nie ruszamy:

- [ ] Kreator źródła w panelu ministerstwa: wgranie pliku, podpowiedź mapowania kolumn po nagłówkach, podgląd, zapis do `aed_standard/sources.json` (dziś nowe źródło wymaga ręcznej edycji JSON).
- [ ] Uzupełnianie `kod_terc` i `kod_simc` ze współrzędnych – puste w trzech z czterech zbiorów miejskich; podnosi kompletność bez udziału właściciela.
- [x] „Przejmij punkt": zarządca potwierdza rekord istniejący tylko w OSM, dane stają się jego i wchodzą do eksportu. Najpierw sprawdzić, ile z tej ścieżki obsługuje już ekran QR.
- [ ] Słabość do pokazania na slajdzie ograniczeń: eksport to 781 rekordów, z czego 708 z Warszawy; wszystkie rekordy rejestru mają status `niepotwierdzony`; średnia kompletność 39,2.

## 5. Kampania – 25% oceny (kolega z zespołu, w toku)

- [ ] Wybrać nazwę i hasło akcji (kandydaci: `kampania/nazwa-i-haslo.md`); sprawdzić domenę i rejestry znaków.
- [ ] Narysować logo; eksport do `.svg`, `.png`, `.jpg`, `.pdf`; warianty kolorowy, monochromatyczny, negatyw (`kampania/brief-logo.md`).
- [ ] Zapisać znak jako `aed_service/naklejka-logo.svg` – usługa wstawi go na naklejkę QR.
- [ ] Księga znaku w PDF na podstawie `kampania/ksiega-znaku-szablon.md`.
- [ ] Wstawić nazwę akcji i znak do interfejsu modułu AED.

## 6. Dokumenty i oddanie

- [x] Zaktualizować `docs/instrukcja-dla-jury.md` o zmiany z wieczora (rejestr źródeł, daty baterii i elektrod, strona startowa `/pl/aed`) i usunąć znaczniki `[do sprawdzenia]` po przejściu w przeglądarce.
- [x] Zaktualizować `docs/prezentacja-konspekt.md` i zrobić plik prezentacji (min. 5 slajdów ze zrzutami, kroki użytkownika, ograniczenia, zakres użycia AI).
- [x] Zapisać raport z przeglądu Codexa z wynikami poprawek w `docs/`.
- [x] Uzupełnić dziennik w `docs/uzycie-ai.md` o wieczorną sesję.
- [x] Zaktualizować `CLAUDE.md` (stan, decyzje, rejestr źródeł jest już dopisany przez zespół).
- [x] Tytuł i szczegółowy opis projektu do formularza zgłoszeniowego.
- [ ] Potwierdzić u organizatora godzinę i sposób oddania.

## 7. Testy ręczne, których nikt nie zrobił

- [ ] Ekran QR na prawdziwym telefonie (geolokalizacja, wybór godzin, wydajność na sieci komórkowej).
- [ ] Czytnik ekranu (VoiceOver) na ścieżce dysponenta i panelu firmy.
- [ ] Powiększenie 200% prawdziwym zoomem przeglądarki.
- [ ] Wydruk arkusza naklejek na drukarce i skan kodu QR z wydruku (ok. 4 cm).
