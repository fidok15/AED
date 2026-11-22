# Prezentacja – konspekt slajd po slajdzie

Wymóg zadania (rozdział 4): min. 5 slajdów z dowodami realizacji wymagań technicznych (zrzuty ekranu), opis funkcjonalności z krokami użytkownika, lista ograniczeń. Proponujemy 12 slajdów. Kryterium „Prezentacja” to 5% oceny, ale na slajdach są dowody dla pozostałych kryteriów, w tym 30% za zgodność z zasadami portalu.

Narracja: **problem (dane rozproszone, bez odpowiedzialnego) → odpowiedź w mechanice portalu: wykaz AED wzorem DGA → jeden standard → kanał sprzedawcy i QR (odpowiedzialny podmiot) → wynik → zachęty i kampania → ograniczenia → co dalej.**

Zasady: liczby tylko z `datasets/out/raport.json` (stan z budowy zbioru 21.11.2026), z naszego eksportu albo ze źródła pierwotnego (zasada 10). Bez obietnic uratowanych istnień (zasada 9). Mierzymy proces: liczbę dostawców i wykazów, kompletność, udział rekordów potwierdzonych.

Zrzuty:

- **są:** `frontend/aed-zrzuty/` (01–18, wersje 320 px, tryby kontrastu, wyniki axe w `DOSTEPNOSC.md`);
- **do zrobienia z portalu z forka:** nazwy plików `portal-*.png`, katalog `docs/zrzuty/` (prowadzi go osoba robiąca zrzuty). Lista na końcu. Zrzuty z portalu powstaną dopiero po uruchomieniu wykazu AED w pełnym stosie, co jest **do potwierdzenia**.

---

## Slajd 1. Tytuł

- **Teza:** Dane o AED w dane.gov.pl mają mieć jeden standard, wielu dostawców i jednego wydawcę zbioru: ministerstwo.
- **Treść:** „[NAZWA AKCJI]: wykaz AED w dane.gov.pl”; podtytuł: „Portal scala wykazy dostawców w jeden zbiór; sprzedawca i zarządca biorą odpowiedzialność za dane”. W pakiecie: wykaz AED w forku portalu, standard i wzorzec XLSX, prototyp kanału sprzedawcy z QR, akcja dla dostawców.
- **Zrzut:** `docs/zrzuty/portal-01-zbior-zbiorczy.png` (zbiór „Krajowy wykaz defibrylatorów AED – wykaz zbiorczy” w portalu); logo akcji `[BRAK: logo]`.
- **Liczby:** brak.
- **Notatki mówcy:** Zaczynamy od tezy, nie od technologii. Rozwiązanie nie stoi obok portalu, tylko korzysta z jego mechanizmów.

## Slajd 2. Problem

- **Teza:** Dane są rozproszone i nikt nie bierze za nie odpowiedzialności. Nie da się tego naprawić jednorazowym sklejeniem plików.
- **Treść:**
  - z treści zadania: nie istnieje kompletna mapa; jest kilka mniej lub bardziej kompletnych baz;
  - diagnoza organizatora (`docs/tips.txt`): dane niezweryfikowane, „nikt nie bierze za nie odpowiedzialności”; publikować może tylko dostawca, który bierze odpowiedzialność za zbiór;
  - nasz pomiar: sześć źródeł (cztery zbiory samorządowe z dane.gov.pl, API Warszawy, OpenStreetMap) → **18 814 rekordów** po usunięciu 266 powtórzeń; **żaden** nie ma potwierdzenia odpowiedzialnego podmiotu (wszystkie `niepotwierdzony`).
- **Zrzut:** `frontend/aed-zrzuty/04-panel-ministerstwa.jpg` (tabele „według statusu” i „według źródła”).
- **Liczby:** `raport.json`: `rejestr_rekordy`, `polaczenia.razem`, `statusy`.
- **Notatki mówcy:** Brak właściciela danych jest ważniejszy niż brak samych danych. Dlatego mamy dwie rzeczy: mechanizm portalu, który zbiera dane od wielu dostawców, i kanał, w którym dane wprowadza ten, kto za urządzenie odpowiada.

