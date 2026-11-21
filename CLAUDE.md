# Misja AED – Dane na ratunek (HackNation 2026)

Zadanie konkursowe Ministerstwa Cyfryzacji: rozwiązanie, które ułatwia zebranie w portalu dane.gov.pl jednego, ogólnopolskiego, otwartego i aktualnego zbioru danych o defibrylatorach AED. Hackathon trwa 24 godziny (21–22 listopada 2026). Na dzień 2026-11-21 repozytorium zawiera tylko dokumenty, bez kodu.

Ten plik jest planem działania i zbiorem zasad. Szczegóły i źródła są w:

- `docs/MC DZD - Pełna treść zadania konkursowego-1.pdf` i `docs/MC DZD - Regulamin zadania konkursowego-1.pdf` – treść zadania i regulamin,
- `docs/tips.txt` – wskazówki organizatora i mentora,
- `docs/research-i-pomysly.md` – research zespołu, **szkic wzorcowego zakresu danych (rozdz. 5)**, katalog pomysłów (rozdz. 6),
- `reports/Innowacje w aplikacjach AED.md` – wzorce zagraniczne, ranking innowacji, stack, lista twierdzeń niezweryfikowanych.

## Co naprawdę budujemy

To nie jest konkurs na mapę AED. OpenStreetMap ma już ok. 18 tys. AED w Polsce i zasila operatorów 112; na dane.gov.pl jest 5 zasobów miejskich (74 rekordy) w czterech niezgodnych schematach. Problem nazwany przez mentora: dane są rozproszone i niezweryfikowane, bo nikt nie bierze za nie odpowiedzialności.

Budujemy więc mechanizm odpowiedzialności: **wzorzec danych + narzędzia dla dysponenta + agregator + kampania**. Mapa „dostępny teraz” jest warstwą pokazową, która dowodzi wartości danych.

| Kryterium | Waga | Co je realizuje |
|---|---|---|
| Zgodność z zasadami dane.gov.pl | 30% | paczka publikacyjna z kreatora (CSV/XLSX + manifest XML + `.md5`), lokalnie uruchomiony portal, metadane |
| Logotyp i hasło | 25% | nazwa akcji, hasło, logo, księga znaku, materiały dla dostawców |
| Kreatywność i innowacyjność | 15% | klasa świeżości, „dostępny teraz”, QR na szafce, raport luk |
| Zgodność z tematem | 15% | konwertery wielu źródeł + agregator ze wskazaniem zakresu każdego źródła |
| Wzorcowy zakres danych | 10% | `wzorzec-aed.xlsx` + schemat maszynowy |
| Prezentacja | 5% | slajdy ze zrzutami, instrukcja dla jury |

## Twarde zasady

Naruszenie którejkolwiek kosztuje punkty albo nagrodę.

1. **Zespół nie publikuje danych na dane.gov.pl.** Publikuje wyłącznie dostawca (instytucja lub firma) biorący odpowiedzialność za zbiór. Nasze narzędzia przygotowują paczkę dla dostawcy. Nie projektujemy niczego w modelu „każdy wgrywa na portal”.
2. **Zgłoszenia obywateli nie edytują danych.** Trafiają do dysponenta jako sygnał; dysponent aktualizuje swój zbiór.
3. **Dane OSM (ODbL) nie trafiają do zbioru rdzeniowego (CC0).** OSM służy tylko jako osobna warstwa z atrybucją, do porównań i raportu luk. Kierunek przepływu: dysponent → dane.gov.pl → OSM, nigdy odwrotnie.
4. **Nie kopiujemy cudzego kodu.** Portal (mcod) jest na GPL v3, backend OpenAEDMap na AGPL; prawa do rozwiązania przechodzą na Ministra Cyfryzacji. Reguły portalu odtwarzamy własnym kodem. Zależności tylko na licencjach permisywnych; każdą inną (np. `opening_hours.js`, LGPL-3.0) zgłoś zespołowi przed dodaniem.
5. **Tylko formaty odczytywalne maszynowo** dla danych (CSV, XLSX, JSON, GeoJSON, XML). PDF dopuszczalny wyłącznie dla logo i księgi znaku.
6. **Żadnych danych osobowych ani kodów do szafek w danych otwartych.** Kontakt wyłącznie instytucjonalny; publikujemy sposób otwarcia, nie kod.
7. **WCAG 2.2 AA i responsywność** od pierwszego ekranu: mapa jest dodatkiem do w pełni dostępnej listy, obsługa klawiaturą, stan przekazany tekstem i ikoną, nie samym kolorem, układ działa przy 320 px.
8. **Użycie AI musi być udokumentowane.** Po każdej sesji pracy dopisz wpis do `docs/uzycie-ai.md`: co wygenerowano, co zweryfikował i zdecydował człowiek. Logo i księga znaku powstają ręcznie – AI nie generuje znaku.
9. **Nie obiecujemy uratowanych istnień.** Badanie randomizowane aplikacji dla ochotników (Dania, 2026) nie wykazało poprawy przeżywalności. W tekstach i na slajdach mierzymy proces: liczbę dostawców, udział rekordów zweryfikowanych i dostępnych w danej chwili.
10. **Liczby na slajdy tylko ze źródła pierwotnego.** Twierdzenia oznaczone `[NZ]` w raporcie wymagają sprawdzenia przed użyciem.

