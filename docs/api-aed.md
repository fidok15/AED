# API usługi AED – kontrakt

Kontrakt między frontendem (`frontend/`, moduł AED) a usługą `aed_service/`. Usługa jest samodzielna (plan B wobec pełnego stosu portalu), napisana we frameworku Falcon – tym samym, którego używa API dane.gov.pl – tak, żeby widoki dało się przenieść do aplikacji `mcod/aed` w forku portalu.

Zasady ogólne:

- prefiks: `/api/aed`; odpowiedzi w JSON, UTF-8; daty `RRRR-MM-DD` (`data_produkcji`, `data_waznosci_elektrod`, `data_waznosci_baterii` także `RRRR-MM` – ważne do ostatniego dnia miesiąca);
- standard danych w wersji 0.3.0 (sekcja `zmiany` w `aed_standard/schema.json`); status rekordu potwierdzonego przez dysponenta to `zweryfikowany` – dawna wartość `aktywny` jest przyjmowana na wejściu jako alias (pliki, formularze, parametr `status=aktywny`) i zawsze zwracana jako `zweryfikowany`;
- kody walidatora nowe w 0.3.0: błąd `wymagane_dla_zweryfikowanego` (dawniej `wymagane_dla_aktywnego`), ostrzeżenia `terc_bez_rodzaju` (6-cyfrowy `kod_terc`), `godziny_nieczytelne` (rekord `zweryfikowany` z godzinami, których nie czyta `aed_standard.hours`), `dysponent_osoba` (`dysponent_nazwa` wygląda na imię i nazwisko – pole jest publiczne);
- baza usługi z wersji 0.2.0 jest migrowana przy starcie (raz na rekord): `aktywny` → `zweryfikowany`; potwierdzenie „sprawny” przez QR → `stan_urzadzenia = gotowy` z datą weryfikacji; ostatnia odpowiedź dysponenta „problem” → `czasowo_niedostepny` (a rekord, który ten problem zdegradował do `niepotwierdzony`, wraca do `zweryfikowany`); współrzędne z importu → `sposob_ustalenia_polozenia = import`; poza tym pola zostają puste;
- stan URZĄDZENIA (`stan_urzadzenia`: `nieznany` – też pusta wartość, `gotowy`, `czasowo_niedostepny`, `wycofany_z_uzycia`; data w `data_stanu`) jest osobno od statusu DANYCH (`status`);
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

`duplikaty` to wiersze, których producent i numer seryjny są już wśród urządzeń **tego samego konta** (albo powtarzają się w pliku) – nie tworzą nowego rekordu. Dopasowanie do urządzenia innej firmy albo z importu nie jest raportowane firmie (odpowiedź nie zdradza, że taki numer jest w rejestrze): wiersz jest przyjmowany, a para trafia do kolejki duplikatów ministerstwa. Wiersz z jawnym `zrodlo = openstreetmap` albo `licencja = ODbL 1.0` jest odrzucany (błąd `dane_osm`). Odpowiedź ma też pole `sucha_proba` (`true` dla `/zgloszenia/sprawdz`; wtedy lista `przyjete` jest pusta, a liczba jest w `podsumowanie.przyjete`).

Identyfikator `id_aed` i pole `zrodlo_id` zgłoszonego urządzenia są losowe – nie da się z nich odtworzyć numeru seryjnego.

