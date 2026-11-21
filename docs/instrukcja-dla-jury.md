# Instrukcja dla jury

Prototyp rozwiązania zadania „Misja AED – Dane na ratunek”. Instrukcja prowadzi przez uruchomienie, trzy ścieżki demonstracyjne (firma, zarządca, ministerstwo) oraz wskazuje, gdzie sprawdzić każde wymaganie i kryterium oceny z treści zadania. Wszystkie dane osobowe w prototypie są fikcyjne (domeny `.example`).

Stan zgodny z repozytorium na dzień 21.11.2026. Rzeczy, które jeszcze nie istnieją, zebrano na końcu w sekcji „Do uzupełnienia”.

## 1. Uruchomienie (jedna komenda)

Wymagany jest Docker (z Docker Compose).

1. Otwórz terminal w katalogu głównym repozytorium.
2. Uruchom: `docker compose up --build`. Pierwsza budowa trwa kilka minut (README). Usługa AED przy pierwszym starcie zakłada konta demo i importuje rejestr z `datasets/raw/` (kilka sekund, wg `aed_service/README.md`).
3. Gdy w terminalu usługi pojawi się gotowość, otwórz `http://localhost:8080/pl/aed`.
4. Zobaczysz żółty pasek „Prototyp hackathonowy HackNation 2026 – to nie jest serwis dane.gov.pl. Dane demonstracyjne.” i zakładki: Rejestr urządzeń, Panel firmy, Panel ministerstwa.
5. Inny port: zmienna `WEB_PORT` (domyślnie 8080). Zatrzymanie: `Ctrl+C`.
6. Reset danych: baza leży w wolumenie Dockera `aed-data`; wyczyść go poleceniem `docker compose down -v` [do sprawdzenia: nie testowano w tej sesji].

Uwagi:

- Strony portalu poza obszarem AED (np. „Dane”, „Dostawcy”) czytają tylko publiczne API dane.gov.pl, więc wymagają internetu. Nie loguj się tam kontami portalu (README). Obszar AED działa bez zewnętrznego API.
- Prototyp nie wysyła e-maili. Wiadomości do zarządców trafiają do skrzynki w panelu ministerstwa (`aed_service/README.md`, „Uwagi prototypu”).

### Konta demonstracyjne (dane fikcyjne, z `aed_service/README.md`)

| Rola | E-mail | Hasło |
|---|---|---|
| ministerstwo | `ministerstwo@aed.example` | `ministerstwo-demo` |
| firma (producent) | `pulsar@aed.example` | `pulsar-demo` |
| firma (sprzedawca) | `serwis@aed.example` | `serwis-demo` |

## 2. Trzy ścieżki demonstracyjne

### Ścieżka A. Firma (sprzedawca) zgłasza urządzenia

Pliki do wgrania: `wzorzec/przyklad-sprzedawca-bledy.csv` (10 wierszy, celowe błędy) i `wzorzec/przyklad-sprzedawca.csv` (10 wierszy poprawnych). Zrzut ekranu: `frontend/aed-zrzuty/02-panel-firmy.jpg`.