## Slajd 3. Pomiar: co jest w istniejących danych

- **Teza:** Pól, które najbardziej przydają się świadkowi zdarzenia, prawie nigdzie nie ma, a źródła mają różne struktury.
- **Treść** (`raport.json`, `pokrycie_pol` – udział rekordów z wypełnionym polem):

| Źródło | Rekordów | Godziny dostępu | Dostęp | Producent | Numer seryjny | Ważność baterii |
|---|---|---|---|---|---|---|
| 4 zbiory samorządowe (Krosno 21, Marki 8, Przemyśl 21, Legionowo 24) | 74 | 0% | 0% | 0% | 0% | 0% |
| API Warszawy | 708 | 14,1% | 100% | 98% | 0% | 0% |
| OpenStreetMap | 18 298 | 37% | 92,4% | 1,9% | 0% | 0% |

  - średnia kompletność (0–100): samorządy 31,1–36,0, OSM 38,8, Warszawa 53,2; rejestr 39,2; eksport do publikacji 51,4;
  - jakość plików (`naprawy_danych`): w Markach 8 wierszy w jednej parze cudzysłowów, w 7 z 8 rekordów zamienione współrzędne, jeden punkt 293 km od reszty.
- **Zrzut:** `[BRAK: wykres z pokrycia pól – do zrobienia z raport.json]`.
- **Liczby:** `raport.json`: `pokrycie_pol`, `kompletnosc_srednia`, `naprawy_danych`, `rekordy_na_zrodlo`.
- **Notatki mówcy:** To pomiar na prawdziwych plikach, nie opinia. Każdy samorząd publikuje inaczej, stąd wspólny standard i walidacja przy publikacji.

## Slajd 4. Odpowiedź: wykaz – mechanizm, który portal już ma

- **Teza:** Portal ma już wykaz, który zbiera zasoby wielu dostawców w jeden zasób zbiorczy: wykaz chronionych danych (DGA). Odtwarzamy jego logikę dla AED.
- **Treść:**
  - DGA w kodzie (`docs/wykaz-dga-analiza.md`): flaga zasobu → walidacja kolumn w panelu → zadanie dzienne 03:30 skleja wykazy → zasób zbiorczy w zbiorze Ministerstwa Cyfryzacji → `GET /dga-aggregated`;
  - wykaz AED (`backend/mcod/aed/`, `aed_standard/wykaz.py`): flaga „Wykaz AED” → walidacja standardem AED z komunikatami po polsku → zadanie dzienne 03:45 lub `manage.py create_main_aed_resource` → walidacja, deduplikacja, profil publikacji → zasób „Krajowy wykaz AED” → `GET /aed-aggregated` z publicznym raportem przyjętych i odrzuconych wykazów;
  - różnice wobec DGA: dostawcą może być każdy typ instytucji, w tym firma; wykaz może być linkiem; odrzucony wykaz jest opisany w publicznym raporcie (w DGA tylko w logach).
- **Zrzut:** schemat (do narysowania) „DGA → AED” z tabeli „Odpowiedniki dla AED” w `docs/wykaz-dga-analiza.md`; `docs/zrzuty/portal-02-formularz-wykaz-aed.png` (pole „Wykaz AED” w formularzu zasobu).
- **Liczby:** brak.
- **Notatki mówcy:** To odpowiedź na wskazówkę prowadzącego: nie budujemy osobnej aplikacji zamiast portalu, tylko dostosowujemy jego logikę. Zmiana jest wydzielona (osobna aplikacja Django i jedno pole zasobu), więc da się ją przenieść do kodu ministerstwa jako łatkę.

## Slajd 5. Wykaz AED w działaniu (kroki użytkownika)