## Urządzenie i naklejka QR

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `GET /api/aed/urzadzenia/{id_aed}` | każdy | rekord w zakresie publicznym (bez pól `"publiczne": false` ze schematu: kontaktu i numeru seryjnego) oraz `waznosc_do: {data_waznosci_baterii, data_waznosci_elektrod}` – ostatni dzień ważności `RRRR-MM-DD` (dla `RRRR-MM` koniec miesiąca, `aed_standard.valid_until`); ekran QR liczy termin z tego pola |
| `GET /api/aed/urzadzenia/{id_aed}` z `Authorization` | ministerstwo, firma zgłaszająca | pełny rekord (z numerem seryjnym i kontaktem); inna firma dostaje zakres publiczny |
| `GET /api/aed/urzadzenia/{id_aed}?t=<token>` | zarządca | pełny rekord do edycji |
| `GET /api/aed/urzadzenia/{id_aed}/naklejka.svg` | każdy | naklejka z kodem QR prowadzącym do `/aed/qr/{id_aed}` |
| `POST /api/aed/urzadzenia/{id_aed}/potwierdzenie` | zarządca (token `t`) | uzupełnienie i potwierdzenie danych; rekord przechodzi w `zweryfikowany` („Zweryfikowany”), urządzenie w `gotowy` |
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
  "pietro": 0,
  "sposob_ustalenia_polozenia": "pomiar_przy_urzadzeniu",
  "stan": "sprawny"
}
```

`stan`: `sprawny` albo `problem` (wtedy wymagane `uwagi`). Zarządca może też podać nowe daty `data_waznosci_baterii` i `data_waznosci_elektrod` po wymianie (`RRRR-MM-DD` albo `RRRR-MM`) – wtedy przypomnienia o terminie przestają przychodzić. Opcjonalnie `pietro` (liczba całkowita −5…60, 0 = parter, ujemne = pod ziemią).

`sposob_ustalenia_polozenia` (opcjonalne; słownik ze schematu): skąd są współrzędne – frontend wysyła `pomiar_przy_urzadzeniu`, gdy wziął je z geolokalizacji telefonu, `wskazanie_na_mapie`, gdy użytkownik wskazał punkt. Bez tego pola usługa nie zgaduje: jeśli współrzędne się zmieniły, pole jest czyszczone (dawna wartość, np. `import`, już ich nie opisuje); jeśli się nie zmieniły, zostaje jak było.

Odpowiedź: pola `id_aed`, `status`, `data_weryfikacji`, `sposob_weryfikacji`, `stan_urzadzenia`, `data_stanu`, `kompletnosc` oraz pełny rekord w `rekord`. Przy `stan = sprawny`: `status = zweryfikowany`, `stan_urzadzenia = gotowy`, `data_stanu` = dziś. Przy `stan = problem`: `stan_urzadzenia = czasowo_niedostepny`, `data_stanu` = dziś, a status DANYCH się nie zmienia (rekord `zweryfikowany` zostaje `zweryfikowany`; rekord jeszcze niepotwierdzony zostaje w swoim statusie). Frontend rozpoznaje zgłoszenie problemu po `stan_urzadzenia`, nie po `status`. Sygnał osoby postronnej (`/sygnal`) nie zmienia stanu urządzenia. Wycofanie rekordu (scalenie duplikatów, zniknięcie ze źródła) ustawia tylko `status = wycofany` – stanu urządzenia nie zmienia.

Podane wartości są zawsze sprawdzane standardem, także przy `stan = problem` (zgłoszenie problemu może być niepełne, ale nie może zawierać błędnych wartości). Błąd: 422 `{"blad": {"kod": "niepoprawne_dane", "komunikat": "…", "problemy": [...]}}`. Przy `stan = problem` lista `problemy` zawiera tylko błędy blokujące zgłoszenie (błędne podane wartości, bez brakujących pól wymaganych).

Rekord `wycofany` nie może zostać potwierdzony także linkiem wystawionym przed wycofaniem: 409 `wycofany`.

Jeśli rekord nie ma jeszcze `dysponent_email` (np. rekord ze zbioru miejskiego bez kontaktu), zarządca może podać `dysponent_nazwa`, `dysponent_email`, `dysponent_telefon`; bez tego przypomnienia pomijają urządzenie. Istniejący kontakt nie jest zmieniany tą drogą. Dane położenia z importu zostają (poza rekordami ODbL – patrz niżej).

Po potwierdzeniu lokalizacji usługa szuka w pobliżu rekordów z importu; prawdopodobne duplikaty trafiają do kolejki ministerstwa (zgłoszone urządzenie jest rekordem zachowywanym), nic nie jest łączone automatycznie. To samo działa w drugą stronę: rekord dodany lub zmieniony przez mapper obok urządzenia zgłoszonego albo potwierdzonego trafia do kolejki przy uruchomieniu mappera. Kandydatów wskazuje `aed_standard.find_candidates` (różne źródła, do 50 m, ten sam numer seryjny; różne znane numery seryjne nie są parą).

### Przejęcie punktu (rekord z importu, np. tylko z OpenStreetMap)

1. Ministerstwo: `POST /api/aed/urzadzenia/{id_aed}/link-aktywacyjny`, ciało `{"email": "<adres instytucjonalny zarządcy>"}` (opcjonalne). Odpowiedź 201: `{"id_aed", "link_aktywacyjny", "waznosc_dni", "wyslano_na"}`. Przy podanym adresie link trafia też do skrzynki nadawczej (`rodzaj: "przejecie"`); kontakt ze źródła (np. tag `email` w OSM) nie jest używany. Rekord `wycofany` – 409 `wycofany`; zły adres – 422 `zly_email`.
2. Zarządca: zwykłe `POST …/potwierdzenie` ze `stan = sprawny`. Jeśli rekord ma licencję ODbL 1.0, usługa zaczyna od pustego rekordu: zostają tylko `id_aed` i powiązanie w `powiazane_zrodla` (`openstreetmap:<zrodlo_id>`); `zrodlo = zgloszenie`, `licencja = CC0 1.0`, `wprowadzajacy_typ = dysponent`. Nazwę, współrzędne, miejscowość, dostęp i godziny zarządca musi podać sam (inaczej 422 `niepoprawne_dane`); przy przejęciu może też podać `dysponent_nazwa`, `dysponent_email`, `dysponent_telefon` (bez kontaktu nie dostanie przypomnień).
3. Rekord jest zweryfikowany (status `zweryfikowany`) i trafia do eksportu publikacyjnego. Kolejne uruchomienia mappera go nie nadpisują (ten sam `id_aed`, rekord nie pochodzi już z importu).

Rekord z importu na licencji otwartej (CC BY 4.0, CC0 1.0) przechodzi tę samą ścieżkę bez czyszczenia – wartości ze źródła wolno zachować.

Sygnał (żądanie): `{"typ": "jest" | "brak" | "uszkodzony" | "zamkniety", "szerokosc_geograficzna": …, "dlugosc_geograficzna": …, "uwagi": "…"}`. Współrzędne są opcjonalne.

## Rejestr krajowy

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `GET /api/aed/urzadzenia` | każdy | lista stronicowana; parametry: filtry (niżej), `q` (nazwa, miejscowość albo dokładny `id_aed`), `lat` i `lon` (najbliższe urządzenia), `strona`, `na_stronie` |
| `GET /api/aed/urzadzenia.geojson` | każdy | punkty do mapy: `id_aed`, `nazwa`, `status`, `dostep`, `godziny_dostepu`, `kompletnosc`, `zrodlo`, `demo`, `stan_urzadzenia`, `data_stanu` (pusty tekst = nieznany); parametry `bbox=minLon,minLat,maxLon,maxLat` i te same filtry co lista. Bez `status` rekordy `wycofany` są pominięte |
| `GET /api/aed/filtry` | każdy | wartości do „Dodatkowych filtrów” z liczbą urządzeń publicznych i niewycofanych: `razem`, `producent: [{wartosc, liczba}]`, `model: [{wartosc, producent, liczba}]`, `miejscowosc: [{wartosc, liczba}]`, `zrodlo: [{wartosc, etykieta, liczba}]` (etykieta z `aed_standard/sources.json`), `dostep: {wartość: liczba}`, `wewnatrz_budynku: {tak, nie}`, `z_godzinami`, `calodobowo`, `stan_urzadzenia: {nieznany, gotowy, czasowo_niedostepny, wycofany_z_uzycia}` (wszystkie wartości słownika, także z liczbą 0; pusta wartość liczy się jako `nieznany`). Pisownie różniące się tylko wielkością liter to jedna wartość (najczęstsza pisownia) |

Filtry wspólne dla listy i mapy (łączą się ze sobą, z `q`, z `lat`/`lon` i ze stronicowaniem; frontend wysyła ten sam zestaw do obu, więc mapa pokazuje to samo co lista): `status`, `zrodlo`, `dostep` (wartość dokładna), `miejscowosc`, `producent`, `model`, `wewnatrz_budynku` (`tak`/`nie`; wielkość liter bez znaczenia), `calodobowo=1` (`godziny_dostepu` = `24/7`), `z_godzinami=1` (godziny podane), `stan_urzadzenia` (wartość ze słownika; `nieznany` obejmuje też pustą), `dostepny_teraz=1`. `status=aktywny` działa jak `status=zweryfikowany` (alias). Urządzenia `dostep = prywatny` nie są zwracane nigdy. Numeru seryjnego nie ma wśród filtrów – nie jest publiczny. Bez parametru `status` lista i mapa pomijają rekordy `wycofany` (oba widoki pokazują ten sam zestaw); `status=wycofany` je zwraca. Licznik „Wszystkie” w rejestrze to `razem` z `/statystyki` minus `wg_statusu.wycofany`.

`dostepny_teraz=1` (łączy się z pozostałymi filtrami) pomija urządzenia ze `stan_urzadzenia` = `czasowo_niedostepny` albo `wycofany_z_uzycia` i zostawia te, których `godziny_dostepu` są otwarte w tej chwili w Polsce (Europe/Warsaw, z przejściem CET/CEST). Godziny czyta `aed_standard.open_now` – odpowiednik `aedOpenNow` z frontendu (wspólna tabela przypadków `frontend/src/app/pages/aed/aed-hours.cases.json`): `24/7` i reguły typu `Mo-Fr 08:00-16:00; Sa 09:00-13:00; Su,PH off` (zakresy i listy dni, kilka przedziałów, święta ustawowe `PH`). Przedziały przez północ, miesiące, `sunrise` i opisy słowne dają stan „nieznany”. Urządzenia bez godzin albo z godzinami nieczytelnymi nie przechodzą filtra; lista podaje wtedy ich liczbę w polu `bez_godzin` obok `razem` (`razem` liczy tylko urządzenia dostępne teraz, stronicowanie działa po filtrze). Bez parametru pola `bez_godzin` nie ma. Filtr liczy się w Pythonie po filtrach SQL (ok. 13 ms dla całej listy, ok. 15 800 rekordów).

`lat` i `lon` (podawane razem, WGS84, kropka dziesiętna; szerokość −90…90, długość −180…180, inaczej `422 zle_wspolrzedne`) pomijają urządzenia `czasowo_niedostepny` i `wycofany_z_uzycia` (lista najbliższych nie kieruje do urządzenia zgłoszonego jako niesprawne), sortują listę rosnąco po odległości od tego punktu i dodają do każdego rekordu `odleglosc_m` – odległość w linii prostej (wzór haversine, metry, liczba całkowita), nie droga dojścia. Rekordy bez współrzędnych wypadają z listy; `razem` je pomija. Parametry łączą się z `status`, `q`, `dostepny_teraz=1` (najpierw filtry, potem sortowanie) i ze stronicowaniem. Punkt nie jest zapisywany; dziennik dostępu usługi (`python -m aed_service`) zapisuje ścieżkę zapytania bez parametrów.
| `GET /api/aed/statystyki` | każdy | `razem`, `srednia_kompletnosc`, `wg_statusu`, `wg_zrodla`, `dostawcy`, `potwierdzone_90_dni`, `ostatnie_uruchomienia: {mapper, przypomnienia}` (czas ostatniego udanego uruchomienia albo `null`), `hasla_demo_domyslne` (`false`, gdy konto ministerstwa ma hasło z `AED_MINISTRY_PASSWORD` lub `AED_DEMO_PASSWORD`; karty logowania nie pokazują wtedy haseł; zmiana haseł po inicjalizacji: `AED_RESET_PASSWORDS=1` przy jednym starcie – nowe hasła, wszystkie sesje wylogowane) |
| `GET /api/aed/sprzedawcy` | każdy | `{"dane": [...], "progi": {...}}`; firma: nazwa, `typ_podmiotu`, miejscowość, współrzędne siedziby, `liczba_urzadzen`, `srednia_kompletnosc` (kompletność rejestru, wszystkie pola), `udzial_zweryfikowanych`, `odznaka`; `progi: {srednia_kompletnosc, udzial_zweryfikowanych}`. Pole `udzial_aktywnych` (w rekordach i w `progi`) to ta sama liczba pod nazwą z wersji 0.2.0 – zostaje do czasu przełączenia frontendu |
| `GET /api/aed/eksport/dane-gov-pl.csv` | każdy | eksport publikacyjny (profil `publikacja`, bez ODbL, bez `dostep = prywatny`, bez rekordów `zgloszony` – publiczny staje się dopiero po potwierdzeniu zarządcy – bez rekordów wycofanych i demonstracyjnych, bez rekordów z kodem do szafki w polach opisowych (błąd `kod_do_szafki`); kolumny pól `"publiczne": false` (kontakt, numer seryjny) puste, a `kompletnosc` liczona tylko z pól publicznych (`aed_standard.public_completeness`) – odpowiada temu, co widać w pliku; komórka tekstowa zaczynająca się od `=`, `+`, `-`, `@`, tabulatora lub CR dostaje prefiks `'`, z wyjątkiem tekstu liczbowego i telefonu `+48…`). Parametr `wersja` jest ignorowany (patrz niżej) |
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
| `POST /api/aed/duplikaty/{id}` | ministerstwo | `{"decyzja": "polacz" | "rozdziel"}`; `polacz` zachowuje rekord A, rekord B dostaje status `wycofany`. Decyzja jest trwała: kolejne uruchomienia mappera jej nie cofają, a para nie wraca do kolejki. Po `polacz` otwarte pary z rekordem B są zamykane i kolejkowane ponownie z rekordem A. Para, której rekord jest już `wycofany`, daje 409 `para_nieaktualna` i znika z kolejki |
| `GET /api/aed/wiadomosci` | ministerstwo | skrzynka nadawcza: prośby o potwierdzenie i przypomnienia (odbiorca, temat, treść, link, data) |
| `POST /api/aed/przypomnienia/uruchom` | ministerstwo | ręczne uruchomienie zadania cyklicznego: prośby o potwierdzenie dla rekordów bez weryfikacji od 6 miesięcy (rekord z importu, `niepotwierdzony`, czeka na link przejęcia); dla urządzenia `czasowo_niedostepny` – prośba o aktualizację stanu 30 dni po `data_stanu` i dalej co 30 dni (ten sam rodzaj wiadomości `prosba`, temat „Zaktualizuj stan urządzenia AED …”); przypomnienia 60 dni przed końcem ważności baterii lub elektrod (`RRRR-MM` = koniec miesiąca); oznaczenie `nieaktualny` po 12 miesiącach bez potwierdzenia rekordu `zweryfikowany` |
| `POST /api/aed/mapper/uruchom` | ministerstwo | ręczne uruchomienie mappera źródeł; odpowiedź: `{"dodano", "zmieniono", "polaczono", "do_przegladu", "wycofano"}`. `do_przegladu` to pary faktycznie dodane do kolejki w tym uruchomieniu (z mappera i z dopasowań do urządzeń zgłoszonych lub potwierdzonych); pary już znane nie są liczone ponownie. `wycofano` to rekordy z importu, których nie ma już w źródłach |
| `GET /api/aed/zadania` | ministerstwo | historia 20 ostatnich uruchomień, od najnowszego: `id`, `start`, `koniec`, `wyzwalacz` (`harmonogram` \| `ministerstwo`), `rodzaj` (`cykl` \| `mapper` \| `przypomnienia`), `odswiezono`, `mapper`, `przypomnienia`, `bledy` |