1. Wejdź na `http://localhost:8080/pl/aed` i kliknij zakładkę „Panel firmy”.
2. Zaloguj się: `serwis@aed.example` / `serwis-demo`. Pojawi się „Zalogowano: Serwis Rytm Sp. z o.o. (firma fikcyjna)”.
3. Rozwiń „Kolumny wymagane przy zgłoszeniu sprzedaży (8)”: to profil `sprzedaz` standardu. Możesz też pobrać pusty plik z nagłówkiem standardu.
4. W polu „Plik CSV z urządzeniami” wybierz `wzorzec/przyklad-sprzedawca-bledy.csv`. Do rejestru nic nie trafia, dopóki nie wyślesz zgłoszenia.
5. Sprawdź raport: wiersze w pliku 10, poprawne 2, do poprawy 8; tabela „Co poprawić w pliku” z numerem wiersza, kolumną, rodzajem (Błąd/Ostrzeżenie) i komunikatem po polsku. Spodziewane problemy (zgodne z walidatorem uruchomionym z linii poleceń): brak numeru seryjnego (wiersz 1), data `15.03.2024` zamiast `2024-03-15` (wiersz 2), termin elektrod minął, ostrzeżenie (wiersz 3), data produkcji z przyszłości (wiersz 4), wartość „otwarty” spoza słownika dostępu (wiersz 5), zamienione współrzędne (wiersz 6), duplikat numeru seryjnego (wiersz 8), zły adres e-mail (wiersz 9), przecinek dziesiętny (wiersz 10).
6. Wybierz teraz `wzorzec/przyklad-sprzedawca.csv`. Raport: 10 wierszy poprawnych, 0 błędów (walidator z linii poleceń: „plik poprawny”).
7. Kliknij „Wyślij zgłoszenie – poprawne wiersze: …”. Pojawi się „Zgłoszenie wysłane” i sekcja „Naklejki i linki dla dysponentów”.
8. Przy dowolnym urządzeniu kliknij „Naklejka z kodem QR (SVG)”. Otworzy się naklejka z kodem QR (`/api/aed/urzadzenia/{id_aed}/naklejka.svg`). Zapisz id urządzenia (`AED-…`).
9. Kliknij „Strona potwierdzenia dla dysponenta”: to początek ścieżki B.
10. Uwaga: ten sam plik wgrany drugi raz zgłosi duplikaty (te same pary producent + numer seryjny), więc nie tworzy nowych rekordów (`aed_service/README.md`, `docs/api-aed.md`).
11. Opcjonalnie: „Dodaj urządzenie” pojedynczo (formularz generowany ze schematu); [do sprawdzenia: nazwa i położenie przycisku w panelu firmy].

### Ścieżka B. Zarządca potwierdza miejsce (telefon lub komputer)

Zrzut ekranu: `frontend/aed-zrzuty/05-qr-dysponent-telefon.jpg`.

1. Otwórz link aktywacyjny: z kroku A9 albo w panelu ministerstwa w sekcji „Wiadomości do dysponentów” przez „Otwórz link dysponenta dla urządzenia AED-…” (to zastępuje e-mail). Adres ma postać `/aed/qr/{id_aed}?t=<token>`; token jest jednorazowym uprawnieniem zarządcy, sam skan kodu bez tokenu nie daje prawa edycji (`docs/api-aed.md`).
2. Strona pokazuje id urządzenia, producenta, model i status „Zgłoszony”, następnie „Potwierdź dane defibrylatora – trzy kroki, około minuty”.
3. Krok 1 z 3, „Gdzie znajduje się urządzenie”: kliknij „Użyj lokalizacji telefonu” albo rozwiń „Wpisz współrzędne ręcznie” (np. 52.229676 i 21.012229) i uzupełnij nazwę miejsca (wymagana), miejscowość i adres.
4. Krok 2 z 3, „Kto i kiedy ma dostęp”: wybierz „Całą dobę, we wszystkie dni” albo „W wybranych godzinach” (wpisz godziny).
5. Krok 3 z 3, „W jakim stanie jest urządzenie”: wybierz „Jest na miejscu i jest gotowe do użycia” (druga opcja: „Wymaga uwagi”).
6. Kliknij „Potwierdź dane”. Wynik: „Dane potwierdzone – urządzenie ma teraz status «aktywny»”, data potwierdzenia i kompletność danych w procentach.
7. Sprawdź w zakładce „Rejestr urządzeń”: filtr statusu „Aktywny” albo wyszukiwanie po nazwie miejsca; na liście widać status, dostęp, godziny i kompletność.
8. Powtórz kroki 2–6 samą klawiaturą (Tab, Spacja, Enter) i przy szerokości okna 320 px.
9. Strona QR otwarta bez tokenu `t` służy do zgłoszenia sygnału z miejsca (urządzenie jest, brakuje, uszkodzone, zamknięte); sygnał nie zmienia danych, trafia do dysponenta (`docs/api-aed.md`) [do sprawdzenia: wygląd formularza sygnału w UI].

