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

## Proces, który budujemy

```
producent / sprzedawca ──(konto firmy: CSV lub formularz)──┐
zarządca ──(skan QR: lokalizacja, godziny, potwierdzenie)──┤
samorządy i inne zbiory na dane.gov.pl ──(mapper)──────────┼─► standard AED ─► walidacja ─► deduplikacja
OpenStreetMap, API Warszawy ──(mapper, cyklicznie)─────────┘                                    │
                                                                                                 ▼
        przypomnienia i prośby o potwierdzenie ◄── rejestr krajowy (ministerstwo) ──► zbiór na dane.gov.pl
        (termin baterii i elektrod, brak weryfikacji)                               (CSV + zasilanie XML)
```

Cykl życia rekordu: `zgloszony` (sprzedawca podał dane urządzenia) → `aktywny` (zarządca potwierdził miejsce i dostęp) → `nieaktualny` (brak potwierdzenia w terminie) → `wycofany`. Rekord z mappera, którego nikt odpowiedzialny nie potwierdził, ma status `niepotwierdzony`.

## Punktacja

| Kryterium | Waga | Co je realizuje |
|---|---|---|
| Zgodność z zasadami dane.gov.pl | 30% | fork portalu z kontami firm i zgłaszaniem CSV; zbiór publikowany mechanizmami portalu |
| Logotyp i hasło | 25% | nazwa akcji, hasło, logo, księga znaku, materiały dla dostawców |
| Kreatywność i innowacyjność | 15% | kanał sprzedawcy, QR, potwierdzenia, wskaźnik kompletności, zachęty |
| Zgodność z tematem | 15% | mapper wielu źródeł, deduplikacja, wskazanie zakresu każdego źródła |
| Wzorcowy zakres danych | 10% | `wzorzec-aed.xlsx` wygenerowany ze standardu |
| Prezentacja | 5% | slajdy ze zrzutami, instrukcja dla jury |

## Twarde zasady

1. **Źródłem prawdy o strukturze danych jest `aed_standard/schema.json`.** Formularze, walidator, mapper, szablon XLSX i eksporty wynikają z tego pliku. Nie duplikuj listy pól w kodzie ani w dokumentach.
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
- **`publikacja`** – rekord gotowy do zbioru otwartego. Wymagane dodatkowo: nazwa miejsca, współrzędne, miejscowość, dostęp, godziny dostępu.

Do zbioru na dane.gov.pl trafia tylko rekord spełniający profil `publikacja`. Kompletność rekordu (0–100) liczymy z pól wymaganych i zalecanych.

Deduplikacja:

- ten sam producent i numer seryjny to to samo urządzenie (pewne);
- bez numeru seryjnego: rekordy z **różnych** źródeł w odległości do 50 m są kandydatami; łączymy automatycznie przy odległości do 15 m albo przy wysokim podobieństwie nazwy i adresu, resztę kierujemy do ręcznego przeglądu;
- dwa rekordy z tego samego źródła nigdy nie są łączone automatycznie (w jednym budynku bywa kilka urządzeń);
- pierwszeństwo źródeł przy łączeniu: sprzedawca lub zarządca → zbiory z dane.gov.pl → API Warszawy → OSM.

## Repozytorium

```
aed_standard/   standard danych: schema.json, walidator, mapper źródeł, deduplikacja, eksporty
                (czysty Python, bez zależności, zgodny z Pythonem 3.8 – importowalny w backendzie portalu)
scripts/        download_aed_data.py (pobranie źródeł), budowa zbioru krajowego, szablon XLSX
datasets/raw/   surowe źródła z manifestem (nie edytować ręcznie)
datasets/out/   zbiór krajowy, lista duplikatów do przeglądu, raport
backend/        fork backendu dane.gov.pl (mcod: Python 3.8, Django 2.2, Falcon, Docker Compose)
frontend/       fork frontendu dane.gov.pl (Angular 18)
kampania/       logo, księga znaku, materiały akcji
docs/           zadanie, research, instrukcja dla jury, użycie AI
```

Stan źródeł na 21.11: pięć zbiorów z dane.gov.pl (Krosno, Marki, Przemyśl, Legionowo, Warszawa), API Warszawy (708 urządzeń), OpenAEDMap (18 297 obiektów). Innych maszynowo czytelnych zbiorów miejskich nie znaleziono; Kraków („Impuls Życia”) i Koszalin („Punkty Życia”) publikują tylko listy na stronach WWW.

Fakty o portalu ustalone w kodzie:

- typy instytucji w `backend/mcod/organizations/models.py`: `local`, `state`, `private`, `developer`, `other`. Typ `developer` (deweloperzy raportujący ceny mieszkań) jest precedensem dla nowego typu „producent lub sprzedawca AED”;
- role użytkowników: redaktor (`is_staff`), pełnomocnik (`is_agent`), urzędnik (`is_official`);
- frontend nie serwuje API; adres backendu ustawia się w plikach `proxy.*.conf.json`.

## Podział zadań

Właściciele wynikają z historii commitów i są propozycją – zmieńcie ją tutaj, jeśli zespół ustali inaczej.

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

### C. Fork portalu – backend – Jakub Zawadzki

1. Uruchomić portal lokalnie (Docker Compose). Limit: 3 godziny; plan B to dowody z produkcyjnego API i osobna usługa.
2. Nowy typ instytucji dla producentów i sprzedawców AED wzorem typu `developer`; konto firmy.
3. Przyjęcie pliku CSV od firmy: walidacja modułem `aed_standard` (profil `sprzedaz`), zapis do rejestru, raport błędów.
4. Publikacja zbioru krajowego jako zasobu dostawcy „ministerstwo” mechanizmami portalu; ustawienie mapy w „Mapy i wykresy”.
5. Mechanizm potwierdzeń: wiadomość do właściciela z linkiem jednorazowym (portal ma lokalną skrzynkę testową), przypomnienie przed końcem ważności baterii i elektrod.

Gotowe, gdy: firma loguje się, wysyła CSV, a rekordy widać w zbiorze krajowym w lokalnym portalu.

### D. Frontend – fidok15 z agentem

1. Uruchomić `frontend/` lokalnie i wydzielić moduł AED.
2. Panel firmy: wgranie CSV z raportem walidacji oraz formularz pojedynczego urządzenia generowany ze schematu.
3. Strona QR dla zarządcy: uzupełnienie lokalizacji (geolokalizacja telefonu), godzin dostępu, potwierdzenie stanu.
4. Widok rejestru: lista i mapa, filtr statusu, wskaźnik kompletności, mapa sprzedawców.
5. Zachęty: odznaka dla firmy z aktualnymi danymi, ranking kompletności.

Gotowe, gdy: juror przechodzi ścieżkę sprzedawca → naklejka QR → potwierdzenie zarządcy na telefonie i komputerze, samą klawiaturą.

### E. Kampania i prezentacja – BRAK WŁAŚCICIELA, przypisać od razu (25% oceny)

1. Nazwa i hasło akcji; sprawdzić kolizje z istniejącymi nazwami.
2. Logo w SVG z eksportem do PNG, JPG, PDF; księga znaku w PDF (koncepcja w 3–5 zdaniach, kolorystyka, pole ochronne, minimalna wielkość, niedozwolone użycia).
3. Pakiet zachęt dla firm i samorządów: odznaka, obecność na mapie sprzedawców, przypomnienia o terminach baterii i elektrod jako usługa, ranking.
4. Prezentacja z narracją sprzedażową (min. 5 slajdów ze zrzutami, kroki użytkownika, ograniczenia, zakres użycia AI) i `docs/instrukcja-dla-jury.md`.

### Kolejność i zależności

1. Teraz: A1 (schemat) – wszyscy pozostali czytają `aed_standard/schema.json`.
2. Równolegle: C1 (portal lokalnie), D1 (frontend lokalnie), E1–E2 (nazwa i logo), B2.
3. Po A2–A4: C3 i D2 podpinają walidator i zbiór krajowy.
4. Na końcu: C4–C5, D3–D5, zrzuty ekranu, prezentacja.

Gdy brakuje czasu, tniemy w tej kolejności: ranking i odznaki → mapa sprzedawców → przypomnienia e-mail (zostają na slajdzie) → publikacja w lokalnym portalu (plan B). Nie tniemy: standardu i szablonu XLSX, mappera z deduplikacją, zgłoszenia CSV przez firmę, strony QR, logo i księgi znaku, instrukcji dla jury.

## Co oddajemy

- [ ] tytuł i szczegółowy opis projektu
- [ ] prezentacja, min. 5 slajdów ze zrzutami, krokami użytkownika i ograniczeniami
- [ ] klikalny prototyp, który jury uruchomi bez konfiguracji
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

## Otwarte decyzje

- Godzina i sposób oddania projektu – potwierdzić u organizatora.
- Kto prowadzi kampanię i logo (ścieżka E).
- Czy numer seryjny jest publikowany w zbiorze otwartym, czy zostaje tylko w rejestrze.
- Gdzie stoi klikalny prototyp (portal w Dockerze wymaga serwera; plan B to nagranie i zrzuty).
- Podstawa prawna obowiązku raportowania przez sprzedawców: dziś brak, więc dobrowolność i zachęty; rekomendacja regulacyjna na slajdzie „co dalej”.
