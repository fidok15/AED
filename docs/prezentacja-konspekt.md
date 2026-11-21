# Prezentacja – konspekt slajd po slajdzie

Wymóg zadania: min. 5 slajdów z dowodami na realizację wymagań technicznych (zrzuty ekranu), opis funkcjonalności z krokami użytkownika, lista ograniczeń. Proponujemy 10 slajdów. Kryterium „Prezentacja” to 5% oceny, ale slajdy są też nośnikiem dowodów dla pozostałych kryteriów.

Narracja sprzedażowa: **problem → dlaczego obecne dane zawodzą (z liczbami) → proces → standard danych → dowód zgodności z dane.gov.pl → kampania i zachęty → ograniczenia → deklaracja użycia AI.**

Zasady: liczby tylko z naszych danych (`datasets/out/raport.json`, stan z budowy zbioru 21.11.2026) albo ze źródła pierwotnego (zasada 10 w `CLAUDE.md`); bez obietnic uratowanych istnień (zasada 9). Źródła danych w pomiarze: cztery zbiory samorządowe z dane.gov.pl (Krosno, Marki, Przemyśl, Legionowo), API Warszawy i OpenAEDMap (OpenStreetMap).

Dostępne zrzuty (katalog `frontend/aed-zrzuty/`): `01-rejestr-lista.jpg`, `02-panel-firmy.jpg`, `03-rejestr-mapa.jpg`, `04-panel-ministerstwa.jpg`, `05-qr-dysponent-telefon.jpg`. Zrzuty brakujące (portal lokalny, naklejka, logo, audyt dostępności) oznaczono `[BRAK: ...]`.

---

## Slajd 1. Tytuł i teza

- **Nagłówek:** „[NAZWA AKCJI]: jeden zbiór o AED, za który ktoś odpowiada” (nazwa akcji do wyboru, kandydaci w `kampania/nazwa-i-haslo.md`)
- Punkty:
  - zadanie: ogólnopolski, otwarty, aktualny zbiór AED na dane.gov.pl;
  - nasza odpowiedź: proces, w którym dane wprowadza podmiot odpowiedzialny, a Ministerstwo publikuje jeden zbiór;
  - w pakiecie: standard danych, działający prototyp (rejestr, panel firmy, strona QR, panel ministerstwa), akcja dla dostawców.
- **Zrzut dowodowy:** `frontend/aed-zrzuty/01-rejestr-lista.jpg`; `[BRAK: logo akcji]`
- **Notatki mówcy:** Zaczynamy od tezy, nie od technologii: dziś nikt nie odpowiada za dane o AED, a my pokazujemy, jak to zmienić. W kilka minut przejdziemy od sprzedaży urządzenia do publikacji zbioru. Na końcu pokażemy, jak sprawić, żeby dostawcy zgłosili się sami.

## Slajd 2. Problem

- **Nagłówek:** „Dane są rozproszone i nikt za nie nie odpowiada”
- Punkty:
  - sytuacja z zadania: 3 marca w centrum Warszawy świadkowie szukali AED, część urządzeń była zamknięta na klucz (opis z treści zadania);
  - nie istnieje kompletna mapa, jest kilka baz mniej lub bardziej kompletnych (treść zadania);
  - diagnoza organizatora: dane niezweryfikowane, „nikt nie bierze za nie odpowiedzialności” (`docs/tips.txt`);
  - nasz pomiar: zebraliśmy **18 814 rekordów** z sześciu źródeł (po usunięciu 266 powtórzeń) i **żaden z nich nie ma potwierdzenia przez odpowiedzialny podmiot** (wszystkie mają status `niepotwierdzony`).
- **Zrzut dowodowy:** `frontend/aed-zrzuty/04-panel-ministerstwa.jpg` (tabele „według statusu” i „według źródła”)
- **Notatki mówcy:** Problem to nie tylko brak danych, ale brak właściciela danych. Samo sklejenie plików nie rozwiąże sprawy, bo dane.gov.pl wymaga dostawcy, który bierze odpowiedzialność za zbiór. Dlatego budujemy proces, a nie jednorazowy plik.

## Slajd 3. Dlaczego obecne dane zawodzą: wyniki naszego pomiaru

