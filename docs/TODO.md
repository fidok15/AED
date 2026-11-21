# Do zrobienia

Stan na 21.11.2026, 22:48, `main` = `4bbe408`. Testy backendu: 61 przechodzi; zbiór krajowy: 18 814 rekordów, eksport 781.

Plan i zasady: `CLAUDE.md` w katalogu głównym. Kontrakt API: `docs/api-aed.md`.

## 1. Frontend – wstrzymane do sygnału

Agent frontendowy został przerwany limitem przed raportem; jego praca jest w commicie `6b7dcda` (`fix: frontend`), nieodebrana.

- [ ] Sprawdzić znalezisko 12 z przeglądu Codexa: wyczyszczenie pola opcjonalnego na ekranie QR ma usuwać starą wartość (dziś niepotwierdzone).
- [ ] Uruchomić testy i linter frontendu po commicie `6b7dcda` (`npm test`, `npm run lint`, `npm run build:aed`).
- [ ] Przejść w przeglądarce trzy poprawki z przeglądu: skrzynka ministerstwa z wiadomością bez linku, ekran po zgłoszeniu problemu, krok „bateria i elektrody” – na usłudze z poprawkami z PR #14.
- [ ] Dostosować frontend do zmian kontraktu z PR #14: licznik `wycofano` w wynikach mappera i historii zadań, błąd 422 także przy `stan = problem`, kilka ważnych linków dysponenta.
- [ ] Pokazać w panelu ministerstwa źródła pominięte i błędy źródeł (dane dodane przez Jakuba w historii zadań i `raport.json`).
- [ ] Filtr „dostępny teraz” na liście rejestru (dziś tylko na mapie) – wymaga parametru w `GET /urzadzenia`.
- [ ] Nowe zrzuty do prezentacji po zakończeniu poprawek (dopiero wtedy).

## 2. Docker i uruchomienie

- [ ] Przebudować obrazy z aktualnego `main` (`docker compose up --build`) – działające kontenery mają obrazy sprzed poprawek po przeglądzie i sprzed zmian zespołu.
- [ ] Sprawdzić, czy `backend/docker-compose.aed-ports.yml` i `frontend/proxy.aed-local.conf.json` (Hubert) nie kolidują z głównym `docker-compose.yml` (porty 8080, 8085).
- [ ] Po przebudowie przejść trzy ścieżki z `docs/instrukcja-dla-jury.md` od zera na świeżym wolumenie.
- [ ] Decyzja: czy wystawić prototyp pod publicznym adresem dla jury (dziś tylko lokalnie).

## 3. Usługa i standard danych

- [ ] Druga runda przeglądu Codexa po poprawkach (pierwsza: FAIL, 1 krytyczne + 11 poważnych; 9 naprawionych w PR #14, 3 frontendowe do potwierdzenia).
- [ ] Przejrzeć zmiany zespołu w `aed_standard` (rejestr źródeł `sources.json`, `registry.py`, zmiany w `dedup.py`) pod kątem zgodności z poprawkami z PR #14 – testy przechodzą, przegląd kodu nie był robiony.
- [ ] Zgodność `aed_service/app.py` z Pythonem 3.8 (operator `|` na słownikach, `traceback.print_exception` z jednym argumentem) – potrzebne tylko przy przenoszeniu do backendu portalu.
- [ ] Usługa korzysta z funkcji `aed_standard` spoza publicznego API (`dedup.CANDIDATE_M`, `similarity`, `haversine_m`) – przepiąć na `find_candidates`.
- [ ] Nowy rekord z importu obok już potwierdzonego urządzenia nie trafia do kolejki duplikatów (dopasowanie działa tylko w chwili potwierdzenia).
- [ ] Decyzja: czy numer seryjny jest publikowany w zbiorze otwartym (dziś kolumna w eksporcie jest pusta).

## 4. Portal dane.gov.pl (Jakub, Hubert)

- [ ] Uruchomić portal lokalnie i wgrać `datasets/out/aed_dane_gov_pl.csv` jako zasób instytucji „ministerstwo”.
- [ ] Ustawić mapę w zakładce „Mapy i wykresy” (kolumny `dlugosc_geograficzna`, `szerokosc_geograficzna`, `nazwa`).
- [ ] Zrzuty: widok tabeli, mapa, API zasobu, poziom otwartości → do prezentacji i `docs/instrukcja-dla-jury.md`.
- [ ] Plan B, jeśli portal nie wstanie: `docs/integracja-portal-backend.md` jako plan wdrożenia i wpis w ograniczeniach.

## 5. Kampania – 25% oceny (zespół)

- [ ] Wybrać nazwę i hasło akcji (kandydaci: `kampania/nazwa-i-haslo.md`); sprawdzić domenę i rejestry znaków.
- [ ] Narysować logo; eksport do `.svg`, `.png`, `.jpg`, `.pdf`; warianty kolorowy, monochromatyczny, negatyw (`kampania/brief-logo.md`).
- [ ] Zapisać znak jako `aed_service/naklejka-logo.svg` – usługa wstawi go na naklejkę QR.
- [ ] Księga znaku w PDF na podstawie `kampania/ksiega-znaku-szablon.md`.
- [ ] Wstawić nazwę akcji i znak do interfejsu modułu AED.

## 6. Dokumenty i oddanie

- [ ] Zaktualizować `docs/instrukcja-dla-jury.md` o zmiany z wieczora (rejestr źródeł, daty baterii i elektrod, strona startowa `/pl/aed`) i usunąć znaczniki `[do sprawdzenia]` po przejściu w przeglądarce.
- [ ] Zaktualizować `docs/prezentacja-konspekt.md` i zrobić plik prezentacji (min. 5 slajdów ze zrzutami, kroki użytkownika, ograniczenia, zakres użycia AI).
- [ ] Zapisać raport z przeglądu Codexa z wynikami poprawek w `docs/`.
- [ ] Uzupełnić dziennik w `docs/uzycie-ai.md` o wieczorną sesję.
- [ ] Zaktualizować `CLAUDE.md` (stan, decyzje, rejestr źródeł jest już dopisany przez zespół).
- [ ] Tytuł i szczegółowy opis projektu do formularza zgłoszeniowego.
- [ ] Potwierdzić u organizatora godzinę i sposób oddania.

## 7. Testy ręczne, których nikt nie zrobił

- [ ] Ekran QR na prawdziwym telefonie (geolokalizacja, wybór godzin, wydajność na sieci komórkowej).
- [ ] Czytnik ekranu (VoiceOver) na ścieżce dysponenta i panelu firmy.
- [ ] Powiększenie 200% prawdziwym zoomem przeglądarki.
- [ ] Wydruk arkusza naklejek na drukarce i skan kodu QR z wydruku (ok. 4 cm).