### Ścieżka C. Ministerstwo prowadzi rejestr

Zrzut ekranu: `frontend/aed-zrzuty/04-panel-ministerstwa.jpg`.

1. Zakładka „Panel ministerstwa”; zaloguj się `ministerstwo@aed.example` / `ministerstwo-demo`.
2. „Stan rejestru”: liczba urządzeń, potwierdzone w ostatnich 90 dniach, firmy zgłaszające, średnia kompletność, tabele „według statusu” i „według źródła” (tekst i ikona przy każdym statusie).
3. „Możliwe duplikaty do przeglądu”: zestawienie pary rekordów (odległość w metrach, podobieństwo nazwy i adresu, kolumna „Zgodność”). Wybierz „To samo urządzenie – połącz”, „Różne urządzenia – zostaw oba” albo „Pomiń tę parę”. Po połączeniu zostaje rekord A, a B dostaje status „wycofany”.
4. „Zadania cykliczne”: „Uruchom przypomnienia” (prośby o potwierdzenie po 183 dniach bez weryfikacji, przypomnienia 60 dni przed końcem ważności baterii lub elektrod, status `nieaktualny` po 365 dniach; reguły w `aed_service/README.md`). Na świeżej bazie wynik to zwykle 0, bo nic nie jest jeszcze po terminie.
5. „Uruchom mapper źródeł”: ponownie czyta źródła, dokłada nowe rekordy i deduplikuje. Wynik na świeżej bazie: dodane 0, zmienione 0, połączone automatycznie 266, do ręcznego przeglądu 214 (te same liczby co w `datasets/out/raport.json`).
6. „Wiadomości do dysponentów”: skrzynka nadawcza (odbiorca, temat, treść, link, data) zamiast wysyłki e-mail.
7. Kliknij „Pobierz zbiór do publikacji na dane.gov.pl (CSV)”. Plik `aed_dane_gov_pl.csv` zawiera tylko rekordy gotowe do publikacji: bez rekordów znanych wyłącznie z OpenStreetMap (licencja ODbL), bez dostępu „prywatny”, bez fikcyjnych urządzeń demonstracyjnych i bez pól `numer_seryjny`, `dysponent_email`, `dysponent_telefon` (kolumny zostają, wartości puste; `aed_service/app.py`).

## 3. Dane maszynowo czytelne i wyniki przetwarzania

| Plik | Co zawiera |
|---|---|
| `datasets/out/aed_dane_gov_pl.csv` | zbiór do publikacji na dane.gov.pl: 781 rekordów, 38 kolumn (zgodnie ze schematem) |
| `datasets/out/aed_rejestr.csv`, `aed_rejestr.geojson` | rejestr krajowy po deduplikacji: 18 814 rekordów, wszystkie ze statusem `niepotwierdzony` (żaden nie ma jeszcze potwierdzenia zarządcy) |
| `datasets/out/duplikaty_do_przegladu.csv` | 214 par do ręcznego przeglądu (153 kandydatów, 61 konfliktów źródeł) |
| `datasets/out/raport.json` | statystyki: rekordy na źródło przed i po, połączenia, pokrycie pól, kompletność, powody wykluczeń z eksportu, `naprawy_danych` |
| `wzorzec/wzorzec-aed.xlsx` | wzorcowy zakres danych: arkusze Dane, Słownik pól, Słowniki, Mapowanie źródeł, Instrukcja |
| `wzorzec/przyklad-*.csv` | trzy przykładowe pliki (sprzedawca, sprzedawca z błędami, publikacja) |
| `aed_standard/schema.json` | źródło prawdy o strukturze: wersja 0.2.0, 38 pól, dwa profile wymagalności (`sprzedaz`: 8 pól, `publikacja`: 8 pól), reguła „status aktywny wymaga: dostęp, godziny dostępu, data weryfikacji” |