Zadania cykliczne (pobranie źródeł → mapper → przypomnienia) usługa uruchamia sama co `AED_CYCLE_HOURS` godzin (domyślnie 24). Ręczne uruchomienie w trakcie działającego zadania daje 409 `zadanie_trwa`, nieudane – 500 `zadanie_nieudane`.

Wiadomości w prototypie nie są wysyłane pocztą – trafiają do skrzynki nadawczej, którą widać w panelu. Wiadomość ze zgłoszenia osoby postronnej nie ma linku (`link: null`).

## Konwerter do standardu (publiczny, bez zapisu)

Narzędzie dla dostawcy, który ma własny plik z defibrylatorami w dowolnym układzie kolumn. Bez logowania; plik jest przetwarzany w pamięci i nie jest zapisywany. Limit rozmiaru jak przy zgłoszeniach (5 MB). Format rozpoznajemy po treści, nie po rozszerzeniu (`aed_standard/formaty.py`; przegląd prawdziwych polskich zbiorów i wyniki na próbkach: `docs/formaty-zbiorow-aed.md`). Każdy format sprowadzamy do tej samej tabeli przed propozycją mapowania. Przyjmowane: CSV, XLSX, ODS, JSON (tablica obiektów, lista pod `features`/`data`/`result`/`records`/`items`…, spłaszczanie do `a.b`), GeoJSON, JSON usługi ArcGIS (z układem z `spatialReference`), KML/KMZ (np. Google Moje Mapy), GPX, GML/WFS, tabela HTML (zapisana strona) i tabela DOCX; wiersze tytułowe nad nagłówkiem arkusza lub tabeli są pomijane. W KML, GeoJSON i GML położenie daje tylko punkt – linia lub obszar zostaje bez położenia z uwagą w `uwagi`; z GPX czytamy tylko punkty `wpt`. Pochodzenie z OpenStreetMap sprawdzamy na dwóch poziomach: metadane dokumentu poza listą obiektów (Overpass `osm3s`/`generator`, licencja lub atrybucja kolekcji, opis dokumentu KML/GPX/GML) – odrzucane są wszystkie wiersze; znaczniki pojedynczego obiektu (`@id: node/…`, `osm_id`, `osm_type`, ODbL lub „© OpenStreetMap” we właściwościach) – odrzucany jest tylko ten wiersz (gdy mają je wszystkie obiekty – cały plik). Kod `dane_osm`; `uwagi` i `ostrzezenia` mówią, po czym rozpoznano. Zniekształcony plik – zawsze 422 `plik_nieczytelny`. PDF, skany, stare XLS/DOC i Shapefile w ZIP – 422 z poradą po polsku. Położenie: dwie kolumny WGS84, stopnie-minuty-sekundy, jedna kolumna z całym punktem (GeoJSON, WKT z opcjonalnym `SRID=`, „52.2297, 21.0122”), dwie kolumny w PUWG 1992 (EPSG:2180), PUWG 2000 (EPSG:2176–2179) albo Web Mercator (EPSG:3857) – przeliczane do WGS84 w czystym Pythonie (`aed_standard/uklady.py`, błąd < 1 mm na punktach referencyjnych). Szczegóły dawnych formatów: `.csv` (UTF-8, UTF-16 z BOM albo Windows-1250; separator `,`, `;` lub tabulator – wykrywany z pierwszych wierszy z pominięciem tekstu w cudzysłowach), `.xlsx` (pierwszy arkusz; czytany biblioteką standardową, bez makr i formuł – liczy się zapisana wartość; po rozpakowaniu najwyżej 50 MB, dane najwyżej w 300 kolumnach i najwyżej 2 mln komórek, łącznie najwyżej 20 mln znaków w komórkach; plik z deklaracją DOCTYPE jest odrzucany), `.geojson`, `.json` (FeatureCollection z punktami). Budżet każdego pliku (sprawdzany przed analizą kolumn): najwyżej 300 kolumn, 50 000 wierszy i 1 mln komórek (wiersze × kolumny); większy plik – 422 z komunikatem po polsku. Usługa obsługuje żądania jednym wątkiem, więc te limity chronią też resztę API. Konwerter niczego nie publikuje: wynikowy plik dostawca sam publikuje jako zasób swojego zbioru na dane.gov.pl z oznaczeniem „Wykaz AED”.