- **Teza:** Dostawca publikuje, portal pilnuje jakości, ministerstwo wydaje jeden zbiór, a każdy może go odczytać bez logowania.
- **Treść (kroki):**
  1. Redaktor samorządu dodaje w swoim zbiorze zasób CSV i zaznacza „Wykaz AED: TAK”.
  2. Plik zgodny (prawdziwy zbiór Legionowa) zapisuje się. Plik niezgodny (Krosno) nie zapisuje się, a formularz pokazuje błędy po polsku, np. „Kolumna »Adres« nie występuje w standardzie”, z podpowiedzią nazwy kolumny.
  3. Ministerstwo publikuje swój wykaz: link do eksportu usługi AED albo plik.
  4. Scalanie: raport bez zapisu (`--dry-run`), potem zasób zbiorczy.
  5. Odczyt: `GET /aed-aggregated`, widok tabeli, mapa, API zasobu.
- **Zrzuty:** `portal-03-bledy-wykazu-krosno.png`, `portal-04-dry-run-raport.png`, `portal-05-aed-aggregated.png`, `portal-06-tabela.png`, `portal-07-mapa.png`, `portal-08-api-i-otwartosc.png`.
- **Liczby:** wynik scalania wykazu Legionowa i eksportu z rejestru (`tests/test_wykaz.py`): 805 rekordów z wykazów, 24 połączenia, 781 w wykazie krajowym. **Do potwierdzenia uruchomieniem w portalu** – dziś to wynik testu poza portalem.
- **Notatki mówcy:** Jury może to sprawdzić samym odczytem pod adresem publicznym, bez konta. Wskazówka prowadzącego mówiła wprost, że rozwiązanie do odczytu jest cenniejsze.

## Slajd 6. Standard danych i wzorzec XLSX

- **Teza:** Jedna struktura dla wszystkich dostawców, zgodna z tym, co już jest na dane.gov.pl.
- **Treść:**
  - `aed_standard/schema.json` – jedyne źródło prawdy: jeden wiersz to jedno urządzenie; CSV UTF-8, daty `RRRR-MM-DD`, współrzędne WGS84 w osobnych kolumnach (warunek mapy w portalu);
  - pola z rozmowy z komisją: identyfikator, producent, model, numer seryjny, data produkcji, daty ważności elektrod i baterii, współrzędne, godziny dostępu, kto wprowadził;
  - dwa profile wymagalności: `sprzedaz` i `publikacja`; status `aktywny` wymaga dostępu, godzin dostępu i daty weryfikacji;
  - nazwy kolumn adresu zgodne ze zbiorem Legionowa, więc jego plik jest poprawnym wykazem bez zmian;
  - ze schematu powstają `wzorzec/wzorzec-aed.xlsx` (Dane, Słownik pól, Słowniki, Mapowanie źródeł, Instrukcja), walidator, formularze i walidacja wykazu w portalu.
- **Zrzuty:** `[BRAK: karta „Słownik pól” z wzorzec/wzorzec-aed.xlsx]`; `frontend/aed-zrzuty/09-raport-walidacji-bledy.jpg`.
- **Liczby:** liczba pól i profili – z `aed_standard/schema.json` w chwili robienia slajdu (nie przepisujemy ich do dokumentów, zasada 1).
- **Notatki mówcy:** Standard jest rozszerzeniem istniejącego zbioru, nie konkurencją. Ten sam walidator sprawdza plik firmy, wykaz samorządu w portalu i eksport ministerstwa.

## Slajd 7. Kanał sprzedawcy i naklejka QR

- **Teza:** Dane wprowadza ten, kto zna urządzenie (sprzedawca), a miejsce potwierdza ten, kto zna miejsce (zarządca).
- **Treść (kroki):**
  1. Sprzedawca zgłasza urządzenia przy sprzedaży plikiem CSV z raportem walidacji po polsku albo formularzem (profil `sprzedaz`); rekord dostaje `AED-…` i status `zgloszony`.
  2. System generuje naklejki z kodem QR (arkusz do druku) i link dla zarządcy.
  3. Zarządca na telefonie: lokalizacja, godziny dostępu, stan, daty baterii i elektrod → `aktywny`.
  4. Osoba postronna skanuje kod bez uprawnień i może tylko zgłosić sygnał (brak, uszkodzenie, zamknięte); dane się nie zmieniają.
  5. Przypomnienia: prośba o potwierdzenie po 183 dniach, `nieaktualny` po 365 dniach, ostrzeżenie 60 dni przed końcem ważności baterii lub elektrod.
  6. Rekord potwierdzony trafia do wykazu ministerstwa, a ten do scalania w portalu (slajd 5, krok 3).
