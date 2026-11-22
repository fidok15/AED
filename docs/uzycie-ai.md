# Zakres wykorzystania sztucznej inteligencji

Regulamin zadania (§2 ust. 7–8) dopuszcza użycie AI pod warunkiem, że rozwiązanie jest efektem analizy i pracy człowieka, i wymaga wskazania zakresu tego użycia. Ten plik prowadzimy na bieżąco; wpis dodaje się po każdej sesji pracy z AI.

## Narzędzie

Claude Code (model Claude firmy Anthropic) w roli asystenta programisty: sesja prowadząca rozdzielała zadania między agenty pomocnicze, a członkowie zespołu wydawali polecenia, podejmowali decyzje i odbierali wyniki.

## Co zrobił człowiek

- Rozmowa z komisją i ustalenie celu rozwiązania (ministerstwo zbiera dane, kanał producenta i sprzedawcy, naklejka QR, potwierdzenia, deduplikacja).
- Decyzje kierunkowe: sposób integracji z portalem, forma prototypu, harmonogram, zakres pól.
- Wybór i pobranie źródeł danych, w tym uzyskanie dostępu do API Warszawy.
- Przygotowanie forka kodu portalu dane.gov.pl w repozytorium.
- Logo, nazwa i hasło akcji oraz księga znaku – projekt w całości po stronie zespołu.
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
| 2026-11-21 | prezentacja w Figma Slides (15 slajdów, notatki mówcy) na podstawie `docs/` i zrzutów z `frontend/aed-zrzuty/`; trzy GIF-y ścieżek firmy, zarządcy i ministerstwa nagrane skryptem Playwright z lokalnego prototypu (`frontend/aed-zrzuty/gif/`) | fidok15 (do przeglądu) |
| 2026-11-22 | szkice koncepcji nazwy i logo w Figma (plik „AED – koncepcje logo”): 3 kierunki (Gotowe!, Opiekun AED, AED na widoku) z ikonami aplikacji, lockupami, naklejką QR i odznaką, potem 2 warianty bez zieleni z komórkami w kolorach stanów rekordu (D serce stanów, E puls stanów); przegląd nazw aplikacji AED w App Store / Google Play przez wyszukiwarkę. Szkic do dyskusji, ostateczny znak rysuje zespół | fidok15 (do decyzji) |
| 2026-11-22 | prezentacja HTML z animacjami (`prezentacja-html/`, 17 slajdów): układ, teksty na podstawie `docs/prezentacja-konspekt.md` i `raport.json`, ilustracje postaci i scenerii rysowane kodem SVG, nagrania i zrzuty z prototypu; skrypt `build.py` składa jeden samodzielny plik `prezentacja.html` | fidok15 (do przeglądu) |
| 2026-11-22 | po wyborze wariantu D przez zespół: eksport znaku z Figmy (SVG, z tego PNG, JPG i wektorowy PDF w `kampania/logo/`, skrypt `kampania/build_logo.py`) oraz księga znaku `kampania/opiekun-aed-ksiega-znaku.pdf` (12 stron: koncepcja, konstrukcja, pole ochronne, minimalna wielkość, kolorystyka, warianty, typografia, niedozwolone użycia, zastosowania); wartości minimalnej wielkości i CMYK do potwierdzenia wydrukiem próbnym; hasło wzięte z kandydatów w `kampania/nazwa-i-haslo.md` | fidok15 (do przeglądu) |
