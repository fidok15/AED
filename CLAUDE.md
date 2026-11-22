# Misja AED – Dane na ratunek (HackNation 2026)

Zadanie Ministerstwa Cyfryzacji: rozwiązanie, które ułatwia zebranie w portalu dane.gov.pl jednego, ogólnopolskiego, otwartego i aktualnego zbioru danych o defibrylatorach AED. Hackathon trwa 24 godziny (21–22 listopada 2026). Zakres: wyłącznie Polska.

Materiały źródłowe:

- `docs/MC DZD - Pełna treść zadania konkursowego-1.pdf`, `docs/MC DZD - Regulamin zadania konkursowego-1.pdf` – zadanie i regulamin,
- `docs/tips.txt` – wskazówki organizatora,
- `docs/research-i-pomysly.md`, `reports/Innowacje w aplikacjach AED.md` – research (wzorce zagraniczne, reguły portalu, pomysły).

## Czego chce komisja (rozmowa z 21.11, ok. 17:00)

Ten rozdział ma pierwszeństwo przed wcześniejszym researchem.

1. **Ministerstwo zbiera dane.** Mamy zaproponować proces, w którym to ministerstwo gromadzi dane o AED i publikuje jeden zbiór. Dostawcą zbioru na dane.gov.pl jest ministerstwo.
2. **Najważniejsza jest ujednolicona, generyczna struktura danych** – jedna dla wszystkich źródeł, zgodna z tym, co już leży na dane.gov.pl.
3. **Dane wprowadza podmiot odpowiedzialny.** Kanał główny: producent lub sprzedawca rejestruje urządzenie przy sprzedaży i raportuje do ministerstwa (plik CSV albo formularz). Firmy mają w portalu własne konta.
4. **Naklejka z kodem QR** trafia razem z urządzeniem do zarządcy. Zarządca uzupełnia i potwierdza lokalizację oraz godziny dostępu. Funkcję QR mamy mocno wyeksponować; w przyszłości samo zeskanowanie ma zgłaszać miejsce i stan urządzenia.
5. **Mechanizm kontaktu z właścicielem**, który okresowo prosi o potwierdzenie danych. Właściciel odpowiada za urządzenie, baterię i elektrody.
6. **Mapper istniejących otwartych źródeł**, uruchamiany cyklicznie, dokłada nowe dane. Dane z formularzy i ze źródeł zewnętrznych są deduplikowane.
7. **Liczy się kompletność danych.**
8. **Zachęty:** dostawcy mają zgłaszać się sami. Trzeba pokazać, co firma kupująca AED i utrzymująca aktualne dane z tego ma (punkt odniesienia: akcja InPostu z AED przy Paczkomatach).
9. **Kampania:** logo, marketing, prezentacja z narracją sprzedażową.

Pola, które komisja wymieniła wprost: identyfikator, producent, model, numer seryjny, data produkcji, data ważności elektrod, data ważności baterii, szerokość i długość geograficzna, godziny dostępu, kto wprowadził urządzenie. Uwaga komisji „10/14 lat żywotności” rozumiemy jako żywotność samego urządzenia (baterie i elektrody są wymienne) – do potwierdzenia.

### Wskazówka prowadzącego (noc 21/22.11) – wykazy w portalu

Ma pierwszeństwo przy wyborze, co pokazujemy jako główną ścieżkę. Streszczenie wypowiedzi:

- dane mają być wystawione jako **zasoby w dane.gov.pl**; struktura jest rozproszona po wielu dostawcach, więc musi powstać **zbiorcza tabela – WYKAZ** (w portalu są wykazy o podobnym rozwiązaniu; odtworzyć ich logikę z kodu);
- postawić środowisko: na localhost ma być strona taka sama jak dane.gov.pl; znaleźć wejście do **panelu administracyjnego**;
- najważniejsze nie jest osobna aplikacja zbierająca dane, tylko **dostosowanie logiki i metod portalu**, żeby wykazy dało się pobierać i scalać w jedną standardową listę;
- jury może nie mieć dostępu do wszystkich domen – cenniejsze jest **rozwiązanie do odczytu**.

