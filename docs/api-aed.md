# API usługi AED – kontrakt

Kontrakt między frontendem (`frontend/`, moduł AED) a usługą `aed_service/`. Usługa jest samodzielna (plan B wobec pełnego stosu portalu), napisana we frameworku Falcon – tym samym, którego używa API dane.gov.pl – tak, żeby widoki dało się przenieść do aplikacji `mcod/aed` w forku portalu.

Zasady ogólne:

- prefiks: `/api/aed`; odpowiedzi w JSON, UTF-8; daty `RRRR-MM-DD`;
- pola urządzenia mają dokładnie nazwy z `aed_standard/schema.json`;
- błąd: `{"blad": {"kod": "...", "komunikat": "..."}}` z właściwym kodem HTTP;
- uwierzytelnienie: nagłówek `Authorization: Bearer <token>` z logowania; role: `firma`, `ministerstwo`;
- konta demonstracyjne są zakładane przy starcie usługi i wypisane w `aed_service/README.md`.

## Sesja

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `POST /api/aed/sesja` | każdy | `{email, haslo}` → `{token, konto: {id, nazwa, rola, typ_podmiotu}}` |
| `GET /api/aed/sesja` | zalogowany | dane bieżącego konta |

## Schemat

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `GET /api/aed/schemat` | każdy | zawartość `aed_standard/schema.json` – z niej frontend buduje formularze |

## Zgłoszenia firmy (producent, sprzedawca)

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `POST /api/aed/zgloszenia` | firma | `multipart/form-data`, pole `plik` (CSV). Walidacja profilem `sprzedaz`. Wiersze poprawne są przyjmowane, błędne odrzucane. |
| `POST /api/aed/zgloszenia/sprawdz` | firma | to samo, ale bez zapisu – podgląd raportu przed wysłaniem |
| `GET /api/aed/zgloszenia` | firma | historia zgłoszeń konta |
| `POST /api/aed/urzadzenia` | firma | jedno urządzenie jako JSON (formularz); ta sama walidacja |

Odpowiedź zgłoszenia:

```json
{
  "id": 12,
  "utworzono": "2026-11-21T19:04:11",
  "podsumowanie": {"wiersze": 10, "przyjete": 8, "odrzucone": 2, "bledy": 3, "ostrzezenia": 1, "duplikaty": 1},
  "problemy": [
    {"wiersz": 4, "pole": "data_produkcji", "poziom": "blad", "kod": "format_daty", "komunikat": "…"}
  ],
  "przyjete": [
    {"id_aed": "AED-7F3K9Q2M4XTB", "producent": "…", "model": "…", "numer_seryjny": "…",
     "naklejka_url": "/api/aed/urzadzenia/AED-7F3K9Q2M4XTB/naklejka.svg",
     "link_aktywacyjny": "/aed/qr/AED-7F3K9Q2M4XTB?t=<token zarządcy>"}
  ]
}
```

`duplikaty` to wiersze, których producent i numer seryjny są już w rejestrze – nie tworzą nowego rekordu. Odpowiedź ma też pole `sucha_proba` (`true` dla `/zgloszenia/sprawdz`; wtedy lista `przyjete` jest pusta, a liczba jest w `podsumowanie.przyjete`).

Identyfikator `id_aed` i pole `zrodlo_id` zgłoszonego urządzenia są losowe – nie da się z nich odtworzyć numeru seryjnego.

## Urządzenie i naklejka QR

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `GET /api/aed/urzadzenia/{id_aed}` | każdy | rekord w zakresie publicznym (bez kontaktu, bez numeru seryjnego) |
| `GET /api/aed/urzadzenia/{id_aed}?t=<token>` | zarządca | pełny rekord do edycji |
| `GET /api/aed/urzadzenia/{id_aed}/naklejka.svg` | każdy | naklejka z kodem QR prowadzącym do `/aed/qr/{id_aed}` |
| `POST /api/aed/urzadzenia/{id_aed}/potwierdzenie` | zarządca (token `t`) | uzupełnienie i potwierdzenie danych; rekord przechodzi w `aktywny` |
| `POST /api/aed/urzadzenia/{id_aed}/sygnal` | każdy | zgłoszenie z miejsca bez uprawnień; nie zmienia danych, trafia do dysponenta |
| `POST /api/aed/urzadzenia/{id_aed}/link-aktywacyjny` | ministerstwo | link zarządcy dla rekordu, który już jest w rejestrze (np. z importu); patrz „Przejęcie punktu” |

