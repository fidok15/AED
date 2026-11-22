# Niezależne przeglądy kodu (Codex)

Kod pisany z Claude Code przeglądał niezależnie Codex (model innego dostawcy). Przegląd zlecała sesja prowadząca, a poprawki szły przez osobne gałęzie i PR. Ten plik zbiera wyniki i ich stan. Pełnych raportów Codexa nie zapisaliśmy w repozytorium. Rundę 1 odtworzono z opisu commita z poprawkami (`9c8ce56`) i z `docs/TODO.md`, rundę 2 z opisu commita `d4eec3b` i z ustaleń sesji prowadzącej.

## Podsumowanie

| Runda | Data | Zakres | Werdykt | Znaleziska | Poprawione | Potwierdzenie po poprawkach |
|---|---|---|---|---|---|---|
| 1 | 21.11 | usługa AED, standard danych, frontend | FAIL | 1 krytyczne + 11 poważnych | 9 w PR #14 (`9c8ce56`); 3 frontendowe do potwierdzenia | nie było |
| 2 | 22.11 | PR #16: wykaz AED w portalu, zasilanie XML, wdrożenie pod domeną | – | 5 (2 × P1, 3 × P2) | 5 w `d4eec3b` | nie było |

**Po żadnej rundzie nie było przeglądu potwierdzającego.** Poprawki sprawdzają testy automatyczne dopisane razem z nimi. Codex nie oceniał ich drugi raz.

## Runda 1 (21.11) – usługa i standard danych

Werdykt FAIL: 1 znalezisko krytyczne i 11 poważnych. Które z nich było krytyczne, nie zachowało się w repozytorium. Poniżej poprawki z PR #14 w kolejności z opisu commita `9c8ce56`:

| # | Problem (odtworzony z poprawki) | Poprawka | Gdzie |
|---|---|---|---|
| 1 | z publicznych danych dało się odtworzyć numer seryjny (przez `zrodlo_id` i identyfikator nowych zgłoszeń) | nieprzejrzyste `zrodlo_id` i `id_aed` dla nowych zgłoszeń | `aed_service/app.py` |
| 2 | w Dockerze katalog zrzutu źródeł nie był zapisywalny, a błąd odświeżenia przerywał cały cykl | zapisywalny katalog; błąd odświeżenia nie przerywa cyklu | `aed_service/Dockerfile`, `app.py` |
| 3 | jeden link zarządcy na urządzenie | kilka ważnych linków na urządzenie, każdy ważny 90 dni | `aed_service/app.py` |
| 4 | potwierdzenie zarządcy nie przyjmowało dat ważności baterii i elektrod | daty przyjmowane i walidowane | `aed_service/app.py` |
| 5 | część przesłanych wartości omijała walidację, np. przy zgłoszeniu problemu | każda przesłana wartość jest walidowana, także przy `stan = problem` (błąd 422) | `aed_service/app.py` |
| 6 | potwierdzone zgłoszenie nie było porównywane z rekordami z importu | dopasowanie do rekordów z importu i kolejka przeglądu ministerstwa | `aed_service/app.py`, `aed_standard/dedup.py` (`find_candidates`) |
| 7 | rekordy, które zniknęły ze źródeł, zostawały w rejestrze | wycofanie (`wycofany`), z zabezpieczeniem przed błędnym przebiegiem mappera | `aed_service/app.py` |
| 8 | uszkodzony plik CSV powodował wyjątek | raport błędu na poziomie pliku | `aed_standard/validate.py` |
| 9 | deduplikacja przestrzenna mogła połączyć dwa urządzenia o różnych znanych numerach seryjnych | takich rekordów nigdy nie łączymy | `aed_standard/dedup.py` |

Testy dopisane w tym samym commicie: `tests/test_aed_service.py`, `tests/test_aed_standard.py`. Zmiany kontraktu opisano w `docs/api-aed.md`.

Trzy znaleziska frontendowe czekają na potwierdzenie w przeglądarce (`docs/TODO.md`, rozdział 1). Ich poprawki są w commicie `6b7dcda` (`fix: frontend`), nieodebranym:

- znalezisko 12: wyczyszczenie pola opcjonalnego na ekranie QR ma usuwać starą wartość;
- dostosowanie ekranów do zmian kontraktu z PR #14: skrzynka ministerstwa z wiadomością bez linku, ekran po zgłoszeniu problemu, krok „bateria i elektrody”;
- licznik `wycofano` w wynikach mappera i historii zadań, błąd 422 przy `stan = problem`, kilka ważnych linków zarządcy.

Dokładnego przypisania tych pozycji do numerów znalezisk 10–12 nie odtworzyliśmy. Z listy znalezisk zachował się tylko numer 12.

Później, poza przeglądem Codexa, sesja prowadząca poprawiła wyniki przeglądu rejestru źródeł (commit `838968e`): rekord ODbL nigdy nie jest głównym rekordem scalonej grupy, plik źródła nie może wstrzyknąć `id_aed` ani `kompletnosc`, rekordy z importu obok zgłoszonych urządzeń trafiają do kolejki przeglądu, a usługa korzysta tylko z publicznego API `aed_standard`.

## Runda 2 (22.11) – PR #16

| # | Waga | Znalezisko | Poprawka w `d4eec3b` | Gdzie |
|---|---|---|---|---|
| 1 | P1 | wdrożenie publiczne z dobrze znanymi hasłami kont demo – każdy z internetu wchodzi do panelu ministerstwa prototypu | hasło kont demo z `AED_DEMO_PASSWORD` (puste = znane hasła demo, decyzja przy wdrożeniu) | `aed_service/app.py`, `docker-compose.prod.yml`, `.env.example` |
| 2 | P1 | dane kontaktowe dysponenta w eksporcie krajowym (`datasets/out/aed_dane_gov_pl.csv`), podczas gdy eksport usługi je czyścił | jedna reguła dla wszystkich eksportów: `HIDDEN_PUBLIC` (`dysponent_email`, `dysponent_telefon`, `numer_seryjny`) | `aed_standard/build.py` |
| 3 | P2 | zbiór zbiorczy w portalu domyślnie na CC0, choć część wykazów jest na CC BY 4.0 | zbiór zbiorczy z warunkami licencji (źródło i przetworzenie), czyli CC BY 4.0 | `backend/mcod/aed/aed_utils.py` (`create_main_aed_dataset`) |
| 4 | P2 | kolizja zastępczych `id_aed` przy powtórzonym identyfikatorze w wykazie (zastępczy identyfikator mógł znowu się powtórzyć) | pętla do skutku z przyrostkiem `#n` i ostrzeżeniem w raporcie | `aed_standard/wykaz.py` |
| 5 | P2 | pobieranie wykazu z linku bez weryfikacji certyfikatu (portal dla DGA używa `verify=False`) | weryfikacja TLS; błąd certyfikatu to czytelny komunikat w raporcie scalania | `backend/mcod/aed/aed_utils.py` (`read_resource_bytes`) |

Stan po poprawkach: cały zestaw testów repozytorium przechodzi (75 testów, uruchomione 22.11 ok. 01:30 na gałęzi `feat/nocna-runda`, `838968e`; testów Django `backend/mcod/aed/tests/` w tym nie ma). Kodu Django nie uruchomiono w portalu, więc poprawki 3 i 5 sprawdzono tylko czytaniem kodu i kompilacją.

Skutek uboczny poprawki 1, który nie był częścią przeglądu: karty „Konta demonstracyjne” we frontendzie pokazują stałe hasła z `frontend/src/environments/environment.aed.ts`. Przy ustawionym `AED_DEMO_PASSWORD` podają więc złe hasło (`docs/wdrozenie-serwer.md`, sekcja 4).

## Co dalej

- Runda potwierdzająca po poprawkach z obu rund, najlepiej razem z przeglądem `docs/wdrozenie-serwer.md` i `backend/docker-compose.aed-domain.yml` (konfiguracja serwera publicznego nie była przeglądana).
- Zapisywać pełny raport Codexa w tym pliku od razu po przeglądzie.
