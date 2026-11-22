# Instrukcja dla jury

Prototyp rozwiązania zadania „Misja AED – Dane na ratunek”. Instrukcja prowadzi przez uruchomienie i cztery ścieżki demonstracyjne: wykaz AED w portalu, firma, zarządca, ministerstwo. Wskazuje też, gdzie sprawdzić każde wymaganie i kryterium oceny z treści zadania. Wszystkie dane osobowe w prototypie są fikcyjne (domeny `.example`).

Stan zgodny z repozytorium na dzień 22.11.2026. Rzeczy, które jeszcze nie istnieją, zebrano na końcu w sekcji „Do uzupełnienia”. Znacznik `[do sprawdzenia]` oznacza krok, którego nikt jeszcze nie przeszedł w przeglądarce. Ścieżki A–D i K przeszliśmy 22.11 w przeglądarce na usłudze AED uruchomionej lokalnie (bez Dockera), a ok. 02:00 jeszcze raz od zera na Dockerze (`docker compose down -v`, potem `docker compose up -d --build`; pierwsza budowa ok. 2,5 min na Macu M-series, gotowość usługi ok. 10 s później).

## 0. Adres publiczny (bez instalacji)

Pełny fork portalu z usługą AED ma działać pod domeną zespołu (`docs/wdrozenie-serwer.md`). [do uzupełnienia po wdrożeniu: adres]

| Co | Adres | Konto |
|---|---|---|
| prototyp AED | `https://<domena>/pl/aed` | konta demo z tabeli w sekcji 1; na serwerze hasło może być inne – przekażemy je osobno [do uzupełnienia] |
| portal z forka: zbiory, zbiór zbiorczy AED, tabela, mapa | `https://<domena>/pl` | bez logowania |
| wykaz AED do odczytu | `https://api.<domena>/aed-aggregated` | bez logowania |
| panel administracyjny portalu | `https://admin.<domena>` | konto redaktora przekazane osobno [do uzupełnienia] |

Wszystko, co służy do oceny, da się sprawdzić samym odczytem, bez logowania. Konto w panelu pozwala dodatkowo samodzielnie dodać wykaz (ścieżka W).

## 1. Uruchomienie lokalne (jedna komenda)

Wymagany jest Docker (z Docker Compose).

1. Otwórz terminal w katalogu głównym repozytorium.
2. Uruchom: `docker compose up --build`. Pierwsza budowa trwa kilka minut (README). Usługa AED przy pierwszym starcie zakłada konta demo i importuje rejestr z `datasets/raw/` (kilka sekund, wg `aed_service/README.md`).
3. Gdy w terminalu usługi pojawi się gotowość, otwórz `http://localhost:8080/pl/aed`.
4. Zobaczysz żółty pasek „Prototyp hackathonowy HackNation 2026 – to nie jest serwis dane.gov.pl. Dane demonstracyjne.” i zakładki: Start, Rejestr urządzeń, Panel firmy, Panel ministerstwa, Ranking firm, Konwerter.
5. Inny port: zmienna `WEB_PORT` (domyślnie 8080). Zatrzymanie: `Ctrl+C`.
6. Reset danych: baza leży w wolumenie Dockera `aed-data`; wyczyść go poleceniem `docker compose down -v` (sprawdzone 22.11: po ponownym `up` usługa zakłada konta demo i importuje rejestr od nowa).

Uwagi:

- Strony portalu poza obszarem AED (np. „Dane”, „Dostawcy”) czytają tylko publiczne API dane.gov.pl, więc wymagają internetu. Mapa zasobu działa w tym buildzie (sprawdzone 22.11 na Dockerze: `http://localhost:8080/pl/dataset/3624/resource/54632/map` – Krosno, znaczniki i kafelki mapy; zasób Legionowa na publicznym portalu ma tylko tabelę). Nie loguj się tam kontami portalu (README). Obszar AED działa bez zewnętrznego API.
- Prototyp nie wysyła e-maili. Wiadomości do zarządców trafiają do skrzynki w panelu ministerstwa (`aed_service/README.md`, „Uwagi prototypu”).

### Konta demonstracyjne (dane fikcyjne, z `aed_service/README.md`)

| Rola | E-mail | Hasło |
|---|---|---|
| ministerstwo | `ministerstwo@aed.example` | `ministerstwo-demo` |
| firma (producent) | `pulsar@aed.example` | `pulsar-demo` |
| firma (sprzedawca) | `serwis@aed.example` | `serwis-demo` |

## 2. Ścieżki demonstracyjne

### Ścieżka W. Wykaz AED w portalu (główny mechanizm)

Wymaga portalu z forka: adres z sekcji 0 albo lokalny stos według `docs/wykaz-aed-w-portalu.md`. Mechanizm odtwarza wykaz chronionych danych (DGA), który już działa w portalu. Porównanie element po elemencie: `docs/wykaz-dga-analiza.md`, tabela „Odpowiedniki dla AED”. Kod: `backend/mcod/aed/`, logika scalania: `aed_standard/wykaz.py`, test: `tests/test_wykaz.py`.

Bez logowania (odczyt):