Kod QR na naklejce jest publiczny, więc sam skan nie daje prawa edycji. Zarządca dostaje prawo edycji przez link z tokenem wysłany na `dysponent_email` (pierwsza aktywacja oraz każde późniejsze potwierdzenie). Każdy wysłany link jest ważny 90 dni, a kilka linków do jednego urządzenia działa równocześnie; link nieznany albo przeterminowany daje 403 `zly_token`.

Publiczny rekord, wiersze listy i punkty geojson mają pole `demo` (`true` dla urządzeń demonstracyjnych).

Potwierdzenie (żądanie):

```json
{
  "t": "<token zarządcy>",
  "nazwa": "Urząd Miasta Legionowo",
  "szerokosc_geograficzna": 52.395198, "dlugosc_geograficzna": 20.931382,
  "miejscowosc": "Legionowo", "nazwa_ulicy": "Piłsudskiego", "nr_budynku": "41", "kod_pocztowy": "05-120",
  "opis_lokalizacji": "Hol główny, przy portierni",
  "wewnatrz_budynku": "tak",
  "dostep": "publiczny",
  "godziny_dostepu": "Mo-Fr 08:00-16:00",
  "stan": "sprawny"
}
```

`stan`: `sprawny` albo `problem` (wtedy wymagane `uwagi`). Zarządca może też podać nowe daty `data_waznosci_baterii` i `data_waznosci_elektrod` po wymianie – wtedy przypomnienia o terminie przestają przychodzić.

Odpowiedź: pola `id_aed`, `status`, `data_weryfikacji`, `sposob_weryfikacji`, `kompletnosc` oraz pełny rekord w `rekord`. Przy `stan = sprawny` rekord przechodzi w `aktywny`; przy `stan = problem` nie jest aktywny, dopóki problem nie zostanie usunięty i potwierdzony ponownie.

Podane wartości są zawsze sprawdzane standardem, także przy `stan = problem` (zgłoszenie problemu może być niepełne, ale nie może zawierać błędnych wartości). Błąd: 422 `{"blad": {"kod": "niepoprawne_dane", "komunikat": "…", "problemy": [...]}}`. Przy `stan = problem` lista `problemy` zawiera tylko błędy blokujące zgłoszenie (błędne podane wartości, bez brakujących pól wymaganych).

Rekord `wycofany` nie może zostać potwierdzony także linkiem wystawionym przed wycofaniem: 409 `wycofany`.

Jeśli rekord nie ma jeszcze `dysponent_email` (np. rekord ze zbioru miejskiego bez kontaktu), zarządca może podać `dysponent_nazwa`, `dysponent_email`, `dysponent_telefon`; bez tego przypomnienia pomijają urządzenie. Istniejący kontakt nie jest zmieniany tą drogą. Dane położenia z importu zostają (poza rekordami ODbL – patrz niżej).

Po potwierdzeniu lokalizacji usługa szuka w pobliżu rekordów z importu; prawdopodobne duplikaty trafiają do kolejki ministerstwa (zgłoszone urządzenie jest rekordem zachowywanym), nic nie jest łączone automatycznie. To samo działa w drugą stronę: rekord dodany lub zmieniony przez mapper obok urządzenia zgłoszonego albo potwierdzonego trafia do kolejki przy uruchomieniu mappera. Kandydatów wskazuje `aed_standard.find_candidates` (różne źródła, do 50 m, ten sam numer seryjny; różne znane numery seryjne nie są parą).

### Przejęcie punktu (rekord z importu, np. tylko z OpenStreetMap)

1. Ministerstwo: `POST /api/aed/urzadzenia/{id_aed}/link-aktywacyjny`, ciało `{"email": "<adres instytucjonalny zarządcy>"}` (opcjonalne). Odpowiedź 201: `{"id_aed", "link_aktywacyjny", "waznosc_dni", "wyslano_na"}`. Przy podanym adresie link trafia też do skrzynki nadawczej (`rodzaj: "przejecie"`); kontakt ze źródła (np. tag `email` w OSM) nie jest używany. Rekord `wycofany` – 409 `wycofany`; zły adres – 422 `zly_email`.
2. Zarządca: zwykłe `POST …/potwierdzenie` ze `stan = sprawny`. Jeśli rekord ma licencję ODbL 1.0, usługa zaczyna od pustego rekordu: zostają tylko `id_aed` i powiązanie w `powiazane_zrodla` (`openstreetmap:<zrodlo_id>`); `zrodlo = zgloszenie`, `licencja = CC0 1.0`, `wprowadzajacy_typ = dysponent`. Nazwę, współrzędne, miejscowość, dostęp i godziny zarządca musi podać sam (inaczej 422 `niepoprawne_dane`); przy przejęciu może też podać `dysponent_nazwa`, `dysponent_email`, `dysponent_telefon` (bez kontaktu nie dostanie przypomnień).
3. Rekord jest `aktywny` i trafia do eksportu publikacyjnego. Kolejne uruchomienia mappera go nie nadpisują (ten sam `id_aed`, rekord nie pochodzi już z importu).