| Metoda i ścieżka | Kto | Opis |
|---|---|---|
| `POST /api/aed/konwerter/analiza` | każdy | `multipart/form-data`, pole `plik`. Zwraca kolumny pliku z przykładowymi wartościami i propozycją pola standardu |
| `POST /api/aed/konwerter/konwersja` | każdy | `multipart/form-data`: `plik`, `mapowanie` (JSON `{kolumna: pole}`; pusty tekst = kolumna pomijana), opcjonalnie `stale` (JSON `{pole: wartość}` – wpisywane w puste komórki całego pliku, np. `miejscowosc`, `dostep`), opcjonalnie `geokodowanie` (`1` = uzupełnij położenie z adresu usługą GUGiK; domyślnie wyłączone) |

Odpowiedź analizy: `plik`, `format` (`csv` \| `xlsx` \| `ods` \| `json` \| `geojson` \| `arcgis` \| `kml` \| `kmz` \| `gpx` \| `gml` \| `html` \| `docx`), `format_opis` (zdanie po polsku: co rozpoznano), `kodowanie`, `separator`, `wiersze`, `kolumny: [{kolumna, przyklady, pole, powod}]`, `przyklad_wierszy` (5 pierwszych wierszy), `pola: [{pole, tytul}]` (dozwolone cele mapowania), `pola_stale: [{pole, tytul, wartosci}]` (pola, którym można nadać wartość stałą; `wartosci` = słownik albo `null`), `uwagi` (naprawy pliku, np. rozpakowane wiersze), `ostrzezenia` (możliwe dane osobowe), `geokodowanie_dostepne` (czy serwer pozwala włączyć geokodowanie; zmienna `AED_GEOKODOWANIE`, domyślnie `1`, `0` wyłącza – np. wdrożenie bez dostępu do sieci).