- **Nagłówek:** „Pola ratunkowe są puste, a wspólnej struktury nie ma”
- Punkty (z `datasets/out/raport.json`, `pokrycie_pol`; udział rekordów z wypełnionym polem):

| Źródło | Rekordów | Godziny dostępu | Dostęp (publiczny/ograniczony) | Producent | Numer seryjny | Daty ważności baterii |
|---|---|---|---|---|---|---|
| 4 zbiory samorządowe z dane.gov.pl (Krosno 21, Marki 8, Przemyśl 21, Legionowo 24) | 74 | 0% | 0% | 0% | 0% | 0% |
| API Warszawy | 708 | 14,1% | 100% | 98% | 0% | 0% |
| OpenStreetMap | 18 298 | 37% | 92,4% | 1,9% | 0% | 0% |

  - **Średnia kompletność rekordu (0–100):** samorządy 31–36, OSM 38,8, Warszawa 53,2; rejestr po scaleniu 39,2; zbiór do publikacji 51,4;
  - OSM: tylko 33% rekordów ma nazwę miejsca, a miejscowość podaje zaledwie 0,4% (większość to same współrzędne);
  - jakość plików samorządowych (`naprawy_danych`): zbiór Marek miał 8 wierszy ujętych w jedną parę cudzysłowów, a w 7 z 8 rekordów szerokość i długość geograficzna były zamienione miejscami; jeden punkt (szkoła podstawowa) leżał 293 km od pozostałych, więc usunęliśmy współrzędne; dwa różne adresy miały identyczne współrzędne (zostawione do sprawdzenia u dostawcy);
  - wnioski: godziny dostępu, czyli to, czego szukają świadkowie, prawie nigdzie nie ma, a numeru seryjnego i terminów baterii nie ma w żadnym zbiorze; stąd potrzeba kanału sprzedawcy i potwierdzenia zarządcy.
- **Zrzut dowodowy:** `[BRAK: wykres z macierzy pokrycia pól; do zrobienia z raport.json]`; pomocniczo `frontend/aed-zrzuty/04-panel-ministerstwa.jpg` (porównanie dwóch rekordów tego samego miejsca)
- **Notatki mówcy:** To nie są opinie, tylko pomiar na prawdziwych plikach źródłowych. W czterech zbiorach samorządowych nie ma ani jednego rekordu z godzinami dostępu, a w żadnym źródle nie ma numeru seryjnego ani terminu baterii. Dodatkowo musieliśmy naprawiać błędy techniczne, np. zamienione współrzędne w pliku Marek.

## Slajd 4. Proces od sprzedaży do zbioru

- **Nagłówek:** „Sprzedawca → naklejka QR → zarządca → zbiór Ministerstwa”
- Punkty (kroki użytkownika):
  1. Producent lub sprzedawca zgłasza urządzenia przy sprzedaży plikiem CSV z raportem walidacji po polsku (profil `sprzedaz`), rekord dostaje identyfikator `AED-…` i status `zgloszony`.
  2. System generuje naklejkę z kodem QR, a zarządca dostaje link z jednorazowym tokenem (w prototypie link widać w skrzynce ministerstwa).
  3. Zarządca potwierdza w trzech krokach: lokalizacja (także z telefonu), godziny dostępu, stan urządzenia; rekord staje się `aktywny`.
  4. Ministerstwo prowadzi rejestr, przegląda duplikaty, uruchamia przypomnienia i mapper, pobiera zbiór do publikacji na dane.gov.pl.
  - brak potwierdzenia w terminie: prośba po 183 dniach, `nieaktualny` po 365 dniach.
- **Zrzuty dowodowe:** `frontend/aed-zrzuty/02-panel-firmy.jpg`, `frontend/aed-zrzuty/05-qr-dysponent-telefon.jpg`, `frontend/aed-zrzuty/04-panel-ministerstwa.jpg`; `[BRAK: zrzut raportu walidacji z wgranym plikiem z błędami]`; `[BRAK: naklejka QR (SVG)]`
- **Notatki mówcy:** To jest sedno rozwiązania: wpisuje ten, kto zna urządzenie (sprzedawca), a miejsce potwierdza ten, kto je zna (zarządca). Ministerstwo agreguje to, co potwierdzone. Cykliczne przypomnienia utrzymują dane przy życiu.

## Slajd 5. Standard danych i wzorzec