Z linii poleceń (Python 3, bez dodatkowych pakietów):

1. Budowa zbioru krajowego z surowych źródeł (ok. 2 s): `python3 -m aed_standard build`
2. Walidacja pliku firmy: `python3 -m aed_standard validate wzorzec/przyklad-sprzedawca-bledy.csv --profil sprzedaz`. Oczekiwane: „Wiersze danych: 10, poprawne: 2, błędy: 8, ostrzeżenia: 1”.
3. Plik poprawny: `python3 -m aed_standard validate wzorzec/przyklad-sprzedawca.csv --profil sprzedaz`. Oczekiwane: „plik poprawny”.
4. Profil publikacji: `python3 -m aed_standard validate wzorzec/przyklad-publikacja.csv --profil publikacja`. Oczekiwane: „plik poprawny”, 3 wiersze. Opcja `--json` daje wynik maszynowy.
5. Testy: `uv run --python 3.13 --with-requirements aed_service/requirements.txt --with xmlschema python -m unittest` (pliki `tests/test_aed_standard.py`, `tests/test_aed_service.py`, `tests/test_feed.py`; testy frontendu: `frontend/src/app/pages/aed/*.spec.ts`) [do sprawdzenia: wynik uruchomienia na maszynie jury].

6. Zasilanie XML dla harwestera dane.gov.pl (sekcja DATA SOURCES panelu portalu): `uv run --python 3.13 --with-requirements aed_service/requirements.txt python -m aed_service.feed --out wynik --url https://przyklad.gov.pl/aed`. Oczekiwane: w katalogu `wynik` pliki `zasilanie.xml` (XSD 1.13 portalu), `zasilanie.md5` i `aed_dane_gov_pl-<hash>.csv`.

## 4. Wymagania z treści zadania i gdzie je sprawdzić

### A. Wymagania formalne (sekcja 4 treści zadania)

| Wymaganie | Gdzie | Kroki |
|---|---|---|
| Szczegółowy opis i tytuł projektu | `README.md` | 1. Otwórz `README.md`. 2. Sprawdź opis działania i tabelę katalogów. Tytuł roboczy: „Misja AED – Dane na ratunek”; tytuł akcji: patrz „Do uzupełnienia”. |
| Prezentacja, min. 5 slajdów | konspekt: `docs/prezentacja-konspekt.md` (10 slajdów); plik prezentacji: patrz „Do uzupełnienia” | 1. Otwórz konspekt. 2. Policz slajdy (10). 3. Sprawdź nazwy zrzutów w katalogu `frontend/aed-zrzuty/`. |
| Dowody na realizację wymagań technicznych (zrzuty ekranu) | `frontend/aed-zrzuty/01-rejestr-lista.jpg`, `02-panel-firmy.jpg`, `03-rejestr-mapa.jpg`, `04-panel-ministerstwa.jpg`, `05-qr-dysponent-telefon.jpg` | 1. Otwórz każdy plik. 2. Porównaj z ekranami z sekcji 2. Zrzut portalu uruchomionego w całości: patrz „Do uzupełnienia”. |
| Opis funkcjonalności i kroki użytkownika | sekcja 2 tej instrukcji; slajd 4 konspektu | 1. Wykonaj ścieżki A, B, C. |
| Lista ograniczeń | slajd 9 konspektu; sekcja 6 tej instrukcji | 1. Przeczytaj listę. |
| Prototyp | `http://localhost:8080/pl/aed` po `docker compose up --build` (adres publiczny: patrz „Do uzupełnienia”) | 1. Wykonaj sekcję 1. 2. Wykonaj ścieżki A–C. |
| Plik z wzorcowym zakresem danych (xlsx) | `wzorzec/wzorzec-aed.xlsx` | 1. Otwórz w arkuszu kalkulacyjnym. 2. Karta „Dane”: nagłówek 38 kolumn. 3. „Słownik pól”: opis pól. 4. „Słowniki”: wartości dozwolone. 5. „Mapowanie źródeł”: skąd pochodzą pola. 6. „Instrukcja”: zasady wypełniania. |
| Kod źródłowy | całe repozytorium: `aed_standard/`, `aed_service/`, `frontend/src/app/pages/aed/`, `docker-compose.yml`, `scripts/` | 1. Otwórz `README.md`, tabela „Co jest w repozytorium”. 2. Sprawdź `aed_standard/schema.json` jako źródło prawdy. 3. Uruchom testy (sekcja 3, krok 5). |
| Logotyp w .jpg, .png, .pdf i formacie otwartym | patrz „Do uzupełnienia” (logo projektuje zespół); wymagania i warianty: `kampania/brief-logo.md` | po dostarczeniu: sprawdź pięć formatów i warianty kolor, mono, negatyw |
| Księga znaku w .pdf | patrz „Do uzupełnienia”; szkielet: `kampania/ksiega-znaku-szablon.md` | po dostarczeniu: sprawdź koncepcję 3–5 zdań, kolorystykę, pole ochronne, minimalną wielkość, niedozwolone użycia |