## Reguły portalu, które kod musi odtwarzać

Odczytane z przewodników portalu i z lustra kodu w wersji 2.62.3 (bieżąca to 2.63.0 – różnice sprawdzić w ścieżce E).

- **CSV:** UTF-8, separator `,`, jeden wiersz nagłówka, kropka dziesiętna, daty ISO 8601, bez scalonych komórek i znaków nowej linii w komórce.
- **Walidacja tabelaryczna portalu:** struktura, schemat, zero wierszy danych.
- **Otwartość:** plik przechowywany w portalu z poprawnym widokiem tabeli dostaje 4 gwiazdki; plik zdalny zostaje na 3.
- **Mapa na portalu** nie powstaje z nazw kolumn. Wymaga osobnych, liczbowych kolumn szerokości i długości (WGS84) oraz kolumny etykiety, które redaktor wskazuje ręcznie w zakładce „Mapy i wykresy”. Kreator dołącza do paczki instrukcję tego kroku.
- **Harvester XML:** plik zgodny z `otwarte_dane_latest.xsd` (przestrzeń nazw `urn:otwarte-dane:harvester:1.13`), obok plik `.md5` z sumą małymi literami, `extIdent` do 36 znaków.
- **Metadane zbioru:** kategoria Zdrowie (`HEAL`), licencja CC0 1.0, częstotliwość aktualizacji, wspólny tag kampanii, po którym agregator znajduje zbiory przez `api.dane.gov.pl/1.4`.
- **Do przetestowania:** zalecany przez portal znak „X” w pustych komórkach może zmienić wywnioskowany typ kolumn liczbowych i dat.

## Architektura

```
źródła (5 zasobów dane.gov.pl, plik dysponenta)      OSM / OpenAEDMap (ODbL)
        │ konwertery                                          │ osobna warstwa
        ▼                                                     ▼
   wzorzec AED (Table Schema) ──► walidator ──► agregator ──► raport luk
        │                             │             │
        ▼                             ▼             ▼
  wzorzec-aed.xlsx            kreator dostawcy   zbiór krajowy CSV/GeoJSON
                              (paczka dla portalu)      │
                                                        ▼
                              aplikacja: lista + mapa „dostępny teraz”,
                              strona urządzenia z QR, licznik i ranking
```

Jedno źródło prawdy: schemat w `schema/`. Szablon XLSX, walidator, konwertery i formularz kreatora wynikają ze schematu – nie duplikuj listy pól w kodzie.

## Domyślne decyzje techniczne

Obowiązują, dopóki zespół nie postanowi inaczej; zmianę zapisz w tym pliku.

- **Jeden język, bez backendu.** TypeScript: moduł `core` (schemat, walidator, konwertery, deduplikacja, generator XML) używany zarówno przez skrypty wiersza poleceń, jak i przez aplikację w przeglądarce. Dzięki temu walidator istnieje raz, a prototyp jest statyczną stroną, którą jury otwiera bez konfiguracji.
- **Aplikacja:** Vite + React + TypeScript, PWA. Mapa: MapLibre GL JS z kafelkami OpenFreeMap (wersję przypiąć przy instalacji). Komponenty na dostępnych prymitywach (Radix).
- **Dane w przeglądarce:** zbiór ma kilkanaście tysięcy punktów, więc statyczny GeoJSON wystarcza; bez bazy danych, bez serwera kafelków, bez własnego routingu.
- **Pliki:** odczyt CSV/XLSX w przeglądarce; szablon XLSX z listami wyboru generowany skryptem.
- **Godziny:** składnia `opening_hours` z OSM w danych, prosty edytor „od–do” w kreatorze; trzy stany w aplikacji: dostępny teraz / zamknięty / nieznane.
- **Zapis bez backendu:** potwierdzenie i zgłoszenie ze strony QR to wiadomość do dysponenta (`mailto:` na kontakt instytucjonalny z rekordu) oraz link do „Zgłoś uwagi” na portalu. Zgodne z zasadą 2.
- **Geokodowanie:** usługa GUGiK UUG. Dostępność z przeglądarki (CORS) niesprawdzona – sprawdzić przed oparciem na niej kreatora; plan B to wskazanie punktu na mapie.
- **Hosting prototypu:** GitHub Pages z tego repozytorium.