Rekord z importu na licencji otwartej (CC BY 4.0, CC0 1.0) przechodzi tę samą ścieżkę bez czyszczenia – wartości ze źródła wolno zachować.

Sygnał (żądanie): `{"typ": "jest" | "brak" | "uszkodzony" | "zamkniety", "szerokosc_geograficzna": …, "dlugosc_geograficzna": …, "uwagi": "…"}`. Współrzędne są opcjonalne.

## Rejestr krajowy

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `GET /api/aed/urzadzenia` | każdy | lista stronicowana; parametry: `status`, `zrodlo`, `dostep`, `q` (nazwa, miejscowość), `strona`, `na_stronie` |
| `GET /api/aed/urzadzenia.geojson` | każdy | punkty do mapy: `id_aed`, `nazwa`, `status`, `dostep`, `godziny_dostepu`, `kompletnosc`, `zrodlo`; parametr `bbox=minLon,minLat,maxLon,maxLat` |
| `GET /api/aed/statystyki` | każdy | `razem`, `srednia_kompletnosc`, `wg_statusu`, `wg_zrodla`, `dostawcy`, `potwierdzone_90_dni`, `ostatnie_uruchomienia: {mapper, przypomnienia}` (czas ostatniego udanego uruchomienia albo `null`), `hasla_demo_domyslne` (`false`, gdy konta demo mają hasło z `AED_DEMO_PASSWORD`; karty logowania nie pokazują wtedy haseł) |
| `GET /api/aed/sprzedawcy` | każdy | `{"dane": [...], "progi": {...}}`; firma: nazwa, `typ_podmiotu`, miejscowość, współrzędne siedziby, `liczba_urzadzen`, `srednia_kompletnosc`, `udzial_aktywnych`, `odznaka` |
| `GET /api/aed/eksport/dane-gov-pl.csv` | każdy | eksport publikacyjny (profil `publikacja`, bez ODbL, bez `dostep = prywatny`, bez rekordów wycofanych i demonstracyjnych; kolumny kontaktu i numeru seryjnego puste). Parametr `wersja` jest ignorowany (patrz niżej) |
| `GET`, `HEAD /api/aed/eksport/dane-gov-pl.xml` | każdy | zasilanie harvestera XML dane.gov.pl (schemat 1.13, `application/xml`): jeden zbiór `aed-krajowy-rejestr` z jednym zasobem `aed-krajowy-rejestr-csv`, który wskazuje na eksport publikacyjny CSV |
| `GET /api/aed/eksport/dane-gov-pl.md5` | każdy | suma MD5 pliku XML (32 znaki szesnastkowe, `text/plain`) |

Zasilanie XML a harvester portalu (`backend/mcod/harvester/utils.py:168-255`):

- portal szuka sumy pod adresem XML z końcówką `.xml` zamienioną na `.md5` (stąd `dane-gov-pl.md5`, nie `dane-gov-pl.xml.md5`), najpierw wysyła `HEAD` i sprawdza typ treści;
- XML zależy tylko od zawartości eksportu CSV, więc przy niezmienionym rejestrze ma te same bajty i tę samą sumę; daty `lastUpdateDate` i `dataDate` to najnowsza `data_aktualizacji` lub `data_weryfikacji` wśród eksportowanych rekordów;
- link do CSV ma parametr `wersja` (12 znaków MD5 pliku CSV): portal pobiera plik zasobu ponownie tylko wtedy, gdy zmieni się jego link (`backend/mcod/resources/models.py:1287-1295`, `1966`);
- linki budowane są z `AED_BASE_URL` (ten sam adres co w kodach QR). Schemat 1.13 wymaga, by adres zasobu zaczynał się od `https://`, więc przy adresie `http://` XML nie przejdzie walidacji portalu;
- GeoJSON nie jest w zasilaniu: `GET /urzadzenia.geojson` zawiera też rekordy z OSM (ODbL) i demonstracyjne.