Odpowiedź (PR #16): wykaz AED w forku portalu wzorem wykazu DGA – analiza `docs/wykaz-dga-analiza.md`, uruchomienie `docs/wykaz-aed-w-portalu.md`. Kod Django nie był jeszcze uruchomiony w pełnym stosie portalu.

## Proces, który budujemy

Dwa kanały zasilają jeden standard; mapper istniejących źródeł daje stan początkowy.

```
KANAŁ 1 (główny): wykazy w portalu
samorząd / instytucja / firma ──(zasób CSV „Wykaz AED: TAK” w swoim zbiorze)──► walidacja przy zapisie (aed_standard)
                                                                                         │
                                           zadanie dzienne 03:45 lub manage.py create_main_aed_resource
                                                                                         ▼
                                walidacja ─► deduplikacja ─► profil publikacja ─► „Krajowy wykaz AED”
                                                                                 (zasób zbiorczy w zbiorze ministerstwa,
                                                                                  odczyt: GET /aed-aggregated, tabela, mapa, API)
KANAŁ 2: usługa AED (aed_service)                                                        ▲
producent / sprzedawca ──(konto firmy: CSV lub formularz)──┐                             │
zarządca ──(skan QR: lokalizacja, godziny, potwierdzenie)──┼─► rejestr ministerstwa ─────┘ wykaz ministerstwa (CSV/link)
mapper: zbiory z dane.gov.pl, API Warszawy, OSM ───────────┘   │                           + zasilanie XML dla harvestera
                                                               └─► przypomnienia i prośby o potwierdzenie
                                                                   (termin baterii i elektrod, brak weryfikacji)
```

Cykl życia rekordu: `zgloszony` (sprzedawca podał dane urządzenia) → `aktywny` (zarządca potwierdził miejsce i dostęp) → `nieaktualny` (brak potwierdzenia w terminie) → `wycofany`. Rekord z mappera, którego nikt odpowiedzialny nie potwierdził, ma status `niepotwierdzony`.

## Punktacja

| Kryterium | Waga | Co je realizuje |
|---|---|---|
| Zgodność z zasadami dane.gov.pl | 30% | wykaz AED w forku portalu wzorem DGA (flaga zasobu, walidacja w panelu, scalanie, publiczny odczyt); zbiór publikuje ministerstwo mechanizmami portalu (zasób, harvester XML); pełny fork pod domeną dla jury |
| Logotyp i hasło | 25% | nazwa akcji, hasło, logo, księga znaku, materiały dla dostawców |
| Kreatywność i innowacyjność | 15% | kanał sprzedawcy, QR, potwierdzenia, wskaźnik kompletności, zachęty |
| Zgodność z tematem | 15% | scalanie wykazów wielu dostawców, mapper wielu źródeł, deduplikacja, wskazanie zakresu każdego źródła |
| Wzorcowy zakres danych | 10% | `wzorzec-aed.xlsx` wygenerowany ze standardu |
| Prezentacja | 5% | slajdy ze zrzutami, instrukcja dla jury |

## Twarde zasady

1. **Źródłem prawdy o strukturze danych jest `aed_standard/schema.json`.** Formularze, walidator, mapper, szablon XLSX i eksporty wynikają z tego pliku. Nie duplikuj listy pól w kodzie ani w dokumentach. Tak samo źródłem prawdy o źródłach danych (pliki, mapowanie kolumn, priorytet, licencja) jest `aed_standard/sources.json` - instrukcja: `docs/dodawanie-zrodla.md`.
2. **Na dane.gov.pl publikuje dostawca, nie zespół i nie obywatel.** Dostawcą zbioru krajowego jest ministerstwo; firmy raportują do ministerstwa przez konta firmowe. Zgłoszenie obywatela (skan QR bez uprawnień) jest sygnałem dla właściciela, nie edycją danych.
3. **Dane OSM (ODbL) nie mieszają się z danymi otwieranymi przez ministerstwo.** Rekord, który istnieje tylko w OSM, zostaje w rejestrze jako `niepotwierdzony` z licencją ODbL i nie trafia do eksportu na dane.gov.pl. Pól z OSM nie przepisujemy do rekordów z innych źródeł; zapisujemy tylko powiązanie. Po potwierdzeniu przez właściciela dane pochodzą od właściciela. Wymaga opinii prawnika – na slajdzie jako ograniczenie.
4. **Kod portalu (`backend/`, `frontend/`) to fork kodu Ministerstwa.** Zmiany w nim trzymaj małe i wydzielone (osobna aplikacja Django, osobny moduł Angular), żeby dało się je pokazać jako łatkę. Nie kopiuj kodu OpenAEDMap (AGPL). Prawa do rozwiązania przechodzą na Ministra Cyfryzacji.
5. **Tylko formaty odczytywalne maszynowo** dla danych (CSV, XLSX, JSON, GeoJSON, XML). PDF tylko dla logo i księgi znaku.
6. **Żadnych danych osobowych ani kodów do szafek w danych otwartych.** Kontakt wyłącznie instytucjonalny. AED prywatne (w domach) nie są publikowane.
7. **WCAG 2.2 AA i responsywność** od pierwszego ekranu: mapa jest dodatkiem do dostępnej listy, obsługa klawiaturą, stan przekazany tekstem i ikoną, układ działa przy 320 px.
8. **Użycie AI dokumentujemy** w `docs/uzycie-ai.md` po każdej sesji: co wygenerowano, co zweryfikował człowiek. Logo i księga znaku powstają ręcznie.
9. **Nie obiecujemy uratowanych istnień** – mierzymy proces: liczbę dostawców, kompletność, udział rekordów potwierdzonych.
10. **Liczby na slajdy tylko ze źródła pierwotnego** albo z naszych własnych danych (`datasets/out/raport.json`).

## Standard danych

Jeden wiersz to jedno urządzenie. CSV: UTF-8, separator `,`, jeden wiersz nagłówka, kropka dziesiętna, daty `RRRR-MM-DD`, współrzędne WGS84 w osobnych kolumnach liczbowych (warunek mapy na portalu). Nazwy kolumn w `snake_case` bez polskich znaków.

Nazwy kolumn adresu i położenia są zgodne ze zbiorem Legionowa, najczystszym z istniejących na dane.gov.pl (`nazwa`, `cecha_ulicy`, `nazwa_ulicy`, `nr_budynku`, `nr_lokalu`, `kod_pocztowy`, `miejscowosc`, `kod_terc`, `kod_simc`, `szerokosc_geograficzna`, `dlugosc_geograficzna`). Plik Legionowa jest więc poprawnym podzbiorem standardu.

Ta sama struktura obsługuje dwa profile wymagalności:

- **`sprzedaz`** – sprzedawca zna urządzenie i nabywcę, nie zna jeszcze miejsca montażu. Wymagane: producent, model, numer seryjny, data produkcji, daty ważności elektrod i baterii, nabywca.
- **`publikacja`** – rekord w zbiorze otwartym. Wymagane: identyfikator, nazwa miejsca, współrzędne, miejscowość, status, źródło, licencja. Dostęp, godziny dostępu i data weryfikacji są wymagane dopiero dla statusu `aktywny`; ich brak w rekordach z importu obniża kompletność.

Do zbioru na dane.gov.pl trafia tylko rekord spełniający profil `publikacja`. Kompletność rekordu (0–100) liczymy z wag pól zapisanych w schemacie.

Deduplikacja:

- ten sam producent i numer seryjny to to samo urządzenie (pewne);
- bez numeru seryjnego: rekordy z **różnych** źródeł w odległości do 50 m są kandydatami; łączymy automatycznie przy odległości do 15 m albo przy wysokim podobieństwie nazwy i adresu, resztę kierujemy do ręcznego przeglądu;
- dwa rekordy z tego samego źródła nigdy nie są łączone automatycznie (w jednym budynku bywa kilka urządzeń);
- pierwszeństwo źródeł przy łączeniu: sprzedawca lub zarządca → zbiory z dane.gov.pl → API Warszawy → OSM.

## Repozytorium

```
aed_standard/   standard danych: schema.json, rejestr źródeł sources.json, walidator, mapper źródeł, deduplikacja, eksporty
                (czysty Python, bez zależności, zgodny z Pythonem 3.8 – importowalny w backendzie portalu)
aed_service/    samodzielna usługa API (Falcon + SQLite): konta firm, zgłoszenia CSV, QR, potwierdzenia, rejestr
scripts/        download_aed_data.py (pobranie źródeł), build_template.py (szablon XLSX)
wzorzec/        wzorzec-aed.xlsx i przykładowe pliki CSV
datasets/raw/   surowe źródła z manifestem (nie edytować ręcznie)
datasets/out/   zbiór krajowy, lista duplikatów do przeglądu, raport
backend/        fork backendu dane.gov.pl (mcod 2.63.0: Python 3.8, Django 2.2, Falcon, Docker Compose)
  mcod/aed/     wykaz AED wzorem wykazu DGA: walidacja, scalanie, zadanie dzienne, GET /aed-aggregated
  docker-compose.aed-domain.yml, aed-domain/   pełny fork pod domeną z HTTPS (docs/wdrozenie-serwer.md)
frontend/       fork frontendu dane.gov.pl (Angular 18)
docker-compose.yml, docker-compose.prod.yml    lekki prototyp (usługa AED + build frontendu), lokalnie i pod domeną
kampania/       nazwa i hasło, brief logo, szablon księgi znaku, zachęty; docelowo pliki logo
docs/           zadanie, research, api-aed.md (kontrakt API), wykaz-dga-analiza.md, wykaz-aed-w-portalu.md,
                panel-portalu-krok-po-kroku.md, integracja-portal-backend.md, wdrozenie-serwer.md,
                prezentacja-konspekt.md, instrukcja-dla-jury.md, opis-projektu.md, przeglad-codex.md, użycie AI
```

Kontrakt między frontendem a usługą: `docs/api-aed.md`. Ustalenia z kodu portalu i plan wdrożenia w forku: `docs/integracja-portal-backend.md`. Wykaz AED w portalu: `docs/wykaz-dga-analiza.md` (jak działa wykaz DGA i co z niego wzięliśmy), `docs/wykaz-aed-w-portalu.md` (włączenie i pokaz). Logika scalania jest w `aed_standard/wykaz.py`, więc ta sama w portalu i w testach.

Stan źródeł na 21.11: cztery zbiory z dane.gov.pl z plikami (Krosno, Marki, Przemyśl, Legionowo – razem 74 rekordy), API Warszawy (708 urządzeń; zbiór Warszawy na dane.gov.pl to tylko odnośnik do tego API), OpenAEDMap (18 298 obiektów). Po mapowaniu i deduplikacji: rejestr 18 814 rekordów, wszystkie `niepotwierdzony`, średnia kompletność 39,2; eksport publikacyjny 781, z czego 708 z API Warszawy (liczby w `datasets/out/raport.json`). Eksporty nie zawierają numeru seryjnego ani kontaktu dysponenta – jedna reguła dla wszystkich (`HIDDEN_PUBLIC` w `aed_standard/build.py`). Usługa pokazuje publicznie mniej rekordów niż rejestr, bo pomija rekordy z dostępem `prywatny`. Innych maszynowo czytelnych zbiorów miejskich nie znaleziono; Kraków („Impuls Życia”) i Koszalin („Punkty Życia”) publikują tylko listy na stronach WWW.

Fakty o portalu ustalone w kodzie:

- typy instytucji w `backend/mcod/organizations/models.py`: `local`, `state`, `private`, `developer`, `other`;
- role użytkowników: redaktor (`is_staff`), pełnomocnik (`is_agent`), urzędnik (`is_official`);
- frontend nie serwuje API; adres backendu ustawia się w plikach `proxy.*.conf.json`; build `aed` woła `/api`, `/cms`, `/media` względnie (nginx przed frontendem decyduje, czy to portal z forka, czy publiczny dane.gov.pl);
- jedyny mechanizm scalania zasobów wielu dostawców to **wykaz DGA** (`resources/dga_utils.py`, zadanie 03:30, `GET /dga-aggregated`); wykaz AED go odtwarza w `mcod/aed/` (flaga `contains_aed_list`, zadanie 03:45, `GET /aed-aggregated`);
- panel administracyjny: `admin.<host>` (lokalnie `admin.mcod.local` albo `localhost:8001`), konto z danych startowych `admin@mcod.local`.

## Podział zadań

Właściciele wynikają z historii commitów i są propozycją – zmieńcie ją tutaj, jeśli zespół ustali inaczej. Bieżąca lista rzeczy do zrobienia: `docs/TODO.md`.

Stan na 22.11, ok. 01:00:

| Zadanie | Stan |
|---|---|
| A. Standard i deduplikacja | zrobione; rejestr źródeł `sources.json` (Jakub Zawadzki) |
| B. Źródła i mapper cykliczny | rejestr źródeł i pobieranie z niego zrobione; tryb przyrostowy i raport „co przybyło” – do potwierdzenia |
| C. Usługa AED | zrobione, testy przechodzą; poprawki po przeglądach w PR #14 i commicie `838968e` (m.in. przejęcie punktu znanego tylko z OSM) |
| C2. Portal lokalnie | w toku; konfiguracja portów i proxy frontendu (HubertK05), wynik uruchomienia – do potwierdzenia |
| C3. Wykaz AED w portalu i wdrożenie pod domeną | kod w PR #16, nieuruchomiony w portalu; konfiguracja serwera gotowa, nieuruchomiona |
| D. Frontend | wstrzymany do sygnału; zmiany w toku w `frontend/src/app/pages/aed/` |
| E. Kampania i prezentacja | nazwa, logo i księga znaku – w toku u zespołu; konspekt, opis projektu, instrukcja dla jury – szkice gotowe |

### A. Standard danych i deduplikacja – Claude (sesja główna). Blokuje resztę.

1. `aed_standard/schema.json` z polami, typami, słownikami, profilami wymagalności i mapowaniami na źródła.
2. Walidator z komunikatami po polsku na poziomie wiersza i pola.
3. Mapper sześciu źródeł do standardu.
4. Deduplikacja, wskaźnik kompletności, zbiór krajowy w `datasets/out/` (CSV, GeoJSON, raport, lista duplikatów do przeglądu).
5. `wzorzec-aed.xlsx` generowany ze schematu.

Gotowe, gdy: jedna komenda buduje zbiór krajowy z surowych źródeł, a testy przechodzą na prawdziwych plikach.

### B. Źródła i mapper cykliczny – HubertK05

1. Utrzymanie `scripts/download_aed_data.py`; kolejne źródła tylko dla Polski.
2. Tryb przyrostowy: ponowne uruchomienie wykrywa rekordy nowe i zmienione względem poprzedniego zrzutu.
3. Harmonogram (zadanie cykliczne w backendzie portalu albo cron) i raport „co przybyło”.

Gotowe, gdy: drugie uruchomienie na zmienionym źródle dokłada tylko różnice.

### C. Usługa AED (`aed_service/`) – agent Claude

Pełna integracja w kodzie portalu to ok. 20 godzin pracy, a stos portalu jest ciężki (ok. 10 kontenerów, emulacja amd64). Dlatego logikę budujemy najpierw jako samodzielną usługę w tym samym frameworku co API portalu (Falcon), według `docs/api-aed.md`.

1. Konta firm i ministerstwa (dane demonstracyjne), logowanie.
2. Przyjęcie CSV i pojedynczego urządzenia: walidacja `aed_standard` (profil `sprzedaz`), nadanie `id_aed`, naklejka QR, link aktywacyjny dla zarządcy.
3. Potwierdzenie przez zarządcę i sygnał od osoby postronnej.
4. Rejestr krajowy zasilony zbiorem z mappera, statystyki, mapa sprzedawców, eksport publikacyjny.
5. Skrzynka nadawcza, przypomnienia i ręczne uruchomienie zadań cyklicznych.

Gotowe, gdy: ścieżka sprzedawca → naklejka → potwierdzenie → rekord `aktywny` w eksporcie przechodzi w teście automatycznym.

### C2. Fork portalu – backend – Jakub Zawadzki

Kroki i pliki: `docs/integracja-portal-backend.md`.

1. Uruchomić portal lokalnie (Docker Compose). Limit: 3 godziny.
2. Wgrać `datasets/out/aed_dane_gov_pl.csv` jako zasób ministerstwa, ustawić mapę w „Mapy i wykresy”, zrobić zrzuty: widok tabeli, mapa, API zasobu, poziom otwartości.

Gotowe, gdy: zbiór krajowy widać w lokalnym portalu z mapą. Plan B po przekroczeniu limitu: zrzuty z usługi `aed_service/` i notatka integracyjna jako plan wdrożenia.

### C3. Wykaz AED w portalu i pełny fork pod domeną – sesja prowadząca z agentami, uruchomienie: osoba z działającym portalem

Odpowiedź na wskazówkę prowadzącego. Kroki: `docs/wykaz-aed-w-portalu.md`, `docs/wdrozenie-serwer.md`.

1. Migracje, oznaczenie zasobów jako wykaz AED, `manage.py create_main_aed_resource`, sprawdzenie `/aed-aggregated`, tabeli i mapy; testy Django `backend/mcod/aed/tests/`.
2. Pełny fork na serwerze kolegi pod domeną: `backend/docker-compose.aed-domain.yml` (Caddy, HTTPS, usługa AED w sieci portalu).
3. Dane do pokazu: wykaz przyjęty (Legionowo), odrzucony (Krosno), wykaz ministerstwa jako link do eksportu usługi; zrzuty do prezentacji.

Gotowe, gdy: juror pod adresem publicznym widzi zbiór zbiorczy w portalu (tabela, mapa, API) i raport wykazów bez logowania.

### D. Frontend – fidok15 z agentem

1. Uruchomić `frontend/` lokalnie i wydzielić moduł AED.
2. Panel firmy: wgranie CSV z raportem walidacji oraz formularz pojedynczego urządzenia generowany ze schematu.
3. Strona QR dla zarządcy: uzupełnienie lokalizacji (geolokalizacja telefonu), godzin dostępu, potwierdzenie stanu.
4. Widok rejestru: lista i mapa, filtr statusu, wskaźnik kompletności, mapa sprzedawców.
5. Zachęty: odznaka dla firmy z aktualnymi danymi, ranking kompletności.

Gotowe, gdy: juror przechodzi ścieżkę sprzedawca → naklejka QR → potwierdzenie zarządcy na telefonie i komputerze, samą klawiaturą.

### E. Kampania i prezentacja – zespół (logo projektują ludzie; 25% oceny)

Materiały przygotowane przez agenta czekają na decyzje człowieka: `kampania/nazwa-i-haslo.md` (kandydaci; czołówka: „Opiekun AED”, „Na Widoku”, „Pokaż AED”), `kampania/brief-logo.md`, `kampania/ksiega-znaku-szablon.md`, `kampania/zachety.md`, `docs/prezentacja-konspekt.md`, `docs/instrukcja-dla-jury.md`. Znak rysuje człowiek.

1. Nazwa i hasło akcji; sprawdzić kolizje z istniejącymi nazwami.
2. Logo w SVG z eksportem do PNG, JPG, PDF; księga znaku w PDF (koncepcja w 3–5 zdaniach, kolorystyka, pole ochronne, minimalna wielkość, niedozwolone użycia).
3. Pakiet zachęt dla firm i samorządów: odznaka, obecność na mapie sprzedawców, przypomnienia o terminach baterii i elektrod jako usługa, ranking.
4. Prezentacja z narracją sprzedażową (min. 5 slajdów ze zrzutami, kroki użytkownika, ograniczenia, zakres użycia AI) i `docs/instrukcja-dla-jury.md`.

### Kolejność i zależności

1. Zrobione: A1 (schemat) – wszyscy czytają `aed_standard/schema.json`.
2. Równolegle: A2–A5, C2.1 (portal lokalnie), D1 (frontend lokalnie), E1–E2 (nazwa i logo), B2.
3. Po A2–A4: usługa C, potem D2–D4 podpinają ją zamiast danych próbnych.
4. Na końcu: C2.2, D5, zrzuty ekranu, prezentacja, niezależny przegląd całości (kod i UI/UX) przez Codexa i poprawki po nim.
5. Od 22.11: C3 (wykaz AED uruchomiony w portalu, serwer pod domeną) przed nowymi funkcjami usługi; zrzuty z portalu zastępują plan B. Przeglądy Codexa: `docs/przeglad-codex.md`.

Git: każdy etap idzie przez osobną gałąź, PR i merge do `main`, gdy testy przechodzą. Agenty nie commitują – robi to sesja prowadząca.

Gdy brakuje czasu, tniemy w tej kolejności: ranking i odznaki → mapa sprzedawców → przypomnienia (zostają na slajdzie) → serwer pod domeną (zostaje lekki prototyp i zrzuty z lokalnego portalu) → publikacja w lokalnym portalu (plan B). Nie tniemy: wykazu AED w forku portalu, standardu i szablonu XLSX, mappera z deduplikacją, zgłoszenia CSV przez firmę, strony QR, logo i księgi znaku, instrukcji dla jury.

## Co oddajemy

- [ ] tytuł i szczegółowy opis projektu
- [ ] prezentacja, min. 5 slajdów ze zrzutami, krokami użytkownika i ograniczeniami
- [ ] klikalny prototyp, który jury uruchomi bez konfiguracji (adres publiczny: `docs/wdrozenie-serwer.md`)
- [ ] `wzorzec-aed.xlsx`
- [ ] kod źródłowy
- [ ] logo: `.svg`, `.png`, `.jpg`, `.pdf`; księga znaku `.pdf`
- [ ] instrukcja dla jury: wymaganie → plik lub ekran → kroki sprawdzenia
- [ ] deklaracja zakresu użycia AI
- [ ] dowody WCAG i responsywności

## Konwencje pracy

- Teksty interfejsu i komunikaty walidatora po polsku; kod i nazwy w kodzie po angielsku; nazwy kolumn danych po polsku zgodnie ze schematem.
- `aed_standard` nie ma zależności zewnętrznych i musi działać na Pythonie 3.8.
- Każda niebanalna logika ma jeden uruchamialny test na prawdziwym pliku źródłowym.
- Najprostsze działające rozwiązanie; bez abstrakcji na zapas.
- Ograniczenie odkryte w trakcie pracy dopisz od razu do listy ograniczeń w prezentacji.

## Decyzje podjęte (fidok15, 21.11 wieczorem)

- **Integracja z portalem:** ekrany AED jako moduł w forku frontendu dane.gov.pl, logika w samodzielnej usłudze `aed_service/`; w backendzie portalu tylko publikacja zbioru. Zadanie nie wymaga wbudowania prototypu w portal – wymaga zgodności z jego zasadami.
- **Klikalny prototyp:** na razie tylko lokalnie w Dockerze – `docker compose up --build`, potem `http://localhost:8080/pl/aed` (usługa AED + nginx z buildem frontendu; reszta portalu czytana z publicznego API dane.gov.pl). Wdrożenie pod publicznym adresem wraca jako osobna decyzja.
- **Logo:** projektuje zespół; agenty dostarczają tylko brief i szablon księgi znaku.
- **Harmonogram:** pierwsza iteracja w 2 godziny (do ok. 20:15), całość „mniej więcej stoi” do północy, potem nowe funkcje i poprawki.
- **Kluczowe decyzje podejmuje człowiek:** gdy agent czegoś nie wie albo wybór zmienia kierunek, pyta zamiast zgadywać.

## Decyzje podjęte (noc 21/22.11, po wskazówce prowadzącego)

- **Główna ścieżka to wykaz AED w portalu.** Dostawcy publikują wykazy jako zasoby w swoich zbiorach, a portal je waliduje i scala w zasób zbiorczy ministerstwa (wzór: wykaz DGA). Zmienia to wcześniejszą decyzję „w backendzie portalu tylko publikacja zbioru”: logika wykazu jest w `backend/mcod/aed/`, wydzielona jako łatka. Usługa AED zostaje drugim kanałem: rekordy potwierdzone przez sprzedawcę i zarządcę trafiają do ministerstwa i wracają do portalu jako jego wykaz (plik lub link) albo zasilanie XML.
- **Prototyp dla jury:** pełny fork portalu na serwerze kolegi pod kupioną domeną (`docs/wdrozenie-serwer.md`); zastępuje decyzję „na razie tylko lokalnie”. Lekki wariant (`docker-compose.prod.yml`) zostaje jako zapas.
- **Dane kontaktowe i numer seryjny** są wycinane z każdego eksportu jedną regułą (`HIDDEN_PUBLIC`); zbiór zbiorczy ma warunki licencji CC BY 4.0, bo część wykazów jest na CC BY (po przeglądzie Codexa, PR #16).

## Otwarte decyzje

- Serwer i domena: architektura (zakładamy Linux amd64), RAM i dysk, nazwa domeny, rekordy `api.`, `admin.`, `cms.`; do kiedy serwer działa i kto go wyłączy.
- Dostęp jury: hasło kont demo AED (`AED_DEMO_PASSWORD` przekazane osobno czy znane hasła demo; karty logowania we frontendzie pokazują dziś stałe hasła) oraz konto w panelu portalu (redaktor instytucji demonstracyjnej czy tylko odczyt bez logowania).
- Wykaz AED: kilka wykazów na instytucję i każdy typ instytucji (dziś tak) czy jak DGA – jeden wykaz, tylko `local`/`state`?
- Czy wymagać `id_aed` albo `zrodlo_id` w wykazie (bez nich identyfikator zależy od kolejności wierszy)?
- Czy dodać `containsAedList` do XSD harvestera (wersja 1.14), żeby wykaz z harvestera oznaczał się sam?
- Harmonogram Celery na serwerze: scalanie samo o 03:45 czy ręcznie na pokazie?
- Ostateczna godzina i sposób oddania projektu – potwierdzić u organizatora.
- Nazwa i hasło akcji (kandydaci w `kampania/nazwa-i-haslo.md`).
- Czy numer seryjny jest publikowany w zbiorze otwartym, czy zostaje tylko w rejestrze (dziś kolumna w eksporcie jest pusta).
- Podstawa prawna obowiązku raportowania przez sprzedawców: dziś brak, więc dobrowolność i zachęty; rekomendacja regulacyjna na slajdzie „co dalej”.