## Docelowa struktura repozytorium

```
schema/      aed.schema.json (Table Schema), słowniki, mapowania na OSM i Géo'DAE
core/        walidator, konwertery źródeł, deduplikacja, świeżość, generator XML + md5
scripts/     pobranie źródeł, budowa zbioru krajowego, generowanie wzorzec-aed.xlsx
data/        raw/ (z datą pobrania), out/ (zbiór krajowy, warstwa OSM osobno)
app/         aplikacja web (kreator, walidator, mapa, strona QR, raport luk)
kampania/    logo (svg, png, jpg, pdf), księga znaku (pdf), materiały
portal/      notatki i zrzuty z lokalnego uruchomienia dane.gov.pl
docs/        zadanie, research, instrukcja dla jury, użycie AI
```

Po utworzeniu szkieletu dopisz tutaj komendy instalacji, uruchomienia, testów i budowy.

## Plan działania

Pięć ścieżek równoległych. Ścieżka A blokuje B i C, więc startuje pierwsza.

### A. Wzorzec danych (blokuje resztę)

1. Zamrozić listę pól na podstawie `docs/research-i-pomysly.md` rozdz. 5 jako `schema/aed.schema.json`.
2. Wygenerować `wzorzec-aed.xlsx`: arkusze pola, słowniki, przykład, instrukcja; listy wyboru dla pól słownikowych.
3. Dodać przykładowy poprawny CSV i tabelę mapowań na tagi OSM, pola Géo'DAE i standard japoński.

Gotowe, gdy: przykładowy CSV przechodzi walidator, a XLSX otwiera się z działającymi listami wyboru.

### B. Dane: konwertery, walidator, agregator

1. Walidator z regułami z rozdz. 5.6 (m.in. zamienione współrzędne, punkt poza Polską, nieparsowalne godziny, przeterminowane daty) i komunikatami po polsku na poziomie wiersza.
2. Konwertery pięciu zasobów z dane.gov.pl (Krosno, Przemyśl, Marki, Legionowo, Warszawa) do wzorca; plik Marek jako przypadek pokazowy błędów.
3. Agregator: scalenie, źródło i licencja przy każdym rekordzie, lista możliwych duplikatów (odległość + podobieństwo nazwy), klasa świeżości z `data_weryfikacji`.
4. Warstwa OSM pobrana raz, zapisana osobno z atrybucją; raport luk „OSM kontra zbiór dysponenta” na poziomie gminy.
5. Generator paczki publikacyjnej: CSV + XLSX + manifest XML + `.md5` + instrukcja mapy.

Gotowe, gdy: jedna komenda buduje zbiór krajowy i macierz „źródło × pokryte pola”, a manifest XML przechodzi walidację względem XSD.

### C. Aplikacja (klikalny prototyp)

Kolejność według wartości dla oceny:

1. **Walidator i kreator dostawcy:** wgraj plik, zmapuj kolumny, zobacz błędy, popraw, pobierz paczkę z instrukcją „jak opublikować w 5 krokach”.
2. **Lista i mapa „dostępny teraz”:** trzy stany dostępności, klasa świeżości na rekordzie, filtr po gminie.
3. **Strona urządzenia z QR:** dwa przyciski („jest i działa” / „zgłoś problem”), bez logowania.
4. **Raport luk dla gminy** oraz licznik dostawców i rekordów z rankingiem.
5. **Tryb ratunkowy:** „Zadzwoń 112” (`tel:112`), najbliższy dostępny AED, odległość, opis miejsca, kierunek z alternatywą tekstową.

Gotowe, gdy: juror przechodzi całą ścieżkę dostawcy od wgrania pliku do pobrania paczki pod publicznym adresem, na telefonie i komputerze, samą klawiaturą.

### D. Kampania (25% oceny – nie zostawiać na koniec)

