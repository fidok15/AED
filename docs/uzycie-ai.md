# Zakres wykorzystania sztucznej inteligencji

Regulamin zadania (§2 ust. 7–8) dopuszcza użycie AI pod warunkiem, że rozwiązanie jest efektem analizy i pracy człowieka, i wymaga wskazania zakresu tego użycia. Ten plik prowadzimy na bieżąco; wpis dodaje się po każdej sesji pracy z AI.

## Narzędzie

Claude Code (model Claude firmy Anthropic) w roli asystenta programisty: sesja prowadząca rozdzielała zadania między agenty podrzędne, a członkowie zespołu wydawali polecenia, podejmowali decyzje i odbierali wyniki.

Codex (model innego dostawcy) – niezależny przegląd kodu napisanego z Claude Code. Znaleziska i poprawki: `docs/przeglad-codex.md`.

## Co zrobił człowiek

- Rozmowa z komisją i ustalenie celu rozwiązania (ministerstwo zbiera dane, kanał producenta i sprzedawcy, naklejka QR, potwierdzenia, deduplikacja).
- Decyzje kierunkowe: sposób integracji z portalem, forma prototypu, harmonogram, zakres pól.
- Wybór i pobranie źródeł danych, w tym uzyskanie dostępu do API Warszawy.
- Przygotowanie forka kodu portalu dane.gov.pl w repozytorium.
- Wybór znaku (wariant D „Serce stanów”), nazwy i hasła akcji; warianty znaku i księgę znaku przygotowało AI na polecenie zespołu.
- Odbiór i weryfikacja wyników pracy AI.

## Co powstało z użyciem AI

| Obszar | Zakres użycia AI | Weryfikacja |
|---|---|---|
| Research (`reports/`, `research_notes/`, `docs/research-i-pomysly.md`) | wyszukiwanie i streszczanie źródeł, synteza raportu | twierdzenia niepotwierdzone w źródle pierwotnym są oznaczone w tekście; liczby na slajdy sprawdzamy przed użyciem |
| Standard danych (`aed_standard/schema.json`) | propozycja struktury na podstawie wymagań komisji i istniejących zbiorów z dane.gov.pl | zakres pól zatwierdzony przez zespół |
| Walidator, mapper, deduplikacja (`aed_standard/`) | kod wygenerowany przez AI | testy automatyczne na prawdziwych plikach źródłowych; przegląd próbki połączonych par |
| Usługa API (`aed_service/`) | kod wygenerowany przez AI | testy automatyczne całej ścieżki; przejście w przeglądarce |
| Moduł AED we frontendzie (`frontend/src/app/pages/aed/`) | kod wygenerowany przez AI na podstawie wytycznych zespołu co do wyglądu i przebiegu | przejście ścieżki użytkownika w przeglądarce; uwagi zespołu |
| Konfiguracja Dockera | wygenerowana przez AI | uruchomienie i sprawdzenie odpowiedzi usług |
| Wykaz AED w forku portalu (`backend/mcod/aed/`, `aed_standard/wykaz.py`, pole `contains_aed_list`) | analiza mechanizmu wykazu DGA w kodzie portalu i kod wygenerowany przez AI | testy logiki na prawdziwych plikach; 22.11 uruchomiony w lokalnym pełnym stosie forka (testy Django, scalanie przez Celery, zrzuty z przeglądarki); nie na serwerze publicznym |
| Wdrożenie pod domeną (`docker-compose.prod.yml`, `backend/docker-compose.aed-domain.yml`, `backend/aed-domain/`) | konfiguracja wygenerowana przez AI na podstawie kodu portalu | uruchomione lokalnie pod domeną testową `aed.localhost` (`docs/wdrozenie-serwer.md`, rozdz. 11); nieuruchomione na serwerze |
| Przegląd kodu | niezależne przeglądy kodu Codexem (kilka rund, `docs/przeglad-codex.md`) i ocena całości 22.11 (`docs/ewaluacja-codex/`) | poprawki z testami; decyzja o każdej poprawce w sesji prowadzącej |
| Materiały kampanii (`kampania/`) | propozycje nazw i haseł, brief, szablon księgi znaku, pakiet zachęt | wybór i ostateczna treść należą do zespołu; warianty znaku i księgę znaku przygotowało AI na polecenie zespołu, wariant wybrał zespół (wpisy z 22.11 w dzienniku) |
| Dokumentacja (`README.md`, `CLAUDE.md`, `docs/`) | redakcja na podstawie ustaleń zespołu | przegląd zespołu |