### B. Wymagania techniczne (sekcja 5)

| Wymaganie | Gdzie | Kroki |
|---|---|---|
| Format maszynowo czytelny dla udostępnianych danych (nie pdf, doc; wyjątek: logotyp i księga znaku) | `datasets/out/` (CSV, GeoJSON), `wzorzec/` (XLSX, CSV), eksport z panelu ministerstwa | 1. Sprawdź rozszerzenia plików w `datasets/out/`. 2. Otwórz `aed_dane_gov_pl.csv`: UTF-8, separator `,`, jeden wiersz nagłówka, daty `RRRR-MM-DD`, współrzędne w osobnych kolumnach `szerokosc_geograficzna` i `dlugosc_geograficzna` (kropka dziesiętna). 3. Pobierz ten sam plik z panelu ministerstwa (ścieżka C, krok 7). 4. Potwierdź, że żaden plik danych nie jest PDF ani DOC. |
| Zgodność z zasadami działania portalu dane.gov.pl | patrz sekcja 5 | patrz sekcja 5 |
| Zgodność z aktualną wersją WCAG | ekrany `/pl/aed`; zakładka AED korzysta z układu portalu (pasek kontrastu i rozmiaru czcionki w nagłówku) | 1. Przejdź ścieżki A–C samą klawiaturą (Tab, Shift+Tab, Enter, Spacja). 2. Sprawdź, że stan jest podany tekstem i ikoną (statusy „Aktywny”, „Niepotwierdzony”, „Zgłoszony” z ikoną). 3. Zwiększ czcionkę i przełącz kontrast w nagłówku portalu. Formalny audyt (np. axe, Lighthouse): [do sprawdzenia: nie znaleziono raportu w repozytorium]. |
| Responsywność (komputer i urządzenia mobilne) | `frontend/aed-zrzuty/05-qr-dysponent-telefon.jpg` (telefon), `02-panel-firmy.jpg` (komputer) | 1. Zawęź okno przeglądarki do 320 px albo otwórz prototyp na telefonie (adres sieci lokalnej komputera [do sprawdzenia: ustawienie `AED_BASE_URL` dla kodów QR]). 2. Sprawdź stronę potwierdzenia i listę rejestru. 3. Mapa jest dodatkiem do listy: wszystkie informacje z mapy są też na liście. |
| Zgodność z zasadami UX | ścieżki A–C | 1. Sprawdź jasny stan procesu (zgłoszony, aktywny, niepotwierdzony). 2. Sprawdź komunikaty walidatora po polsku (wiersz, kolumna, co poprawić). 3. Sprawdź, że nic nie trafia do rejestru bez wysłania zgłoszenia. |
| Użycie AI dozwolone pod warunkiem pracy autorskiej | `docs/uzycie-ai.md` | 1. Otwórz plik. 2. Sprawdź tabele „Co zrobił człowiek”, „Co powstało z użyciem AI” (z weryfikacją), „Czego AI nie robiło” i dziennik sesji. |