- **Nagłówek:** „Jedna struktura dla wszystkich źródeł”
- Punkty:
  - schemat w wersji 0.2.0: **38 pól**, jeden wiersz = jedno urządzenie; CSV UTF-8, daty `RRRR-MM-DD`, współrzędne WGS84 w osobnych kolumnach;
  - pola z rozmowy z komisją: identyfikator, producent, model, numer seryjny, data produkcji, daty ważności elektrod i baterii, współrzędne, godziny dostępu, kto wprowadził;
  - dwa profile wymagalności: `sprzedaz` (8 pól wymaganych) i `publikacja` (8 pól); status `aktywny` wymaga dostępu, godzin dostępu i daty weryfikacji;
  - `wzorzec-aed.xlsx` (arkusze: Dane, Słownik pól, Słowniki, Mapowanie źródeł, Instrukcja) i walidator wynikają ze schematu `aed_standard/schema.json`; nazwy kolumn adresu zgodne ze zbiorem Legionowa.
- **Zrzut dowodowy:** `[BRAK: arkusz wzorzec/wzorzec-aed.xlsx, karta „Słownik pól”]`; `[BRAK: wynik walidatora w terminalu dla wzorzec/przyklad-sprzedawca-bledy.csv: „poprawne: 2, błędy: 8, ostrzeżenia: 1”]`
- **Notatki mówcy:** Standard jest zgodny z istniejącym zbiorem Legionowa, więc jest jego rozszerzeniem, a nie konkurencją. Walidator mówi po polsku, co poprawić w którym wierszu i polu. Wszystko wynika z jednego schematu, więc formularze, walidator i szablon XLSX nie rozjeżdżają się.

## Slajd 6. Dowód zgodności z dane.gov.pl

- **Nagłówek:** „Publikujemy tak, jak pozwala portal”
- Punkty:
  - dostawcą zbioru krajowego jest Ministerstwo; firmy raportują przez konta firmowe; obywatel bez uprawnień wysyła tylko sygnał dla właściciela (skan QR bez tokenu nie edytuje danych);
  - zbiór do publikacji: `datasets/out/aed_dane_gov_pl.csv`, **781 rekordów**, 38 kolumn, tylko format maszynowy; zachowane licencje źródeł (CC0 1.0, CC BY 4.0) w kolumnie `licencja`;
  - nie publikujemy numeru seryjnego, e-maila i telefonu dysponenta w eksporcie; prywatne AED i rekordy z OpenStreetMap (ODbL) zostają w rejestrze;
  - moduł AED działa w forku frontendu portalu (nagłówek, stopka i nawigacja dane.gov.pl); reszta portalu jest czytana z publicznego API tylko do odczytu;
  - integracja w backendzie portalu to **plan** (`docs/integracja-portal-backend.md`: 10 kroków z szacunkiem godzin, nowy typ instytucji wzorem typu `developer`), nie wdrożenie.
- **Zrzut dowodowy:** `frontend/aed-zrzuty/01-rejestr-lista.jpg`, `frontend/aed-zrzuty/03-rejestr-mapa.jpg`; `[BRAK: lokalny portal dane.gov.pl z opublikowanym zbiorem (od kolegi odpowiedzialnego za portal)]`
- **Notatki mówcy:** To odpowiedź na uwagę organizatora, że nie można przebudować mechaniki portalu tak, żeby każdy publikował. Dostawcą jest instytucja, a my dajemy jej narzędzia. Uczciwie mówimy, że wbudowanie w backend portalu to plan wdrożenia, a prototyp pokazuje cały proces w osobnej usłudze.

## Slajd 7. Kampania i zachęty dla dostawców

- **Nagłówek:** „[NAZWA AKCJI]: co ma firma, która zgłasza AED”
- Punkty:
  - cel: zgłaszają się producenci i sprzedawcy AED, zarządcy i samorządy (nie opinia publiczna);
  - zachęty (`kampania/zachety.md`): jedno miejsce raportowania, odznaka dla firmy z aktualnymi danymi (próg: kompletność co najmniej 70 i co najmniej połowa urządzeń `aktywnych`), ranking sprzedawców, darmowe przypomnienia o bateriach i elektrodach;
  - punkt odniesienia: InPost „Helpbox 365” na Paczkomatach (komunikat z 13.08.2025): pożyczamy widoczny znak w przestrzeni publicznej i narrację o „białych plamach”;
  - naklejka z QR niesie znak akcji na każdym urządzeniu.