Lista stronicowana: `{"dane": [...], "razem": 19000, "strona": 1, "na_stronie": 50}`.

## Panel ministerstwa

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `GET /api/aed/duplikaty` | ministerstwo | pary do ręcznego przeglądu: oba rekordy, odległość w metrach, podobieństwo |
| `POST /api/aed/duplikaty/{id}` | ministerstwo | `{"decyzja": "polacz" | "rozdziel"}`; `polacz` zachowuje rekord A, rekord B dostaje status `wycofany`. Decyzja jest trwała: kolejne uruchomienia mappera jej nie cofają, a para nie wraca do kolejki |
| `GET /api/aed/wiadomosci` | ministerstwo | skrzynka nadawcza: prośby o potwierdzenie i przypomnienia (odbiorca, temat, treść, link, data) |
| `POST /api/aed/przypomnienia/uruchom` | ministerstwo | ręczne uruchomienie zadania cyklicznego: prośby o potwierdzenie dla rekordów bez weryfikacji od 6 miesięcy, przypomnienia 60 dni przed końcem ważności baterii lub elektrod, oznaczenie `nieaktualny` po 12 miesiącach bez potwierdzenia |
| `POST /api/aed/mapper/uruchom` | ministerstwo | ręczne uruchomienie mappera źródeł; odpowiedź: `{"dodano", "zmieniono", "polaczono", "do_przegladu", "wycofano"}`. `do_przegladu` to pary faktycznie dodane do kolejki w tym uruchomieniu (z mappera i z dopasowań do urządzeń zgłoszonych lub potwierdzonych); pary już znane nie są liczone ponownie. `wycofano` to rekordy z importu, których nie ma już w źródłach |
| `GET /api/aed/zadania` | ministerstwo | historia 20 ostatnich uruchomień, od najnowszego: `id`, `start`, `koniec`, `wyzwalacz` (`harmonogram` \| `ministerstwo`), `rodzaj` (`cykl` \| `mapper` \| `przypomnienia`), `odswiezono`, `mapper`, `przypomnienia`, `bledy` |

Zadania cykliczne (pobranie źródeł → mapper → przypomnienia) usługa uruchamia sama co `AED_CYCLE_HOURS` godzin (domyślnie 24). Ręczne uruchomienie w trakcie działającego zadania daje 409 `zadanie_trwa`, nieudane – 500 `zadanie_nieudane`.

Wiadomości w prototypie nie są wysyłane pocztą – trafiają do skrzynki nadawczej, którą widać w panelu. Wiadomość ze zgłoszenia osoby postronnej nie ma linku (`link: null`).

## Konwerter do standardu (publiczny, bez zapisu)

Narzędzie dla dostawcy, który ma własny plik z defibrylatorami w dowolnym układzie kolumn. Bez logowania; plik jest przetwarzany w pamięci i nie jest zapisywany. Limit rozmiaru jak przy zgłoszeniach (5 MB). Przyjmowane pliki: `.csv` (UTF-8, UTF-16 z BOM albo Windows-1250; separator `,`, `;` lub tabulator – wykrywany), `.xlsx` (pierwszy arkusz; czytany biblioteką standardową, bez makr i formuł – liczy się zapisana wartość; po rozpakowaniu najwyżej 50 MB; plik z deklaracją DOCTYPE jest odrzucany), `.geojson`, `.json` (FeatureCollection z punktami). Konwerter niczego nie publikuje: wynikowy plik dostawca sam publikuje jako zasób swojego zbioru na dane.gov.pl z oznaczeniem „Wykaz AED”.

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `POST /api/aed/konwerter/analiza` | każdy | `multipart/form-data`, pole `plik`. Zwraca kolumny pliku z przykładowymi wartościami i propozycją pola standardu |
| `POST /api/aed/konwerter/konwersja` | każdy | `multipart/form-data`: `plik`, `mapowanie` (JSON `{kolumna: pole}`; pusty tekst = kolumna pomijana), opcjonalnie `stale` (JSON `{pole: wartość}` – wpisywane w puste komórki całego pliku, np. `miejscowosc`, `dostep`) |