- **Zrzuty:** `02-panel-firmy.jpg`, `10-wynik-zgloszenia-naklejki-linki.jpg`, `11-naklejka.jpg`, `07-naklejki-wydruk-a4.jpg`, `05-qr-dysponent-telefon.jpg`, `08-qr-godziny-dostepu-telefon.jpg`, `18-qr-bateria-i-elektrody-telefon.jpg`, `14-qr-potwierdzone-telefon.jpg`, `17-qr-zgloszenie-problemu-telefon.jpg`.
- **Liczby:** progi z `aed_service/README.md`.
- **Notatki mówcy:** QR jest wyeksponowany zgodnie z prośbą komisji. Docelowo samo zeskanowanie ma zgłaszać miejsce i stan urządzenia.

## Slajd 8. Mapper, deduplikacja i wynik

- **Teza:** Stan początkowy z istniejących źródeł, uczciwie policzony i bez mieszania licencji.
- **Treść:**
  - rejestr po deduplikacji: **18 814** (OSM 18 298 → 18 032, Warszawa 708, Krosno 21, Marki 8, Przemyśl 21, Legionowo 24);
  - **266** połączeń automatycznych (reguły: odległość 151, odległość i podobieństwo 6, numer referencyjny Warszawy 109); **214** par do ręcznego przeglądu (153 kandydatów, 61 konfliktów źródeł); dwóch rekordów z tego samego źródła nigdy nie łączymy automatycznie;
  - do publikacji **781 z 18 814**: 18 032 rekordów wykluczonych przez licencję ODbL, poza tym 3 048 z dostępem prywatnym oraz braki miejscowości (17 959) i nazwy (12 131); powody mogą się nakładać;
  - nowe źródło to jeden wpis w `aed_standard/sources.json` (`docs/dodawanie-zrodla.md`).
- **Zrzuty:** `04-panel-ministerstwa.jpg`, `13-ministerstwo-historia-zadan.jpg`, `01-rejestr-lista.jpg`, `03-rejestr-mapa.jpg`; `[BRAK: wykres „co odpadło z eksportu i dlaczego”]`.
- **Liczby:** `raport.json`: `rekordy_na_zrodlo`, `polaczenia`, `do_przegladu`, `eksport_dane_gov_pl`.
- **Notatki mówcy:** Wynik pokazuje skalę problemu. Rekordów z OpenStreetMap nie publikujemy w zbiorze ministerstwa, dopóki właściciel ich nie potwierdzi.

## Slajd 9. Zachęty i kampania

- **Teza:** Dostawca ma się zgłosić sam, bo coś z tego ma.
- **Treść:**
  - adresaci: producenci i sprzedawcy AED, zarządcy obiektów, samorządy (logo i hasło służą akcji dla dostawców, nie pitchowi – `docs/tips.txt`);
  - zachęty (`kampania/zachety.md`): jedno miejsce raportowania, darmowe przypomnienia o bateriach i elektrodach, ranking i odznaka firmy z aktualnymi danymi (próg: kompletność co najmniej 70 i co najmniej połowa urządzeń `aktywnych`), dla samorządu gotowy standard i walidacja w portalu;
  - punkt odniesienia: akcja InPostu z AED przy Paczkomatach – widoczny znak w przestrzeni publicznej (źródło pierwotne do podania na slajdzie);
  - naklejka z QR niesie znak akcji na każde urządzenie.