- **Zrzuty dowodowe:** `frontend/aed-zrzuty/02-panel-firmy.jpg`; `[BRAK: logo i hasło akcji]`; `[BRAK: makieta naklejki QR]`; `[BRAK: odznaka dostawcy i baner dla samorządu]`. Odznaka i ranking są w API (`GET /api/aed/sprzedawcy`); widoku w interfejsie nie znaleziono: `[do sprawdzenia]`
- **Notatki mówcy:** Akcja nie obiecuje skutków zdrowotnych, tylko wartość dla dostawcy: widoczność, mniej pracy, uznanie. Logo trafia na urządzenia i do komunikacji z dostawcami. Mierzymy liczbę dostawców, kompletność i udział potwierdzonych rekordów.

## Slajd 8. Zakres i kompletność: wynik

- **Nagłówek:** „Zbiór krajowy z pierwszych sześciu źródeł”
- Punkty:
  - rejestr po deduplikacji: **18 814 rekordów** (OpenStreetMap 18 298 → 18 032, Warszawa 708, Krosno 21, Marki 8, Przemyśl 21, Legionowo 24);
  - **266 automatycznych połączeń** (230 OSM + Warszawa, 36 OSM + zbiory samorządowe); reguły: odległość 151, odległość i podobieństwo 6, numer referencyjny Warszawy 109; **214 par do ręcznego przeglądu** (153 kandydatów, 61 konfliktów źródeł);
  - średnia kompletność: rejestr 39,2, zbiór do publikacji 51,4 (z 0–100);
  - do publikacji trafia **781 z 18 814** rekordów: 18 033 wykluczonych, z czego 18 032 z powodu licencji ODbL, a ponadto 3 048 z dostępem prywatnym, brak miejscowości (17 959) lub nazwy (12 131); powody mogą się nakładać;
  - w zbiorze do publikacji tylko 100 z 781 rekordów (12,8%) ma godziny dostępu (wszystkie z API Warszawy): tu widać, po co jest potwierdzenie zarządcy.
- **Zrzut dowodowy:** `frontend/aed-zrzuty/04-panel-ministerstwa.jpg`; `frontend/aed-zrzuty/01-rejestr-lista.jpg`; `[BRAK: wykres „ile rekordów odpadło z eksportu i dlaczego”]`
- **Notatki mówcy:** Każda liczba na tym slajdzie pochodzi z naszego raportu. Deduplikacja nigdy nie łączy automatycznie dwóch rekordów z tego samego źródła, bo w jednym budynku bywa kilka urządzeń. Rekordy bez potwierdzenia odpowiedzialnego podmiotu i z licencją ODbL nie trafiają do eksportu na dane.gov.pl.

## Slajd 9. Ograniczenia i dostępność

- **Nagłówek:** „Co działa, a czego jeszcze nie ma”
- Punkty (lista uczciwa, do uzupełniania w miarę pracy):
  - prototyp działa **lokalnie w Dockerze**, bez publicznego adresu;
  - wiadomości do zarządców trafiają do **skrzynki w panelu ministerstwa**, nie są wysyłane e-mailem;
  - **pełna integracja w backendzie portalu to plan** (`docs/integracja-portal-backend.md`), nie wdrożenie;
  - rekordy znane tylko z OpenStreetMap (ODbL) zostają **poza eksportem** do dane.gov.pl ze względów licencyjnych; wymaga opinii prawnika;
  - żaden rekord zbioru z surowych źródeł nie jest jeszcze potwierdzony przez zarządcę; status `aktywny` powstaje dopiero po ścieżce potwierdzenia;
  - brak podstawy prawnej obowiązku raportowania przez sprzedawców, więc opieramy się na dobrowolności i zachętach; rekomendacja regulacyjna na slajdzie „co dalej”;
  - numer seryjny nie jest w eksporcie otwartym; decyzja otwarta; „10/14 lat żywotności” rozumiemy jako żywotność urządzenia, do potwierdzenia z komisją;
  - usługa demonstracyjna: jednowątkowa, bez limitu prób logowania;
  - odznaka i ranking sprzedawców są w API; w interfejsie nie znaleziono osobnego widoku mapy sprzedawców `[do sprawdzenia]`;
  - **dostępność (WCAG 2.2 AA) i responsywność:** interfejs wykorzystuje komponenty i układ portalu, strona potwierdzenia jest przygotowana pod telefon (`05-qr-dysponent-telefon.jpg`); formalny audyt (axe, Lighthouse, test klawiaturą na 320 px) `[do sprawdzenia: raportu nie ma w repozytorium]`.