1. Otwórz `https://api.<domena>/aed-aggregated`. Odpowiedź zawiera identyfikatory zbioru i zasobu zbiorczego oraz raport: które wykazy przyjęto, które odrzucono i dlaczego. Sprawdzone 22.11 w przeglądarce na lokalnym stosie (`http://localhost:8000/aed-aggregated`, zrzut `docs/zrzuty/portal-10-aed-aggregated-przegladarka.png`).
2. W portalu otwórz zbiór „Krajowy wykaz defibrylatorów AED – wykaz zbiorczy” (dostawca: Ministerstwo Cyfryzacji) i zasób „Krajowy wykaz AED”. Sprawdź poziom otwartości (3 gwiazdki), widok tabeli (781 rekordów, 40 stron po 20) i zakładkę „Mapa” (współrzędne i nazwa mają znaczniki mapy ustawione już przy tworzeniu zasobu). Strona zbioru, tabela i mapa sprawdzone 22.11 w przeglądarce na lokalnym stosie (zrzuty `portal-01`, `-06`, `-07`, `-08`); okno „Polityka prywatności i RODO” zamknij przyciskiem „Zamknij”. Pobrania CSV z karty zasobu nie sprawdzono (lokalnie odnośnik prowadzi pod `https://api.mcod.local`) [do sprawdzenia].
3. `https://api.<domena>/resources/<id zasobu>/data` – te same dane przez API portalu. [do sprawdzenia]
4. W pliku sprawdź: kolumny standardu, brak rekordów z OpenStreetMap (ODbL) i z dostępem prywatnym, puste `numer_seryjny`, `dysponent_email`, `dysponent_telefon`.

Z kontem redaktora (panel `https://admin.<domena>`):

5. Dodaj zasób w zbiorze swojej instytucji z plikiem `datasets/raw/dane_gov_pl/legionowo/resource_2625221.csv` i zaznacz „Wykaz AED: TAK”. Zapis przechodzi, bo plik Legionowa jest podzbiorem standardu (sprawdzone 22.11: dodanie `curl`em, a w przeglądarce edycja istniejącego zasobu z przełączeniem „NIE” → „TAK”). Formularz wymaga też zaznaczenia „Tak/Nie” w pięciu polach „Zawiera …” i wyboru zbioru.
6. To samo z `datasets/raw/dane_gov_pl/krosno/resource_54632.csv`. Formularz nie zapisze zasobu i pokaże błędy po polsku przy polu „Wykaz AED”, np. „Kolumna »Adres« nie występuje w standardzie”, z podpowiedzią właściwej nazwy kolumny (10 komunikatów; sprawdzone 22.11 w przeglądarce, zrzut `portal-03`). To samo przy edycji: przełączenie istniejącego zasobu z plikiem Krosna na „TAK” nie zapisuje zmiany.
7. Scalanie uruchamia harmonogram (codziennie 03:45) albo zespół poleceniem `manage.py create_main_aed_resource`. Nowy wykaz pojawi się w raporcie `/aed-aggregated` po najbliższym scalaniu. Gdy scalanie odrzuci wykaz albo przyjmie go częściowo, dostawca dostaje e-mail (adres do powiadomień zbioru, inaczej adres instytucji): liczba przyjętych i odrzuconych wierszy, do 10 problemów, link do zasobu w panelu. Wiadomość idzie tylko przy zmianie wyniku, a po naprawie przychodzi jedna wiadomość „przyjęty w całości”. Sprawdzone 22.11 na lokalnym stosie: wiadomość o odrzuconym wykazie Krosna w skrzynce testowej MailHog, zrzut `docs/zrzuty/portal-12-mail-odrzucony-wykaz.png`; ponowne scalanie bez zmian nie wysłało nic. Wiadomość „przyjęty w całości” sprawdzona tylko testem automatycznym.

### Zasilanie XML (drugi mechanizm portalu: harvester)

- Adres: `https://<domena>/api/aed/eksport/dane-gov-pl.xml`, suma kontrolna `…/dane-gov-pl.md5`. Plik jest zgodny z XSD harvestera 1.13 (`backend/data/harvester/xml_import_otwarte_dane_1_13.xsd`); sprawdza to test `tests/test_aed_service.py::HarvesterFeedTest`.
- Kroki w panelu (źródło danych typu XML, „Sprawdź poprawność pliku”, import): `docs/panel-portalu-krok-po-kroku.md`, rozdział 3. [do sprawdzenia]

### Rejestr źródeł (stan początkowy z istniejących danych)

- `aed_standard/sources.json` opisuje każde źródło: plik, mapowanie kolumn, priorytet i licencję. Nowa gmina to jeden wpis (`docs/dodawanie-zrodla.md`).
- Wynik dla każdego źródła (przed i po deduplikacji, pominięte źródła, błędy źródeł): `datasets/out/raport.json`, klucze `rekordy_na_zrodlo`, `pominiete_zrodla`, `bledy_zrodel`.

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
11. Opcjonalnie: link „Zgłoś jedno urządzenie formularzem” na dole panelu firmy (pod „Co dzieje się po zgłoszeniu”) otwiera formularz pojedynczego urządzenia generowany ze schematu.

### Ścieżka B. Zarządca potwierdza miejsce (telefon lub komputer)

Zrzut ekranu: `frontend/aed-zrzuty/05-qr-dysponent-telefon.jpg`.