- **Zrzuty:** `06-ranking-firm.jpg`, `11-naklejka.jpg`; `[BRAK: logo i hasło]`, `[BRAK: makiety materiałów dla dostawców]`.
- **Liczby:** brak; miary sukcesu akcji: liczba dostawców wykazów, udział rekordów potwierdzonych, średnia kompletność.
- **Notatki mówcy:** Akcja nie obiecuje skutków zdrowotnych. Obiecuje dostawcy mniej pracy, widoczność i uznanie.

## Slajd 10. Ograniczenia

- **Teza:** Wiemy, gdzie są granice, i każda ma następny krok.
- **Treść (pełna lista):**
  - **kod wykazu AED w portalu nie był jeszcze uruchomiony w pełnym stosie** (migracje, formularz, zadanie Celery, `/aed-aggregated`, testy Django) – `[do aktualizacji po uruchomieniu]`;
  - serwer pod domeną: konfiguracja gotowa i sprawdzona składniowo, nieuruchomiona (`docs/wdrozenie-serwer.md`) – `[do aktualizacji]`;
  - eksport to 781 rekordów, z czego 708 z API Warszawy – zbiór jest dziś w praktyce warszawski;
  - wszystkie rekordy rejestru z importu mają status `niepotwierdzony`; status `aktywny` powstaje dopiero po ścieżce zarządcy;
  - średnia kompletność rejestru 39,2 na 100; tylko 100 z 781 rekordów eksportu ma godziny dostępu (wszystkie z API Warszawy);
  - rekordy znane tylko z OpenStreetMap (ODbL) zostają poza eksportem; wymaga to opinii prawnika;
  - typy kolumn w portalu wymagają ręcznej korekty po wgraniu CSV (`nr_budynku`, `kod_terc`, `kod_simc`, `zrodlo_id` jako tekst), bo portal zgaduje typy z wartości (`docs/panel-portalu-krok-po-kroku.md`); zasób zbiorczy AED ma schemat ustawiony od razu;
  - harvester XML i CKAN nie przenoszą flagi wykazu AED (brak `containsAedList` w XSD 1.13); zasób z harvestera oznacza redaktor;
  - plik XLSX wykazu jest sprawdzany dopiero przy scalaniu, nie w formularzu;
  - bez `id_aed` i `zrodlo_id` w wykazie identyfikator zależy od kolejności wierszy;
  - brak podstawy prawnej obowiązku raportowania przez sprzedawców – dobrowolność i zachęty;
  - numer seryjny nie jest publikowany (decyzja otwarta); „10/14 lat żywotności” rozumiemy jako żywotność urządzenia – do potwierdzenia z komisją;
  - wiadomości do zarządców trafiają do skrzynki w panelu ministerstwa, nie są wysyłane e-mailem;
  - usługa AED jest demonstracyjna: jednowątkowa, bez limitu prób logowania;
  - dostępność: axe bez naruszeń w obszarze AED po poprawkach, przejście klawiaturą, 320 px (`frontend/aed-zrzuty/DOSTEPNOSC.md`); bez czytnika ekranu i bez prawdziwego telefonu; nagłówek i stopka portalu mają naruszenia z kodu forka;
  - nikt nie przeszedł jeszcze w przeglądarce kroków instrukcji dla jury od zera (znaczniki `[do sprawdzenia]`);
  - po przeglądzie Codexa (runda 2) nie było rundy potwierdzającej (`docs/przeglad-codex.md`).
- **Zrzut:** `frontend/aed-zrzuty/320px-qr-dysponent.jpg`.
- **Liczby:** `raport.json` (`statusy`, `kompletnosc_srednia`, `rekordy_na_zrodlo`); 100 z 781 i 708 z 781 policzone z `datasets/out/aed_dane_gov_pl.csv`.
- **Notatki mówcy:** Mówimy otwarcie, co działa, a co jest planem.

## Slajd 11. Co dalej