1. Wybrać nazwę i hasło; sprawdzić kolizje z istniejącymi nazwami („Mapa AED”, „Ratuj z sercem”, „Pierwszy Ratownik”, „Porusz serce”, „Akcja defibrylacja”). Nazwa musi działać jako tag zbioru, hashtag i podpis odznaki.
2. Narysować logo: jeden plik SVG, eksport do PNG, JPG i PDF; warianty kolorowy, monochromatyczny, negatyw. Nie przerabiać znaku ISO 7010 E010, nie używać orła ani form biało-czerwonych.
3. Księga znaku w PDF: koncepcja w 3–5 zdaniach, kolorystyka, pole ochronne, minimalna wielkość, niedozwolone użycia, zastosowania (odznaka dostawcy, naklejka QR, baner dla gminy).
4. Materiały akcji adresowane do dostawców: checklista publikacji, wzór pisma, odznaka „udostępnia dane AED”.

Gotowe, gdy: komplet plików leży w `kampania/`, a aplikacja używa znaku i nazwy akcji.

### E. Zgodność z portalem (wskazówka nr 3 organizatora)

1. Uruchomić portal lokalnie z kodu z `dane.gov.pl/source-code/`. Limit czasu: 3 godziny.
2. Założyć dostawcę demonstracyjnego, wczytać naszą paczkę (ręcznie i przez harvester XML), ustawić mapę w „Mapy i wykresy”, sprawdzić poziom otwartości i API zasobu.
3. Zebrać zrzuty ekranu do `portal/` i porównać reguły walidacji z wersją kodu 2.63.0.

Plan B po przekroczeniu limitu: dowody z produkcyjnego API portalu, walidacja XML względem XSD i wpis w liście ograniczeń.

### Finał: dowody i oddanie

1. `docs/instrukcja-dla-jury.md`: tabela „wymaganie → plik lub ekran → kroki sprawdzenia”.
2. Prezentacja (min. 5 slajdów): zrzuty jako dowody wymagań technicznych, kroki użytkownika, ograniczenia, zakres użycia AI.
3. Dowody dostępności: raport axe lub Lighthouse, test klawiaturą i czytnikiem ekranu, zrzuty z telefonu.
4. README z tytułem, opisem i instrukcją uruchomienia.

### Kolejność cięć, gdy brakuje czasu

Od pierwszego do wycięcia: tryb ratunkowy → ranking i licznik → raport luk → strona QR → harvester w lokalnym portalu (zostaje plan B). Nie tniemy nigdy: wzorca XLSX, walidatora, konwerterów, paczki publikacyjnej, logo i księgi znaku, instrukcji dla jury.

## Co oddajemy

- [ ] tytuł i szczegółowy opis projektu
- [ ] prezentacja, min. 5 slajdów ze zrzutami, krokami użytkownika i ograniczeniami
- [ ] klikalny prototyp pod publicznym adresem
- [ ] `wzorzec-aed.xlsx` (plus schemat JSON, przykładowy CSV, szablon XML)
- [ ] kod źródłowy
- [ ] logo: `.svg`, `.png`, `.jpg`, `.pdf`; księga znaku `.pdf`
- [ ] instrukcja dla jury
- [ ] deklaracja zakresu użycia AI
- [ ] dowody WCAG i responsywności
- [ ] dowód zgodności z dane.gov.pl

## Konwencje pracy

- Nazwy kolumn danych: `snake_case`, bez polskich znaków. Teksty interfejsu i komunikaty walidatora po polsku. Kod i nazwy w kodzie po angielsku.
- Każda niebanalna logika w `core` (walidacja, deduplikacja, świeżość, generator XML) ma jeden uruchamialny test na prawdziwym pliku źródłowym.
- Surowe dane źródłowe zapisuj w `data/raw/` z datą pobrania; nie edytuj ich ręcznie.
- Najprostsze działające rozwiązanie: bez abstrakcji na zapas, bez nowych zależności dla kilku linijek kodu.
- Ograniczenie odkryte w trakcie pracy dopisz od razu do listy ograniczeń w prezentacji – jury jej wymaga.

## Otwarte decyzje

- Nazwa i hasło akcji (propozycje: `docs/research-i-pomysly.md` rozdz. E1 oraz raport).
- Model publikacji pokazany w prototypie: federacja wielu zbiorów dysponentów z agregatorem (rekomendowana) czy jeden dostawca krajowy.
- Ostateczna lista pól wymaganych we wzorcu.
- Godzina i sposób oddania projektu – potwierdzić u organizatora.
- Opinia prawna o licencjach ODbL i CC0 – poza hackathonem; na slajdzie jako ograniczenie.