1. Otwórz link aktywacyjny: z kroku A9 albo w panelu ministerstwa w sekcji „Wiadomości do dysponentów” przez „Otwórz link dysponenta dla urządzenia AED-…” (to zastępuje e-mail). Adres ma postać `/pl/aed/qr/{id_aed}?t=<token>`; token jest jednorazowym uprawnieniem zarządcy, sam skan kodu bez tokenu nie daje prawa edycji (`docs/api-aed.md`).
2. Strona pokazuje id urządzenia, producenta, model i status „Zgłoszony”, następnie „Potwierdź dane defibrylatora – trzy kroki, około minuty”.
3. Krok 1 z 3, „Gdzie znajduje się urządzenie”: kliknij „Użyj lokalizacji telefonu” albo rozwiń „Wpisz współrzędne ręcznie” (np. 52.229676 i 21.012229) i uzupełnij nazwę miejsca (wymagana), miejscowość i adres.
4. Krok 2 z 3, „Kto i kiedy ma dostęp”: wybierz dostęp (np. „Publiczny”), a w „Godziny dostępu” – „Całą dobę, we wszystkie dni” albo „W wybranych dniach i godzinach” (zaznacz np. „Dni robocze (poniedziałek–piątek)” i wpisz godziny od–do).
5. Krok 3 z 3, „W jakim stanie jest urządzenie”: wybierz „Jest na miejscu i jest gotowe do użycia” (druga opcja: „Wymaga uwagi”).
6. Kliknij „Potwierdź dane”. Wynik: „Dane potwierdzone – urządzenie ma teraz status «aktywny»”, data potwierdzenia i kompletność danych w procentach.
7. Sprawdź w zakładce „Rejestr urządzeń”: filtr statusu „Aktywny” albo wyszukiwanie po nazwie miejsca; na liście widać status, dostęp, godziny i kompletność.
8. Powtórz kroki 2–6 samą klawiaturą (Tab, Spacja, Enter) i przy szerokości okna 320 px.
9. Strona QR otwarta bez tokenu `t` służy do zgłoszenia sygnału z miejsca (urządzenie jest, brakuje, uszkodzone, zamknięte); sygnał nie zmienia danych, trafia do dysponenta (`docs/api-aed.md`). Formularz „Co widzisz przy tym defibrylatorze”: cztery odpowiedzi do wyboru, uwagi, opcjonalna lokalizacja telefonu, „Wyślij zgłoszenie”. Wiadomość „Zgłoszenie osoby postronnej” pojawia się w skrzynce panelu ministerstwa.

### Ścieżka C. Ministerstwo prowadzi rejestr

Zrzut ekranu: `frontend/aed-zrzuty/04-panel-ministerstwa.jpg`.

1. Zakładka „Panel ministerstwa”; zaloguj się `ministerstwo@aed.example` / `ministerstwo-demo`.
2. „Stan rejestru”: liczba urządzeń, potwierdzone w ostatnich 90 dniach, firmy zgłaszające, średnia kompletność, tabele „według statusu” i „według źródła” (tekst i ikona przy każdym statusie).
3. „Możliwe duplikaty do przeglądu”: na świeżej bazie „Para 1 z 195”; zestawienie pary rekordów (odległość w metrach, podobieństwo nazwy i adresu, kolumna „Zgodność”). Wybierz „To samo urządzenie – połącz”, „Różne urządzenia – zostaw oba” albo „Pomiń tę parę”. Po połączeniu zostaje rekord A, a B dostaje status „wycofany”.
4. „Zadania cykliczne”: „Uruchom przypomnienia” (prośby o potwierdzenie po 183 dniach bez weryfikacji, przypomnienia 60 dni przed końcem ważności baterii lub elektrod, status `nieaktualny` po 365 dniach; reguły w `aed_service/README.md`). Wynik zależy od danych demonstracyjnych; na świeżej bazie (22.11, Docker) było: prośby o potwierdzenie 1, przypomnienia o terminach 1, nieaktualne 0.
5. „Uruchom mapper źródeł”: ponownie czyta źródła, dokłada nowe rekordy i deduplikuje. Wynik na bazie po pierwszym imporcie (22.11, Docker): dodane 0, zmienione 0, połączone automatycznie 266, wycofane 0 (jak w `datasets/out/raport.json`), do ręcznego przeglądu 0 – pary z pierwszego importu są już w kolejce z kroku 3, a ta liczba obejmuje tylko nowe pary.
6. „Wiadomości do dysponentów”: skrzynka nadawcza (odbiorca, temat, treść, link, data) zamiast wysyłki e-mail.
7. Kliknij „Pobierz zbiór do publikacji na dane.gov.pl (CSV)”. Plik `aed_dane_gov_pl.csv` zawiera tylko rekordy gotowe do publikacji: bez rekordów znanych wyłącznie z OpenStreetMap (licencja ODbL), bez dostępu „prywatny”, bez fikcyjnych urządzeń demonstracyjnych i bez pól `numer_seryjny`, `dysponent_email`, `dysponent_telefon` (kolumny zostają, wartości puste; `aed_service/app.py`).

### Ścieżka D. Ministerstwo zaprasza dysponenta do przejęcia punktu

Zrzut ekranu: `docs/zrzuty/09-przejecie-punktu.png`.