Cele mapowania to pola schematu wypełniane przez dysponenta lub sprzedawcę, `zrodlo_id` (identyfikator w pliku dostawcy), `data_weryfikacji` i dwa cele specjalne: `_adres` (pełny adres w jednej kolumnie, np. „ul. Jasna 12, 38-400 Krosno”, dzielony na ulicę, numer, kod i miejscowość) oraz – w GeoJSON albo przy kolumnie z punktami GeoJSON – pseudokolumny `geometria: szerokość` i `geometria: długość`. Pozostałe kolumny systemowe (`zrodlo`, `licencja`, `status`, `id_aed`…) zostają puste – portal wypełnia je przy odczycie wykazu.

Propozycja: najpierw wartości (współrzędne w zakresie Polski – także przy zamienionych nagłówkach, kody pocztowe, pełny adres z kodem, adresy e-mail), potem nazwy kolumn (nazwa i tytuł pola w `schema.json`, kolumny źródeł z `sources.json` i `zrodla` w schemacie, krótka lista synonimów w `aed_standard/konwerter.py`). Każde pole dostaje najwyżej jedną kolumnę; kolumna z tą samą wartością w każdym wierszu ustępuje innym.

Odpowiedź konwersji: `nazwa_pliku`, `plik_csv` (tekst CSV w standardzie: wszystkie kolumny ze schematu, UTF-8, przecinek) i `raport`: `status` (`przyjety` \| `czesciowo` \| `odrzucony`), `wiersze`, `poprawne`, `odrzucone`, `poza_wykazem_krajowym` (np. `dostep = prywatny`), `kompletnosc_srednia` (z pól publicznych), `problemy` (jak w walidatorze: `wiersz`, `pole`, `poziom`, `kod`, `komunikat`; najwyżej 20, jak w raporcie wykazu w portalu), `problemy_razem`, `poprawki` (naprawy: zamienione współrzędne, rozpakowane wiersze, wspólne współrzędne różnych adresów), `normalizacje: [{kolumna, pole, liczba, z, na, komunikat}]` (jedna pozycja na kolumnę, w której zmieniono zapis wartości; `z` → `na` to pierwszy przykład). `bez_wspolrzednych`, `bez_wspolrzednych_komunikat`: liczba wierszy z adresem, ale bez położenia – zostają w pobranym pliku z pustymi współrzędnymi do uzupełnienia, a wykaz ich nie przyjmuje (chyba że użytkownik włączył geokodowanie i usługa znalazła punkt adresowy). `geokodowanie`: `null`, gdy użytkownik go nie włączył; `{wylaczone: true, komunikat}`, gdy serwer ma `AED_GEOKODOWANIE=0` (adresy nie wychodzą z serwera); w przeciwnym razie `{zrodlo, uzupelnione, nieuzupelnione, kody_uzupelnione, zapytania, wiersze_uzupelnione: [{wiersz, nazwa, adres, szerokosc, dlugosc, uwaga}], wiersze_nieuzupelnione: [{wiersz, nazwa, powod}], komunikat}` (listy do 100 pozycji). Opis działania: niżej. `ukryte_pola`, `ukryte_komunikat`: plik jest przeznaczony do publikacji, więc kolumny pól `"publiczne": false` ze schematu (`aed_standard.hidden_fields()`: e-mail i telefon dysponenta, numer seryjny) są w nim puste jak w każdym eksporcie publicznym; `ukryte_pola` wymienia te z nich, które w pliku dostawcy miały wartości, a komunikat każe przekazać je ministerstwu kanałem rejestru. Wiersz, który sam oznacza się jako pochodzący z OpenStreetMap (kolumna `zrodlo`/„Źródło”/`source` z `openstreetmap` lub `osm` albo kolumna `licencja`/„Licencja”/`license` z ODbL), zachowuje te znaczniki i jest odrzucany kodem `dane_osm` – dane OSM nie wchodzą do wykazu (zasada twarda 3). Gdy zmapowano zarówno pełny adres (`_adres`), jak i osobne kolumny adresu, wartości z osobnych kolumn mają pierwszeństwo; adres z jednego pola tylko uzupełnia puste.

