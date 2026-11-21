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
| Materiały kampanii (`kampania/`) | propozycje nazw i haseł, brief, szablon księgi znaku, pakiet zachęt | wybór i ostateczna treść należą do zespołu; AI nie tworzyło znaku graficznego |
| Dokumentacja (`README.md`, `CLAUDE.md`, `docs/`) | redakcja na podstawie ustaleń zespołu | przegląd zespołu |

## Czego AI nie robiło

- Nie projektowało logo ani elementów księgi znaku.
- Nie publikowało niczego na dane.gov.pl ani w innych serwisach zewnętrznych.
- Nie podejmowało decyzji o kierunku rozwiązania.

## Dziennik sesji

| Data | Co zrobiono z AI | Kto odebrał |
|---|---|---|
| 2026-11-21 | research; plan; standard danych; walidator, mapper i deduplikacja; usługa API; pierwsza wersja modułu AED we frontendzie; Docker; szkice materiałów kampanii i prezentacji | fidok15 |