1. Panel ministerstwa (konto ministerstwa), sekcja „Zaproś dysponenta do przejęcia punktu”. W polu „Identyfikator urządzenia” wpisz id rekordu znanego tylko z OpenStreetMap (np. z rejestru, filtr „Niepotwierdzony”, źródło `openstreetmap`), opcjonalnie e-mail instytucji, i kliknij „Wystaw link dysponenta”. Pojawi się „Link dla urządzenia AED-… jest ważny 90 dni” i pole „Link do skopiowania”; przy podanym e-mailu wiadomość trafia do skrzynki.
2. Otwórz link. Ekran QR pokazuje komunikat „Ten punkt znaleźliśmy w otwartej mapie (OpenStreetMap). Nie przepisujemy z niej danych…” i pusty formularz (nazwa, współrzędne, adres, dostęp, godziny). Jest też sekcja „Kontakt do dysponenta”.
3. Uzupełnij nazwę, współrzędne, miejscowość, dostęp, godziny i stan, kliknij „Potwierdź dane”. Wynik: status „aktywny”.
4. W panelu ministerstwa pobierz zbiór CSV (kroki 1–4 sprawdzone 22.11 na Dockerze): rekord ma `status = aktywny`, `licencja = CC0 1.0`, `zrodlo = zgloszenie`, `wprowadzajacy_typ = dysponent`, w `powiazane_zrodla` tylko odnośnik `openstreetmap:node/…`; kontakt dysponenta jest pusty.
5. To samo dla rekordu ze zbioru miejskiego bez kontaktu (np. Krosno, źródło `dane.gov.pl/3624`): formularz ma wypełnione dane położenia ze źródła i sekcję „Kontakt do dysponenta”; po potwierdzeniu rekord zostaje przy źródle i licencji zbioru miejskiego, a podany e-mail zapisuje się w rejestrze (w eksporcie pusty). [do sprawdzenia na Dockerze]

### Ścieżka K. Konwerter pliku dostawcy do standardu (bez logowania)

Zrzuty ekranu: `docs/zrzuty/07-konwerter-mapowanie.png`, `docs/zrzuty/08-konwerter-wynik.png`.

1. Na stronie startowej `/pl/aed` kliknij „Konwerter do standardu AED” (adres `/pl/aed/konwerter`).
2. Krok 1 z 3: wybierz `datasets/raw/dane_gov_pl/krosno/resource_54632.csv`. Krok 2 z 3 pokazuje plik, format (CSV, przecinek), kodowanie (UTF-8), 21 wierszy i tabelę „Kolumny pliku i pola standardu” z propozycjami (np. „Lokalizacja” → „Nazwa miejsca”, „Adres” → „Adres w jednym polu”, kolumna „Nazwa” pominięta).
3. Kliknij „Przekształć plik do standardu”. Krok 3 z 3: „Wykaz jest zgodny ze standardem”, wiersze 21, poprawne 21, odrzucone 0, średnia kompletność 32,4% (kroki 1–3 sprawdzone 22.11 na Dockerze). „Pobierz wykaz w standardzie (CSV)” zapisuje plik `resource_54632-wykaz-aed.csv` z kolumnami standardu (kolumny systemowe – status, źródło, licencja – zostają puste; uzupełnia je portal przy wczytaniu wykazu).
4. Plik Marek `datasets/raw/dane_gov_pl/marki/resource_68353.csv` ma zamienione nagłówki współrzędnych: konwerter proponuje przypisanie według wartości (kolumna „Długość geograficzna” → szerokość) i informuje o rozpakowaniu wierszy w cudzysłowach; wynik: 8 z 8 poprawnych.
5. Błędy [do sprawdzenia: konwerter czyta już także XLSX, więc komunikat o formatach się zmienił]: plik `.xlsx` – „Przyjmujemy pliki: .csv, .geojson, .json.”; pusty plik – „Plik jest pusty.”; plik większy niż 5 MB – „Plik jest większy niż 5 MB. Podziel go na mniejsze części.”

## 3. Dane maszynowo czytelne i wyniki przetwarzania

| Plik | Co zawiera |
|---|---|
| `datasets/out/aed_dane_gov_pl.csv` | zbiór do publikacji na dane.gov.pl: 781 rekordów, 38 kolumn (zgodnie ze schematem) |
| `datasets/out/aed_rejestr.csv`, `aed_rejestr.geojson` | rejestr krajowy po deduplikacji: 18 814 rekordów, wszystkie ze statusem `niepotwierdzony` (żaden nie ma jeszcze potwierdzenia zarządcy) |
| `datasets/out/duplikaty_do_przegladu.csv` | 195 par do ręcznego przeglądu (148 kandydatów, 47 konfliktów źródeł) |
| `datasets/out/raport.json` | statystyki: rekordy na źródło przed i po, połączenia, pokrycie pól, kompletność, powody wykluczeń z eksportu, `naprawy_danych` |
| `wzorzec/wzorzec-aed.xlsx` | wzorcowy zakres danych: arkusze Dane, Słownik pól, Słowniki, Mapowanie źródeł, Instrukcja |
| `wzorzec/przyklad-*.csv` | trzy przykładowe pliki (sprzedawca, sprzedawca z błędami, publikacja) |
| `aed_standard/schema.json` | źródło prawdy o strukturze: wersja 0.2.0, 38 pól, dwa profile wymagalności (`sprzedaz`: 8 pól, `publikacja`: 8 pól), reguła „status aktywny wymaga: dostęp, godziny dostępu, data weryfikacji” |