Normalizacja przed walidacją (tylko w kolumnach przypisanych do pól schematu; listy wartości i typy z `schema.json`): pola słownikowe – po kluczu albo etykiecie, bez rozróżniania wielkości liter, polskich znaków, spacji i podkreślników, także gdy pierwsze słowo jest kluczem („Ograniczony dostęp” → `ograniczony`); pola logiczne – `tak`/`nie`, `TAK`, `1`/`0`, `true`/`false`, `x`; daty – `DD.MM.RRRR`, `DD-MM-RRRR`, `RRRR/MM/DD`, `DD/MM/RRRR` (tylko gdy jednoznaczne: dzień > 12 albo dzień = miesiąc) → `RRRR-MM-DD`; `RRRR-MM`, `RRRR/M`, `RRRR.M` w datach produkcji i ważności baterii i elektrod → `RRRR-MM` (bez dopisywania dnia; od 0.3.0); dawne wartości słownikowe (aliasy ze schematu, np. status `aktywny` → `zweryfikowany`); `parter` w polu `pietro` → `0`; współrzędne z przecinkiem dziesiętnym i spacjami; kod pocztowy `12345` → `12-345`; wiodący apostrof arkusza przed cyfrą lub `+` (`'+48…`). Daty niejednoznaczne i niemożliwe (np. `03/04/2030`, `31.02.2030`) zostają bez zmian i walidator je zgłasza. W XLSX liczba w komórce o formacie daty (wbudowanym albo własnym z `d`/`y`) staje się datą `RRRR-MM-DD`. Raport powstaje tym samym odczytem (`aed_standard.wykaz.read_wykaz`), którym portal sprawdza wykaz AED. Błędy: 415 `tylko_csv` (rozszerzenie spoza listy `CONVERTER_FILES` w `aed_service/app.py`; `.pdf`, `.xls`, `.doc` i obrazy są przyjmowane tylko po to, żeby odpowiedzieć poradą 422), 422 `plik_nieczytelny` (plik się nie czyta, także uszkodzony UTF-16 oraz uszkodzony, zbyt duży po rozpakowaniu albo zbyt szeroki XLSX), 422 `zle_mapowanie` (np. jedno pole przypisane do dwóch kolumn, nieznane pole), 400 `zly_format` (`mapowanie`/`stale` nie są obiektami JSON).