### C. Wymagania funkcjonalne (sekcje 2 i 3)

| Wymaganie | Gdzie | Kroki |
|---|---|---|
| Ogólnopolski, otwarty, możliwie aktualny zbiór | `datasets/out/aed_dane_gov_pl.csv`, panel ministerstwa | 1. Sprawdź liczbę wierszy (781). 2. Sprawdź kolumny `data_aktualizacji`, `data_weryfikacji`, `status`. 3. Uruchom przypomnienia i mapper (ścieżka C). |
| Dane z wielu rozproszonych źródeł ze wskazaniem referencyjnego zakresu | `datasets/raw/manifest.json`, `datasets/out/raport.json` (`rekordy_na_zrodlo`), kolumny `zrodlo`, `zrodlo_id`, `licencja` w CSV | 1. Otwórz manifest: źródło, identyfikator zbioru, licencja i data danych (m.in. Krosno 3624, Marki 4955, Przemyśl 4581, Legionowo 40593, API Warszawy, OpenAEDMap/OSM). 2. W `raport.json` sprawdź liczbę rekordów przed i po deduplikacji dla każdego źródła. 3. Zakres terytorialny: jedno źródło = jedna gmina, API Warszawy = Warszawa, OSM = cała Polska [do sprawdzenia: formalny opis zakresu w jednej tabeli]. |
| Integracja informacji od wszystkich dysponentów w jednym zbiorze | `raport.json` (`polaczenia`, `do_przegladu`), `duplikaty_do_przegladu.csv`, panel ministerstwa | 1. W `raport.json` sprawdź: 266 połączeń (reguły: odległość 151, odległość i podobieństwo 6, numer referencyjny Warszawy 109), 214 par do przeglądu. 2. W panelu ministerstwa przejrzyj parę duplikatów. 3. Zasada: dwa rekordy z tego samego źródła nie są nigdy łączone automatycznie. |
| Wzorcowy zakres danych, jednolity sposób udostępniania | `aed_standard/schema.json`, `wzorzec/wzorzec-aed.xlsx` | 1. Otwórz schemat, sprawdź pola z rozmowy z komisją: `id_aed`, `producent`, `model`, `numer_seryjny`, `data_produkcji`, `data_waznosci_elektrod`, `data_waznosci_baterii`, `szerokosc_geograficzna`, `dlugosc_geograficzna`, `godziny_dostepu`, `wprowadzajacy_typ`, `wprowadzajacy_nazwa`. 2. Uruchom walidator (sekcja 3, kroki 2–4). |
| Proces: sprzedawca → naklejka QR → zarządca → zbiór ministerstwa | prototyp | ścieżki A, B, C po kolei |
| Prośby o potwierdzenie i przypomnienia o terminach baterii i elektrod | panel ministerstwa, „Zadania cykliczne” i „Wiadomości do dysponentów” | 1. Ścieżka A: zgłoś urządzenia. 2. W skrzynce zobacz „Aktywacja urządzenia AED-…”. 3. „Uruchom przypomnienia”: na świeżych danych wynik 0, bo terminy z przykładu (bateria 2030) są odległe [do sprawdzenia: wywołanie pierwszych przypomnień wymaga rekordu z terminem w ciągu 60 dni]. |
| Zachęty dla dostawców | `kampania/zachety.md`; w prototypie: panel firmy, odznaka sprzedawcy i ranking | 1. Otwórz `kampania/zachety.md`. 2. W prototypie widać panel firmy i raport walidacji. Odznaka sprzedawcy i ranking są dostępne w API (`GET /api/aed/sprzedawcy`, progi w `aed_service/README.md`); osobnego widoku mapy sprzedawców w interfejsie nie znaleziono [do sprawdzenia]. |

### D. Akcja, logotyp i księga znaku