Z linii poleceń (Python 3, bez dodatkowych pakietów):

1. Budowa zbioru krajowego z surowych źródeł (ok. 2 s): `python3 -m aed_standard build`
2. Walidacja pliku firmy: `python3 -m aed_standard validate wzorzec/przyklad-sprzedawca-bledy.csv --profil sprzedaz`. Oczekiwane: „Wiersze danych: 10, poprawne: 2, błędy: 8, ostrzeżenia: 1”.
3. Plik poprawny: `python3 -m aed_standard validate wzorzec/przyklad-sprzedawca.csv --profil sprzedaz`. Oczekiwane: „plik poprawny”.
4. Profil publikacji: `python3 -m aed_standard validate wzorzec/przyklad-publikacja.csv --profil publikacja`. Oczekiwane: „plik poprawny”, 3 wiersze. Opcja `--json` daje wynik maszynowy.
5. Testy: `uv run --python 3.13 --with-requirements aed_service/requirements.txt python -m unittest` (pliki `tests/test_aed_standard.py`, `tests/test_aed_service.py`; testy frontendu: `frontend/src/app/pages/aed/*.spec.ts`) [do sprawdzenia: wynik uruchomienia na maszynie jury].

## 4. Wymagania z treści zadania i gdzie je sprawdzić

### A. Wymagania formalne (sekcja 4 treści zadania)

| Wymaganie | Gdzie | Kroki |
|---|---|---|
| Szczegółowy opis i tytuł projektu | `docs/opis-projektu.md`, `README.md` | 1. Otwórz `docs/opis-projektu.md`: tytuł roboczy, opis szczegółowy, wersja krótka. 2. W `README.md` sprawdź opis dwóch kanałów i tabelę katalogów. Nazwa akcji: patrz „Do uzupełnienia”. |
| Prezentacja, min. 5 slajdów | konspekt: `docs/prezentacja-konspekt.md` (12 slajdów); plik prezentacji: patrz „Do uzupełnienia” | 1. Otwórz konspekt. 2. Policz slajdy (12). 3. Sprawdź nazwy zrzutów w katalogu `frontend/aed-zrzuty/` i listę zrzutów z portalu na końcu konspektu. |
| Dowody na realizację wymagań technicznych (zrzuty ekranu) | `frontend/aed-zrzuty/` (zrzuty 01–18 prototypu AED, wersje 320 px, tryby kontrastu, wyniki axe) | 1. Otwórz pliki. 2. Porównaj z ekranami z sekcji 2. Zrzuty portalu z forka (wykaz AED, tabela, mapa, panel): `docs/zrzuty/portal-*.png`, opis w sekcji 5, pkt 7. |
| Opis funkcjonalności i kroki użytkownika | sekcja 2 tej instrukcji; slajdy 5 i 7 konspektu | 1. Wykonaj ścieżki W, A, B, C. |
| Lista ograniczeń | slajd 10 konspektu; sekcja 6 tej instrukcji | 1. Przeczytaj listę. |
| Prototyp | adres publiczny z sekcji 0 albo `http://localhost:8080/pl/aed` po `docker compose up --build` | 1. Wykonaj sekcję 0 albo 1. 2. Wykonaj ścieżki W i A–C. |
| Plik z wzorcowym zakresem danych (xlsx) | `wzorzec/wzorzec-aed.xlsx` | 1. Otwórz w arkuszu kalkulacyjnym. 2. Karta „Dane”: nagłówek 38 kolumn. 3. „Słownik pól”: opis pól. 4. „Słowniki”: wartości dozwolone. 5. „Mapowanie źródeł”: skąd pochodzą pola. 6. „Instrukcja”: zasady wypełniania. |
| Kod źródłowy | całe repozytorium: `aed_standard/`, `aed_service/`, `backend/mcod/aed/` (wykaz AED w forku portalu), `frontend/src/app/pages/aed/`, `docker-compose*.yml`, `scripts/` | 1. Otwórz `README.md`, tabela „Co jest w repozytorium”. 2. Sprawdź `aed_standard/schema.json` jako źródło prawdy. 3. Uruchom testy (sekcja 3, krok 5). |
| Logotyp w .jpg, .png, .pdf i formacie otwartym | patrz „Do uzupełnienia” (logo projektuje zespół); wymagania i warianty: `kampania/brief-logo.md` | po dostarczeniu: sprawdź pięć formatów i warianty kolor, mono, negatyw |
| Księga znaku w .pdf | patrz „Do uzupełnienia”; szkielet: `kampania/ksiega-znaku-szablon.md` | po dostarczeniu: sprawdź koncepcję 3–5 zdań, kolorystykę, pole ochronne, minimalną wielkość, niedozwolone użycia |

### B. Wymagania techniczne (sekcja 5)