## Czego AI nie robiło

- Nie wybierało znaku: warianty logo powstały z pomocą AI, a wybór wariantu D „Serce stanów” należy do zespołu (fidok15, 22.11).
- Nie publikowało niczego na dane.gov.pl ani w innych serwisach zewnętrznych.
- Nie podejmowało decyzji o kierunku rozwiązania.

## Dziennik sesji

| Data | Co zrobiono z AI | Kto odebrał |
|---|---|---|
| 2026-11-21 | research; plan; standard danych; walidator, mapper i deduplikacja; usługa API; pierwsza wersja modułu AED we frontendzie; Docker; szkice materiałów kampanii i prezentacji | fidok15 |
| 2026-11-21 | przegląd stanu aplikacji i jej uruchomienie; zamykanie połączeń SQLite w usłudze i testach (koniec `ResourceWarning`) | Jakub Zawadzki |
| 2026-11-21 | zasilanie XML dla harvestera dane.gov.pl w usłudze (`/eksport/dane-gov-pl.xml` i `.md5`) z testem walidacji XSD 1.13; analiza kodu harvestera i walidacji CSV portalu, w tym odtworzenie wykrywania typów na wersjach bibliotek portalu; instrukcja `docs/panel-portalu-krok-po-kroku.md` (wynik w panelu portalu jeszcze niesprawdzony przez człowieka) | fidok15 |
| 2026-11-21 | prezentacja w Figma Slides (15 slajdów, notatki mówcy) na podstawie `docs/` i zrzutów z `frontend/aed-zrzuty/`; trzy GIF-y ścieżek firmy, zarządcy i ministerstwa nagrane skryptem Playwright z lokalnego prototypu (`frontend/aed-zrzuty/gif/`) | fidok15 (do przeglądu) |
| 2026-11-22 | analiza mechanizmu wykazu DGA w kodzie portalu i odtworzenie go dla AED (`backend/mcod/aed/`, `aed_standard/wykaz.py`, pole `contains_aed_list`); testy czystej logiki uruchomione na prawdziwych plikach; kodu Django nie uruchomiono – do weryfikacji przez człowieka w działającym portalu; konfiguracja wdrożenia pod domeną (`docker-compose.prod.yml`) | fidok15 |
| 2026-11-22 (noc) | niezależny przegląd PR #16 Codexem: 5 znalezisk (2 × P1, 3 × P2), wszystkie poprawione przez AI w commicie `d4eec3b` | PR #16 zmergował Adam Korwin; poprawek w działającym portalu nikt jeszcze nie sprawdził |
| 2026-11-22 (noc) | sesja prowadząca z agentami podrzędnymi: poprawki po przeglądzie rejestru źródeł, kolejka duplikatów przy imporcie, przejęcie punktu znanego tylko z OpenStreetMap w usłudze (`838968e`); równolegle agent frontendowy (zmiany w `frontend/src/app/pages/aed/`) i agent uruchamiający portal | oczekuje na odbiór (gałąź `feat/nocna-runda`, bez PR) |
| 2026-11-22 (noc) | agent dokumentacji: aktualizacja `CLAUDE.md` i `README.md` o wskazówkę prowadzącego (wykazy), konfiguracja pełnego forka pod domeną (`backend/docker-compose.aed-domain.yml`, `backend/aed-domain/`, `docs/wdrozenie-serwer.md`; sprawdzona tylko składnia), opis projektu, nowy konspekt prezentacji, uzupełnienie instrukcji dla jury, raport z przeglądów Codexa | oczekuje na odbiór; kierunek (wykaz w portalu, serwer pod domeną) wskazał zespół |
| 2026-11-22 (noc, 01:45–03:00) | agenty podrzędne pod sesją prowadzącą: uruchomienie wykazu AED w stosie portalu z testami w kontenerze i zrzutami z przeglądarki; konwerter do standardu (mapowanie kolumn, normalizacja, XLSX); filtr „dostępny teraz" (parser godzin w Pythonie zgodny z wersją TypeScript); przeprojektowanie mapy rejestru i lista najbliższych urządzeń; poprawki UI; próbne wdrożenie pod domeną lokalnie. Codex: trzy kolejne przeglądy kodu (7 + 4 znaleziska, wszystkie poprawione) i dwie oceny UI na zrzutach ekranu. Uwagę o nieczytelnej mapie i decyzję o kierunku zgłosił człowiek. | PR #17–#23 zmergowane; wyników nie odebrał jeszcze człowiek w przeglądarce ani na telefonie |
| 2026-11-22 (ok. 03:20) | ewaluacja Codexem, cztery oceny: juror (kryteria konkursu, deklaracje bez dowodów, niespójności dokumentów), audyt usługi AED, przegląd zmian w forku portalu, UI – wyniki w `docs/ewaluacja-codex/`. Na tej podstawie agenty poprawiają kod usługi, frontend i dokumenty (m.in. stan wdrożenia, harvester, etykiety liczb, render karty „Słownik pól” do prezentacji) | poprawki w toku; odbiór przez człowieka – do zrobienia |
| 2026-11-22 (noc, 03:40–04:45) | poprawki po czterech ocenach Codexa (audyt usługi: 15 znalezisk; przegląd zmian w forku: 15; ocena jurora: dokumenty; UI: runda 2), siódmy przegląd kodu Codexem z poprawkami, skan bezpieczeństwa z próbami na osobnej instancji (jedno znalezisko: wgrany plik HTML uruchamiany w domenie – naprawione); po uwagach człowieka do ekranu rejestru: mapa na górze, dodatkowe filtry, etykieta „Zweryfikowany"; przegląd formatów polskich zbiorów AED w sieci i rozbudowa konwertera o te formaty. Decyzje człowieka: hasła demo jawne, konto demo dla jury, numer seryjny ukryty, zasilanie XML 1.13. | PR #27–#31; człowiek obejrzał ekran rejestru i zgłosił uwagi; pozostałe ekrany czekają na wspólne przejście |
| 2026-11-22 (ok. 05:45) | wideo promocyjne (`video/`, Remotion): scenariusz, teksty plansz i animacje wygenerowane przez AI ze zrzutów `docs/zrzuty/`; liczby wczytywane z `datasets/out/raport.json`; bez dźwięku, bez logo (tytuł roboczy) | AI sprawdziło klatki kontrolne każdej sceny; całego filmu nie obejrzał jeszcze człowiek |
| 2026-11-22 | szkice koncepcji nazwy i logo w Figma (plik „AED – koncepcje logo”): 3 kierunki (Gotowe!, Opiekun AED, AED na widoku) z ikonami aplikacji, lockupami, naklejką QR i odznaką, potem 2 warianty bez zieleni z komórkami w kolorach stanów rekordu (D serce stanów, E puls stanów); przegląd nazw aplikacji AED w App Store / Google Play przez wyszukiwarkę. Szkic do dyskusji, ostateczny znak rysuje zespół | fidok15 (do decyzji) |
| 2026-11-22 | prezentacja HTML z animacjami (`prezentacja-html/`, 17 slajdów): układ, teksty na podstawie `docs/prezentacja-konspekt.md` i `raport.json`, ilustracje postaci i scenerii rysowane kodem SVG, nagrania i zrzuty z prototypu; skrypt `build.py` składa jeden samodzielny plik `prezentacja.html` | fidok15 (do przeglądu) |
| 2026-11-22 | po wyborze wariantu D przez zespół: eksport znaku z Figmy (SVG, z tego PNG, JPG i wektorowy PDF w `kampania/logo/`, skrypt `kampania/build_logo.py`) oraz księga znaku `kampania/opiekun-aed-ksiega-znaku.pdf` (12 stron: koncepcja, konstrukcja, pole ochronne, minimalna wielkość, kolorystyka, warianty, typografia, niedozwolone użycia, zastosowania); wartości minimalnej wielkości i CMYK do potwierdzenia wydrukiem próbnym; hasło wzięte z kandydatów w `kampania/nazwa-i-haslo.md` | fidok15 (do przeglądu) |
| 2026-11-22 | poprawka kontrastu znaku na białym tle: komórka „niepotwierdzony” w wersji kolorowej zmieniona z `#A9C8FF` (1,69 : 1) na `#5F8DF5` (3,17 : 1) w SVG (`kampania/logo/svg/`, kopia we frontendzie, logo naklejki, stała `SKY` w `prezentacja-html/index.html`), eksporty PNG/JPG/PDF, księga znaku i `prezentacja.html` przebudowane skryptami; plik Figma nie został zaktualizowany | AI obejrzało eksporty PNG i JPG; fidok15 (do przeglądu) |
| 2026-11-22 (ok. 09:00) | nowa wersja wideo (`video/src/Pitch.tsx`, 85 s, bez dźwięku): paleta i kroje z księgi znaku, logo z plików `kampania/logo/svg/`, scenariusz nastawiony na wspólne budowanie bazy; przykład Wielkiej Brytanii (The Circuit: 82 108 AED, 55 235 opiekunów, 54% wcześniej nieznanych pogotowiu, 14 służb) – liczby AI odczytało z artykułu O’Sullivan i in., „Resuscitation Plus” 2024 (PMC11382004); pozostałe liczby z `datasets/out/raport.json` | AI obejrzało 10 z 12 klatek kontrolnych (po jednej na scenę); całego filmu nie obejrzał jeszcze człowiek; liczby brytyjskie do potwierdzenia przez człowieka w źródle |
| 2026-11-22 (ok. 09:15) | końcowy przegląd kodu przez Codexa (12 uwag); AI poprawiło trzy: błędy wykazu przed ostrzeżeniami w obciętym raporcie, rozpoznanie pisowni „OSM” i „odbl” w wierszu wykazu, klucz `zweryfikowany` w wideo; pozostałe uwagi przekazane zespołowi; sprawdzenie serwera publicznego (adresy, `/aed-aggregated`, logowanie konta jury) i wpisanie adresów do instrukcji dla jury | testy automatyczne (162); człowiek nie przeglądał |
| 2026-11-22 (ok. 08:30–09:00) | publiczne wdrożenie pełnego forka na Proxmoxie zespołu: nowy LXC, Cloudflare Tunnel i rekordy DNS `aed*.heckyeah.pl` (przez API Cloudflare), nakładka `backend/docker-compose.aed-tunnel.yml`, nazwy hostów jednopoziomowe w nakładce domenowej, automat wdrożeń `deploy/pve/` (timer co 2 min), `docs/wdrozenie-pve.md`; sprawdzone curl przez tunel (strony, `/aed-aggregated` 781 rekordów, 403 dla `/media/reports`, HTTPS w przekierowaniach panelu) i jedno wdrożenie automatem | Adimac93 zlecił i wybrał wariant, nazwy i wyzwalacz; strony w przeglądarce – do obejrzenia przez człowieka |
| 2026-11-22 (ok. 09:30) | strona „Wykaz AED” w forku frontendu wzorem wykazu DGA (`/pl/wykaz-aed/table`): resolver z `/aed-aggregated`, komponenty strony i tabeli DGA użyte bez zmian, pozycja w menu i w mapie strony, tabela widoczna także bez strony CMS; testy jednostkowe frontendu; sprawdzenie w przeglądarce na lokalnym mocku `/aed-aggregated` i CMS z prawdziwym zasobem Legionowa z dane.gov.pl. Strony CMS w backendzie nie dodano (brak czasu na budowę stosu portalu) | Jakub Zawadzki wybrał kierunek (wzorzec DGA, mock zamiast budowy stosu); na prawdziwym forku nikt jeszcze nie sprawdził |