| Wymaganie | Gdzie | Kroki |
|---|---|---|
| Nazwa i hasło akcji | `kampania/nazwa-i-haslo.md` (kandydaci, kolizje, top 3) | wybór ostateczny: patrz „Do uzupełnienia” |
| Logotyp (proste, nowoczesne, kreatywne, potencjał promocyjny) | patrz „Do uzupełnienia” | po dostarczeniu: sprawdź czytelność przy 16 px i na naklejce |
| Księga znaku: kolorystyka, pole ochronne, minimalna wielkość, niedozwolone użycia, koncepcja 3–5 zdań | patrz „Do uzupełnienia”; szkielet w `kampania/ksiega-znaku-szablon.md` | po dostarczeniu: strony 2, 5, 6, 7, 10 |

### E. Kryteria oceny (sekcja 8)

| Kryterium (waga) | Gdzie szukać dowodów |
|---|---|
| Zgodność z zasadami działania portalu dane.gov.pl (30%) | sekcja 5 |
| Logotyp i hasło (25%) | sekcja D powyżej |
| Kreatywność i innowacyjność (15%) | ścieżki A–C: kanał sprzedawcy z walidacją, naklejka QR, potwierdzenie zarządcy, kompletność, deduplikacja z kolejką przeglądu; `kampania/zachety.md` |
| Zgodność z tematem wyzwania (15%) | sekcja C powyżej |
| Wzorcowy zakres danych (10%) | `wzorzec/wzorzec-aed.xlsx`, `aed_standard/schema.json` |
| Prezentacja (5%) | `docs/prezentacja-konspekt.md` oraz plik prezentacji (patrz „Do uzupełnienia”) |

## 5. Zgodność z zasadami dane.gov.pl: co pokazujemy

1. **Dostawca jest instytucją, nie obywatelem.** Zbiór krajowy ma publikować Ministerstwo jako dostawca; firmy raportują przez konta firmowe, a skan kodu QR bez tokenu zarządcy jest tylko sygnałem dla właściciela. Sprawdź: ścieżka B, krok 1 i 9; `docs/api-aed.md`, rozdział „Urządzenie i naklejka QR”.
2. **Reguły pliku CSV zgodne z portalem:** UTF-8, jeden wiersz nagłówka, współrzędne w osobnych kolumnach liczbowych (warunek wyświetlenia mapy), daty `RRRR-MM-DD`. Sprawdź: `datasets/out/aed_dane_gov_pl.csv` (sekcja 4B, pierwszy wiersz) oraz walidator w trybie `--profil publikacja`. Nazwy kolumn adresu zgodne ze zbiorem Legionowa (`CLAUDE.md`, rozdział „Standard danych”).
3. **Licencje źródeł są zachowane.** Kolumna `licencja` w każdym rekordzie (CC0 1.0, CC BY 4.0, ODbL 1.0). Rekordy z OpenStreetMap (ODbL) nie trafiają do eksportu: w `raport.json` pole `eksport_dane_gov_pl.powody_wykluczenia` ma 18 032 takich wykluczeń. Wymaga opinii prawnika (patrz sekcja 6).
4. **Prototyp używa portalu tylko do odczytu.** Strony poza obszarem AED pobierają dane z publicznego API dane.gov.pl; konta portalu są wyłączone w trybie prototypu (strona „portal-accounts” informuje o tym, `aed-prototype.ts`). Prototyp niczego nie publikuje na dane.gov.pl.
5. **Fork frontendu portalu.** Moduł AED to osobna ścieżka `frontend/src/app/pages/aed/` w forku frontendu portalu (nagłówek, stopka i nawigacja portalu). Backend portalu (`backend/`) pozostaje niezmieniony.
6. **Plan wdrożenia w backendzie portalu:** `docs/integracja-portal-backend.md`: wniosek z kodu, że portal pozwala firmie prywatnej wgrać zasób CSV po założeniu instytucji i konta; rekomendowany kształt integracji w 10 krokach (nowy typ instytucji wzorem typu `developer`, aplikacja `mcod/aed`, zadania cykliczne w Celery), każdy z szacunkiem godzin. To jest **plan, nie wdrożenie**: kod backendu portalu nie został zmieniony.
7. **Publikacja mechanizmem portalu (DATA SOURCES).** Rejestr wystawia `zasilanie.xml` zgodny z XSD 1.13 portalu, a harwester portalu codziennie pobiera go i aktualizuje zbiór „Defibrylatory AED w Polsce” instytucji „Ministerstwo Cyfryzacji”. Identyfikatory zbioru i zasobu są stałe, każda wersja CSV ma własną nazwę pliku, a stare wersje zostają. Sprawdzone na lokalnie uruchomionym portalu: `docs/integracja-portal-backend.md`, rozdział „Zasilanie XML przez harwester”.
8. Zrzut lokalnie uruchomionego portalu z opublikowanym zbiorem: patrz „Do uzupełnienia”.