| Wymaganie | Gdzie | Kroki |
|---|---|---|
| Format maszynowo czytelny dla udostępnianych danych (nie pdf, doc; wyjątek: logotyp i księga znaku) | `datasets/out/` (CSV, GeoJSON), `wzorzec/` (XLSX, CSV), eksport z panelu ministerstwa | 1. Sprawdź rozszerzenia plików w `datasets/out/`. 2. Otwórz `aed_dane_gov_pl.csv`: UTF-8, separator `,`, jeden wiersz nagłówka, daty `RRRR-MM-DD`, współrzędne w osobnych kolumnach `szerokosc_geograficzna` i `dlugosc_geograficzna` (kropka dziesiętna). 3. Pobierz ten sam plik z panelu ministerstwa (ścieżka C, krok 7). 4. Potwierdź, że żaden plik danych nie jest PDF ani DOC. |
| Zgodność z zasadami działania portalu dane.gov.pl | sekcja 5; ścieżka W | patrz sekcja 5 |
| Zgodność z aktualną wersją WCAG | ekrany `/pl/aed`; zakładka AED korzysta z układu portalu (pasek kontrastu i rozmiaru czcionki w nagłówku) | 1. Przejdź ścieżki A–C samą klawiaturą (Tab, Shift+Tab, Enter, Spacja). 2. Sprawdź, że stan jest podany tekstem i ikoną (statusy „Aktywny”, „Niepotwierdzony”, „Zgłoszony” z ikoną). 3. Zwiększ czcionkę i przełącz kontrast w nagłówku portalu. 4. Wyniki testu automatycznego (axe-core 4.10.2, reguły WCAG 2.2 AA), przejścia klawiaturą, 320 px i trybów kontrastu: `frontend/aed-zrzuty/DOSTEPNOSC.md` i pliki `axe-4.10.2-*.json`. Bez czytnika ekranu i prawdziwego telefonu (opisane w tym pliku). [do sprawdzenia: powtórzenie na serwerze] |
| Responsywność (komputer i urządzenia mobilne) | `frontend/aed-zrzuty/05-qr-dysponent-telefon.jpg` (telefon), `02-panel-firmy.jpg` (komputer) | 1. Zawęź okno przeglądarki do 320 px albo otwórz prototyp na telefonie (adres sieci lokalnej komputera [do sprawdzenia: ustawienie `AED_BASE_URL` dla kodów QR]). 2. Sprawdź stronę potwierdzenia i listę rejestru. 3. Mapa jest dodatkiem do listy: wszystkie informacje z mapy są też na liście. |
| Zgodność z zasadami UX | ścieżki A–C | 1. Sprawdź jasny stan procesu (zgłoszony, aktywny, niepotwierdzony). 2. Sprawdź komunikaty walidatora po polsku (wiersz, kolumna, co poprawić). 3. Sprawdź, że nic nie trafia do rejestru bez wysłania zgłoszenia. |
| Użycie AI dozwolone pod warunkiem pracy autorskiej | `docs/uzycie-ai.md` | 1. Otwórz plik. 2. Sprawdź tabele „Co zrobił człowiek”, „Co powstało z użyciem AI” (z weryfikacją), „Czego AI nie robiło” i dziennik sesji. |

### C. Wymagania funkcjonalne (sekcje 2 i 3)