Geokodowanie (`aed_standard/geokod.py`, na żądanie użytkownika): wiersze bez współrzędnych, a z ulicą i numerem budynku, idą do Usługi Uniwersalnego Geokodowania GUGiK (`GET https://services.gugik.gov.pl/uug/?request=GetAddress&address=Miejscowość, Ulica Numer&srid=4326`). Przyjmujemy tylko wynik typu `address` (punkt adresowy budynku) z tym samym numerem, pewną miejscowością (`city_accuracy = 1`), jednym najlepszym dopasowaniem i `accuracy ≥ 0.7` albo tym samym ostatnim słowem nazwy ulicy („Piłsudskiego” → „Marszałka Józefa Piłsudskiego”); dopasowanie do osi ulicy lub środka miejscowości nie jest położeniem urządzenia, więc taki wiersz zostaje bez współrzędnych z powodem w raporcie. Inny kod pocztowy niż w punkcie adresowym: przy pełnym dopasowaniu (`accuracy = 1`) uwaga w raporcie, przy częściowym – odrzucenie. W uzupełnionym wierszu `sposob_ustalenia_polozenia = geokodowanie_adresu` (od 0.3.0; `opis_lokalizacji` zostaje taki, jak podał dostawca). Puste `kod_terc` (6 cyfr, bez rodzaju gminy) i `kod_simc` uzupełniamy z tego samego wyniku; w wierszach ze współrzędnymi – z najbliższego punktu adresowego w promieniu 100 m (`request=GetAddressReverse&location=POINT(dł. szer.)&srid=4326`), tylko gdy jego miejscowość jest taka sama jak w wierszu. Najwyżej 200 zapytań i 40 s na jedną konwersję, przerwa 0,1 s, pamięć podręczna w obrębie żądania; błąd sieci nie przerywa konwersji.