Odpowiedź analizy: `plik`, `format` (`csv` \| `xlsx` \| `geojson`), `kodowanie`, `separator`, `wiersze`, `kolumny: [{kolumna, przyklady, pole, powod}]`, `przyklad_wierszy` (5 pierwszych wierszy), `pola: [{pole, tytul}]` (dozwolone cele mapowania), `pola_stale: [{pole, tytul, wartosci}]` (pola, którym można nadać wartość stałą; `wartosci` = słownik albo `null`), `uwagi` (naprawy pliku, np. rozpakowane wiersze), `ostrzezenia` (możliwe dane osobowe).

Cele mapowania to pola schematu wypełniane przez dysponenta lub sprzedawcę, `zrodlo_id` (identyfikator w pliku dostawcy), `data_weryfikacji` i dwa cele specjalne: `_adres` (pełny adres w jednej kolumnie, np. „ul. Jasna 12, 38-400 Krosno”, dzielony na ulicę, numer, kod i miejscowość) oraz – w GeoJSON albo przy kolumnie z punktami GeoJSON – pseudokolumny `geometria: szerokość` i `geometria: długość`. Pozostałe kolumny systemowe (`zrodlo`, `licencja`, `status`, `id_aed`…) zostają puste – portal wypełnia je przy odczycie wykazu.

Propozycja: najpierw wartości (współrzędne w zakresie Polski – także przy zamienionych nagłówkach, kody pocztowe, pełny adres z kodem, adresy e-mail), potem nazwy kolumn (nazwa i tytuł pola w `schema.json`, kolumny źródeł z `sources.json` i `zrodla` w schemacie, krótka lista synonimów w `aed_standard/konwerter.py`). Każde pole dostaje najwyżej jedną kolumnę; kolumna z tą samą wartością w każdym wierszu ustępuje innym.

Odpowiedź konwersji: `nazwa_pliku`, `plik_csv` (tekst CSV w standardzie: wszystkie kolumny ze schematu, UTF-8, przecinek) i `raport`: `status` (`przyjety` \| `czesciowo` \| `odrzucony`), `wiersze`, `poprawne`, `odrzucone`, `poza_wykazem_krajowym` (np. `dostep = prywatny`), `kompletnosc_srednia`, `problemy` (jak w walidatorze: `wiersz`, `pole`, `poziom`, `kod`, `komunikat`; najwyżej 20, jak w raporcie wykazu w portalu), `problemy_razem`, `poprawki` (naprawy: zamienione współrzędne, rozpakowane wiersze, wspólne współrzędne różnych adresów), `normalizacje: [{kolumna, pole, liczba, z, na, komunikat}]` (jedna pozycja na kolumnę, w której zmieniono zapis wartości; `z` → `na` to pierwszy przykład).

Normalizacja przed walidacją (tylko w kolumnach przypisanych do pól schematu; listy wartości i typy z `schema.json`): pola słownikowe – po kluczu albo etykiecie, bez rozróżniania wielkości liter, polskich znaków, spacji i podkreślników, także gdy pierwsze słowo jest kluczem („Ograniczony dostęp” → `ograniczony`); pola logiczne – `tak`/`nie`, `TAK`, `1`/`0`, `true`/`false`, `x`; daty – `DD.MM.RRRR`, `DD-MM-RRRR`, `RRRR/MM/DD`, `DD/MM/RRRR` (tylko gdy jednoznaczne: dzień > 12 albo dzień = miesiąc) → `RRRR-MM-DD`, a `RRRR-MM` w datach ważności baterii i elektrod → ostatni dzień miesiąca; współrzędne z przecinkiem dziesiętnym i spacjami; kod pocztowy `12345` → `12-345`; wiodący apostrof arkusza przed cyfrą lub `+` (`'+48…`). Daty niejednoznaczne i niemożliwe (np. `03/04/2030`, `31.02.2030`) zostają bez zmian i walidator je zgłasza. W XLSX liczba w komórce o formacie daty (wbudowanym albo własnym z `d`/`y`) staje się datą `RRRR-MM-DD`. Raport powstaje tym samym odczytem (`aed_standard.wykaz.read_wykaz`), którym portal sprawdza wykaz AED. Błędy: 415 `tylko_csv` (inny typ pliku, np. `.xls`), 422 `plik_nieczytelny` (plik się nie czyta, także uszkodzony lub zbyt duży po rozpakowaniu XLSX), 422 `zle_mapowanie` (np. jedno pole przypisane do dwóch kolumn, nieznane pole), 400 `zly_format` (`mapowanie`/`stale` nie są obiektami JSON).