| Wymaganie | Gdzie | Kroki |
|---|---|---|
| Ogólnopolski, otwarty, możliwie aktualny zbiór | `datasets/out/aed_dane_gov_pl.csv`, panel ministerstwa | 1. Sprawdź liczbę wierszy (781). 2. Sprawdź kolumny `data_aktualizacji`, `data_weryfikacji`, `status`. 3. Uruchom przypomnienia i mapper (ścieżka C). |
| Dane z wielu rozproszonych źródeł ze wskazaniem referencyjnego zakresu | `aed_standard/sources.json` (rejestr źródeł), `datasets/raw/manifest.json`, `datasets/out/raport.json` (`rekordy_na_zrodlo`), kolumny `zrodlo`, `zrodlo_id`, `licencja` w CSV; w portalu: każdy wykaz AED to osobne źródło z nazwą dostawcy | 1. Otwórz manifest: źródło, identyfikator zbioru, licencja i data danych (m.in. Krosno 3624, Marki 4955, Przemyśl 4581, Legionowo 40593, API Warszawy, OpenAEDMap/OSM). 2. W `raport.json` sprawdź liczbę rekordów przed i po deduplikacji dla każdego źródła. 3. Zakres terytorialny: jedno źródło = jedna gmina, API Warszawy = Warszawa, OSM = cała Polska [do sprawdzenia: formalny opis zakresu w jednej tabeli]. |
| Integracja informacji od wszystkich dysponentów w jednym zbiorze | wykaz AED w portalu (ścieżka W): scalanie wykazów wielu dostawców w zasób zbiorczy ministerstwa; `raport.json` (`polaczenia`, `do_przegladu`), `duplikaty_do_przegladu.csv`, panel ministerstwa | 0. Ścieżka W, kroki 1–2 (`/aed-aggregated`, zasób zbiorczy). 1. W `raport.json` sprawdź: 266 połączeń (reguły: odległość 151, odległość i podobieństwo 6, numer referencyjny Warszawy 109), 195 par do przeglądu. 2. W panelu ministerstwa przejrzyj parę duplikatów. 3. Zasada: dwa rekordy z tego samego źródła nie są nigdy łączone automatycznie. |
| Wzorcowy zakres danych, jednolity sposób udostępniania | `aed_standard/schema.json`, `wzorzec/wzorzec-aed.xlsx` | 1. Otwórz schemat, sprawdź pola z rozmowy z komisją: `id_aed`, `producent`, `model`, `numer_seryjny`, `data_produkcji`, `data_waznosci_elektrod`, `data_waznosci_baterii`, `szerokosc_geograficzna`, `dlugosc_geograficzna`, `godziny_dostepu`, `wprowadzajacy_typ`, `wprowadzajacy_nazwa`. 2. Uruchom walidator (sekcja 3, kroki 2–4). |
| Proces: sprzedawca → naklejka QR → zarządca → zbiór ministerstwa | prototyp; wykaz ministerstwa w portalu | ścieżki A, B, C po kolei; potem ścieżka W, krok 1: eksport usługi jest wykazem ministerstwa (link) [do sprawdzenia] |
| Prośby o potwierdzenie i przypomnienia o terminach baterii i elektrod | panel ministerstwa, „Zadania cykliczne” i „Wiadomości do dysponentów” | 1. Ścieżka A: zgłoś urządzenia. 2. W skrzynce zobacz „Aktywacja urządzenia AED-…”. 3. „Uruchom przypomnienia”: urządzenia z plików przykładowych mają odległe terminy (bateria 2030); na bazie z danymi demonstracyjnymi w przebiegu 22.11 wynik: prośby o potwierdzenie 1, przypomnienia o terminach 1, a w skrzynce pojawia się „Prośba o potwierdzenie danych”. |
| Zachęty dla dostawców | `kampania/zachety.md`; w prototypie: panel firmy, ranking firm z odznaką (`/pl/aed/sellers`, zrzut `frontend/aed-zrzuty/06-ranking-firm.jpg`) | 1. Otwórz `kampania/zachety.md`. 2. Otwórz zakładkę „Ranking firm”: tabela „Ranking firm według średniej kompletności danych” (urządzenia, średnia kompletność, potwierdzone, odznaka) i mapa siedzib; próg odznaki opisany na stronie (kompletność ≥ 70% i ≥ 50% potwierdzonych), te same dane w API `GET /api/aed/sprzedawcy`. |

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
| Kreatywność i innowacyjność (15%) | wykaz AED z publicznym raportem przyjętych i odrzuconych wykazów (ścieżka W); ścieżki A–C: kanał sprzedawcy z walidacją, naklejka QR, potwierdzenie zarządcy, kompletność, deduplikacja z kolejką przeglądu; `kampania/zachety.md` |
| Zgodność z tematem wyzwania (15%) | sekcja C powyżej; ścieżka W |
| Wzorcowy zakres danych (10%) | `wzorzec/wzorzec-aed.xlsx`, `aed_standard/schema.json` |
| Prezentacja (5%) | `docs/prezentacja-konspekt.md` oraz plik prezentacji (patrz „Do uzupełnienia”) |

## 5. Zgodność z zasadami dane.gov.pl: co pokazujemy

0. **Dane są zasobami w portalu, scalanymi mechanizmem portalu.** Dostawcy publikują wykazy AED jako zwykłe zasoby w swoich zbiorach; portal waliduje je przy zapisie i scala w zasób zbiorczy w zbiorze ministerstwa – tak jak robi to dziś z wykazem chronionych danych (DGA). Sprawdź: ścieżka W; `docs/wykaz-dga-analiza.md` (odwołania `plik:linia` do kodu portalu).
1. **Dostawca jest instytucją, nie obywatelem.** Zbiór krajowy ma publikować Ministerstwo jako dostawca; firmy raportują przez konta firmowe, a skan kodu QR bez tokenu zarządcy jest tylko sygnałem dla właściciela. Sprawdź: ścieżka B, krok 1 i 9; `docs/api-aed.md`, rozdział „Urządzenie i naklejka QR”.
2. **Reguły pliku CSV zgodne z portalem:** UTF-8, jeden wiersz nagłówka, współrzędne w osobnych kolumnach liczbowych (warunek wyświetlenia mapy), daty `RRRR-MM-DD`. Sprawdź: `datasets/out/aed_dane_gov_pl.csv` (sekcja 4B, pierwszy wiersz) oraz walidator w trybie `--profil publikacja`. Nazwy kolumn adresu zgodne ze zbiorem Legionowa (`CLAUDE.md`, rozdział „Standard danych”).
3. **Licencje źródeł są zachowane.** Kolumna `licencja` w każdym rekordzie (CC0 1.0, CC BY 4.0, ODbL 1.0). Rekordy z OpenStreetMap (ODbL) nie trafiają do eksportu: w `raport.json` pole `eksport_dane_gov_pl.powody_wykluczenia` ma 18 032 takich wykluczeń. Wymaga opinii prawnika (patrz sekcja 6).
4. **Prototyp niczego nie publikuje na produkcyjnym dane.gov.pl.** W lekkim wariancie (`docker compose up`) strony poza obszarem AED czytają publiczne API dane.gov.pl tylko do odczytu; w wariancie pod domeną czytają portal z forka. Logowanie do kont portalu we frontendzie jest wyłączone w trybie prototypu (`aed-prototype.ts`).
5. **Zmiany w kodzie portalu są małe i wydzielone.** Frontend: moduł `frontend/src/app/pages/aed/`. Backend: aplikacja `backend/mcod/aed/` (walidacja wykazu, scalanie, zadanie Celery, widok `/aed-aggregated`, polecenie `create_main_aed_resource`) oraz pole zasobu `contains_aed_list` (model, formularz, migracja `resources/0076`). Lista zmienionych plików: `docs/wykaz-dga-analiza.md`, koniec dokumentu.
6. **Stan uruchomienia:** kod wykazu AED w portalu był kompilowany, a jego logika (`aed_standard/wykaz.py`) przechodzi testy na prawdziwych plikach (`tests/test_wykaz.py`); 22.11 uruchomiono go lokalnie w pełnym stosie forka (Docker na Macu): migracje, 8 testów AED i 148 testów regresji DGA, panelu i Celery, scalanie przez Celery, zasób zbiorczy 781 wierszy z tabelą i mapą we frontendzie, `/aed-aggregated` (`docs/wykaz-aed-w-portalu.md`, „Co sprawdzono”). Nie uruchomiono go na serwerze publicznym; harmonogram 03:45 nie był sprawdzony (zadanie uruchamiano ręcznie). Dalsze kroki integracji (np. nowy typ instytucji dla firm AED): `docs/integracja-portal-backend.md`.
7. Zrzuty portalu z forka z zasobem zbiorczym (ekrany przeglądarki z lokalnego stosu): `docs/zrzuty/portal-01`, `-02`, `-03`, `-06`, `-07`, `-08`, `-10`, `-11`; `portal-04` i `-05` to wyjście terminala.