## 6. Znane ograniczenia (skrót)

- Prototyp działa lokalnie w Dockerze; brak publicznego adresu.
- Wiadomości do zarządców trafiają do skrzynki w panelu, nie są wysyłane e-mailem.
- Pełna integracja z backendem portalu jest planem (`docs/integracja-portal-backend.md`), nie zbudowaną funkcją.
- Rekordy znane tylko z OSM (ODbL) są w rejestrze, ale poza eksportem do dane.gov.pl; wymaga to opinii prawnika.
- Żaden rekord zbioru krajowego zbudowanego z surowych źródeł nie ma jeszcze potwierdzenia zarządcy (wszystkie `niepotwierdzony`); status `aktywny` pojawia się dopiero po ścieżce B.
- Usługa AED jest serwerem demonstracyjnym: jednowątkowym, bez limitu prób logowania (`aed_service/README.md`).
- Audyt dostępności (WCAG): [do sprawdzenia].
- Numer seryjny nie jest publikowany w eksporcie; decyzja, czy ma być w zbiorze otwartym, jest otwarta (`CLAUDE.md`).
- Liczby w rejestrze zależą od stanu bazy: patrz uwaga poniżej.

**Uwaga o liczbach.** `datasets/out/raport.json` podaje 18 814 rekordów w rejestrze (z urządzeniami o dostępie „prywatny”), a panel ministerstwa w usłudze AED pokazuje ok. 15,8 tys. (zrzut `04-panel-ministerstwa.jpg`: 15 769). Różnica 3 048 odpowiada liczbie rekordów z dostępem „prywatny”, których usługa nie wystawia (kod `aed_service/app.py` filtruje `dostep != 'prywatny'`). Pozostałe kilka rekordów to dane demonstracyjne i zgłoszenia z prób. [do sprawdzenia: potwierdzić wyjaśnienie na świeżej bazie].

## Do uzupełnienia (rzeczy, których jeszcze nie ma)

| Brakuje | Gdzie ma trafić |
|---|---|
| Pliki logo (`.svg`, `.png`, `.jpg`, `.pdf` i warianty) | `kampania/logo/` [do ustalenia] |
| Księga znaku `.pdf` | `kampania/ksiega-znaku.pdf` [do ustalenia] |
| Ostateczna nazwa i hasło akcji | `kampania/nazwa-i-haslo.md` (decyzja zespołu) |
| Plik prezentacji (PDF lub link) | `docs/prezentacja.pdf` [do ustalenia]; konspekt jest gotowy |
| Publiczny adres prototypu (jeśli zostanie wystawiony) | sekcja 1 |
| Zrzuty lokalnie uruchomionego portalu dane.gov.pl z opublikowanym zbiorem (od kolegi) | `frontend/aed-zrzuty/` lub osobny katalog; sekcja 5, pkt 7 |
| Raport audytu dostępności i responsywności (WCAG 2.2) | np. `docs/dostepnosc.md`; sekcja 4B |
| Tytuł projektu (obecnie robocze: „Misja AED – Dane na ratunek”) | `README.md` |
| Adres repozytorium (jeśli ma być podany jury) | sekcja 4A |