- **Zrzut dowodowy:** `frontend/aed-zrzuty/05-qr-dysponent-telefon.jpg`; `[BRAK: raport audytu dostępności]`
- **Notatki mówcy:** Mówimy otwarcie, co jest zrobione, a co jest planem. Granice rozwiązania są częścią uczciwej oferty, a każda z nich ma kolejny krok. Dostępność deklarujemy tylko w zakresie, który potwierdzi raport.

## Slajd 10. Deklaracja użycia AI i prawa

- **Nagłówek:** „Autorskie rozwiązanie zespołu; AI jako narzędzie”
- Punkty (z `docs/uzycie-ai.md`):
  - narzędzie: Claude Code jako asystent programisty; ludzie prowadzili rozmowę z komisją, decydowali o kierunku, wybierali źródła, odbierali i weryfikowali wyniki;
  - AI pomagało przy: researchu, szkicu standardu danych, walidatorze, mapperze i deduplikacji, usłudze API, module AED we frontendzie, konfiguracji Dockera, materiałach kampanii (propozycje, brief, szablon księgi znaku) i dokumentacji; weryfikacja: testy na prawdziwych plikach, przejście ścieżek w przeglądarce, przegląd zespołu;
  - **logo, nazwa, hasło i księga znaku:** projekt w całości po stronie zespołu; AI nie tworzyło znaku graficznego;
  - AI nie publikowało niczego na dane.gov.pl; prawa do rozwiązania przechodzą na Ministra Cyfryzacji; kod OpenAEDMap (AGPL) nie został skopiowany.
- **Zrzut dowodowy:** `[BRAK: fragment docs/uzycie-ai.md (tabela „Co powstało z użyciem AI”)]`
- **Notatki mówcy:** Zadanie dopuszcza AI pod warunkiem, że praca jest autorskim rozwiązaniem zespołu z prawami po jego stronie; tak to dokumentujemy. Pokazujemy, co wygenerowano i co sprawdził człowiek. Instrukcja dla jury prowadzi krok po kroku przez dowody.

---

## Lista zrzutów: co jest, czego brakuje

| Zrzut | Plik | Slajd |
|---|---|---|
| Rejestr: lista | `frontend/aed-zrzuty/01-rejestr-lista.jpg` | 1, 6, 8 |
| Panel firmy | `frontend/aed-zrzuty/02-panel-firmy.jpg` | 4, 7 |
| Rejestr: mapa | `frontend/aed-zrzuty/03-rejestr-mapa.jpg` | 6 |
| Panel ministerstwa | `frontend/aed-zrzuty/04-panel-ministerstwa.jpg` | 2, 3, 4, 8 |
| Strona QR na telefonie | `frontend/aed-zrzuty/05-qr-dysponent-telefon.jpg` | 4, 9 |
| **Do zrobienia:** raport walidacji z błędami (panel firmy), naklejka QR, arkusz XLSX, walidator w terminalu, wykres pokrycia pól, wykres wykluczeń z eksportu, lokalny portal dane.gov.pl, logo, naklejka/odznaka/baner, audyt dostępności, fragment `docs/uzycie-ai.md` | – | 3, 4, 5, 6, 7, 8, 9, 10 |

Uwaga o liczbach: `raport.json` podaje 18 814 rekordów w rejestrze krajowym, a usługa AED (panel ministerstwa, zrzut `04`) pokazuje ok. 15,8 tys., bo nie wystawia 3 048 rekordów z dostępem „prywatny”. Na slajdach 2 i 8 używamy liczb z `raport.json` i podpisujemy ich źródło; zrzut `04` pokazuje stan usługi. [do sprawdzenia: ujednolicić przed oddaniem, np. nowym zrzutem po tym samym stanie bazy].