## 6. Znane ograniczenia (skrót)

- Wykaz AED w portalu działa w lokalnym pełnym stosie forka, ale nie na serwerze publicznym; wdrożenie pod domeną uruchomiono 22.11 tylko lokalnie, pod domeną testową `aed.localhost` (`docs/wdrozenie-serwer.md`, rozdział 11). Harmonogram 03:45 nie był sprawdzony – scalanie uruchamiano ręcznie.
- Zbiór do publikacji ma 781 rekordów, z czego 708 z API Warszawy; średnia kompletność rejestru 39,2 na 100.
- Harvester XML i CKAN nie przenoszą flagi „Wykaz AED” (XSD 1.13 jej nie ma); zasób z harvestera oznacza redaktor w panelu.
- Po wgraniu zwykłego CSV do portalu typy kolumn wykrytych jako liczby całkowite (`nr_budynku`, `kod_terc`, `kod_simc`, `zrodlo_id`, `kompletnosc`) trzeba zmienić ręcznie na tekst w zakładce „Zmiana typu” – sprawdzone 22.11, potem walidacja danych SUCCESS (`docs/panel-portalu-krok-po-kroku.md`); zasób zbiorczy AED ma schemat ustawiony od razu.
- Wiadomości do zarządców trafiają do skrzynki w panelu, nie są wysyłane e-mailem.
- Rekordy znane tylko z OSM (ODbL) są w rejestrze, ale poza eksportem do dane.gov.pl; wymaga to opinii prawnika.
- Żaden rekord zbioru krajowego zbudowanego z surowych źródeł nie ma jeszcze potwierdzenia zarządcy (wszystkie `niepotwierdzony`); status `aktywny` pojawia się dopiero po ścieżce B.
- Usługa AED jest serwerem demonstracyjnym: jednowątkowym, bez limitu prób logowania (`aed_service/README.md`).
- Dostępność: test automatyczny, klawiatura, 320 px i tryby kontrastu w `frontend/aed-zrzuty/DOSTEPNOSC.md`; bez czytnika ekranu i prawdziwego telefonu.
- Numer seryjny nie jest publikowany w eksporcie; decyzja, czy ma być w zbiorze otwartym, jest otwarta (`CLAUDE.md`).
- Liczby w rejestrze zależą od stanu bazy: patrz uwaga poniżej.

**Uwaga o liczbach.** `datasets/out/raport.json` podaje 18 814 rekordów w rejestrze (z urządzeniami o dostępie „prywatny”), a panel ministerstwa w usłudze AED pokazuje ok. 15,8 tys. (zrzut `04-panel-ministerstwa.jpg`: 15 769). Różnica 3 048 odpowiada liczbie rekordów z dostępem „prywatny”, których usługa nie wystawia (kod `aed_service/app.py` filtruje `dostep != 'prywatny'`). Pozostałe kilka rekordów to dane demonstracyjne i zgłoszenia z prób. Sprawdzone 22.11 na świeżej bazie: import 18 814 rekordów, z nich 3 048 z dostępem „prywatny”; panel pokazuje 15 784 = 18 814 − 3 048 + 18 urządzeń demonstracyjnych.

## Do uzupełnienia (rzeczy, których jeszcze nie ma)

| Brakuje | Gdzie ma trafić |
|---|---|
| Pliki logo (`.svg`, `.png`, `.jpg`, `.pdf` i warianty) | `kampania/logo/` [do ustalenia] |
| Księga znaku `.pdf` | `kampania/ksiega-znaku.pdf` [do ustalenia] |
| Ostateczna nazwa i hasło akcji | `kampania/nazwa-i-haslo.md` (decyzja zespołu) |
| Plik prezentacji (PDF lub link) | `docs/prezentacja.pdf` [do ustalenia]; konspekt jest gotowy |
| Publiczny adres prototypu, hasło kont demo i konto redaktora w panelu | sekcja 0 |
| Tytuł z nazwą akcji (tytuł roboczy w `docs/opis-projektu.md`) | `docs/opis-projektu.md`, `README.md` |
| Adres repozytorium (jeśli ma być podany jury) | sekcja 4A |