- **Teza:** Ścieżka wdrożenia u ministerstwa jest krótka, bo zmiany są małe i wydzielone.
- **Treść:**
  - łatka `mcod/aed` + pole zasobu do kodu portalu; strona CMS „Wykaz AED” wzorem strony „Wykaz chronionych danych”;
  - `containsAedList` w XSD harvestera 1.14 i w imporcie CKAN – wykazy oznaczają się same;
  - decyzje: jeden czy wiele wykazów na instytucję, wymagany identyfikator w wykazie, publikacja numeru seryjnego;
  - rekomendacja regulacyjna: obowiązek zgłaszania AED przy sprzedaży albo zachęty finansowe;
  - opinia prawna o danych OSM; ścieżka „przejmij punkt” (zarządca potwierdza punkt znany tylko z OSM i dane stają się jego – w usłudze od commitu `838968e`, we frontendzie w toku);
  - uzupełnianie `kod_terc` i `kod_simc` ze współrzędnych; kreator źródła w panelu ministerstwa.
- **Zrzut:** brak.
- **Notatki mówcy:** Każdy punkt to osobna, mała zmiana. Żaden nie wymaga przebudowy portalu.

## Slajd 12. Użycie AI i prawa

- **Teza:** Rozwiązanie jest autorskie; AI było narzędziem pod kontrolą zespołu.
- **Treść** (`docs/uzycie-ai.md`): Claude Code w roli asystenta programisty (sesja prowadząca i agenty podrzędne); niezależne przeglądy kodu Codexem (`docs/przeglad-codex.md`); ludzie prowadzili rozmowę z komisją, decydowali o kierunku i odbierali wyniki; logo, nazwa, hasło i księga znaku po stronie zespołu; AI niczego nie publikowało na dane.gov.pl; kod OpenAEDMap (AGPL) nie został skopiowany; prawa przechodzą na Ministra Cyfryzacji.
- **Zrzut:** `[BRAK: fragment tabeli „Co powstało z użyciem AI”]`.
- **Notatki mówcy:** Regulamin dopuszcza AI, jeśli praca jest efektem analizy i pracy człowieka. Pokazujemy, co wygenerowano i co kto sprawdził.

---

## Zrzuty z portalu do zrobienia

Kolejność odpowiada `docs/wykaz-aed-w-portalu.md` („Zrzuty ekranu do prezentacji”) i `docs/panel-portalu-krok-po-kroku.md`.

| Plik | Co | Slajd |
|---|---|---|
| `portal-01-zbior-zbiorczy.png` | zbiór „Krajowy wykaz defibrylatorów AED – wykaz zbiorczy” na liście zbiorów ministerstwa | 1 |
| `portal-02-formularz-wykaz-aed.png` | formularz zasobu w panelu z polem „Wykaz AED” i tekstem pomocy | 4 |
| `portal-03-bledy-wykazu-krosno.png` | błędy po polsku po wgraniu pliku z Krosna | 5 |
| `portal-04-dry-run-raport.png` | wynik `create_main_aed_resource --dry-run` | 5 |
| `portal-05-aed-aggregated.png` | odpowiedź `GET /aed-aggregated` | 5 |
| `portal-06-tabela.png` | widok tabeli zasobu zbiorczego | 5 |
| `portal-07-mapa.png` | mapa zasobu zbiorczego | 5 |
| `portal-08-api-i-otwartosc.png` | `/resources/<id>/data` i ocena otwartości | 5 |
| `portal-09-harvester-xml.png` | źródło XML: „Sprawdź poprawność pliku” i zakładka „Importy” (opcjonalnie) | 5 |
| `portal-10-strona-glowna.png` | strona główna forka pod domeną (dowód „strona taka sama jak dane.gov.pl”) | 1 lub 4 |

Uwaga o liczbach: panel ministerstwa w usłudze (zrzut `04`) pokazuje mniej rekordów niż `raport.json`, bo usługa nie wystawia 3 048 rekordów z dostępem „prywatny”. Na slajdach podajemy liczby z `raport.json` i podpisujemy źródło. `[do sprawdzenia: ujednolicić nowym zrzutem po tym samym stanie bazy]`.
