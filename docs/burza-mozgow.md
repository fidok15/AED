# Burza mózgów – iteracje (21.11, wieczór)

Plik roboczy: pomysły i wnioski z kolejnych przejść przez wytyczne. Nie jest decyzją zespołu – decyzje trafiają do `CLAUDE.md`.

Hierarchia źródeł (od najważniejszego):

1. rozmowa z komisją 21.11 ok. 17:00 (`CLAUDE.md`, rozdział „Czego chce komisja”),
2. hasła mentorów z wieczora 21.11 (lista w `CLAUDE.md`, „Wskazówki komisji”),
3. wskazówki organizatora (`docs/tips.txt`, `docs/OdMentora.md`),
4. treść zadania i regulamin (PDF w `docs/`).

Legenda: **koszt** S (do 1 h), M (kilka godzin), L (ponad dzień); **wpływ** – kryterium oceny, którego dotyczy.

---

## Podsumowanie – najważniejsze wnioski (stan: noc 21/22.11; wersja końcowa z 7:00 – na końcu pliku)

Poprawki (błędy lub ryzyka w tym, co już mamy):

1. **Licencja zbioru z harwestera = CC0**, a 715 z 781 rekordów ma CC BY 4.0 – w zasilaniu brakuje `<conditions><source>true</source></conditions>` (iteracja 21).
2. **Strona QR i naklejka bez „112”** – osoba w sytuacji nagłej zobaczy formularz; blok „Zadzwoń 112” na górze strony i napis na naklejce (iteracja 42).
3. **Prototyp tylko przez Dockera**, a `tips.txt` mówi, że jury nie skonfiguruje środowiska – publiczny adres to decyzja ludzi (iteracja 10).
4. **`.gitattributes` jest błędny** (składnia pliku konfiguracyjnego) – test nie przechodzi u jurora z `autocrlf=true`; sprawdzone na świeżych klonach (iteracja 31).
5. **Publiczny ranking firm** (z linkiem do oferty w `zachety.md`) koliduje z „nie premiować danych” – neutralna lista dostawców (iteracje 2, 39).
6. **Dwie definicje eksportu publikacyjnego** – pola niepublikowane żyją w kodzie usługi, nie w `schema.json` (iteracja 43); **`wprowadzajacy_nazwa` puste** we wszystkich 781 rekordach, a komisja wymieniła to pole wprost (iteracja 46).
7. **Wycofane rekordy znikają z eksportu** – „dane stare mają pozostać” i ciągłość identyfikatorów wymagają, by zostały ze statusem i powiązaniem (iteracje 2, 23).
8. **Raporty importu harwestera nie idą e-mailem** (niezaimplementowane w 2.63.0) – monitor publikacji po stronie rejestru (iteracja 45).

Szanse (mechanizmy portalu, które już istnieją):

9. **„Wykaz” z hasła mentorów = „Propozycje nowych danych”** – głosują tylko pełnomocnicy instytucji, więc to narzędzie mobilizowania dostawców; pętla na 4 zrzutach (iteracje 3, 25).
10. **Pakiet dostawcy jak w programach ministerstwa** (rzeczy znalezione, ceny mieszkań): instrukcja profilu, instrukcja panelu administracyjnego, wzorzec XLSX/CSV, szablon XML – publikowany jako strona bazy wiedzy w CMS portalu (iteracje 34, 52).
11. **Interpelacja 20440 do Ministra Cyfryzacji** pyta o połączenie baz AED i odpowiedzialność za dane – nasze rozwiązanie na nią odpowiada (iteracja 34).
12. **Gotowe w portalu, do pokazania**: osadzanie mapy zasobu na stronie gminy („Umieść na swojej stronie”, iteracja 51), liczniki pobrań jako informacja zwrotna dla dostawcy (iteracja 27), dokumenty uzupełniające ze słownikiem pól przy zbiorze (iteracja 49), 4 gwiazdki otwartości automatycznie (iteracja 27).

Sprostowania nocy (ważne przy czytaniu wcześniejszych iteracji):

- dowody WCAG i responsywności **już są** – `frontend/aed-zrzuty/DOSTEPNOSC.md` (it. 68); w dokumentach trzeba je tylko podlinkować;
- link zarządcy **nie jest jednorazowy** (ważny 90 dni, wielokrotny) – poprawić trzy dokumenty (it. 74);
- widok „dostępne teraz” już jest na mapie (it. 22); głosować przy propozycjach danych mogą tylko pełnomocnicy (it. 25); raporty importu harwestera nie idą e-mailem (it. 45); „zachowaj najstarszy `id_aed`” był złym pomysłem – wygrywa id z naklejki (it. 23).

Fakty do slajdów (nasze dane, zasada 10):

13. Zbiór krajowy to w 91% Warszawa; miejsca komercyjne to 0,3% rekordów (iteracje 30, 37); najlepszy otwarty rekord ma kompletność 62/100, rekord po ścieżce sprzedawca → zarządca 97/100 (iteracje 46, 47); najczystszy zbiór gminy ma w portalu tytuł „Zdrowie” (iteracja 46); **Marki skopiowały plik Krosna jako szablon – razem z jednym punktem z Krosna** (iteracja 80).

Pytania do mentorów: iteracja 7. Ograniczenia na slajd: iteracja 41. Stan punktów rozmowy z komisją: iteracja 50.

---

## Iteracja 1. Czego jeszcze nie wyczytaliśmy z treści zadania

Przeczytane ponownie zdania z PDF, które dotąd miały mało uwagi:

- „Zbierz dane z wielu rozproszonych źródeł **ze wskazaniem ich referencyjnego zakresu**” (podkreślone w oryginale). Mamy `sources.json` i `raport.json` (`pokrycie_pol`), ale jury nie widzi tego w portalu ani w interfejsie jako „zakres referencyjny źródła”.
- „Użytkownikiem rozwiązania są **służby ratownicze**, ale także każdy z nas”. Prototyp mówi o ministerstwie, firmach i zarządcach. Służby ratownicze pojawiają się tylko w researchu (112/997/998 używają dziś OpenAEDMap).
- „trzeba wiedzieć, gdzie jest najbliższe urządzenie, **czy jest dostępne i czy działa**”. Mamy pola `dostep`, `godziny_dostepu`, `stan`, ale nie ma widoku, który odpowiada na pytanie „który AED mogę użyć teraz”.
- Sposób testowania: „Uruchomienie prototypu mechanizmu i weryfikacja wymogów”. Słowo **mechanizmu** – jury chce zobaczyć działający proces, nie tylko ekrany.

Pomysły:

| # | Pomysł | Koszt | Wpływ |
|---|---|---|---|
| 1.1 | **Zakres referencyjny źródła jako dane.** Drugi zasób w zasilaniu XML: `zrodla.csv` – jedno źródło na wiersz: dysponent, licencja, liczba rekordów przed i po deduplikacji, pokrycie każdego pola (z `raport.json`), data pobrania. Ten sam plik jako tabela w panelu ministerstwa. Dosłownie realizuje podkreślone zdanie zadania i trafia do portalu mechanizmem portalu. | S–M | temat 15%, zgodność 30% |
| 1.2 | **Widok „dostępne teraz”** w rejestrze: filtr po `godziny_dostepu` (parser już jest: `aed-hours.ts`) i `dostep=publiczny`. Scenariusz z PDF (zamknięte AED w centrum Warszawy, 3 marca) jako pierwszy slajd i pierwsze kliknięcie jury. | S | temat, kreatywność |
| 1.3 | **Persona „dyspozytor 112”** w prezentacji: dziś podkład mapowy z OpenAEDMap (odpowiedź MSWiA na interpelację 16205); po wdrożeniu – zbiór ministerstwa przez API dane.gov.pl, z polem `stan`, godzinami i datą weryfikacji. Bez budowania integracji, tylko kontrakt: „ten sam CSV, ten sam adres, codziennie”. | S | temat |
| 1.4 | **Demo „mechanizmu” jedną komendą:** skrypt, który na czystej bazie wykonuje zgłoszenie CSV → potwierdzenie QR → zapis zasilania → (opcjonalnie) import w lokalnym portalu i wypisuje, co się stało. Jury zobaczy proces w terminalu nawet bez przeglądarki. | M | prezentacja, zgodność |

## Iteracja 2. Hasła mentorów – drugie czytanie, konflikty z tym, co mamy

| Hasło | Co mamy | Konflikt / luka | Pomysł |
|---|---|---|---|
| „Portal ma zbierać dane od różnych dostawców” | jeden dostawca (ministerstwo) + mapper | komisja o 17:00 mówiła „ministerstwo zbiera”; mentorzy mówią „portal od różnych dostawców” | **dwa poziomy, oba przez portal**: (a) duży dysponent z własnym systemem (sieć sklepów, PKP, InPost) wystawia własne zasilanie XML w naszym standardzie jako źródło danych w panelu portalu – portal to obsługuje natywnie; (b) mapper ministerstwa czyta zbiory AED z portalu po tagu kampanii i składa zbiór krajowy. Jeden standard, dwa kanały, zero zmian w portalu. |
| „Prasowanie danych, aby id się nie powtórzyło” | `make_id(zrodlo, zrodlo_id)`, deduplikacja | **przy scaleniu przeżywa id źródła o najwyższym priorytecie** (`dedup.py:171`). Gdy później zgłosi się sprzedawca urządzenia, które było w zbiorze Warszawy, opublikowany `id_aed` zmieni się – konsument (112, aplikacja) zobaczy „zniknięcie” i „nowe urządzenie”. | **id wieczny:** przy scaleniu zostaje najstarszy opublikowany `id_aed`, a pozostałe trafiają do kolumny `id_aed_scalone` (lista). Test: rekord Warszawy + późniejsze zgłoszenie sprzedawcy → ten sam `id_aed`. Koszt M (mapper potrzebuje poprzedniego stanu – jest w bazie usługi). |
| „Nie można wybitnie premiować jakichś danych” | publiczny **ranking firm** (`!sellers`: „Ranking firm według średniej kompletności danych”) i mapa siedzib firm | państwowy portal, który publicznie szereguje prywatne firmy, może być odebrany jako promowanie wybranych podmiotów (i ich produktów) | ranking zastąpić **listą dostawców danych w kolejności alfabetycznej** z neutralnym znakiem „dane aktualne” przy progu; pozycję w rankingu widzi tylko sama firma i ministerstwo. Nie włączać `is_promoted` dla zbioru AED. |
| „Nie ma zaburzyć stylistyki strony” | moduł AED w forku frontendu | w `pages/aed` są własne kolory (`#1d7a3a`, `#c25400`, `#0052a5`, `#f4f6fb`) | przegląd: zamienić własne kolory na zmienne motywu portalu; sprawdzić tryb wysokiego kontrastu portalu (portal ma przełącznik). |
| „Dane stare mają pozostać” | eksport pomija `status = 'wycofany'` (`publication_csv`) | rekord znika ze zbioru – konsument nie wie, czy AED usunięto, czy to błąd | **wycofane zostają w zbiorze ze statusem** (pomysł C6 z researchu). 112 filtruje po statusie. Zmiana w jednym zapytaniu + test. Do decyzji: jak długo trzymać wycofane (np. 12 mies.). |
| „Flaga, która nie jest fakultatywna / kategorie” | flagi zbioru ustawione jawnie w zasilaniu | możliwa druga interpretacja: w **naszym standardzie** ma być obowiązkowe pole-kategoria, np. typ miejsca (szkoła, urząd, sklep, transport, sport, ochrona zdrowia) | dodać `kategoria_miejsca` ze słownikiem (zgodny z kategoriami OSM `amenity`/`shop` przy mapowaniu) – do potwierdzenia u mentora, którą interpretację miał na myśli. |
| „Dostęp do panelu administratora / adres panelu” | panel lokalnie pod `localhost:8001` | jury nie ma jak wejść | w instrukcji dla jury: adres, konto, 3 kliknięcia (DATA SOURCES → raport importu → zbiór). Jeśli prototyp nie będzie publiczny – nagranie ekranu 60 s. Dodatkowo: firmy w procesie docelowym pracują w **panelu dostawcy dane.gov.pl** (admin) jako redaktorzy swojej instytucji – nasze „konto firmy” to w docelowym wdrożeniu konto w tym panelu. |
| „Zautomatyzowanie procesów” | harmonogram usługi, harwester portalu | brak automatycznego odkrywania nowych źródeł | **odkrywanie źródeł:** zadanie cykliczne pyta API portalu (`/search?q=defibrylator`, `?q=AED`), porównuje z `sources.json` i dopisuje do raportu „nowe zbiory-kandydaci” do zatwierdzenia przez człowieka. |
| „Gdzieś na portalu jest wykaz i można zmobilizować rozwiązanie” | interpretacja: PoCoTo | niepewne | trzy hipotezy do sprawdzenia na portalu: (a) PoCoTo – zgłoszenie rozwiązania jako przykładu wykorzystania; (b) **wykaz instytucji (dostawców)** – lista, z której można zmobilizować dostawców (kampania celowana do gmin, które już publikują na portalu, ale nie AED); (c) „Zgłoś propozycję nowych danych” (`suggestions`). |

## Iteracja 3. „Wykaz, gdzie można zmobilizować rozwiązanie” – sprawdzone w kodzie portalu

Publiczne API dane.gov.pl nie odpowiadało z naszego środowiska (brak połączenia), więc liczby z produkcji są do sprawdzenia. W kodzie portalu znalazły się trzy „wykazy”:

| Kandydat | Co to jest w kodzie | Pasuje do hasła? |
|---|---|---|
| **Propozycje nowych danych** (`suggestions`, ekran „Propozycje nowych danych”) | obywatel zgłasza „Zaproponuj dane”; redakcja przyjmuje propozycję (`AcceptedDatasetSubmission`), może ją opublikować dla wszystkich (`is_published_for_all`); użytkownicy głosują plus/minus (`feedback_counters`, `suggestions/models.py:256`); dostawca zamyka sprawę komentarzem i datą „publikacja zakończona” | **najlepiej** – to publiczny wykaz, a głosy mobilizują dostawców |
| PoCoTo (`showcases`) | wykaz przykładów ponownego wykorzystania danych + formularz „Zaproponuj” | dobrze, ale to wykaz *rozwiązań*, nie mobilizacja dostawców |
| Wykaz chronionych danych (DGA) | flaga zasobu „zawiera wykaz chronionych danych” | słabo – dotyczy danych chronionych |

Pomysły:

- **3.1 Domknąć pętlę mechanizmem portalu (koszt S, wpływ: zgodność 30%).** W lokalnym portalu: (1) propozycja „Ogólnopolski zbiór o defibrylatorach AED” w „Propozycjach nowych danych”, (2) redakcja przyjmuje i publikuje dla wszystkich, (3) głosy „plus”, (4) po imporcie z harwestera status „publikacja zakończona” z linkiem do zbioru. Cztery zrzuty = historia „obywatel prosi → ministerstwo dostarcza” w całości na mechanizmach portalu.
- **3.2 Kampania obywatelska przez wykaz (S).** Hasło do kampanii: „Poprzyj dane o AED w swojej gminie” – link do propozycji na portalu. Kampania ma dwa adresy: dostawców (firmy, samorządy) i obywateli, którzy przez głosy pokazują popyt. Głos nie jest daną – zgodne z zasadą „obywatel nie publikuje”.
- **3.3 Zgłoś uwagi do zbioru (S).** Portal ma „Zgłoś uwagi do zbioru/zasobu” (`/datasets/{id}/comments`) – mail do dostawcy. Na stronie QR dodać drugi link: „błąd w danych na dane.gov.pl? zgłoś uwagę do zbioru” – sygnał od obywatela płynie wtedy oficjalnym kanałem portalu do ministerstwa, a nasz sygnał „AED brak/uszkodzony” idzie do zarządcy. Dwa kanały, jasny podział.
- **3.4 PoCoTo na koniec (S).** Mapa „dostępne teraz” zgłoszona jako przykład wykorzystania zbioru AED – zrzut formularza „Zaproponuj przykład ponownego wykorzystania danych”.
- Pytanie do mentora: który wykaz miał na myśli. Jeśli „Propozycje nowych danych” – 3.1 i 3.2 mają pierwszeństwo przed resztą tej listy.

## Iteracja 4. Mapa mechanizmów portalu, które wykorzystujemy (do slajdu „zgodność 30%”)

Każdy wiersz to mechanizm portalu, plik w kodzie i nasz dowód. Wiersze bez dowodu to zadania.

| Mechanizm portalu | Gdzie w kodzie mcod | Jak go używamy | Dowód | Stan |
|---|---|---|---|---|
| Instytucja-dostawca odpowiada za zbiór | `organizations/models.py` | Ministerstwo Cyfryzacji (typ `state`) jest dostawcą zbioru krajowego | lokalny portal, instytucja 2839 | jest (zrzut do zrobienia) |
| Harwester XML (DATA SOURCES) | `harvester/` | codzienne zasilanie z rejestru ministerstwa | raport importu, zbiór 4211 | jest (zrzut do zrobienia) |
| Walidacja tabelaryczna + mapa | `resources/indexed_data.py`, `lib/widgets.py` | CSV z kolumnami współrzędnych, znaczniki `b`, `l`, `label` | `has_map=True`, API `/geo` | jest |
| Flagi i kategorie zbioru | `datasets/forms.py:92-150` | podane jawnie w zasilaniu | XML, panel zbioru | jest |
| Propozycje nowych danych + głosy | `suggestions/` | historia „obywatel prosi → ministerstwo dostarcza” (3.1) | – | **do zrobienia** |
| Zgłoś uwagi do zbioru | `datasets/views.py:258` | link na stronie QR (3.3) | – | **do zrobienia** |
| PoCoTo | `showcases/` | zgłoszenie mapy jako przykładu (3.4) | – | do zrobienia |
| Panel dostawcy (role redaktor, pełnomocnik) | `users/models.py` | docelowo konta firm = redaktorzy instytucji typu `private` | `docs/integracja-portal-backend.md` | plan |
| Powiadomienia o terminie aktualizacji zbioru | `datasets/models.py:829-849` | ministerstwo dostaje przypomnienie, gdy zbiór nie był aktualizowany | – | do sprawdzenia, czy działa dla zbiorów z harwestera |
| Historia zmian / wersje zasobu | `resources/` | stare wersje CSV zostają u dostawcy; portal aktualizuje zasób | test aktualizacji 21.11 | jest (czy portal trzyma stare pliki – do sprawdzenia) |

Wniosek: slajd „zgodność” warto zbudować z tej tabeli – jury z ministerstwa rozpozna własne mechanizmy po nazwach z ich panelu.

## Iteracja 5. Standard danych – luki wobec zdania „czy jest dostępne i czy działa”

Przegląd 38 pól `schema.json` pod kątem scenariusza z PDF (zamknięta szafka, centrum Warszawy):

| Luka | Dziś | Skutek | Propozycja | Koszt |
|---|---|---|---|---|
| **Stan techniczny nie trafia do danych otwartych** | zarządca wybiera „sprawny/problem” (`aed_service/app.py:591`), ale „problem” tylko obniża status do `niepotwierdzony` | 112 nie odróżni „AED w naprawie” od „nikt nie potwierdził” | status `niedostepny_czasowo` (jak „not ready” w The Circuit) albo pole `stan_techniczny` (sprawny / w naprawie / nieznany) | S–M |
| **Zamknięta szafka** – sedno historii z 3 marca | brak pola; OSM ma `locked` (wypełnione w 3 obiektach na 18 tys.) | nie da się filtrować „dostępne bez klucza” | `szafka_zamknieta` (tak/nie) + `sposob_otwarcia` (słownik: otwarta, kod od dyspozytora 112, klucz u ochrony/recepcji); **kodów nie publikujemy** (zasada 6) | S |
| Piętro | brak | w dużym budynku opis słowny nie wystarcza | `pietro` (liczba; OSM `level`) | S |
| Typ miejsca (możliwa „obowiązkowa flaga/kategoria” z hasła mentorów) | brak | brak statystyk „szkoły/urzędy/transport”, brak filtrów | `kategoria_miejsca` ze słownikiem (oświata, administracja, ochrona zdrowia, transport, handel i usługi, sport i rekreacja, zakład pracy, inne) | S |
| Żywotność urządzenia („10/14 lat” z rozmowy z komisją) | jest `data_produkcji` | brak ostrzeżenia o końcu życia | reguła walidatora: ostrzeżenie, gdy od `data_produkcji` minęło więcej niż N lat (N do potwierdzenia u komisji); bez nowego pola | S |
| Ciągłość identyfikatora po scaleniu | `powiazane_zrodla` wskazuje źródła | zmiana `id_aed` po scaleniu (iteracja 2) | zachować najstarszy opublikowany `id_aed`; pozostałe w `powiazane_zrodla` albo nowej kolumnie | M |
| Generyczność struktury (rozmowa z komisją, pkt 2) | struktura nazwana „AED” | komisja mówiła o **generycznej** strukturze zgodnej z tym, co leży na portalu | pokazać na slajdzie, że wzorzec = adres i położenie wg Legionowa + blok „urządzenie” + blok „odpowiedzialność”; ten sam szkielet obsłuży apteczki (Helpbox 365 = AED + apteczka) czy inne punkty ratunkowe przez pole `typ_urzadzenia` (na przyszłość, nie teraz) | S (slajd) |

Uwaga: każda nowa kolumna zmienia `wzorzec-aed.xlsx`, formularze i eksport (wszystko generuje się ze schematu), ale też **zmienia schemat tabeli w portalu** – przy zasileniu harwesterem nowa kolumna to nowy plik; redaktor musi raz przejrzeć typy kolumn. Lepiej dodać pola teraz niż po pierwszej publikacji.

## Iteracja 6. Priorytety na resztę hackathonu (wpływ × koszt)

Kryteria i wagi z PDF. „Nie tniemy” z `CLAUDE.md`: standard i XLSX, mapper z deduplikacją, zgłoszenie CSV, strona QR, logo i księga znaku, instrukcja dla jury.

| Priorytet | Zadanie | Kryterium (waga) | Koszt | Kto |
|---|---|---|---|---|
| 1 | Logo, hasło, księga znaku (decyzja i pliki) | 25% | M | ludzie (zasada: logo ręcznie) |
| 2 | Zrzuty lokalnego portalu: instytucja, DATA SOURCES z raportem importu, zbiór z tabelą i mapą, API zasobu | 30% | S | ktoś z dostępem do lokalnego portalu |
| 3 | Pętla „Propozycje nowych danych” (iteracja 3.1) – 4 zrzuty | 30% | S | jw. |
| 4 | Ranking firm → neutralna lista dostawców (iteracja 2) | 30% (zasady portalu), ryzyko wizerunkowe | S | frontend |
| 5 | Pola `szafka_zamknieta`, `sposob_otwarcia`, status `niedostepny_czasowo` + widok „dostępne teraz” | temat 15%, kreatywność 15% | M | standard + frontend |
| 6 | Wycofane rekordy zostają w zbiorze ze statusem | zgodność, „dane stare mają pozostać” | S | usługa |
| 7 | Zasób `zrodla.csv` w zasilaniu (zakres referencyjny źródeł) | temat 15% | S–M | standard |
| 8 | Stały `id_aed` po scaleniu | temat, jakość | M | standard |
| 9 | Odkrywanie nowych źródeł przez API portalu | automatyzacja | M | mapper |
| 10 | ~~Audyt WCAG~~ – **już jest**: `frontend/aed-zrzuty/DOSTEPNOSC.md` (sprostowanie z it. 68); zostaje podlinkowanie w instrukcji i konspekcie | wymóg techniczny | S | dokumenty |
| 11 | Kolory modułu AED → zmienne motywu portalu | „nie zaburzać stylistyki” | S | frontend |
| 12 | PoCoTo, „Zgłoś uwagi” na stronie QR | zgodność (drobne) | S | frontend |

Kolejność cięcia przy braku czasu: 12 → 9 → 8 → 7 → 5 (zostaje na slajdzie jako „następny krok”). Pozycje 1–4 i 6 nie powinny wypaść.

## Iteracja 7. Pytania do mentorów przy stoisku (krótko, z gotowymi wariantami odpowiedzi)

1. „Wykaz, gdzie można zmobilizować rozwiązanie” – chodzi o **Propozycje nowych danych** (z głosowaniem), PoCoTo czy listę instytucji?
2. „Flaga, która nie jest fakultatywna” – flagi zbioru w formularzu portalu (dynamiczne, wysokiej wartości, badawcze) czy obowiązkowe pole w naszym standardzie (np. kategoria miejsca, dostęp)?
3. Czy zbiór AED oznaczyć jako **dane o wysokiej wartości** (geoprzestrzenne, bezpieczeństwo)? Dziś `false`.
4. Kto docelowo jest dostawcą: Ministerstwo Cyfryzacji (jak w rozmowie o 17:00) czy Ministerstwo Zdrowia / Centrum e-Zdrowia (kompetencje wg odpowiedzi MSWiA)?
5. „Nie premiować danych” – czy publiczny ranking firm jest w porządku, czy lepsza neutralna lista?
6. „Dane stare mają pozostać” – dotyczy zbiorów samorządów (nie zastępujemy ich), historii wersji pliku, czy rekordów wycofanych w zbiorze?
7. Czy jury dostanie dostęp do panelu administratora lokalnego portalu (nagranie, zdalny pulpit), czy wystarczą zrzuty?
8. „10/14 lat żywotności” – urządzenia, baterii czy elektrod? Jaką wartość przyjąć w ostrzeżeniu walidatora?
9. Godzina i forma oddania (CLAUDE.md, otwarte decyzje).

## Iteracja 8. Prezentacja: co zmienić w konspekcie po hasłach mentorów

Konspekt (`docs/prezentacja-konspekt.md`) jest kompletny; propozycje to zmiany punktowe, nie nowa prezentacja.

- **Slajd 1 – teza w jednym zdaniu, którą jury powtórzy:** „Dane o AED wprowadza ten, kto za urządzenie odpowiada, a portal dane.gov.pl pobiera je sam – codziennie, własnym mechanizmem”. Druga połowa zdania to nowość z dzisiejszego wieczoru (harwester).
- **Slajd 2 – historia z 3 marca jako pytanie o dane:** „Które z trzech pobliskich AED było dostępne o 14:00 i nie stało w zamkniętej szafce?” – dziś żaden zbiór nie odpowiada; po wdrożeniu odpowiada filtr „dostępne teraz” (iteracja 5: `szafka_zamknieta`, `godziny_dostepu`, `stan`).
- **Slajd 4 – piąty krok procesu:** „Portal pobiera zbiór codziennie o 03:00 (sekcja DATA SOURCES), tworzy tabelę i mapę”. Bez tego proces urywa się na „pobiera zbiór do publikacji”, czyli na ręcznym kroku.
- **Slajd 6 – zbudować z tabeli mechanizmów (iteracja 4):** jury z ministerstwa rozpozna nazwy ze swojego panelu: instytucja, źródło danych, raport importu, flagi, propozycje nowych danych. Zrzuty z lokalnego portalu zamiast `[BRAK]`. Zdanie „integracja to plan, nie wdrożenie” zamienić na „kod portalu bez zmian; publikacja działa na lokalnej kopii portalu”.
- **Slajd 7 – dwie grupy odbiorców kampanii:** dostawcy (firmy, samorządy) – naklejka, przypomnienia, lista dostawców; obywatele – głos „plus” przy propozycji danych na portalu i skan QR. Usunąć słowo „ranking” (iteracja 2).
- **Slajd 9 – nowe ograniczenia:** harwester usuwa obiekty, których zabraknie w pliku; wymóg HTTPS; ręczne ustawienie typów kolumn przez redaktora; publiczne API nie było osiągalne z naszego środowiska, więc liczby z produkcyjnego portalu nie są aktualne na 21.11.
- **Narracja „sprzedażowa” – kupującym jest ministerstwo.** Trzy argumenty po kolei: (1) nie wymaga zmian w kodzie portalu ani ustawy na start, (2) koszt ministerstwa to jedna usługa rejestru + kampania, reszta to mechanizmy, które już utrzymuje, (3) ścieżka rozwoju: obowiązek zgłaszania (jak Francja 2018) jest opcją, nie warunkiem.

Scenariusz demo dla jury (5 minut, jedna osoba klika, druga mówi):

| Min. | Ekran | Co mówimy |
|---|---|---|
| 0:00 | rejestr: filtr „dostępne teraz” | problem z 3 marca w jednym kliknięciu |
| 0:45 | panel firmy: wgranie `przyklad-sprzedawca-bledy.csv` | walidator po polsku, wiersz i pole |
| 1:30 | naklejka QR → telefon: potwierdzenie zarządcy | odpowiedzialność przechodzi na zarządcę |
| 2:30 | panel ministerstwa: duplikaty, przypomnienia, źródła | mapper i deduplikacja, zakres referencyjny źródeł |
| 3:30 | lokalny portal: DATA SOURCES → raport importu → zbiór z mapą | publikacja mechanizmem portalu |
| 4:30 | propozycja nowych danych z głosami, zamknięta linkiem do zbioru | pętla obywatel → ministerstwo |

## Iteracja 9. Kampania i zachęty – po korekcie „nie premiować”

- **Neutralność państwa.** Zachęty muszą być równe dla wszystkich, którzy spełnią próg: znak „dane aktualne” przy progu kompletności i potwierdzeń, bez kolejności miejsc. Publicznie: lista dostawców alfabetycznie. Prywatnie (w panelu firmy): „Twoja kompletność 82, mediana dostawców 64” – motywacja bez publicznego rankingu.
- **Zachęta, która nic nie kosztuje ministerstwa i ma wartość dla firmy:** przypomnienia o terminach baterii i elektrod to usługa posprzedażowa sprzedawcy (kontakt z klientem, sprzedaż elektrod). Sprzedawca zgłasza urządzenie, bo dostaje darmowy system przypomnień dla swoich klientów – to argument, który komisja chciała usłyszeć (pkt 8 rozmowy: „co firma z tego ma”).
- **Naklejka jako nośnik marki akcji** – jedyny element kampanii, który fizycznie wisi przy każdym urządzeniu. Logo musi działać w 2 cm i w jednym kolorze (wymaganie do briefu: minimalna wielkość w księdze znaku = rozmiar naklejki).
- **Kampania obywatelska przez portal**: głosy przy „Propozycjach nowych danych” (iteracja 3.2). Obywatel nie publikuje danych, ale pokazuje popyt – zgodnie z zasadą dostawcy.
- **Moment startu**: Europejski Dzień Przywracania Czynności Serca (16 października) – data do slajdu „harmonogram akcji”, nie do obietnic.
- **Nazwa** (decyzja ludzi): z hasłami mentorów najlepiej współgra „Opiekun AED” – rola dostawcy jest centralna (odpowiedzialność, konto, panel), a znak „Opiekun AED – dane potwierdzone RRRR-MM” na naklejce jest zachętą neutralną (każdy może go zdobyć).

## Iteracja 10. Wskazówki organizatora (`tips.txt`) – drugie czytanie, zdanie po zdaniu

| Zdanie z `tips.txt` | Stan | Luka | Pomysł |
|---|---|---|---|
| „W ponumerowanych krokach wskażcie, który plik otworzyć … gdzie sprawdzić realizację **każdego wymagania**” | `docs/instrukcja-dla-jury.md` ma sekcję wymagań | kroki są rozproszone; część wymagań odsyła do „Do uzupełnienia” | na górze instrukcji tabela „wymaganie → 1 link → 1 oczekiwany wynik” mieszcząca się na jednym ekranie; reszta niżej jako szczegóły |
| „**Jury nie będzie miało czasu na samodzielną konfigurację środowiska.** Przygotujcie prototyp, w którym jurorzy będą mogli przejść cały proces od początku do końca” | prototyp tylko lokalnie (`docker compose up`) | **największe ryzyko oddania**: wymaganie wprost mówi „bez konfiguracji”, a my wymagamy Dockera | wystawić `docker-compose.yml` z katalogu głównego (usługa AED + nginx z frontendem, bez portalu) pod publicznym adresem: VPS członka zespołu, Fly.io/Render (Docker), ewentualnie tymczasowy tunel (cloudflared) na czas oceny. Dane fikcyjne, więc ryzyko niskie. Konta demo w instrukcji. Plan B: nagranie 3–5 min całej ścieżki. **Decyzja człowieka** (koszt, konto w usłudze). |
| „Uruchomcie portal we własnym środowisku … Sprawdźcie w praktyce, jak działają jego mechanizmy, i uwzględnijcie je” | zrobione 21.11 (harwester, walidacja tabelaryczna, mapa) | dowód tylko w dokumentacji | slajd „Co sprawdziliśmy w kodzie i na uruchomionym portalu”: 4 ustalenia, każde z plikiem i linią (HTTPS, `.md5`, usuwanie brakujących `extIdent`, ponowne pobranie tylko po zmianie linku, wnioskowanie typów kolumn). Pokazuje, że praca wynika z kodu portalu, a nie z założeń. |
| „Obecne rozwiązania nie są zadowalające, ponieważ dane są rozproszone i niezweryfikowane (**nikt nie bierze za nie odpowiedzialności**)” | proces z odpowiedzialnym podmiotem | patrz iteracja 11 | – |
| „Logotyp i hasło są przeznaczone do realizacji akcji promocyjnej **dla potencjalnych dostawców danych** – nie do prezentacji rozwiązania” | brief logo istnieje | ryzyko, że logo powstanie „pod pitch” | w księdze znaku przykłady zastosowań wyłącznie dla dostawców: naklejka na szafkę, baner w panelu dostawcy, stopka maila z przypomnieniem, znak „dane aktualne”, pismo do samorządu |
| „nie możecie przebudować mechaniki portalu, żeby każdy publikował … Potrzebny jest dostawca” | spełnione | – | w prezentacji jedno zdanie: „W portalu nic nie przebudowaliśmy. Dostawcą jest ministerstwo, korzysta ze źródła danych XML jak każdy inny dostawca.” |

## Iteracja 11. Odpowiedzialność za każdy wiersz zbioru ministerstwa

Problem: ministerstwo publikuje w zbiorze krajowym także rekordy, których nikt nie potwierdził (`niepotwierdzony` z samorządów i API Warszawy). To osłabia tezę „za dane ktoś odpowiada”.

Warianty:

1. **Tylko potwierdzone** (`aktywny`) w zbiorze ministerstwa. Czysto, ale dziś zbiór miałby kilka rekordów – słaby efekt na start.
2. **Wszystko, z jawną odpowiedzialnością na poziomie wiersza** (obecnie): kolumny `zrodlo`, `licencja`, `status`, `data_weryfikacji` mówią, kto i kiedy ręczy. Rekordy samorządów są już opublikowane przez odpowiedzialnego dostawcę na portalu – ministerstwo je tylko scala.
3. **Dwa zasoby w jednym zbiorze**: „potwierdzone przez zarządców” i „zebrane z istniejących zbiorów, do potwierdzenia”. Konsument (112) wybiera, co bierze; liczba rekordów w pierwszym zasobie jest miarą postępu akcji (zasada 9: mierzymy proces).

Rekomendacja do dyskusji: wariant 3 – dobrze się prezentuje („zasób potwierdzonych rośnie z każdym skanem QR”) i nie wymaga zmian w portalu (drugi `resource` w XML ze stałym `extIdent`). Koszt S–M.

## Iteracja 12. QR „mocno wyeksponowany” (pkt 4 rozmowy z komisją) – co jeszcze da się wycisnąć

Dziś: naklejka SVG z kodem QR; zarządca z tokenem potwierdza dane; osoba postronna wysyła sygnał `jest / brak / uszkodzony / zamkniety` (`aed_service/app.py:627`), który trafia do skrzynki dysponenta i do tabeli `signals`. Sygnały nie wpływają na dane otwarte.

Pomysły:

- **12.1 „Ostatnio widziany” jako wskaźnik ministerstwa, nie edycja danych.** Z sygnałów `jest` liczymy datę ostatniego potwierdzenia obecności przez kogokolwiek. To obserwacja ministerstwa (dostawcy zbioru), więc może trafić do zbioru jako osobna kolumna, np. `data_ostatniego_sygnalu`. Dane zarządcy pozostają nietknięte – zgodne z zasadą 2. Komisja mówiła: „w przyszłości samo zeskanowanie ma zgłaszać miejsce i stan” – to jest pierwszy krok tej przyszłości. Koszt S.
- **12.2 „Wymaga sprawdzenia”.** Dwa niezależne sygnały `brak` lub `uszkodzony` w ciągu 7 dni → status `niedostepny_czasowo` do czasu reakcji zarządcy (iteracja 5) i natychmiastowy mail do dysponenta. Do decyzji: czy obywatelski sygnał może zmienić status publiczny (ryzyko nadużyć: złośliwe zgłoszenia). Bezpieczniejsza wersja: tylko mail i flaga w panelu ministerstwa.
- **12.3 Identyfikator czytelny dla człowieka na naklejce.** `AED-…` drukowany dużą czcionką obok QR. Dyspozytor 112 może zapytać „podaj numer z naklejki”, a świadek bez smartfona może zgłosić problem telefonicznie. Koszt: zmiana szablonu naklejki.
- **12.4 Adres w kodzie QR musi przetrwać lata.** Naklejka wisi dłużej niż prototyp. Kod powinien prowadzić na stały adres w domenie rządowej (np. `dane.gov.pl/aed/AED-…` albo `aed.gov.pl/AED-…`), który przekierowuje do aktualnej usługi. Do slajdu „wdrożenie” i do księgi znaku (QR jako element znaku).
- **12.5 Prywatność sygnałów.** Sygnał zapisuje współrzędne osoby skanującej (`signals.lat/lon`). Dodać okres retencji (np. 90 dni) i informację na stronie QR, po co są współrzędne. Zasada 6 (bez danych osobowych w danych otwartych) jest spełniona, ale RODO dotyczy też danych w rejestrze.
- **12.6 Skan jako miara procesu.** Liczba skanów na urządzenie i odsetek urządzeń zeskanowanych w ostatnich 90 dniach – wskaźnik do panelu ministerstwa i slajdu „mierzymy proces” (zasada 9).

## Iteracja 13. Automatyzacja (hasło mentorów) – pełny łańcuch bez człowieka i z człowiekiem

Łańcuch dobowy, który da się opisać na jednym slajdzie (godziny przykładowe):

| Godzina | Krok | Kto/co | Stan |
|---|---|---|---|
| 01:00 | pobranie źródeł (`download_aed_data.py`) i mapper z deduplikacją | harmonogram usługi (`AED_CYCLE_HOURS`) | jest |
| 01:10 | przypomnienia: termin baterii/elektrod, brak potwierdzenia 183 dni, `nieaktualny` po 365 dniach | usługa | jest |
| 01:15 | zapis zasilania XML i nowej wersji CSV | usługa (`AED_FEED_DIR`, `AED_FEED_URL`) | jest (21.11) |
| 03:00 | import w portalu | harwester dane.gov.pl | jest w portalu |
| 03:xx | walidacja tabelaryczna, mapa, indeks wyszukiwarki, ocena otwartości | Celery portalu | jest w portalu |
| rano | raport importu widoczny w panelu przy źródle danych (wysyłka e-mail w 2.63.0 **niezaimplementowana**, `harvester/admin.py:370` – sprostowanie z iteracji 45) | portal | jest w portalu |
| tydzień | odkrywanie nowych zbiorów AED na portalu i lista „kandydaci na źródła” | usługa | **pomysł** (iteracja 2) |
| na żądanie | przegląd duplikatów, decyzje o nowych źródłach | człowiek (ministerstwo) | jest |

Zasada do slajdu: **automatyzujemy przepływ, człowiek decyduje o zaufaniu** (nowe źródło, scalenie niepewnych rekordów, zmiana statusu z sygnału obywatela).

## Iteracja 14. Wzorcowy zakres danych (10%) – „aby **wszystkie organizacje** udostępniały dane w jednolity sposób”

Zdanie z PDF mówi o jednolitym udostępnianiu przez wszystkie organizacje, a nie tylko o kolumnach. Jednolitość na dane.gov.pl to także **metadane zbioru**: tytuł, kategoria, tagi, częstotliwość, flagi, licencja. Dziś `wzorzec-aed.xlsx` ma arkusze Dane, Słownik pól, Słowniki, Mapowanie źródeł, Instrukcja (`scripts/build_template.py`).

- **14.1 Arkusz „Metadane zbioru”** generowany z `zbior_dane_gov_pl`: jak nazwać zbiór (wzór „Defibrylatory AED – {dostawca}”), kategoria Zdrowie, tagi (w tym **wspólny tag akcji**, po którym mapper znajdzie zbiór przez API), częstotliwość, wartości flag z uzasadnieniem, licencja zalecana (CC0 1.0 albo CC BY 4.0). Jedno źródło prawdy, zero duplikacji. Koszt S.
- **14.2 Arkusz „Publikacja w portalu”**: dwie drogi dla samorządu lub firmy – (a) ręcznie w panelu dostawcy: dodaj zbiór, zasób CSV, ustaw typy kolumn tekstowych (`kod_terc`, `kod_simc`, `nr_budynku`) i znaczniki mapy; (b) automatycznie: źródło danych XML. Ustalenia z lokalnego portalu przenoszą się 1:1 do instrukcji dla dostawców. Koszt S.
- **14.3 Szablon zasilania XML dla każdego dostawcy.** `aed_standard.feed` ma dziś metadane ministerstwa na sztywno. Parametr „metadane dostawcy” (tytuł, `extIdent`) i komenda `python3 -m aed_standard feed PLIK.csv --url … --dostawca …` daje każdemu dużemu dysponentowi gotowe zasilanie w tym samym standardzie. To realizuje hasło „portal ma zbierać dane od różnych dostawców” bez zmian w portalu. Koszt M.
- **14.4 Typy kolumn w nagłówku pliku nie przejdą do portalu**, ale może je przenieść Table Schema: portal wnioskuje typy sam. W instrukcji dla dostawców krótka lista „kolumny, które portal rozpozna źle, i co ustawić”. Ewentualnie w przyszłości: propozycja dla portalu, by harwester przyjmował opis typów kolumn (to już zmiana portalu – tylko na slajd „rekomendacje”).
- **14.5 Wersjonowanie standardu.** `schema.json` ma `version: 0.2.0`. Dodanie pól z iteracji 5 to 0.3.0. W zbiorze warto mieć metadaną „wersja standardu” (w opisie zbioru albo w tagu `aed-standard-0.3`), żeby konsumenci wiedzieli, jaki układ kolumn czytają.

## Iteracja 15. Model federacyjny po hasłach mentorów (wiele dostawców + ministerstwo)

Połączenie rozmowy z 17:00 („ministerstwo zbiera i publikuje”) z hasłem „portal zbiera od różnych dostawców”:

```
firma bez systemu ──(konto firmy: CSV/formularz)──────────────► rejestr ministerstwa ──XML──► zbiór krajowy (ministerstwo)
zarządca ──(QR)────────────────────────────────────────────────►        ▲
duży dysponent z systemem ──XML w standardzie──► własny zbiór na portalu ┤ (mapper czyta po tagu akcji)
samorząd ──CSV w standardzie──► własny zbiór na portalu ───────────────────┘
```

- Każdy, kto może być dostawcą na portalu, **publikuje sam** i odpowiada za swój zbiór (zgodne z `tips.txt`).
- Kto nie może albo nie chce – raportuje do ministerstwa, a ministerstwo odpowiada za zbiór krajowy.
- Zbiór krajowy jest **sumą**: rekordy wszystkich zbiorów w standardzie (znalezionych po tagu) + rekordy z rejestru, bez duplikatów, z kolumną `zrodlo` wskazującą dostawcę.
- Zachęta do własnej publikacji: zbiór dysponenta liczy się do ocen otwartości jego instytucji na portalu.
- Ryzyko: podwójna publikacja tych samych urządzeń (zbiór gminy + zbiór krajowy). To nie błąd – zbiór krajowy jest agregatem z deklarowanym pochodzeniem; deduplikacja działa między źródłami.

## Iteracja 16. WCAG, responsywność, UX – jak zebrać dowody tanio

Wymaganie z PDF: „zgodność z aktualną wersją WCAG oraz responsywność … a także zgodność z zasadami UX”. **Sprostowanie (it. 68):** dowody już istnieją w `frontend/aed-zrzuty/DOSTEPNOSC.md` (axe, klawiatura, 320 px, wysoki kontrast); poniższe propozycje dotyczą tylko luk wskazanych w tym raporcie i podlinkowania go w dokumentach.

- **Dowód minimalny (S):** dla 5 ekranów (rejestr, panel firmy, formularz urządzenia, strona QR, panel ministerstwa) – wynik automatycznego audytu (axe lub Lighthouse, sekcja Dostępność), zrzut przy szerokości 320 px, krótka notatka z testu samą klawiaturą (kolejność fokusu, widoczny fokus, brak pułapek). Wszystko w `docs/dostepnosc.md` + jeden slajd.
- **Uczciwość ponad wynik:** automat wykrywa ok. 30–40% problemów (ogólnie przyjmowane oszacowanie – na slajd tylko jako „audyt automatyczny nie wystarcza”, bez liczby). Dlatego test klawiaturą i czytnikiem (NVDA na Windows) dla jednej ścieżki: strona QR.
- **Mapa jako dodatek (zasada 7):** każda informacja z mapy jest też w tabeli/liście – przy filtrze „dostępne teraz” sprawdzić, że wynik filtra jest ogłaszany tekstem (`aria-live`) i widoczny w liście.
- **UX dla zarządcy na telefonie:** potwierdzenie w trzech krokach – zmierzyć czas (stoperem, 3 osoby). Jeśli < 2 min, mamy liczbę do hasła kampanii („Minuta dla AED”) zgodną z zasadą 10 (własny pomiar).
- **Stylistyka portalu (hasło mentorów):** zamiana własnych kolorów modułu AED na zmienne motywu portalu i sprawdzenie trybu wysokiego kontrastu portalu (przełącznik w nagłówku) – jeden zrzut.

## Iteracja 17. Ryzyka w dniu oddania i zabezpieczenia

| Ryzyko | Skutek | Zabezpieczenie |
|---|---|---|
| Jury nie uruchomi Dockera | ocena prototypu bez prototypu | publiczny adres (iteracja 10) + nagranie |
| Lokalny portal nie wstanie u osoby, która robi zrzuty | brak dowodów do 30% | zrzuty zrobić **teraz**, dopóki stos działa; `.env` wskazuje adres WSL, który zmienia się po restarcie (`MCOD_NGINX_FRONTEND`) |
| Test `test_committed_outputs_match_build` nie przechodzi przez `core.autocrlf=true` | jury uruchomi testy i zobaczy błąd | `.gitattributes` z `datasets/out/* -text` albo `eol=lf` dla plików danych; sprawdzić na czystym klonie |
| Nazwa akcji koliduje z istniejącą | ryzyko prawne i wizerunkowe | 15-minutowe sprawdzenie UPRP/EUIPO/domena/KRS z `kampania/nazwa-i-haslo.md` przed drukiem logo |
| Liczby na slajdach rozjeżdżają się (18 814 vs 15 769) | podważona wiarygodność | jedna liczba na slajd, ze źródłem i datą; zrzut panelu po tej samej budowie |
| Generator zasilania używa adresu `api.mcod.local` | w dokumentacji wygląda jak produkcja | w instrukcji: adres lokalny = demonstracja; produkcyjnie adres HTTPS ministerstwa |
| Zmiana pól standardu po zrzutach | zrzuty nieaktualne | zamrozić standard (0.3.0) przed zrzutami; zmiany po zamrożeniu tylko na slajd „następne kroki” |

## Iteracja 18. Adwokat diabła – pytania sceptycznego jurora z ministerstwa i odpowiedzi

| Pytanie jurora | Krótka odpowiedź | Dowód |
|---|---|---|
| „Kto za to zapłaci i kto to utrzyma?” | rejestr to jedna mała usługa; publikację, tabelę, mapę, API i powiadomienia robi portal, który już utrzymujecie | tabela mechanizmów (iteracja 4) |
| „Dlaczego sprzedawca miałby raportować bez obowiązku?” | dostaje za darmo przypomnienia dla klientów o bateriach i elektrodach (sprzedaż posprzedażowa) i znak „dane aktualne” na liście dostawców | `kampania/zachety.md` |
| „Czy nie publikujecie niezweryfikowanych danych pod szyldem ministerstwa?” | każdy wiersz ma status, źródło i datę weryfikacji; propozycja dwóch zasobów: potwierdzone / do potwierdzenia | iteracja 11 |
| „Co z OpenStreetMap, z którego dziś korzysta 112?” | OSM zostaje w rejestrze jako porównanie (ODbL); nie mieszamy licencji; po potwierdzeniu przez zarządcę rekord jest danymi zarządcy | zasada 3, `raport.json` |
| „Czy to wymaga zmian w kodzie portalu?” | nie; harwester, instytucja, źródło danych, propozycje – sprawdzone na lokalnej kopii portalu | `docs/integracja-portal-backend.md` |
| „Co, jeśli harwester usunie zbiór przez błąd pliku?” | stałe `extIdent`, zbiór i zasób zawsze w pliku; plik zapisywany atomowo; przy błędzie pobrania lub walidacji import jest oznaczony jako nieudany i harwester niczego nie usuwa | `harvester/models.py:1211` (`if not dsi.is_failed`), `aed_service/feed.py`, test XSD |
| „Jak sprawdzicie, że AED faktycznie wisi?” | zarządca potwierdza przy naklejce; obywatelski skan to sygnał „ostatnio widziany” (iteracja 12) | strona QR |
| „Ile to uratuje osób?” | nie obiecujemy; mierzymy liczbę dostawców, kompletność i udział potwierdzonych | zasada 9 |
| „Dlaczego nie rejestr w Ministerstwie Zdrowia?” | rozwiązanie jest neutralne wobec dostawcy zbioru; komisja wskazała ministerstwo zbierające dane; zmiana dostawcy to zmiana jednej instytucji w źródle danych | – |

## Iteracja 19. Przypomnienia portalu a zbiory z harwestera (sprawdzone w kodzie)

- Portal sam przypomina dostawcy o aktualizacji zbioru (`datasets/managers.py:113`, `datasets_to_notify`), ale **tylko dla zbiorów dodanych ręcznie** (`source__isnull=True`) i dla częstotliwości od tygodniowej do rocznej (bez `daily`).
- Wniosek dla zbioru ministerstwa: przypomnienia portalu go nie dotyczą; zamiast nich jest raport importu w panelu przy źródle danych (sprostowanie z iteracji 45: wysyłka raportu e-mailem nie jest zaimplementowana w 2.63.0). Na slajd „automatyzacja”: dwa różne mechanizmy portalu dla dwóch kanałów.
- Wniosek dla samorządów publikujących ręcznie (model federacyjny, iteracja 15): w metadanych wzorca (iteracja 14.1) zalecić częstotliwość „co miesiąc” albo „co kwartał” – wtedy **portal sam przypomni gminie** o aktualizacji. To darmowy „mechanizm kontaktu z właścicielem” (pkt 5 rozmowy z komisją) na poziomie zbioru, bez naszej usługi.
- Portal ma też archiwum plików zasobów zbioru do pobrania jako ZIP (`archived_resources_files`, `datasets/models.py:852`). Czy zawiera poprzednie wersje pliku po aktualizacji z harwestera – do sprawdzenia na lokalnym portalu (stos jest teraz zatrzymany). Jeśli tak, to gotowa odpowiedź na „dane stare mają pozostać” po stronie portalu.

## Iteracja 20. Najbliższe kroki – propozycja kolejności (do potwierdzenia przez zespół)

1. Decyzja: publiczny adres prototypu (kto, gdzie) – bez tego reszta ma mniejszą wartość.
2. Uruchomić lokalny portal i zrobić zrzuty: DATA SOURCES + raport importu, zbiór z tabelą i mapą, API; propozycja nowych danych z głosami i zamknięciem (iteracja 3.1).
3. Neutralna lista dostawców zamiast rankingu; wycofane rekordy w zbiorze ze statusem.
4. Standard 0.3.0: `szafka_zamknieta`, `sposob_otwarcia`, `niedostepny_czasowo`, `kategoria_miejsca` (jeśli mentor potwierdzi) + widok „dostępne teraz”; potem zamrozić standard i zrobić zrzuty XLSX.
5. Arkusze „Metadane zbioru” i „Publikacja w portalu” w `wzorzec-aed.xlsx`.
6. `.gitattributes` dla plików danych (test na czystym klonie).
7. Audyt dostępności (5 ekranów) i `docs/dostepnosc.md`.
8. Prezentacja wg iteracji 8; demo wg scenariusza 5-minutowego.

Rzeczy, których świadomie nie robimy teraz: zmiany w kodzie portalu, integracja z SWD PRM, IoT w szafkach, automatyczne TERYT z geometrii PRG – zostają na slajdzie „co dalej”.

---

## Kolejka researchu (noc 21/22.11, do 7:00 CET)

Oznaczenia: [ ] do zrobienia, [x] zrobione (numer iteracji obok).

- [x] R1 (it. 21). Licencja zbioru z harwestera: jaką licencję portal nadaje zbiorowi z XML i jak ją ustawić (`conditions`, `licenseId`?).
- [x] R2 (it. 22). OSM w surowych danych: pokrycie `locked`, `level`, `defibrillator:code`, `opening_hours` – liczby pod nowe pola standardu.
- [x] R3 (it. 22). API Warszawy w surowych danych: które atrybuty gubimy w mapowaniu.
- [x] R4 (it. 22). Godziny dostępu: jaki odsetek rekordów da się sparsować – wykonalność widoku „dostępne teraz”.
- [x] R5 (it. 23). Deduplikacja: jak często `id_aed` scalonego rekordu pochodzi ze źródła o wyższym priorytecie niż najstarsze (skala problemu stałego id).
- [x] R6 (it. 24). Portal: rejestracja dostawcy prywatnego (firmy) – ścieżka w kodzie, role, typ instytucji.
- [x] R7 (it. 25). Portal: propozycje nowych danych – statusy, kroki w panelu, co widzi obywatel.
- [x] R8 (it. 26). Portal: PoCoTo – pola zgłoszenia, wymagania.
- [x] R9 (it. 27). Portal: ocena otwartości (4 gwiazdki zasobu AED) – jak liczona, jak dostać 5.
- [x] R10 (it. 27). Portal: DCAT-AP / RDF – czy zbiór z harwestera trafia do katalogu RDF (data.europa.eu).
- [x] R11 (it. 28). Frontend AED: przegląd dostępności w kodzie (nagłówki, etykiety, aria, fokus) – lista problemów.
- [x] R12 (it. 28). Frontend AED: własne kolory vs zmienne motywu portalu – co podmienić.
- [x] R13 (it. 29). Instrukcja dla jury: zdanie po zdaniu – co jest nieaktualne po 21.11.
- [x] R14 (it. 30). Liczby w dokumentach vs `raport.json` – spójność.
- [x] R15 (it. 31). Testy: przyczyna błędu CRLF i rekomendacja `.gitattributes` (sprawdzić na kopii w katalogu tymczasowym).
- [x] R16 (it. 32). `docs/api-aed.md` vs trasy w `aed_service/app.py` – rozbieżności.
- [x] R17 (it. 32). RODO w rejestrze: dane kontaktowe dysponenta, sygnały z położeniem – retencja, podstawa.
- [x] R18 (it. 33). Kampania: brief logo i szablon księgi znaku vs wymagania zadania (minimalna wielkość pod naklejkę, zastosowania dla dostawców).
- [x] R19 (it. 34). Źródła spoza portalu (Kraków, Koszalin, inne miasta) – czy jest coś maszynowo czytelnego w `research_notes/`.
- [x] R20 (it. 35). Skrypt pobierania: tryb przyrostowy (zadanie B) – stan i luki.

## Iteracja 21 (R1). Licencja zbioru z harwestera – **błąd w obecnym zasilaniu**

Ustalenia z kodu portalu:

- Licencja zbioru nie jest polem wprost; portal ją **wylicza** (`datasets/models.py:569`, `license_code`): domyślnie CC0 1.0; jeśli ustawiono którykolwiek warunek (`license_condition_source`, `…_modification`, `…_responsibilities` i in.) – CC BY 4.0; jeśli wybrano `license_chosen` wyższą – ta wygrywa.
- W XML warunki idą w `<conditions>` (`harvester/serializers.py:716-724`): `source` (obowiązek podania źródła), `modification`, `responsibilities`, `dbOrCopyrighted` + `dbOrCopyrightedLicenseChosen` (para wymagana razem, `serializers.py:757-770`), `personalData`.
- Nasze `zasilanie.xml` nie ma `<conditions>`, więc **zbiór ministerstwa dostaje CC0 1.0**.
- Tymczasem w eksporcie (`datasets/out/aed_dane_gov_pl.csv`) **715 z 781 rekordów ma licencję CC BY 4.0** (API Warszawy, 708; Marki), a tylko 66 – CC0 1.0. Publikacja danych CC BY pod CC0 łamie warunek uznania autorstwa źródła.

Poprawka (koszt S, do zrobienia rano – zmiana w moim kodzie z 21.11):

1. W `schema.json` → `zbior_dane_gov_pl` dodać `warunki`: `{"source": true}` plus opis obowiązku w opisie zbioru („przy wykorzystaniu podaj źródło: dostawcę zbioru i źródło rekordu z kolumny `zrodlo`”).
2. `aed_standard/feed.py` – wypisać `<conditions><source>true</source></conditions>`; portal ustawi CC BY 4.0.
3. Test: XML ma `conditions/source = true`; reguła ogólna – licencja zbioru nie może być łagodniejsza niż najbardziej restrykcyjna licencja rekordów w eksporcie (CC0 < CC BY < ODbL). Ten test od razu złapałby błąd.
4. Do rozważenia: gdy w eksporcie są wyłącznie rekordy CC0 i potwierdzone przez zarządców – zbiór mógłby być CC0 (rekomendacja z researchu dla danych ratunkowych). Wtedy licencja zbioru wynikałaby z danych, a nie była stała. Prościej: zawsze CC BY 4.0 dla zbioru krajowego.

Wniosek ogólny do slajdu „zgodność”: licencja w portalu jest **pochodną warunków ponownego wykorzystania**, a nie polem wyboru – to kolejny dowód, że czytaliśmy kod portalu.

## Iteracja 22 (R2, R3, R4). Surowe dane: co mamy, co gubimy, czy „dostępne teraz” ma z czego liczyć

**Sprostowanie do iteracji 1.2 i 5:** widok „dostępne teraz” już jest – mapa ma filtr „według dostępności teraz”, lista pokazuje stan w każdym wierszu (`frontend/.../aed-hours.ts`, czytelny podzbiór składni `opening_hours`, bez zgadywania). Brakuje danych, nie interfejsu.

OpenStreetMap (18 298 obiektów, `datasets/raw/openaedmap/PL.geojson`):

| Tag | Obiekty | Udział | Wniosek |
|---|---|---|---|
| `access` | 16 918 | 92,5% | już mapowany na `dostep` |
| `indoor` | 15 970 | 87,3% | już mapowany |
| `defibrillator:location` | 12 318 | 67,3% | już mapowany (`opis_lokalizacji`) |
| `opening_hours` | 6 781 | 37,1% | już mapowany |
| `level` | 3 701 | 20,2% | **gubimy**; wartości głównie 0 (3 049), 1 (407) – argument za polem `pietro` (iteracja 5) |
| `wheelchair` | 459 | 2,5% | marginalne; pomijamy |
| `locked` | 3 | 0,0% | potwierdza: informacji o zamkniętej szafce praktycznie nie ma w żadnym źródle → pole musi wypełniać zarządca |
| `defibrillator:code` | 0 | 0% | dobrze: nikt nie publikuje kodów |
| `ref:api-um-warszawa-pl` | 113 | 0,6% | już używany jako jawne powiązanie z API Warszawy (`dedup.py:203`) |

API Warszawy (708 urządzeń):

- `device_access_description` (opis godzin wolnym tekstem) ma **612 urządzeń (86%)**, ale do `godziny_dostepu` trafia tylko „24/7” dla 100 urządzeń z `device_availability = Tak`; reszta idzie do `godziny_dostepu_opis` (`sources.py:260`). Dlatego „dostępne teraz” działa dla ok. 14% rekordów Warszawy.
- Prototyp konwersji (skrypt badawczy poza repozytorium, prosty zestaw wyrażeń regularnych): **402 z 612 opisów (66%)** daje regułę w składni czytanej przez frontend, np. „Poniedziałek: godz. 8:00-18:00; Wtorek-Piątek: godz. 8:00-16:00” → `Mo 08:00-18:00; Tu-Fr 08:00-16:00`. Nieskonwertowane: skróty „Pn - Pt”, „sob - niedz.”, „poniedziałki”, opisy typu „W godzinach otwarcia stacji metra” (38).
- **Ryzyko:** prototyp myli się w przypadkach brzegowych (np. „soboty i niedziele 9.00-20.00” → tylko `Sa`). Błędne godziny w danych ratunkowych są gorsze niż brak godzin. Zasada, jeśli to wdrożymy: konwertujemy tylko wzorce o pewnej składni, oryginalny tekst zostaje w `godziny_dostepu_opis`, rekord dostaje uwagę „godziny przetworzone automatycznie” w raporcie, a wynik jest sprawdzony na losowej próbie 30 rekordów przed publikacją. Koszt M. Zysk: pokrycie godzin w Warszawie z 14% do ok. 60–70% → liczba do slajdu 3 (zasada 10 – własny pomiar).
- `device_specifications` (Tak 400, Nie 179, Brak informacji 129) – znaczenie nieopisane w naszym mapowaniu; do sprawdzenia w `api_parametry.json`, czy to np. elektrody pediatryczne (pole przydatne dla ratowników).
- `device_public_access = Prywatny` (100) mapujemy na `ograniczony` z uzasadnieniem w kodzie (szkoły, baseny, recepcje z godzinami) – spójne z zasadą „prywatne w domach nie są publikowane”.

## Iteracja 23 (R5). Stały identyfikator – korekta pomysłu z iteracji 2

Jak to działa dziś w usłudze (`aed_service/app.py:570`, `:763`): gdy zarządca potwierdzi urządzenie zgłoszone przez sprzedawcę, a w promieniu kandydata jest rekord z importu (np. API Warszawy), para trafia do przeglądu z **nowym rekordem jako tym, który zostaje**. Po decyzji „połącz” rekord z importu dostaje status `wycofany`, a nowy zapisuje jego `id_aed` w `powiazane_zrodla`.

Wnioski:

- **Pomysł „zachowaj najstarszy id” (iteracja 2) jest błędny w naszym procesie**: identyfikator nowego rekordu jest wydrukowany na naklejce QR przy urządzeniu. Naklejka wygrywa – to jej numer poda świadek dyspozytorowi (iteracja 12.3). Zmienia się więc id rekordu z importu, i to jest właściwe.
- Problem dla konsumentów jest inny: rekord z importu ze statusem `wycofany` **znika z eksportu** (`publication_csv` pomija `wycofany`), więc konsument nie zobaczy, że `um.warszawa.pl/622` został zastąpiony przez `AED-…`.
- **Jedna zmiana rozwiązuje dwa hasła mentorów** („id się nie powtarza” i „dane stare mają pozostać”): wycofane rekordy zostają w eksporcie ze statusem `wycofany`, a powiązanie zastępowania jest widoczne w kolumnie `powiazane_zrodla` rekordu, który przejął urządzenie. Dobrze byłoby dodać kierunek odwrotny (w wycofanym rekordzie: „zastąpiony przez `AED-…`”) – np. ten sam `powiazane_zrodla` po obu stronach. Koszt S.
- Mapper ministerstwa (`aed_standard.dedup`) przy pełnej przebudowie bierze `id_aed` z rekordu o najwyższym priorytecie (`dedup.py:171`). W usłudze rekordy firm nie przechodzą przez tę przebudowę (`origin` ≠ `import`), więc nadpisania naklejkowego id nie ma. Do sprawdzenia testem: rekord z naklejką + nowy import tego samego miejsca → id z naklejki zostaje.

## Iteracja 24 (R6). Jak firma zostaje dostawcą w portalu (ustalenia z kodu)

- Typy instytucji (`organizations/models.py:29-39`): `local`, `state`, `private` („podmioty prywatne”), `developer`, `other`. Sprzedawca lub producent AED to `private`.
- Konto użytkownika: publiczna rejestracja z weryfikacją e-maila (`/auth/registration`, `users/views.py:169`) albo logowanie przez login.gov.pl (`mcod/logingovpl`, `users/views.py:695-722`). Adres w domenie `gov.pl` daje automatycznie rolę urzędnika (`users/models.py:123`).
- Uprawnienie do publikacji ma **pełnomocnik instytucji** (`is_agent`, `agent_organizations`) – zarządza zbiorami swojej instytucji w panelu administracyjnym. Instytucję zakłada redakcja portalu; w kodzie nie ma samoobsługowej rejestracji instytucji (ani dla deweloperów, ani dla firm) – to proces organizacyjny.
- Ograniczenia typów: instytucja `private` lub `developer` **nie może** oznaczyć danych jako wysokiej wartości z wykazu KE (`datasets/forms.py:318`, `harvester/serializers.py:548, 585, 778`). Zbiór firmy AED ma więc te flagi zawsze `false` – zgodne z naszym zasilaniem.

Wnioski do procesu:

1. **Kanał „firma publikuje sama”** (model federacyjny, iteracja 15) wymaga od firmy: konta (e-mail lub login.gov.pl), wniosku do redakcji o instytucję `private` i nadania pełnomocnictwa. To kilka dni pracy organizacyjnej – dlatego dla małych sprzedawców prostszy jest **kanał przez ministerstwo** (konto w rejestrze, CSV). Dwa kanały mają sens: duzi (sieci, producenci) publikują sami, mali raportują.
2. **Logowanie firm w rejestrze ministerstwa** docelowo przez login.gov.pl (ten sam mechanizm co portal) – na slajd „wdrożenie”; w prototypie konta demonstracyjne.
3. Hasło mentorów „dostęp do panelu administratora” w tym świetle: firma-dostawca **pracuje w panelu administracyjnym portalu** jako pełnomocnik swojej instytucji. Instrukcja dla firm (pakiet startowy) powinna mieć zrzuty tego panelu: lista zbiorów instytucji, dodanie zasobu, źródło danych XML.

## Iteracja 25 (R7). „Propozycje nowych danych” – korekta: to wykaz dla **dostawców**, nie dla obywateli

Ustalenia z kodu (`backend/mcod/suggestions/`):

- Obywatel (także bez konta) zgłasza „Zaproponuj dane” – trafia to do redakcji (`DatasetSubmission`, decyzja `accepted`/`rejected`).
- Przyjęta propozycja staje się `AcceptedDatasetSubmission` ze statusami `draft` → `published` → `publication_finished` (z komentarzem i datą zakończenia). Na publicznej liście widać ją po `is_published_for_all = true` (`suggestions/views.py:58`).
- **Głosować („plus”/„minus”) mogą tylko zalogowani redaktorzy, administratorzy i pełnomocnicy instytucji** (`suggestions/views.py:136`, `roles=["editor", "admin", "agent"]`), i tylko przy propozycji opublikowanej i aktywnej (`is_active`, `suggestions/views.py:160`).

Wniosek – zmienia iterację 3:

- Hasło „wykaz, gdzie można zmobilizować rozwiązanie” pasuje jeszcze lepiej niż sądziliśmy: to **wykaz, w którym portal mobilizuje dostawców**. Redakcja publikuje propozycję „Dane o lokalizacji defibrylatorów AED”, a pełnomocnicy instytucji (samorządy, szpitale, uczelnie, firmy) widzą ją i deklarują poparcie. To naturalny punkt startu kampanii po stronie portalu.
- **Iteracja 3.2 („obywatele głosują”) jest błędna** – obywatel może tylko zgłosić propozycję. Kampania obywatelska: „zaproponuj dane o AED” (zgłoszenie) + skan QR; kampania dla dostawców: „poprzyj propozycję i opublikuj” (głos + publikacja).
- Pętla do zrzutów (iteracja 3.1) zostaje: zgłoszenie obywatela → przyjęcie przez redakcję → publikacja dla wszystkich → głosy pełnomocników → `publication_finished` z linkiem do zbioru ministerstwa i do zbiorów gmin.
- Do kampanii (`kampania/zachety.md`): liczba głosów „plus” pełnomocników przy propozycji AED to **mierzalny wskaźnik mobilizacji dostawców** (zasada 9 – mierzymy proces).

## Iteracja 26 (R8). PoCoTo – co trzeba do zgłoszenia

Pola propozycji (`showcases/models.py:45-245`): kategoria (`app` / `www` / `other`), tytuł (do 300 znaków), opis, autor, adres aplikacji, platformy (mobilna/desktop i adresy sklepów), typ licencji (`free`/`commercial`), **obraz i grafika ilustracyjna z tekstem alternatywnym**, **powiązane zbiory danych** (lista), data zgłoszenia, e-mail zgłaszającego. Redakcja przyjmuje albo odrzuca; przyjęta staje się wpisem PoCoTo (może trafić na stronę główną: `main_page_position`).

Wnioski:

- Zgłoszenie PoCoTo ma sens dopiero, gdy **zbiór AED istnieje w portalu** (pole „powiązane zbiory”). Kolejność w demonstracji: harwester → zbiór → PoCoTo z mapą „dostępne teraz” jako przykład wykorzystania.
- Przykład wykorzystania robi ktoś inny niż dostawca: w narracji – aplikacje ratunkowe (Pierwszy Ratownik, mapy AED) i 112 korzystają ze zbioru przez API; PoCoTo pokazuje to publicznie i daje dostawcom dowód, że ich dane są używane (zachęta!).
- Do zrzutu potrzebny obraz z tekstem alternatywnym – przy okazji ćwiczenie WCAG.
- Pomysł do kampanii: „Twoje dane w aplikacjach” – w panelu firmy liczba wpisów PoCoTo i pobrań zbioru (portal liczy wyświetlenia i pobrania: `mcod/counters`) jako informacja zwrotna dla dostawcy. Do sprawdzenia, czy liczniki są dostępne przez API dla zbioru.

## Iteracja 27 (R9, R10). Ocena otwartości i katalog DCAT

- Ocena otwartości zasobu to **maksimum ocen jego plików** (`resources/models.py:1046`). Plik CSV daje 3 gwiazdki; portal sam tworzy z CSV wersję JSON-LD (`resources/models.py:705-725`, warunek: UTF-8 i przecinek jako separator – nasz eksport to spełnia), co podnosi zasób do 4 gwiazdek. Tak było na lokalnym portalu (`openness_score = 4`). 5 gwiazdek wymaga danych powiązanych (odnośniki do innych zasobów sieci) – poza zakresem; na slajd: „4/5 w skali portalu automatycznie, bo trzymamy się reguł pliku”.
- Wniosek dla wzorca: wymóg „UTF-8, separator przecinek” to nie tylko estetyka – od niego zależy automatyczna konwersja do JSON-LD i czwarta gwiazdka. Plik Przemyśla (separator `;`) tej konwersji nie przejdzie bez wykrycia dialektu. Dobry argument do arkusza „Publikacja w portalu” (iteracja 14.2).
- Katalog RDF/DCAT portalu (`/catalog`, `/catalog.{format}`, `datasets/views.py` `CatalogRDFView`, profile `core/api/rdf/profiles/dcat_ap_pl.py`) bierze opublikowane zbiory z indeksu wyszukiwarki bez filtra po pochodzeniu – zbiór z harwestera trafia tam jak każdy inny. Z katalogu korzysta data.europa.eu (wg researchu, `docs/research-i-pomysly.md` 4.1) – na slajd: „zbiór AED jest automatycznie widoczny w europejskim portalu danych”, z dopiskiem [do sprawdzenia na produkcji].
- Portal liczy wyświetlenia i pobrania zbioru (`views_count`, `downloads_count` w API zbioru, `datasets/serializers.py:428`). To gotowa **informacja zwrotna dla dostawcy** („Twoje dane pobrano N razy”) – zachęta bez publicznego rankingu (iteracja 9).

## Iteracja 28 (R11, R12). Moduł AED: stylistyka portalu i dostępność – przegląd kodu (bez uruchamiania)

Korekta iteracji 2 („własne kolory zaburzają stylistykę”): moduł **już** opiera się na tokenach portalu (`aed.scss` używa `base/variables`: `$color-gov-primary #0052a5`, `$color-hover-2`, `$color-grey-dark`, `$color-darker-red`, `$color-highlight`), ma tryb wysokiego kontrastu (`@mixin high-contrast`) i zasadę „stan zawsze tekstem i kształtem ikony, kolor tylko powtarza”. Własne są tylko: tekst `#1b1b1b`, tła `#f1f1f1`/`#f4f6fb` (gov.pl / mObywatel – opisane w nagłówku pliku) i dwa kolory stanów, których portal nie ma: `--aed-ok #1d7a3a`, `--aed-warn #c25400`.

Kontrast (WCAG 2.x, liczony ze wzoru luminancji):

| Kolor tekstu | na `#fff` | na `#f4f6fb` | na `#f1f1f1` |
|---|---|---|---|
| `#1d7a3a` (ok) | 5,39 | 4,98 | 4,77 |
| `#c25400` (warn) | 4,60 | **4,26** | **4,08** |
| `#0052a5` (primary) | 7,64 | 7,06 | 6,76 |
| `#1b1b1b` (tekst) | 17,22 | 15,93 | 15,25 |

- `--aed-warn` jest używany jako **kolor tekstu** statusu `nieaktualny` (`aed.scss:216`, `:704`). Na białym spełnia AA (4,6 ≥ 4,5), na tłach `#f4f6fb`/`#f1f1f1` – **nie** (4,26/4,08), jeśli tekst jest zwykłej wielkości. Poprawka S: przyciemnić do `#b04c00` (przeliczone: 4,79 na `#f1f1f1`, więcej na jaśniejszych tłach) albo zostawić kolor tylko dla ramki/ikony, a tekst w `--aed-ink`.
- Struktura nagłówków: każdy ekran ma jeden `h1`; wielokrotne `h1` w `aed-qr` i formularzu urządzenia są w rozłącznych gałęziach `@if` (renderuje się jeden). Po wysłaniu formularza fokus przechodzi na nagłówek wyniku (`tabindex="-1"`) – dobra praktyka dla czytników.
- Komunikaty dynamiczne: `aria-live`/`role="status"` są w każdym widoku z formularzem (QR: 7, panel ministerstwa: 4).
- Brak w kodzie obrazów bez `alt` (modułu nie dotyczy – brak `<img>`).
- Do audytu w przeglądarce zostaje: kolejność fokusu na mapie (Leaflet), widoczność fokusu na kafelkach, przewijane tabele (`tabindex="0"` + `role="region"` już są), układ przy 320 px.

Wniosek: hasło „nie zaburzać stylistyki strony” jest w kodzie spełnione świadomie; na slajd warto dać cytat z nagłówka `aed.scss` („government services, not a new identity”) i zrzut w trybie wysokiego kontrastu portalu.

## Iteracja 29 (R13). Instrukcja dla jury – zdania nieaktualne lub sprzeczne po 21.11

| Miejsce w `docs/instrukcja-dla-jury.md` | Problem | Poprawka |
|---|---|---|
| sekcja 5, pkt 3 „Licencje źródeł są zachowane” | sprzeczne z iteracją 21: zbiór z harwestera dostaje CC0, a 715 rekordów ma CC BY 4.0 | najpierw poprawić zasilanie (`conditions/source`), potem dopisać „licencja zbioru w portalu: CC BY 4.0 (wynika z warunku podania źródła)” |
| sekcja 4C, „Zachęty”: „osobnego widoku mapy sprzedawców w interfejsie nie znaleziono” | nieaktualne: ekran `!sellers` ma tabelę i mapę „Siedziby firm na mapie” | usunąć `[do sprawdzenia]`; jeśli ranking zostanie zamieniony na listę (iteracja 2), opisać nową formę |
| sekcja 4C, „referencyjny zakres”: `[do sprawdzenia: formalny opis zakresu w jednej tabeli]` | luka wprost z treści zadania | tabela źródeł: dysponent, terytorium, licencja, rekordy przed/po, pokrycie kluczowych pól, data pobrania – generowana z `raport.json` i `sources.json` (iteracja 1.1, `zrodla.csv`) |
| sekcja 2B, krok 9: `[do sprawdzenia: wygląd formularza sygnału w UI]` | formularz istnieje: strona QR bez tokenu ma nagłówek „Co widzisz przy tym defibrylatorze” (`aed-qr.component.html:201`) | opisać kroki: wybór sygnału, opcjonalna lokalizacja, „Zgłoszenie wysłane” |
| sekcja 2C, krok 4 i 4C: „na świeżej bazie wynik to zwykle 0” | nieaktualne przy domyślnym `AED_DEMO_SEED`: urządzenie demo `PUL` nr 4 ma baterię ważną 30 dni, nr 5 – weryfikację sprzed 200 dni (`aed_service/app.py:329`, `:346`) | podać oczekiwany wynik przypomnień z danymi demo (przypomnienie o baterii + prośba o potwierdzenie) – do policzenia przy następnym uruchomieniu |
| sekcja 6 „Pełna integracja z backendem portalu jest planem” | prawda dla kodu, ale publikacja przez harwester jest sprawdzona | dopisać: „publikacja zbioru mechanizmem portalu (harwester XML) sprawdzona na lokalnej kopii portalu, bez zmian w jego kodzie” |
| sekcja 1 „jedna komenda” | `tips.txt`: jury nie skonfiguruje środowiska | na górze adres publiczny, a Docker jako droga zapasowa (iteracja 10) |
| brak | jury nie ma kroków dla portalu (DATA SOURCES) | nowa ścieżka D: zrzuty albo nagranie 60 s; jeśli jury ma lokalny portal – kroki z `docs/integracja-portal-backend.md` |

Wniosek: przed oddaniem jedno przejście instrukcji „na czysto” przez osobę spoza zespołu jest warte więcej niż kolejna funkcja – każdy `[do sprawdzenia]` w instrukcji to punkt, w którym juror może się zatrzymać.

## Iteracja 30 (R14). Liczby w dokumentach a `raport.json` – spójne; dwa nowe fakty do narracji

Sprawdzone z `datasets/out/raport.json`: rejestr 18 814 (= 19 080 rekordów źródłowych − 266 połączeń), połączenia 266 (odległość 151, odległość i podobieństwo 6, numer referencyjny Warszawy 109), do przeglądu 214 (153 kandydatów, 61 konfliktów źródeł), eksport 781, kompletność (samorządy 31,1–36,0, OSM 38,8, Warszawa 53,2, rejestr 39,2, eksport 51,4). Liczby w `CLAUDE.md`, instrukcji dla jury i konspekcie są zgodne. Znana rozbieżność 18 814 vs 15 769 (usługa nie pokazuje 3 048 rekordów „prywatny”) jest już opisana.

Nowe fakty z tych samych danych (zasada 10 – nasze dane):

1. **Zbiór krajowy to dziś w 91% Warszawa**: 708 z 781 rekordów eksportu pochodzi z API Warszawy, 73 z czterech gmin. Poza Warszawą otwartych danych o AED z odpowiedzialnym dostawcą praktycznie nie ma – to najmocniejszy argument za kanałem sprzedawcy i kampanią (slajd 2 lub 3). Mapa zbioru krajowego to dziś „jedna kropka Warszawy i kilka punktów” – warto pokazać ją obok mapy OSM (18 tys. punktów bez odpowiedzialnego dostawcy).
2. **Wykluczenia z eksportu: 18 033** = 18 032 rekordy znane tylko z OSM (ODbL) + **1 rekord Marek** (punkt 293 km od reszty, współrzędne usunięte przy naprawie → nie spełnia profilu `publikacja`). Pokazuje, że walidacja działa także na danych już opublikowanych na portalu.
3. Udział rekordów z licencją CC BY 4.0 w eksporcie: 715 z 781 (iteracja 21) – wymusza CC BY 4.0 dla zbioru krajowego.

## Iteracja 31 (R15). Błąd testu na końcach linii – przyczyna potwierdzona na świeżych klonach

- `.gitattributes` w repozytorium zawiera jedną linię `core.autocrlf=false` (commit `4e5cfb3 Turn off autocrlf`). To **składnia pliku konfiguracyjnego git, nie atrybutów** – git czyta ją jako wzorzec ścieżki bez atrybutów, więc plik nic nie zmienia (`git check-attr -a datasets/out/aed_dane_gov_pl.csv` – pusto).
- Globalnie (`~/.gitconfig`) jest `core.autocrlf=true`, więc przy pobraniu pliki tekstowe dostają CRLF.
- Sprawdzone na dwóch świeżych klonach gałęzi w katalogu tymczasowym: klon z `autocrlf=true` – CSV z CRLF, test `test_committed_outputs_match_build` **nie przechodzi**; klon z `autocrlf=false` – CSV z LF, test **przechodzi**.
- Ryzyko dla jury: juror na Windows z domyślnym Git for Windows (`autocrlf=true`) zobaczy nieprzechodzący test.

Poprawka (S): zastąpić zawartość `.gitattributes` regułami atrybutów, np.:

```
* text=auto eol=lf
*.xlsx binary
*.jpg binary
*.png binary
*.pdf binary
```

albo co najmniej `datasets/** text eol=lf` i `wzorzec/*.csv text eol=lf`. Po zmianie: `git add --renormalize .` i sprawdzenie testu na świeżym klonie z `autocrlf=true`. Uwaga: CSV z eksportu usługi celowo używa `\r\n` (`publication_csv`, RFC 4180) – reguła `eol=lf` dotyczy plików w repozytorium, nie odpowiedzi HTTP.

## Iteracja 32 (R16, R17). Kontrakt API i dane osobowe w rejestrze

**R16.** Trasy w `docs/api-aed.md` i w `aed_service/app.py` (`build_app`) są zgodne 1:1 (porównanie automatyczne, jedna pozorna różnica to błąd porównania). Zasilanie XML nie jest trasą API, tylko plikiem (CLI i harmonogram) – w kontrakcie wystarczy akapit „publikacja na dane.gov.pl: pliki zasilania w katalogu HTTPS”.

**R17. Dane osobowe – co rejestr przechowuje i co z tego wynika**

| Gdzie | Co | Czy może być daną osobową | Publikowane? |
|---|---|---|---|
| `devices.data`: `dysponent_email`, `dysponent_telefon` | kontakt dysponenta | tak, jeśli to skrzynka lub telefon osoby (np. dyrektora) | nie – kolumny wyczyszczone w eksporcie (`HIDDEN_PUBLIC`) |
| `devices.data`: `dysponent_nazwa` | nazwa dysponenta | **tak przy jednoosobowej działalności** („Jan Kowalski Usługi Medyczne”) | **tak** – kolumna jest w eksporcie |
| `zgloszenia.plik` | cały wgrany plik CSV firmy | tak (kontakty) | nie |
| `messages` | odbiorca, treść, link z tokenem | tak | nie |
| `signals.lat/lon` | położenie osoby zgłaszającej | tak (lokalizacja osoby w chwili zgłoszenia) | nie |
| `accounts` | e-mail konta firmy | zwykle służbowy | nie |

Wnioski:

- Zasada 6 (bez danych osobowych w danych otwartych) jest spełniona dla kontaktów, ale **`dysponent_nazwa` może zawierać imię i nazwisko** przedsiębiorcy. Opcje: (a) w profilu `publikacja` publikować `dysponent_nazwa` tylko dla podmiotów z REGON osoby prawnej / jednostki (pole `dysponent_regon` jest w standardzie), (b) oświadczenie przy zgłoszeniu „wyrażam zgodę na publikację nazwy”, (c) zawsze publikować, bo dane z CEIDG są jawne – do decyzji prawnika; na slajd ograniczeń.
- Portal ma na to mechanizm: warunek `personalData` w `<conditions>` zasilania (`harvester/serializers.py:724`, XSD: „warunki wykorzystywania informacji sektora publicznego zawierającej dane osobowe”, art. 14 ust. 1 pkt 4 ustawy o ponownym wykorzystywaniu ISP). Jeśli `dysponent_nazwa` zostaje w zbiorze, warto wpisać tam krótki warunek – to kolejny mechanizm portalu, który uwzględniamy świadomie.
- Retencja (propozycja do `aed_service/README.md`): sygnały z położeniem – 90 dni; pliki zgłoszeń – do rozliczenia zgłoszenia (np. 30 dni), potem tylko raport; wiadomości – 12 miesięcy. Wdrożenie: zadanie w cyklu harmonogramu (S).

## Iteracja 33 (R18). Brief logo i księga znaku a hasła mentorów – plus odpowiedź na „rozmiar naklejki”

Brief (`kampania/brief-logo.md`) i szablon księgi (`kampania/ksiega-znaku-szablon.md`) pokrywają wymagania zadania (koncepcja, kolory, pole ochronne, minimalna wielkość, niedozwolone użycia) i `tips.txt` (odbiorca: dostawcy, nie pitch). Korekty po nocnych ustaleniach:

- Brief wymienia zastosowanie „pinezka na mapie sprzedawców” i „odznaka dostawcy”. Po iteracji 2/9 (bez publicznego rankingu) – „znak «dane aktualne» na liście dostawców” zamiast pinezki rankingowej.
- Dodać zastosowanie w **panelu dostawcy portalu** (baner przy propozycji „Dane o AED” w „Propozycjach nowych danych”, iteracja 25) – to miejsce, w którym pełnomocnicy instytucji zobaczą akcję.

Kod QR na naklejce – policzone dla obecnego generatora (`aed_service/app.py:530`: `segno`, korekcja błędów M, strefa ciszy 4 moduły zgodnie ze specyfikacją QR):

| Adres w kodzie | Wersja QR | Moduły z ramką | Moduł przy kodzie 30 mm | przy 25 mm |
|---|---|---|---|---|
| `http://localhost:8080/aed/qr/AED-…` | 4 | 41 | 0,73 mm | 0,61 mm |
| `https://dane.gov.pl/aed/qr/AED-…` | 4 | 41 | 0,73 mm | 0,61 mm |
| `https://aed.gov.pl/aed/qr/AED-…` | 3 | 37 | 0,81 mm | 0,68 mm |

Wnioski:

- Krótszy, stały adres (iteracja 12.4) daje mniejszą wersję kodu, czyli większe moduły przy tym samym rozmiarze – łatwiejsze skanowanie przy słabym świetle i z porysowanej naklejki. Argument za krótką domeną akcji.
- Strefa ciszy (4 moduły) przy kodzie 30 mm to ok. 3 mm z każdej strony – tę wartość można wpisać do księgi znaku w miejsce `[do sprawdzenia]` (pole ochronne znaku nie wchodzi w te 3 mm).
- Rozmiar kodu: ogólna reguła praktyczna (nie norma) – odległość skanowania ok. 10× szerokość kodu, czyli kod 30 mm czyta się z ok. 30 cm. Wystarczy, bo naklejka jest przy urządzeniu. Próbny wydruk i test telefonem nadal potrzebny.

## Iteracja 34 (R19). Precedensy ministerstwa w bazie wiedzy portalu – wzór dla naszego pakietu (najważniejsze ustalenie nocy obok licencji)

Z `research_notes/Innowacje w aplikacjach AED/poland_data_and_dane_gov_pl.md` (sekcja B9, źródła: baza wiedzy dane.gov.pl):

- **Rzeczy znalezione (starostowie)** i **ceny mieszkań (deweloperzy)** – ministerstwo już prowadzi dwa programy „wielu dostawców, jeden wzorzec”. Każdy ma w bazie wiedzy ten sam pakiet: **instrukcję zakładania profilu dostawcy, wskazówki przygotowania danych, instrukcję panelu administracyjnego, plik „wzorcowy zakres danych” w XLSX i CSV (UTF-8), ogólny przewodnik importu XML i szablon pliku XML** (np. `RZECZ_Szablon_budowy_pliku_xml_v.1.14_24.04.2026.xml` z ustalonym wzorem tytułu, `updateFrequency`, kategorią, `availability=local`, tagiem).
- Dla deweloperów Minister Cyfryzacji wydał 10.11.2026 rozporządzenie o strukturze danych (Dz.U. 2026 poz. 1489) z „wzorcowymi dokumentami elektronicznymi”.

Co to znaczy dla nas – wyjaśnia trzy hasła mentorów naraz:

1. **„Dostęp do panelu administratora / adres panelu”** – w programach ministerstwa dostawca dostaje *instrukcję panelu administracyjnego*. Komisja najpewniej oczekuje, że nasz pakiet dla dostawców AED też ją ma (adres panelu, logowanie, gdzie dodać zbiór, gdzie źródło danych XML).
2. **„Flaga, która nie jest fakultatywna / kategorie”** – szablon XML ministerstwa *ustala* kategorię i flagi dla wszystkich dostawców. Nasz odpowiednik: `zbior_dane_gov_pl` w `schema.json` jako szablon dla każdego dostawcy AED (iteracja 14.3).
3. **„Zautomatyzowanie procesów”** – deweloperzy publikują codziennie przez XML (w API widać zbiory deweloperów z `source.type = xml` i codziennym importem z własnej domeny). To samo proponujemy dla dużych dysponentów AED.

Propozycja (koszt M, wysoki wpływ na 30% i 10%): **„Pakiet dostawcy danych o AED”** w układzie identycznym jak pakiety ministerstwa, jako katalog `wzorzec/pakiet-dostawcy/`:

| Element pakietu ministerstwa | Nasz odpowiednik | Stan |
|---|---|---|
| instrukcja profilu dostawcy | kroki z iteracji 24 (konto, login.gov.pl, wniosek o instytucję `private`, pełnomocnik) | do napisania (S) |
| wskazówki przygotowania danych | arkusz „Instrukcja” w XLSX + typy kolumn tekstowych, separator przecinek, UTF-8 (iteracje 14.2, 27) | częściowo |
| instrukcja panelu administracyjnego | zrzuty z lokalnego portalu: zbiór, zasób, typy kolumn, znaczniki mapy, źródło danych XML | **zrzuty do zrobienia** |
| wzorcowy zakres danych XLSX + CSV | `wzorzec-aed.xlsx`, `przyklad-publikacja.csv` | jest |
| przewodnik importu XML | link do przewodnika portalu + nasze ustalenia (HTTPS, `.md5`, stałe `extIdent`) | do napisania (S) |
| szablon XML | wygenerowany z `zbior_dane_gov_pl` z miejscami do uzupełnienia (`{dostawca}`, `{extIdent}`) | do zrobienia (S) z `aed_standard/feed.py` |

Na slajd: „Robimy to tak, jak ministerstwo już robi to dla rzeczy znalezionych i cen mieszkań” – jury z ministerstwa rozpozna własny wzorzec. Ścieżka regulacyjna (slajd „co dalej”): rozporządzenie o strukturze danych o AED na wzór Dz.U. 2026 poz. 1489, jeśli powstanie podstawa ustawowa.

Uwaga z przewodnika XML (ta sama notatka): „przy `availability=local` do podmiany pliku potrzebny jest nowy `extIdent`”. Nasz test na lokalnym portalu (21.11) pokazał, że **zmiana adresu przy tym samym `extIdent` też podmienia plik** (`resources/models.py:1285`, `is_link_updated`). Działa w kodzie 2.63.0, ale przewodnik mówi inaczej – w instrukcji dla dostawców podać nasze ustalenie z zastrzeżeniem, że sprawdzono je na wersji 2.63.0.

Dodatkowo z tej samej notatki – **interpelacja 20440 (15.10.2026) do Ministra Cyfryzacji**: pytanie o mapę AED w mObywatelu, o to, czy ministerstwo „rozważa wykorzystanie i połączenie istniejących baz danych o AED” i **jak ustalić odpowiedzialność za wiarygodność danych**. Odpowiedzi brak (stan 21.11). Nasze rozwiązanie odpowiada dokładnie na te pytania – na slajd 1 lub 2 jako kontekst („pytanie, które ministerstwo już dostało”), z linkiem do źródła pierwotnego (api.sejm.gov.pl). Kanał mObywatel jako konsument zbioru – na slajd „co dalej”.

## Iteracja 35 (R20). Tryb przyrostowy (zadanie B) – stan faktyczny

- Przyrostowość jest **po stronie usługi**, nie skryptu pobierania: `import_registry` (`aed_service/app.py:223`) porównuje wynik mappera z bazą i liczy `dodano`, `zmieniono`, `polaczono`, `do_przegladu`, `wycofano`. Wynik każdego przebiegu jest zapisany w tabeli `jobs` i widoczny w panelu ministerstwa („Zadania cykliczne”) – to jest raport „co przybyło” z zadania B3.
- Zabezpieczenia są przemyślane: rekordy ze zgłoszeń i potwierdzone przez zarządców nie są dotykane (`origin != import`); źródło pominięte w danym przebiegu nie traci rekordów; gdy mapper zwróci podejrzanie mało rekordów (poniżej `RETIRE_MIN_SHARE` = 50%), nic nie jest wycofywane i jest ostrzeżenie (`app.py:265`). Na slajd „automatyzacja”: „automat nie skasuje rejestru przez zepsute źródło”.
- Skrypt `scripts/download_aed_data.py` za każdym razem nadpisuje pliki i dopisuje do manifestu `sha256` i `downloaded_at`. Mapper jest szybki (ok. 2 s), więc pełne przeliczenie + różnicowanie w bazie wystarcza; osobny tryb przyrostowy pobierania nie jest potrzebny. Drobny pomysł: w raporcie przebiegu podać, które pliki źródłowe zmieniły `sha256` – jury zobaczy „zmieniło się źródło X” obok „dodano N”.
- Spójność z iteracjami 2 i 23: rekord usunięty u źródła dostaje `wycofany` z powodem („Brak w wynikach mappera…”, `app.py:273`) i **znika z eksportu**. Jeśli przyjmiemy „wycofane zostają w zbiorze”, konsument zobaczy też powód – kolumna `powod` jest w bazie, ale nie w standardzie. Do rozważenia pole `powod_wycofania` (krótki słownik: scalony, usunięty u źródła, zgłoszony przez zarządcę).
- [x] R21 (it. 36). Szablon XML dla dostawcy: jak sparametryzować `zbior_dane_gov_pl` (tytuł z nazwą dostawcy, `extIdent`) – projekt bez zmian w kodzie.
- [x] R22 (it. 36). CKAN: czy samorząd z portalem CKAN (jak Warszawa, Lublin) może dostarczać dane o AED tym kanałem; co trafia do zasobu (link zdalny vs plik).
- [x] R23 (it. 37). Kategorie miejsc: słownik `kategoria_miejsca` – z czego go wyprowadzić (OSM, nazwy w danych Warszawy), ile rekordów da się sklasyfikować automatycznie.
- [x] R24 (it. 38). Godziny dostępu w zgłoszeniach firm i potwierdzeniach zarządców – czy formularz zarządcy tworzy składnię czytaną przez „dostępne teraz”.
- [x] R25 (it. 39). Przegląd `kampania/zachety.md` i `nazwa-i-haslo.md` pod kątem nocnych ustaleń (neutralność, wykaz propozycji, precedensy ministerstwa).
- [x] R26 (it. 40). Pierwsze 60 sekund jury: co zobaczy po otwarciu repozytorium (README) – czy prowadzi do najważniejszych dowodów.
- [x] R27 (it. 41). Ograniczenia na slajd – jedna skonsolidowana lista z całej nocy.


## Iteracja 36 (R21, R22). Szablon dla dostawców i kanał CKAN

**R21 – szablon zasilania dla dowolnego dostawcy (projekt, bez kodu):**

- W `zbior_dane_gov_pl` dodać wzory zamiast stałych: `tytul_wzor` („Defibrylatory AED – {dostawca}” / „AED defibrillators – {provider}”), `ext_ident_wzor` („aed-{kod}”, ≤ 36 znaków), opis ze wstawką `{dostawca}` i `{obszar}`. Ministerstwo to po prostu jeden dostawca z `{dostawca} = „Polska (zbiór krajowy)”`.
- `aed_standard.feed.feed_files` dostaje argument `dostawca` (słownik z wartościami do wzorów); CLI: `python3 -m aed_standard feed PLIK.csv --url https://… --dostawca "Gmina X" --kod gmina-x`. Gmina albo sieć sklepów dostaje gotowe `zasilanie.xml` + `.md5` dla własnego pliku w standardzie.
- Wspólny **tag akcji** w każdym zbiorze (np. nazwa akcji z kampanii) – po nim mapper ministerstwa znajdzie wszystkie zbiory AED w portalu (`/search?q=…&tag=…` w API portalu) zamiast utrzymywać ręczną listę w `sources.json`.
- Walidacja przed zapisem: zbiór przechodzi profil `publikacja` (walidator już jest); zasilanie nie powstaje, gdy plik ma błędy – dostawca nie opublikuje przez przypadek złego pliku.

**R22 – kanał CKAN (miasta z własnym portalem danych):**

- Portal pobiera zbiory z portali CKAN miast (w notatkach: Warszawa `dane.um.warszawa.pl`, Lublin `otwartedane.lublin.eu`, oba codziennie). Zasób z CKAN to **link** (`ResourceSchema.link = url`, `harvester/serializers.py:236-300`); format wykrywany z odpowiedzi, gdy go brak.
- Zbiór Warszawy o AED (39512) na dane.gov.pl to właśnie taki link (dlatego w portalu nie ma pliku, a my czytamy API miasta).
- Wniosek: miasto z CKAN publikuje AED w standardzie **u siebie**, a portal sam to pobierze – trzeci kanał bez zmian w portalu (obok formularza/CSV i XML). W pakiecie dostawcy (iteracja 34) wystarczy akapit „masz CKAN – opublikuj plik w standardzie z tagiem akcji; portal pobierze go automatycznie”.
- Słabość: zasób-link do API miasta (jak Warszawa) nie daje w portalu tabeli i mapy, jeśli pod linkiem nie ma pliku tabelarycznego. Rekomendacja dla miast: link do **pliku CSV w standardzie**, nie do API.

## Iteracja 37 (R23). Kategoria miejsca – czy da się ją wyprowadzić, i co mówi o luce w danych

Prototyp (wyrażenia regularne na `nazwa` + `opis_lokalizacji`, skrypt badawczy, wynik przybliżony) na 781 rekordach eksportu:

| Kategoria | Rekordy | Udział |
|---|---|---|
| oświata (szkoły, przedszkola, biblioteki) | 281 | 36% |
| administracja (urzędy, OPS, policja, straż) | 112 | 14% |
| sport i rekreacja | 55 | 7% |
| transport (metro, stacje) | 54 | 7% |
| ochrona zdrowia | 50 | 6% |
| zakład pracy / biuro | 37 | 5% |
| kultura | 26 | 3% |
| **handel i usługi** | **2** | **0,3%** |
| nierozpoznane | 164 | 21% (głównie skróty typu „SPZZLO” – przychodnie; dwie reguły podniosłyby rozpoznanie do ok. 85%) |

Wnioski:

- Automatyczna klasyfikacja nadaje się na **podpowiedź** dla zarządcy w formularzu potwierdzenia („wygląda na: szkoła – zgadza się?”), nie na publikację bez potwierdzenia.
- **Fakt do narracji (nasze dane, z zastrzeżeniem metody):** otwarte dane o AED to dziś prawie wyłącznie urządzenia w jednostkach samorządu (szkoły, urzędy, obiekty sportowe miasta). Sklepy, galerie handlowe, stacje paliw, hotele – czyli miejsca, gdzie AED kupują firmy – to **0,3%** zbioru. To dokładnie luka, którą zamyka kanał sprzedawcy (pkt 3 rozmowy z komisją) – firmy kupują AED, ale nikt nie publikuje ich lokalizacji. Dobry slajd 3: „kto dziś publikuje, a kogo brakuje”.
- Słownik `kategoria_miejsca` (iteracja 5) potwierdzony danymi: 8 kategorii pokrywa praktycznie wszystkie rozpoznane rekordy.

## Iteracja 38 (R24). Godziny dostępu: formularz – walidator – „dostępne teraz”

- Formularz zarządcy (`aed-hours-picker.component.ts`) nie każe wpisywać składni: „całą dobę” albo dni + godziny; sam zapisuje `opening_hours` w podzbiorze czytanym przez `aedOpenNow`. Ścieżka QR → „dostępne teraz” jest więc spójna.
- **Luka: walidator (`aed_standard/validate.py`) nie sprawdza składni `godziny_dostepu`.** Plik CSV firmy albo gminy z wartością „pn-pt 8-16” przejdzie bez ostrzeżenia, a w interfejsie urządzenie dostanie „dostępność teraz nieznana”.
- Pomiar (port wyrażenia z `aed-hours.ts` do Pythona): z 6 781 wartości `opening_hours` w OSM **6 572 (96,9%) jest czytelnych** dla gramatyki frontendu. Nieczytelne to głównie opisy słowne („Całodobowo”, „Dostępne w godzinach pracy kolei linowej”) i drobne błędy składni („Su10:00-18:00”, „07:30 -17:00”).
- Wniosek: gramatyka „prosty podzbiór opening_hours” jest dobrym wyborem do standardu – pokrywa prawie wszystkie realne wpisy. Propozycja (S): reguła walidatora „`godziny_dostepu` poza obsługiwaną składnią → ostrzeżenie z podpowiedzią: przenieś opis do `godziny_dostepu_opis` albo użyj wzoru `Mo-Fr 08:00-16:00`”. Ta sama gramatyka w Pythonie i w TypeScript, opisana raz w `schema.json` (wzorzec w polu `constraints.pattern` albo w opisie) – zgodnie z zasadą jednego źródła prawdy.
- Liczba do slajdu 3 (nasze dane): dostępność czasowa jest w 37% rekordów OSM i prawie zawsze w poprawnej składni; problemem jest **brak** godzin, nie ich format – znowu argument za zarządcą, który je potwierdza.

## Iteracja 39 (R25). Pakiet zachęt (`kampania/zachety.md`) po nocnych ustaleniach

Do poprawy:

| Pozycja w `zachety.md` | Problem | Propozycja |
|---|---|---|
| (a) „Obecność na publicznej mapie sprzedawców … z linkiem do oferty (przewaga marketingowa przy przetargach i zakupach samorządów)” | najostrzej koliduje z hasłem „nie premiować” – państwowy serwis dawałby wybranym firmom przewagę w zamówieniach publicznych (ryzyko także z punktu widzenia równego traktowania wykonawców) | lista dostawców danych bez linków do ofert i bez kolejności; znak „dane aktualne” na równych zasadach |
| (a) „dostawca typu «producent lub sprzedawca AED» jako nowy typ konta (wzorzec: `developer`)” | niepotrzebna zmiana w portalu: typ `private` już istnieje i ma właściwe ograniczenia (iteracja 24) | firmy jako instytucje `private`; nowy typ tylko na slajd „opcja”, jeśli ministerstwo chce osobnego filtra |
| (c) „Ranking kompletności i aktualności gmin” | mniejsze ryzyko (podmioty publiczne), ale słowo „ranking” wraca w kontrze do hasła mentorów | nazwać „postęp gmin” – mapa udziału potwierdzonych rekordów, bez miejsc w tabeli |

Nowe zachęty znalezione w kodzie portalu (bez kosztu budowy – portal już to ma):

1. **Licznik wyświetleń i pobrań zbioru** (`views_count`, `downloads_count` w API, iteracja 27) – „Twoje dane pobrano N razy” w mailu do dostawcy.
2. **PoCoTo** (iteracja 26) – przykład wykorzystania z powiązanym zbiorem dostawcy: publiczny dowód, że dane są używane.
3. **Przypomnienia portalu o aktualizacji** dla zbiorów dodanych ręcznie (iteracja 19) – gmina dostaje je za darmo przy częstotliwości miesięcznej lub kwartalnej.
4. **Ocena otwartości** – zbiór w standardzie (UTF-8, przecinek) automatycznie dostaje 4/5 gwiazdek (iteracja 27); dla samorządu to mierzalny wynik w portalu.
5. **„Propozycje nowych danych”** – głos „plus” pełnomocnika przy propozycji AED (iteracja 25) jako publiczna deklaracja udziału w akcji.

Mierniki kampanii – dopisać (nadal proces, nie skutki zdrowotne): liczba głosów „plus” przy propozycji AED, liczba zbiorów z tagiem akcji na portalu (iteracja 36), liczba źródeł danych XML z danymi o AED, odsetek urządzeń zeskanowanych w ostatnich 90 dniach (iteracja 12.6).

## Iteracja 40 (R26). Pierwsze 60 sekund jurora w repozytorium

Juror otwiera `README.md`. Dziś widzi: tytuł roboczy („Misja AED – Dane na ratunek” – to nazwa zadania, nie projektu i nie akcji), akapit „jak to działa”, uruchomienie przez Dockera, tabelę katalogów. Brakuje:

1. **Nazwy akcji i logo** na samej górze (25% oceny, a juror nie widzi ich w pierwszym ekranie).
2. **Linku do instrukcji dla jury** (`docs/instrukcja-dla-jury.md`) – to plik, o który prosi `tips.txt`, a README go nie wymienia w pierwszym ekranie.
3. **Adresu publicznego prototypu** (iteracja 10) – dziś pierwsza instrukcja wymaga Dockera.
4. **Trzech zdań „co jest zgodne z portalem”** – dowód 30% (instytucja-dostawca, harwester XML, bez zmian w kodzie portalu).
5. Wiersz o `backend/` mówi „niezmieniony; notatka integracyjna” – dopisać „publikacja przez harwester sprawdzona na lokalnej kopii portalu” i plik `backend/docker-compose.aed-ports.yml` (jedyny nasz plik w forku backendu).

Proponowany układ pierwszego ekranu README (do 15 linii): nazwa akcji + hasło + logo; jedno zdanie o rozwiązaniu; trzy linki: prototyp (adres), instrukcja dla jury, prezentacja; trzy punkty dowodowe (standard + XLSX, proces sprzedawca → QR → zarządca, publikacja harwesterem); dopiero potem uruchomienie lokalne i struktura katalogów.

## Iteracja 41 (R27). Skonsolidowana lista ograniczeń (do slajdu 9 i sekcji 6 instrukcji)

Pogrupowane, każde z odpowiedzią „co dalej”. Pozycje oznaczone * są nowe z 21/22.11.

**Prawne i organizacyjne**
1. Brak podstawy prawnej obowiązku raportowania przez sprzedawców → dobrowolność + zachęty; ścieżka: rozporządzenie o strukturze danych jak dla deweloperów (Dz.U. 2026 poz. 1489), jeśli powstanie podstawa ustawowa.*
2. Dane OSM (ODbL) poza zbiorem otwartym; wymaga opinii prawnika.
3. Licencja zbioru krajowego musi być CC BY 4.0 (715 z 781 rekordów pochodzi ze źródeł CC BY); zasilanie trzeba uzupełnić o warunek podania źródła.*
4. `dysponent_nazwa` może zawierać dane osobowe przedsiębiorcy (jednoosobowa działalność) – do decyzji prawnika; portal ma na to warunek `personalData`.*
5. Założenie instytucji-dostawcy w portalu to proces redakcyjny (nie samoobsługa) – dlatego dla małych firm kanał przez ministerstwo.*

**Mechanika portalu (sprawdzona w kodzie 2.63.0)**
6. Harwester usuwa zbiór lub zasób, którego zabraknie w pliku XML; wymaga HTTPS i pliku `.md5`.*
7. Portal sam wnioskuje typy kolumn; redaktor raz ustawia jako tekst `kod_terc`, `kod_simc`, `nr_budynku`, `zrodlo_id` i znaczniki mapy.*
8. Przypomnienia portalu o aktualizacji nie obejmują zbiorów z harwestera (zastępuje je raport importu).*
9. Przewodnik XML portalu i kod 2.63.0 różnią się w opisie podmiany pliku – opieramy się na zachowaniu sprawdzonym w kodzie.*

**Dane**
10. Zbiór krajowy to dziś w 91% Warszawa; miejsca komercyjne (sklepy, stacje, hotele) to 0,3% rekordów.*
11. Żaden rekord z istniejących źródeł nie ma potwierdzenia zarządcy (wszystkie `niepotwierdzony`).
12. Godziny dostępu są tylko w 37% rekordów OSM i ok. 14% rekordów Warszawy w formie czytelnej maszynowo (opisy słowne są, ale niekonwertowane).*
13. Informacji o zamkniętej szafce praktycznie nie ma w żadnym źródle (OSM `locked`: 3 obiekty na 18 298).*

**Prototyp**
14. Działa lokalnie w Dockerze; publiczny adres – decyzja otwarta.
15. Wiadomości do zarządców trafiają do skrzynki w panelu, nie są wysyłane e-mailem.
16. Usługa demonstracyjna: jednowątkowa, bez limitu prób logowania.
17. Audyt dostępności: automatyczny (axe, 0 naruszeń w obszarze AED), klawiatura, 320 px i wysoki kontrast – **zrobione** (`frontend/aed-zrzuty/DOSTEPNOSC.md`, sprostowanie z it. 68); brak testu czytnikiem ekranu i na prawdziwym telefonie; jeden kolor stanu (`#c25400`) do sprawdzenia na jasnoszarym tle.*
18. Test porównujący zbiór z plikami w repozytorium nie przechodzi przy `core.autocrlf=true` (błędny `.gitattributes`) – do poprawy przed oddaniem.*
- [x] R28 (it. 42). Strona QR bez tokenu: co widzi przypadkowa osoba (świadek NZK!) – czy pierwszym komunikatem jest „zadzwoń 112”, a nie formularz.
- [x] R29 (it. 43). Eksport: kolumny puste dla wszystkich rekordów (np. `numer_seryjny` zawsze pusty) – czy nie mylą konsumentów; co mówi o tym portal (kolumny puste w tabeli).
- [x] R30 (it. 44). Wydajność i skala: ile rekordów i jaki rozmiar CSV przy pełnym pokryciu kraju (szacunek z OSM 18 tys.) – limity portalu dla zasobu i walidacji tabelarycznej.
- [x] R31 (it. 45). Dane demo i fikcyjne w eksporcie – czy flaga `demo` nigdy nie wycieka do zasilania XML.
- [x] R32 (it. 45). Spójność słowników standardu z portalem: `licencja` (CC0 1.0 / CC BY 4.0) vs lista licencji portalu; kategorie.
- [x] R33 (it. 45). Scenariusz awarii: rejestr niedostępny o 3:00 – co robi harwester (raport błędu, brak usuwania – iteracja 18) i jak ministerstwo się dowie.


## Iteracja 42 (R28). Strona QR a osoba w sytuacji nagłej – **brak „112”**

- Strona QR bez tokenu (`aed-qr.component.html`) zaczyna się kartą urządzenia i nagłówkiem „Co widzisz przy tym defibrylatorze” z formularzem sygnału. **Ani na stronie, ani w komponencie nie ma numeru 112** (`grep 112` – brak). Napis na naklejce: „Zeskanuj kod QR i sprawdź lub zgłoś stan AED” (`app.py:524`).
- Ryzyko: naklejka wisi na szafce AED. Osoba, która w stresie zeskanuje kod w czasie zatrzymania krążenia, dostanie formularz zamiast instrukcji. Jury z ministerstwa i każdy ratownik to zauważy; to też kryterium „zasady UX”.
- Poprawka (S, wysoki priorytet – bezpieczeństwo i UX):
  1. Na samej górze strony QR, przed kartą urządzenia: wyraźny blok „Ktoś stracił przytomność i nie oddycha? **Zadzwoń 112** (link `tel:112`). Otwórz AED i postępuj według poleceń głosowych urządzenia.” – tekst, nie tylko ikona; przycisk duży, w zasięgu kciuka.
  2. Na naklejce, nad kodem QR: „W nagłym wypadku: 112”. Księga znaku: ten napis ma pierwszeństwo przed znakiem akcji (pole ochronne nie może go zasłaniać).
  3. Formularz sygnału dopiero pod blokiem 112, z nagłówkiem typu „Sprawdzasz urządzenie? Zgłoś, co widzisz”.
- Zgodne z zasadą 9 (nie obiecujemy uratowanych istnień): blok nie jest obietnicą, tylko przekierowaniem do właściwej pomocy.
- Ten sam wniosek dla przyszłego „samo zeskanowanie zgłasza miejsce i stan” (pkt 4 rozmowy z komisją): automatyczne zgłoszenie przy skanie nie może opóźnić pokazania bloku 112.

## Iteracja 43 (R29). Puste kolumny i **dwie różne definicje „eksportu publikacyjnego”**

Pomiar `datasets/out/aed_dane_gov_pl.csv` (781 rekordów, 38 kolumn):

- **10 kolumn jest zawsze pustych**: `nr_lokalu`, `numer_seryjny`, `data_produkcji`, `data_waznosci_elektrod`, `data_waznosci_baterii`, `dysponent_nazwa`, `dysponent_regon`, `wprowadzajacy_nazwa`, `data_weryfikacji`, `sposob_weryfikacji`; kolejne 5 jest wypełnionych w mniej niż 10% (`cecha_ulicy` 52, `kod_terc`/`kod_simc` 24, `dysponent_email` 2, `dysponent_telefon` 1).
- To uczciwy obraz stanu danych (wszystkie pola kanału sprzedawcy i zarządcy są puste, bo te kanały dopiero ruszają) – warto to powiedzieć w opisie zasobu i na slajdzie 3: „kolumny czekają na dostawców”.
- **Niespójność:** usługa przy eksporcie czyści `dysponent_email`, `dysponent_telefon`, `numer_seryjny` (`HIDDEN_PUBLIC`, `aed_service/app.py:51`), ale `python3 -m aed_standard build` tego nie robi. W zatwierdzonym pliku `datasets/out/aed_dane_gov_pl.csv` są **2 adresy e-mail i 1 telefon** – instytucjonalne (domena urzędu miasta Przemyśla, przejęte z jego zbioru na portalu), więc bez naruszenia zasady 6, ale plik w repozytorium i plik z usługi to dwie różne definicje „zbioru do publikacji”.
- Przyczyna: lista pól niepublikowanych żyje w kodzie usługi, a nie w `schema.json` – wbrew zasadzie 1 (jedno źródło prawdy). Poprawka (S): atrybut pola w schemacie, np. `"publiczne": false` dla `dysponent_email`, `dysponent_telefon`, `numer_seryjny`; `publication_export` w `aed_standard` czyści te pola; usługa używa tej samej funkcji. Wtedy otwarta decyzja „czy publikować numer seryjny” (CLAUDE.md) to zmiana jednej wartości w schemacie.

## Iteracja 44 (R30). Skala – czy portal udźwignie zbiór krajowy przy pełnym pokryciu

- Dziś: 781 rekordów = 247 583 B, czyli ok. 317 B na rekord. Przy 18 298 urządzeniach (tyle zna OSM) ≈ 5,8 MB; przy 100 000 (rząd wielkości deklaracji we Francji: 105 250, iteracja z `zachety.md`) ≈ 32 MB.
- Limity portalu (`settings/base.py`): plik zasobu do 1 GB (`RESOURCE_MAX_FILE_SIZE`), raport do 100 000 wierszy (`RESOURCE_MAX_REPORT_SIZE`). Zapas jest ogromny.
- **Pułapka**: portal wnioskuje typy kolumn z **pierwszych 5 000 wierszy** (`indexed_data.py:589`, `infer(limit=5000)`), a walidacja zatrzymuje się po 10 błędach (`error_limit=10`, `:614`). Przy dużym pliku typ ustalony na początku pliku (np. `integer` dla `nr_budynku`, jeśli pierwsze 5 000 rekordów ma same liczby) wywoła błąd dalej w pliku. To kolejny argument za ustawieniem typów kolumn tekstowych przez redaktora (iteracja 21/R1 lokalnie: `nr_budynku`, `kod_terc`, `kod_simc`, `zrodlo_id`) – i za zapisaniem tych typów w pakiecie dostawcy.
- Kolejność wierszy w eksporcie: sortowanie po `id_aed` (losowy identyfikator) miesza źródła – dobrze dla wnioskowania typów (próbka reprezentatywna).

## Iteracja 45 (R31, R32, R33). Dane demo, słowniki licencji, awaria rejestru – i sprostowanie o raportach e-mail

**R31 – dane demonstracyjne:** `publication_csv` pomija `demo=1` (`aed_service/app.py:724`), a zasilanie XML korzysta z tej samej funkcji – fikcyjne urządzenia z seedu nie trafią do portalu. Urządzenia zgłoszone przez jurorów w publicznym prototypie *trafią* do eksportu (nie mają flagi `demo`) – dlatego publiczny prototyp **nie może mieć ustawionych `AED_FEED_DIR`/`AED_FEED_URL` wskazujących na prawdziwy portal**. Do instrukcji wdrożenia prototypu.

**R32 – słowniki:** licencje w standardzie (`CC0 1.0`, `CC BY 4.0`, `ODbL 1.0`) – pierwsze dwie są na liście licencji portalu (`Dataset.LICENSES`), ODbL nie, co jest spójne z wykluczeniem OSM z eksportu. Kategoria `HEAL` istnieje w XSD i w bazie portalu (sprawdzone 21.11, kategoria „Zdrowie”).

**R33 – awaria rejestru o 3:00:** harwester zapisze import ze statusem błędu i **niczego nie usunie** (`harvester/models.py:1211`, iteracja 18). Ale:

- **Sprostowanie:** raport importu **nie jest wysyłany e-mailem** – pole `is_report_email_sent` istnieje, lecz w panelu jest komentarz „email reports aren't implemented” (`harvester/admin.py:370`). Wcześniejsze zdania w iteracjach 13 i 19 poprawione. Ministerstwo dowie się o błędzie tylko z panelu (status ostatniego importu).
- Pomysł (S–M, automatyzacja): **monitor publikacji po stronie rejestru** – codziennie po 3:00 usługa pyta API portalu o zbiór ministerstwa i porównuje adres zasobu z nazwą bieżącej wersji CSV (`aed_dane_gov_pl-<hash>.csv`). Rozbieżność albo brak aktualizacji przez 2 dni → wiadomość w skrzynce ministerstwa („portal nie pobrał wersji z dnia …”). Domyka pętlę automatyzacji bez zmian w portalu i bez polegania na niezaimplementowanych mailach.
- Do slajdu ograniczeń: „portal nie wysyła raportów importu e-mailem (wersja 2.63.0) – rejestr sam sprawdza, czy publikacja się udała”.

## Iteracja 46. „Kto wprowadził urządzenie” i metadane istniejących zbiorów – dowód na potrzebę wzorca metadanych

**„Kto wprowadził urządzenie”** (pole wymienione wprost przez komisję): w eksporcie wszystkie 781 rekordów mają `wprowadzajacy_typ = import` i **puste `wprowadzajacy_nazwa`**. Dla importu odpowiedź na pytanie komisji jest znana – to dostawca zbioru źródłowego (instytucja na portalu albo Urząd m.st. Warszawy). Poprawka (S): pole `dostawca` w każdym wpisie `sources.json` (nazwa instytucji z metadanych zbioru na portalu) i wypełnianie nim `wprowadzajacy_nazwa` przez mapper. Bez tego jury, sprawdzając pole z listy komisji, zobaczy pustą kolumnę.

**Metadane czterech zbiorów samorządowych** (z `datasets/raw/dane_gov_pl/*/dataset_metadata.json`):

| Zbiór | Tytuł w portalu | Częstotliwość aktualizacji | Licencja |
|---|---|---|---|
| Krosno (3624) | Defibrylatory zlokalizowane w Mieście Krosno | „Nie dotyczy” | CC0 1.0 |
| Legionowo (40593) | **„Zdrowie”** | nieregularnie | CC0 1.0 |
| Marki (4955) | Defibrylatory zlokalizowane na terenie Miasta Marki | **„Jednorazowe udostępnienie”** | CC BY 4.0 |
| Przemyśl (4581) | Lokalizacje AED – Automatycznych Defibrylatorów Zewnętrznych w Przemyślu | codziennie | CC0 1.0 |

Wnioski (nasze dane, do slajdu 3 obok tabeli pokrycia pól):

- Najczystszy plik (Legionowo) ma zbiór zatytułowany **„Zdrowie”** – wyszukiwarka portalu po „AED” czy „defibrylator” go nie znajdzie po tytule. To konkretny dowód, że **wzorzec musi obejmować metadane** (tytuł, tagi, częstotliwość), nie tylko kolumny (iteracja 14.1).
- Trzy z czterech zbiorów nie deklarują regularnej aktualizacji („nie dotyczy”, „jednorazowe”, „nieregularnie”) – dane o urządzeniach, które się zmieniają (baterie, elektrody, godziny), są publikowane jak dokument archiwalny. Argument za mechanizmem potwierdzeń i zasilaniem codziennym.
- Kompletność rekordów w eksporcie: minimum 31, mediana 51, **maksimum 62 na 100** – w Polsce nie ma dziś ani jednego otwartego rekordu AED z kompletnością powyżej 62. Rekord po ścieżce sprzedawca → zarządca w prototypie ma ok. 90+ (do potwierdzenia liczbą z panelu przy zrzutach). Dobry kontrast na slajd 8.

## Iteracja 47. Wskaźnik kompletności (pkt 7 rozmowy z komisją) – liczby i dwie pułapki

- Wagi w `schema.json`: 22 pola z wagą > 0, suma 39. Rekord z `wzorzec/przyklad-publikacja.csv` (status `aktywny`, pełna ścieżka) ma **97/100**; brakuje mu tylko `kod_terc`.
- Kontrast na slajd 8 (nasze dane): **najlepszy otwarty rekord AED w Polsce dziś – 62/100, rekord po ścieżce sprzedawca → zarządca – 97/100.** To jedno zdanie streszcza wartość procesu i jest zgodne z zasadą 9 (mierzymy dane, nie skutki zdrowotne).

Pułapki:

1. **97 to sufit ścieżki QR.** Formularz zarządcy nie pyta o `kod_terc` (nie ma go w `CONFIRM_FIELDS`, `aed_service/app.py:52`), a sprzedawca go nie zna. Żaden rekord z prototypu nie dojdzie do 100. Opcje: (a) uzupełniać TERC automatycznie z adresu lub współrzędnych (wymaga rejestru TERYT/PRG – poza zakresem nocy), (b) waga `kod_terc` = 0 do czasu automatu, (c) zostawić i wyjaśnić. Najprościej (b) albo (c) z przypisem.
2. **Kompletność liczona jest na rekordzie z rejestru, a publiczny wiersz nie ma pól ukrytych.** `numer_seryjny` (waga 2), `dysponent_email` (1), `dysponent_telefon` (1) = 4/39 ≈ 10 punktów, które konsument zbioru widzi jako puste kolumny przy wysokiej `kompletnosc`. W opisie kolumny w `schema.json` dopisać: „kompletność rekordu w rejestrze, łącznie z polami niepublikowanymi”. Alternatywa: osobna „kompletność publikacyjna” – raczej niepotrzebna komplikacja.

## Iteracja 48. Przegląd duplikatów – ile pracy ministerstwa wpływa na publikowany zbiór; rozmiar naklejki

**Duplikaty** (`datasets/out/duplikaty_do_przegladu.csv`, 214 par, mediana odległości 24 m):

- **212 z 214 par to „źródło publikowalne + OpenStreetMap”** (186 par Warszawa–OSM, 26 par gmina–OSM, w tym 2 „konflikty źródeł”); par między dwoma źródłami publikowalnymi jest **zero**.
- Ponieważ rekordy OSM nie trafiają do eksportu (zasada 3), decyzja w tych parach **nie zmienia zbioru na dane.gov.pl** – zmienia tylko liczebność rejestru i to, czy urządzenie z OSM „czeka” na potwierdzenie jako osobny punkt.
- „Konflikt źródeł” przy odległości 0 m i podobieństwie 1,0 (np. ten sam urząd w Warszawie i w OSM) oznacza najpewniej, że węzeł OSM pasuje do więcej niż jednego urządzenia z drugiego źródła (kilka AED w jednym budynku) – dlatego decyzja jest ręczna; zgodne z zasadą „dwa rekordy z jednego źródła nigdy nie są łączone automatycznie”.
- Wniosek dla procesu (S): **kolejka przeglądu z priorytetem** – najpierw pary, w których oba rekordy są publikowalne (wpływają na zbiór otwarty), potem pary z rekordem zgłoszonym przez firmę lub zarządcę (wpływają na naklejki), na końcu pary z OSM (wpływają tylko na statystykę rejestru). Na slajd „automatyzacja”: „człowiek przegląda tylko to, co zmienia publikowany zbiór”.

**Rozmiar naklejki** (odpowiedź na `[do sprawdzenia]` w briefie i księdze znaku): arkusz do druku w panelu firmy ma 3 naklejki w rzędzie na A4 (`aed.scss:1262`, odstęp 4 mm, margines wewnętrzny 3 mm) – po odjęciu marginesów drukarki naklejka ma ok. **55–60 mm szerokości**, a kod QR zajmuje ok. 80% szerokości (287 z 360 jednostek SVG), czyli ok. **45 mm** – moduł ok. 1,1 mm (wersja 4). „3 cm” z briefu to więc najwyżej średnica odznaki, nie cała naklejka. SVG naklejki nie ma jednostek fizycznych (`width` w jednostkach użytkownika, `app.py:551`) – przy druku pojedynczej naklejki poza arkuszem rozmiar zależy od programu; poprawka (S): `width="60mm"` w SVG.

## Iteracja 49. Dokumenty uzupełniające w zasilaniu XML – słownik pól widoczny przy zbiorze w portalu

- XSD 1.13 pozwala dołączyć do zbioru i do zasobu do 10 **dokumentów uzupełniających** (`supplements/supplement`: `url` HTTPS, `name` PL/EN, `language` pl/en). Harwester pobiera plik i akceptuje formaty **doc, docx, odt, pdf, txt** (`harvester/serializers.py:165-200`) – to dokumentacja, nie dane.
- Pomysł (S): w zasilaniu dołączyć do zbioru AED dokument „Opis struktury danych – wzorcowy zakres danych o AED” w formacie **ODT albo TXT** (otwarte), generowany z `schema.json` (nazwa kolumny, opis, typ, słownik wartości, wymagalność). Użytkownik zbioru na portalu widzi słownik pól bez szukania repozytorium; ministerstwo publikuje wzorzec mechanizmem portalu. XLSX (wzorzec dla dostawców) nie jest dozwolony jako dokument uzupełniający – zostaje w pakiecie dostawcy i ewentualnie jako osobny zasób.
- Zgodne z wymaganiem zadania „formaty odczytywalne maszynowo dla danych” – dokument uzupełniający nie jest zasobem z danymi.
- Generator jednego pliku TXT ze schematu to kilkanaście linii w `aed_standard` (bez zależności); ODT wymagałby biblioteki albo szablonu – TXT wystarczy.

## Iteracja 50. Rozmowa z komisją (pkt 1–9) – stan po nocy, punkt po punkcie

| Pkt | Oczekiwanie komisji | Stan | Co zostało (z iteracji tej nocy) |
|---|---|---|---|
| 1 | ministerstwo zbiera i publikuje jeden zbiór | rejestr + zasilanie XML → zbiór ministerstwa w portalu (sprawdzone lokalnie) | licencja CC BY w zasilaniu (it. 21); zrzuty |
| 2 | ujednolicona, **generyczna** struktura zgodna z tym, co leży na portalu | `schema.json` zgodny z Legionowem | metadane jako część wzorca (it. 14, 46); słownik pól jako dokument uzupełniający (it. 49); „generyczność” na slajdzie (it. 5) |
| 3 | sprzedawca raportuje CSV/formularzem, firmy mają konta | panel firmy | onboarding firmy jako instytucji `private` dla dużych (it. 24); `wprowadzajacy_nazwa` dla importów (it. 46) |
| 4 | naklejka QR, zarządca potwierdza; QR mocno wyeksponowany; w przyszłości skan zgłasza stan | strona QR, naklejki A4 | **blok 112** (it. 42); „ostatnio widziany” z sygnałów (it. 12.1); stały krótki adres w QR (it. 12.4, 33) |
| 5 | okresowe prośby o potwierdzenie; właściciel odpowiada za baterię i elektrody | przypomnienia 183/365 dni, 60 dni przed terminem | monitor publikacji (it. 45); przypomnienia portalu dla gmin publikujących ręcznie (it. 19) |
| 6 | mapper cykliczny + deduplikacja formularzy i źródeł | jest, z zabezpieczeniami (it. 35) | priorytet kolejki przeglądu (it. 48); odkrywanie nowych zbiorów po tagu (it. 2, 36) |
| 7 | kompletność | wskaźnik 0–100 | „62 vs 97” na slajd (it. 47); sufit 97 przez `kod_terc` |
| 8 | zachęty: **co ma firma kupująca AED** i utrzymująca dane (InPost) | `zachety.md` (sprzedawcy, zarządcy, samorządy) | patrz niżej |
| 9 | logo, marketing, prezentacja sprzedażowa | brief, szablon księgi, konspekt | decyzje ludzi; narracja „robimy jak przy rzeczach znalezionych i cenach mieszkań” (it. 34) |

**Pkt 8 – doprecyzowanie, którego brakowało:** komisja pytała o firmę **kupującą** AED (właściciela, np. biurowiec, sieć sklepów, zakład pracy), a punkt odniesienia to InPost – firma, która *instaluje* AED i zyskuje na widoczności. `zachety.md` mówi głównie o sprzedawcach. Dla kupującego:

- **Widoczność bez reklamy:** potwierdzony AED pokazuje się w zbiorze państwowym, w mapach i aplikacjach pod nazwą miejsca (np. „Galeria X, poziom 0”) – na równych zasadach dla wszystkich, więc zgodnie z „nie premiować”.
- **Dowód do raportów i audytów:** potwierdzenie z rejestru (data, status `aktywny`, terminy baterii/elektrod) jako załącznik do dokumentacji BHP, raportu ESG/CSR czy rozmowy z ubezpieczycielem – bez tezy, że to wymóg prawny [do sprawdzenia, czy jakikolwiek standard raportowania to uznaje].
- **Zero pracy po stronie IT:** skan naklejki od sprzedawcy, trzy kroki, przypomnienia o serwisie przychodzą same – „utrzymywanie aktualnych danych” to jedna minuta co pół roku (do zmierzenia, it. 16).
- **Spokój prawny:** odpowiedź „mamy AED, jest zgłoszony i sprawdzany” zamiast „nie wiemy, czy działa” – język procesu, nie obietnic.

## Iteracja 51. „Umieść na swojej stronie” – gotowa mapa AED dla gmin i firm, bez naszego kodu

- Frontend portalu ma moduł osadzania: `/embed/!resource/!{id}/!map` (oraz `!table`, `!chart`), `pages/embedded/embedded-routing.module.ts`, i przycisk „Umieść na swojej stronie” na stronie zasobu z gotowym kodem HTML (szerokość, wysokość, podpis „Dane pochodzą z portalu”; `dataset-resource.component.html:284-393`, tłumaczenia `Embed` w `pl.json`). Mapa jest dostępna, gdy zasób ma dane geo (`hasGeoData`, `dataset-resource.component.ts:211`) – nasz zbiór ma je po ustawieniu znaczników `b`, `l`, `label` (sprawdzone 21.11).
- Pomysł D5 z researchu („widget dla stron gmin”) **nie wymaga budowy** – portal go ma. Zachęta dla samorządu i firmy-kupującego: „opublikuj w standardzie albo potwierdź urządzenie, a mapę AED wkleisz na stronę urzędu jednym kodem z dane.gov.pl”. Zero kosztu dla ministerstwa.
- Ograniczenie: osadzona mapa pokazuje cały zasób (cały kraj), nie wycinek gminy – filtr po gminie wymagałby zasobu na gminę albo parametru filtra w adresie osadzenia – `MapComponent` (`shared/map/map.component.ts:209-230`) synchronizuje filtr zasobu z parametrem `q` w adresie, więc osadzenie z `?q=<nazwa gminy>` prawdopodobnie pokaże tylko pasujące punkty [do sprawdzenia na uruchomionym portalu]. Dla gminy publikującej własny zbiór (model federacyjny) problem znika.
- Do zrzutów: modal „Umieść na swojej stronie” przy zasobie AED + przykładowa strona HTML z osadzoną mapą – mocny, tani dowód „zgodności z mechanizmami portalu” i element pakietu zachęt.

## Iteracja 52. CMS portalu jako kanał kampanii i pakietu dostawcy (panel CMS działa lokalnie na `localhost:8002/admin/`)

Typy stron w CMS portalu (`backend/mcod/cms/models/`): `KBRootPage` → `KBCategoryPage` → `KBPage` (baza wiedzy), `NewsPage` (aktualności), `LandingPage` (strona akcji z treścią w edytorze bloków), `FormPage` (ankieta/formularz z adresem e-mail odbiorcy i tekstem podziękowania), `SimplePage`.

Pomysł (S–M, ludzie + CMS, bez kodu): **cała warstwa informacyjna akcji mechanizmem portalu**, tak jak ministerstwo robi to dla starostów i deweloperów (iteracja 34):

| Element | Typ strony CMS | Treść |
|---|---|---|
| „Udostępnianie danych o defibrylatorach AED – informacje dla dostawców” | `KBPage` w kategorii materiałów dla dostawców | pakiet dostawcy: instrukcja profilu, instrukcja panelu, wzorzec XLSX/CSV, szablon XML, przewodnik |
| Strona akcji (nazwa, hasło, logo, „jak dołączyć”) | `LandingPage` | dwie ścieżki: dostawca (firma, samorząd) i obywatel (zaproponuj dane, skan QR); bez rankingu firm |
| Ogłoszenie startu akcji | `NewsPage` | jeden akapit + link do strony akcji |
| „Zgłoś chęć udziału” dla firm bez konta | `FormPage` (wysyła e-mail do ministerstwa) | nazwa firmy, liczba urządzeń, kontakt służbowy – pierwszy krok onboardingu |

- To odpowiada na „dostęp do panelu administratora” także od strony CMS: redakcja ministerstwa publikuje akcję w panelu CMS portalu (lokalnie `http://localhost:8002/admin/`, sprawdzone logowanie 21.11).
- Na zrzuty: `LandingPage` akcji z logo + `KBPage` pakietu dostawcy – pokazuje, że kampania żyje *w* portalu, a nie na osobnej stronie (spójne z „nie zaburzać stylistyki strony”).
- Ryzyko: strona akcji w CMS to treść redakcyjna portalu – decyzja i odpowiedzialność ministerstwa; w prototypie to makieta na lokalnej kopii.

## Iteracja 53. Rytm przypomnień, nadużycia sygnałów i druga interpretacja „nie premiować danych”

**Rytm przypomnień** (`aed_service/app.py:46-51`): prośba o potwierdzenie po 183 dniach, `nieaktualny` po 365, ostrzeżenie 60 dni przed końcem ważności baterii/elektrod, odstęp powtórek 30 dni, ważność linku 90 dni. Porównanie: The Circuit (UK) przypomina co 3 miesiące o kontroli gotowości (`docs/research-i-pomysly.md` 3.5). Wniosek: 6 miesięcy to rozsądny kompromis dla danych (lokalizacja i godziny zmieniają się rzadko), ale **gotowość urządzenia** (to, czy działa) ma krótszy cykl. Propozycja na slajd: dwa rytmy – „potwierdź dane” co 6 miesięcy, „potwierdź gotowość” co 3 miesiące (jedno kliknięcie „jest i działa” z linku w mailu, bez całego formularza). Koszt S (druga stała i drugi rodzaj wiadomości).

**Nadużycia sygnałów obywatelskich:** `POST /api/aed/urzadzenia/{id}/sygnal` nie ma limitu (brak limitów w ogóle, `aed_service/README.md:115`). Złośliwe masowe „brak” zasypie skrzynkę dysponenta. W prototypie akceptowalne; do ograniczeń i do wdrożenia: limit na adres IP i urządzenie (np. 3 sygnały na dobę), a statusu nie zmieniamy na podstawie sygnałów bez zarządcy (iteracja 12.2 – wersja bezpieczna).

**Druga interpretacja „nie można wybitnie premiować jakichś danych”:** może dotyczyć **priorytetu źródeł przy scalaniu** (sprzedawca/zarządca → zbiory z portalu → API Warszawy → OSM). Odpowiedź do przygotowania: priorytet wynika z **odpowiedzialności za dane** (potwierdzone przez właściciela > opublikowane przez instytucję > API miasta > społeczność), nie z tego, kto jest dostawcą; jest jawny (`sources.json`, `priority`), a żadne dane nie giną – rekord przegrany zostaje powiązany (`powiazane_zrodla`), a pola OSM nie są przepisywane (zasada 3). Na slajd standardu jedno zdanie: „pierwszeństwo ma ten, kto odpowiada za urządzenie”.

## Iteracja 54. „Metody zbierania danych” (hasło mentorów) – wszystkie kanały na jednym slajdzie

| # | Kanał | Kto | Mechanizm | Odpowiedzialność | Stan |
|---|---|---|---|---|---|
| 1 | plik CSV z konta firmy | producent, sprzedawca | rejestr ministerstwa, walidacja profilem `sprzedaz` | firma za dane urządzenia | jest |
| 2 | formularz jednego urządzenia | firma, mały sprzedawca | rejestr | firma | jest |
| 3 | skan QR z tokenem | zarządca obiektu | rejestr, potwierdzenie miejsca, godzin i stanu | zarządca za miejsce i dostęp | jest |
| 4 | skan QR bez tokenu | każdy | sygnał do dysponenta (nie edytuje danych) | – | jest (bez bloku 112 – it. 42) |
| 5 | mapper: zbiory AED z dane.gov.pl | samorządy | odczyt przez API portalu, mapowanie do standardu | instytucja publikująca | jest (lista w `sources.json`) |
| 6 | mapper: API Warszawy | miasto | API miejskie | miasto | jest |
| 7 | mapper: OpenStreetMap | społeczność | porównanie i wykrywanie luk; poza zbiorem otwartym | brak | jest |
| 8 | zasilanie XML (DATA SOURCES) | ministerstwo; docelowo duzi dysponenci | harwester portalu | dostawca zasilania | jest dla ministerstwa; szablon dla innych – it. 36 |
| 9 | CKAN miasta | miasta z portalem CKAN | harwester CKAN portalu | miasto | istnieje w portalu; rekomendacja w pakiecie – it. 36 |
| 10 | odkrywanie zbiorów po tagu akcji | ministerstwo | API portalu, zadanie cykliczne | – (człowiek zatwierdza źródło) | pomysł – it. 2, 36 |
| 11 | „Zaproponuj dane” | obywatel | propozycje nowych danych w portalu | redakcja → dostawcy | istnieje w portalu – it. 25 |
| 12 | „Zgłoś chęć udziału” | firma bez konta | formularz CMS (`FormPage`) → e-mail do ministerstwa | – | pomysł – it. 52 |

Narracja do slajdu: **dane wchodzą tylko kanałami z przypisaną odpowiedzialnością (1–3, 5, 6, 8, 9); kanały bez odpowiedzialności (4, 7, 11) dają sygnał, porównanie albo popyt – nigdy rekord w zbiorze otwartym.** To w jednym zdaniu odpowiada na diagnozę z `tips.txt` („nikt nie bierze odpowiedzialności”).

## Iteracja 55. Zakres terytorialny zasobu w portalu (`regions/terytIdent`) – „referencyjny zakres” mechanizmem portalu

- XSD 1.13 pozwala podać przy zasobie listę **identyfikatorów TERYT regionów**, których dotyczą dane („miasto, gmina, powiat lub województwo”; kod 2- albo 7-znakowy). Portal zamienia je na regiony przez usługę geokodowania Pelias (`harvester/serializers.py:511-530`, `regions/models.py`) i pokazuje zakres na mapie regionów przy zbiorze (`frontend/.../regions-map.component.ts`); zbiory można filtrować po regionie w wyszukiwarce.
- To jest **„wskazanie referencyjnego zakresu” w języku portalu** (zdanie podkreślone w treści zadania, iteracja 1): zakres terytorialny każdego zasobu jest metadaną widoczną i wyszukiwalną w portalu.
- Propozycje:
  - zbiór krajowy: 16 kodów województw (`02`, `04`, … `32`) – wyszukiwanie „AED + moje województwo” znajdzie zbiór ministerstwa;
  - zbiory gmin w modelu federacyjnym (it. 15): kod TERYT gminy (np. Legionowo) – zakres widać przy zbiorze;
  - zasób `zrodla.csv` (it. 1.1): kolumna z TERYT obszaru każdego źródła.
- **Ryzyko**: walidacja regionów woła zewnętrzną usługę Pelias. Na lokalnej kopii portalu Pelias najpewniej nie działa (nie ma go w stosie Docker), więc dodanie `regions` do zasilania może **zablokować import** (błąd walidacji zasobu). Dodawać dopiero po sprawdzeniu na portalu z działającym Pelias; w prototypie – tylko na slajd i w szablonie jako opcja.

## Iteracja 56. „Zgłoś uwagi do zbioru” przy zbiorze z harwestera – dokąd trafia

- Odbiorcy uwag do zbioru (`datasets/models.py:468-485`): zawsze kontakt portalu (`CONTACT_MAIL`) oraz – **dla zbioru z harwestera – adresy e-mail podane w źródle danych** (`self.source.emails_list`); dla zbioru dodanego ręcznie – adres do powiadomień o aktualizacji albo ostatni edytor.
- Wniosek: pole „e-mail” w źródle danych (DATA SOURCES) to **realny kanał kontaktu obywatel → ministerstwo**. W instrukcji wdrożenia: wpisać tam skrzynkę zespołu rejestru AED (nie osobę – zasada 6), bo tam trafią zgłoszenia błędów w danych z portalu.
- Domyka iterację 3.3: link „błąd w danych? zgłoś uwagę do zbioru” na stronie QR prowadzi do mechanizmu portalu, a mail ląduje u zespołu rejestru – bez naszego kodu po stronie portalu.
- Uwaga do iteracji 45: wysyłka *raportów importu* nie działa, ale wysyłka *uwag do zbioru* działa (inna ścieżka kodu) – nie mylić na slajdzie.

## Iteracja 57. Kto zakłada źródło danych (DATA SOURCES) – proces, nie przycisk

- `DataSourceAdmin` (`harvester/admin.py:133`) to zwykły panel Django bez specjalnych uprawnień dla pełnomocników; według przewodnika XML portalu (notatki, iteracja 34) dostawca **wysyła e-mail na kontakt@dane.gov.pl** z nazwą dostawcy, adresem pliku XML i częstotliwością, a źródło zakłada redakcja portalu. Pełnomocnik instytucji nie dodaje źródła sam.
- Dla ministerstwa (operatora portalu) to formalność. Dla dużego dysponenta w modelu federacyjnym (it. 15) – jeden e-mail; w pakiecie dostawcy gotowy wzór wiadomości (nazwa dostawcy, adres `zasilanie.xml`, „codziennie”).
- Konsekwencja dla hasła „dostęp do panelu administratora”: w procesie są **dwie role w panelu** – redakcja portalu (zakłada instytucję i źródło danych, publikuje propozycję w „Propozycjach nowych danych”, stronę akcji w CMS) i pełnomocnik dostawcy (zarządza zbiorami instytucji, typami kolumn, mapą, głosuje przy propozycji). Instrukcja dla jury i pakiet dostawcy powinny rozdzielić te role.
- Usunięcie aktywnego źródła jest zablokowane (`has_delete_permission`: nie dla statusu `active`, `harvester/admin.py:222`) – dodatkowe zabezpieczenie przed przypadkowym skasowaniem zbioru; na slajd „bezpieczeństwo publikacji” obok iteracji 18.

## Iteracja 58. Strona startowa modułu AED (pierwszy ekran prototypu) a nocne ustalenia

Dziś (`aed-home.component.ts`): nagłówek „Jeden rejestr defibrylatorów AED dla Polski”, trzy ścieżki (firma, dysponent z naklejki, ministerstwo), sekcja „Dane i standard” z linkami: rejestr z mapą, **„Ranking firm”**, zbiór CSV do publikacji.

Propozycje (S, tekst i linki):

1. „Ranking firm” → „Dostawcy danych” (iteracja 2/39).
2. Czwarta pozycja w „Dane i standard”: **„Publikacja w dane.gov.pl: zasilanie XML dla harwestera portalu”** z linkiem do pliku. Dziś zasilanie powstaje tylko z linii poleceń, więc w klikalnym prototypie jury go nie zobaczy. Najprościej: trasa tylko do odczytu `GET /api/aed/eksport/zasilanie.xml` (i `.md5`) zwracająca ten sam dokument co `aed_service.feed` z adresem bazowym prototypu – juror klika i widzi plik zgodny z XSD portalu. Koszt S (funkcje już są: `publication_csv`, `aed_standard.feed_files`).
3. Link do **wzorca XLSX** (`wzorzec-aed.xlsx`) z tej strony – 10% oceny, a dziś juror musi szukać go w repozytorium.
4. Przy ścieżce dysponenta: wzmianka, że strona z naklejki zaczyna się od „112” (po wdrożeniu iteracji 42).
5. Na samej górze (jeśli zespół wybierze nazwę): nazwa akcji i znak – prototyp jest też nośnikiem kampanii dla dostawców.

## Iteracja 59. Kto ma najwięcej AED – lista „dużych dysponentów” do kampanii (nasze dane z OSM)

Tag `operator` w OSM (wypełniony w 33% obiektów, 4 074 różne wartości). Najczęstsi operatorzy:

| Operator (zapis z OSM) | AED w OSM | Uwagi |
|---|---|---|
| ZUS / Zakład Ubezpieczeń Społecznych | 177 + 16 = **193** | instytucja państwowa – może być dostawcą na portalu od ręki; w OSM część oznaczona źródłem „email od ZUS” (research 3.2) |
| **InPost** | **95** | punkt odniesienia komisji (Helpbox 365); stacje są w OSM, ale nie w żadnym zbiorze z odpowiedzialnym dostawcą |
| Tauron | 69 | spółka energetyczna |
| WBiZK (Warszawa) | 40 | biuro miejskie |
| Tramwaje Warszawskie | 38 (+18 oznaczonych jako prywatne) | spółka miejska |
| Biedronka | 36 | sieć handlowa – brakujący segment „handel” (it. 37) |
| UAM Poznań, Uniwersytet Gdański, UMCS, WUM, Politechnika Częstochowska | 32, 27, 18, 16, 14 | uczelnie publiczne |
| Koszalin (biuro zarządzania kryzysowego) | 32 | miasto publikuje tylko listę na stronie (CLAUDE.md) |
| Urząd Dozoru Technicznego, NIK, Archiwum Państwowe | 30, 20, 14 | instytucje państwowe |
| Castorama, Stora Enso | 13, 13 | firmy |

Wnioski:

- **Pierwsza fala kampanii („duzi dysponenci”)**: kilkanaście podmiotów odpowiada za kilkaset urządzeń. Instytucje państwowe (ZUS, UDT, NIK, Archiwum) mogą opublikować własny zbiór w standardzie przez portal (już są lub mogą być dostawcami); firmy sieciowe (InPost, Biedronka, Castorama, Tauron) – zasilanie XML albo plik CSV do ministerstwa. Jeden partner = dziesiątki urządzeń z odpowiedzialnością.
- **InPost w danych**: 95 stacji Helpbox widocznych w OSM to dowód, że partner wskazany przez komisję ma urządzenia, ale **nie ma ich w otwartym zbiorze z odpowiedzialnym dostawcą** – gotowy przykład na slajd zachęt („InPost: 95 AED w danych społecznościowych, 0 w zbiorze z odpowiedzialnością”). Zastrzeżenie: liczba z OSM z 21.11, nie od InPostu.
- Zapis operatorów jest niespójny („ZUS” vs „Zakład Ubezpieczeń Społecznych”) – argument za polem `dysponent_regon` (identyfikator zamiast nazwy) w standardzie, które już mamy.

Aktualność danych społecznościowych (`check_date` w OSM, 5 982 obiekty z datą): 2026 – 2 981, 2025 – 1 672, 2024 – 756, 2023 – 425, 2022 – 129, starsze – 19. Społeczność weryfikuje dużo i niedawno, ale tylko jedna trzecia obiektów ma jakąkolwiek datę weryfikacji. Nasze reguły (prośba po 183 dniach, `nieaktualny` po 365) oznaczałyby dziś jako aktualne ok. 4,6 tys. z 18,3 tys. obiektów OSM, gdyby je stosować do OSM.

Urządzenia `access=private` (3 045): w 1 481 brak operatora; wśród oznaczonych – OSP, Tramwaje Warszawskie, MPK Kraków, ENEA, PSP. To głównie AED służb i zakładów pracy, nie domy prywatne – zasada „prywatne nie publikujemy” dotyczy więc w praktyce **urządzeń wewnętrznych instytucji**. Pytanie do kampanii: czy część z nich mogłaby być `ograniczony` (dostępne z pomocą personelu), jak w mapowaniu Warszawy (it. 22)?
- [x] R34 (it. 60). Reguła walidatora dla `godziny_dostepu` – szkic komunikatów i przykładów (bez kodu), zgodny z gramatyką `aed-hours.ts`.
- [x] R35 (it. 60). Słowniki `sposob_otwarcia` i `kategoria_miejsca` – wartości, opisy, mapowanie z OSM.
- [x] R36 (it. 66). Scenariusz demo 5 min – kwestie mówione słowo w słowo.
- [x] R37 (it. 67). Instrukcja dla jury – nowa tabela „wymaganie → link → oczekiwany wynik” (tekst gotowy do wklejenia).
- [x] R38 (it. 61). Pakiet dostawcy – spis treści strony bazy wiedzy (KBPage) i treść kroków.
- [x] R39 (it. 61). Wzór e-maila do kontakt@dane.gov.pl o założenie źródła danych.
- [x] R40 (it. 63). Mapa ryzyk prawnych (ODbL, RODO, licencje, odpowiedzialność za błędne dane) z rekomendacją.
- [x] R41 (it. 62). Porównanie standardu z Géo'DAE (Francja) i The Circuit (UK) – pole po polu, statusy, role.
- [x] R42 (it. 64). Hasło i nazwa akcji – test długości na naklejce 55 mm i w nagłówku panelu.
- [x] R43 (it. 63). Liczby do slajdów – finalna lista z dokładnym źródłem każdej liczby.
- [x] R44 (it. 68). Lista zrzutów do zrobienia rano – kolejność i co musi być widać.
- [x] R45 (it. 69). Plan pracy od 7:00 do oddania – kolejność zadań z oszacowaniem.


## Iteracja 60 (R34, R35). Reguła dla godzin dostępu i słowniki nowych pól – projekt do wklejenia

**R34 – reguła walidatora `godziny_dostepu`** (poziom: ostrzeżenie, nie błąd – nie blokuje zgłoszenia):

- Akceptowane: `24/7`; reguły `DNI GODZINY` rozdzielone `;`, gdzie DNI to `Mo Tu We Th Fr Sa Su PH` pojedynczo, zakresem (`Mo-Fr`) albo listą (`Sa,Su`), a GODZINY to `HH:MM-HH:MM` (kilka po przecinku) albo `off`. Dokładnie to, co czyta `aed-hours.ts` – jedna gramatyka w dwóch językach, opisana raz w `schema.json` (np. `constraints.pattern` z tym wyrażeniem albo osobny klucz `skladnia`).
- Komunikaty (po polsku, z podpowiedzią):
  - „Pole „Godziny dostępu” ma wartość „pn-pt 8-16”, której system nie odczyta. Użyj zapisu `Mo-Fr 08:00-16:00` albo przenieś opis do pola „Opis godzin dostępu”.”
  - „Wartość „Całodobowo” – użyj `24/7`.”
- Pomiar z iteracji 38: reguła przepuści 96,9% realnych wpisów OSM, więc nie będzie hałasu.

**R35 – słowniki** (w OSM nie ma praktycznie żadnych tagów szafki ani typu miejsca przy węzłach AED: `locked` 3 obiekty, `amenity`/`shop`/`office` po 1–2 – słowników nie da się wyprowadzić z OSM, trzeba je zaprojektować):

`sposob_otwarcia` (wypełnia zarządca; **nigdy kod**):

| Wartość | Znaczenie |
|---|---|
| `otwarta` | szafka bez zamka albo z plombą |
| `alarm` | szafka otwarta, otwarcie włącza alarm |
| `kod_od_112` | zamek szyfrowy; kod podaje dyspozytor 112 (kod tylko w systemie dyspozytorskim, poza danymi otwartymi) |
| `klucz_personel` | klucz u ochrony, recepcji, personelu |
| `wewnatrz_obiektu` | urządzenie w pomieszczeniu dostępnym w godzinach otwarcia |

`kategoria_miejsca` (8 wartości z iteracji 37): `oswiata`, `administracja`, `ochrona_zdrowia`, `transport`, `sport_rekreacja`, `kultura`, `handel_uslugi`, `zaklad_pracy` (+ `inne`). Mapowanie do OSM tylko w jedną stronę (z naszego standardu do tagów `amenity`/`shop` przy ewentualnym eksporcie do OSM), bo OSM tych informacji przy AED nie trzyma.

Pole `szafka_zamknieta` (tak/nie) staje się zbędne, jeśli jest `sposob_otwarcia` – jedno pole zamiast dwóch (prostsze dla zarządcy, zgodne z „najprostsze działające rozwiązanie”).

## Iteracja 61 (R38, R39). Pakiet dostawcy – strona bazy wiedzy i wzór e-maila

**Strona bazy wiedzy (KBPage w CMS portalu): „Udostępnianie danych o defibrylatorach AED – informacje dla dostawców”** – spis treści na wzór stron dla starostów i deweloperów:

1. Po co i dla kogo (2 zdania; bez obietnic zdrowotnych): jeden otwarty zbiór o AED, w którym za każdy wpis ktoś odpowiada.
2. Trzy drogi udziału:
   - mam kilka urządzeń / jestem sprzedawcą → konto w rejestrze ministerstwa, plik CSV albo formularz;
   - mam własny system / wiele urządzeń → zasilanie XML (zbiór na portalu pod moją instytucją);
   - jestem samorządem z portalem CKAN → plik CSV w standardzie z tagiem akcji, portal pobierze go automatycznie.
3. Wzorcowy zakres danych: `wzorzec-aed.xlsx` i przykładowy CSV (UTF-8, separator przecinek, daty `RRRR-MM-DD`, współrzędne WGS84 w dwóch kolumnach).
4. Jak założyć profil dostawcy na portalu (konto, login.gov.pl, wniosek o instytucję, pełnomocnik).
5. Panel administracyjny – krok po kroku ze zrzutami: zbiór → zasób → typy kolumn tekstowych (`kod_terc`, `kod_simc`, `nr_budynku`, `zrodlo_id`) → znaczniki mapy (`b`, `l`, `label`) → publikacja.
6. Zasilanie XML: szablon pliku, `.md5`, HTTPS, stałe `extIdent`, kategoria Zdrowie, flagi, licencja (warunek podania źródła), wzór e-maila (niżej).
7. Naklejka QR i potwierdzenia: co dostaje zarządca, jak często przyjdzie prośba o potwierdzenie.
8. Czego nie publikujemy: kody do szafek, dane osobowe, AED w domach prywatnych.
9. Pytania i odpowiedzi (KBQAPage): „czy muszę?”, „kto odpowiada za błędny wpis?”, „co jeśli urządzenie zdjęto?” (status `wycofany`).

**Wzór e-maila do kontakt@dane.gov.pl** (założenie źródła danych XML):

> Temat: Zasilanie XML – dane o defibrylatorach AED – [nazwa dostawcy]
>
> Dzień dobry, jako pełnomocnik [nazwa instytucji] proszę o utworzenie źródła danych typu XML dla zbioru danych o defibrylatorach AED zgodnego ze wzorcowym zakresem danych akcji [nazwa akcji].
> Adres pliku: https://[domena]/[ścieżka]/zasilanie.xml (plik .md5 pod tym samym adresem z rozszerzeniem .md5).
> Częstotliwość importu: codziennie.
> Adres e-mail do zgłoszeń dotyczących danych: [skrzynka instytucjonalna].
> Plik został sprawdzony względem schematu XSD w wersji 1.13.
> Z poważaniem, [imię i nazwisko, funkcja]

(Imię i nazwisko jest w korespondencji, nie w danych otwartych – zasada 6.)

## Iteracja 62 (R41). Nasz standard a Géo'DAE (Francja) i The Circuit (UK) – co potwierdza, czego brakuje

Źródło: `research_notes/.../europe_america_aed_systems.md` (schemat `schema-dae` v1.0.8, FAQ The Circuit, O'Sullivan i in. 2024).

| Temat | Géo'DAE (FR) | The Circuit (UK) | My | Wniosek |
|---|---|---|---|---|
| Format schematu | Frictionless Table Schema, 45 pól, 16 wymaganych | szablon Excel, 4 kolumny wymagane | Frictionless (`schema.json`), 38 pól, dwa profile | zgodny wzorzec; nasze profile `sprzedaz`/`publikacja` to coś, czego FR nie ma |
| Godziny | `dispo_horaires` w składni OSM `opening_hours`, walidowane wyrażeniem (od v1.0.8; wcześniej słowniki) | dni i godziny | `godziny_dostepu` w składni OSM, **bez walidacji** | FR przeszła z słowników na OSM i **waliduje** → R34 to krok zgodny z dojrzałym standardem |
| Stan działania | `etat_fonct`: w działaniu / niesprawny / usunięty / **chwilowo nieobecny** / nieznany (wymagane) | „Emergency Ready” vs „usunięty z użytku” z powodem; migawka gotowości codziennie | status rekordu (zgłoszony/aktywny/…); stan techniczny nie trafia do danych | potwierdza lukę z it. 5: dodać stan działania (słownik jak FR) |
| Piętro, dostępność | `acc_etg` (piętro), `acc_lib` (wolny dostęp), `acc_pcsec` (ochrona), `acc_acc` (recepcja) | dostęp publiczny/ograniczony | `dostep` (3 wartości), brak piętra | `pietro` (it. 22) i `sposob_otwarcia` (it. 60) pokrywają `acc_etg`, `acc_pcsec`, `acc_acc` |
| Elektrody dziecięce | `lc_ped`, `dtpr_lcped` | – | brak | do rozważenia: `elektrody_dzieciece` (tak/nie) – ważne dla ratownika; może to być `device_specifications` z API Warszawy (it. 22, do sprawdzenia) |
| Serwis | `dermnt` (data ostatniego przeglądu, wymagana), `mnt_rais` (serwisant), `dispsurv` (zdalny monitoring) | e-maile o elektrodach | daty ważności baterii i elektrod | `data_ostatniego_przegladu` – naturalne pole dla sprzedawcy/serwisu |
| Zdjęcie | `photo1`, `photo2` (bez praw autorskich) | – | brak | pomysł na stronę QR: zdjęcie miejsca od zarządcy (uwaga na prawa i dane osobowe na zdjęciu) |
| Pola niepubliczne | aneksy rozporządzenia określają pola publiczne; CSV otwarty pomija telefony, e-maile, producenta, model, **numer seryjny** | – | `HIDDEN_PUBLIC` w usłudze (it. 43) | FR rozstrzyga naszą otwartą decyzję: numer seryjny **niepubliczny**; i robi to w schemacie/akcie – jak proponuje it. 43 |
| Kolumny po stronie rejestru | `c_etat_valid`, `c_doublon`, `c_maj_don`, precyzja geokodowania | statusy: szkic, wymaga działania, **potencjalny duplikat**, oczekujący, zarejestrowany | `status`, `kompletnosc`, `powiazane_zrodla`, `data_aktualizacji` | podobny model; FR publikuje flagę duplikatu – my powiązanie |
| Skala | 192 453 rekordy (stan 21.11.2026) przy obowiązku prawnym | ok. 124 000 dobrowolnie | 781 w zbiorze, 18 814 w rejestrze | argument o potrzebie podstawy prawnej i kampanii |
| Rytm | – | e-mail co 3 miesiące, eskalacja do organizacji | 183/365 dni | it. 53: dwa rytmy (dane 6 mies., gotowość 3 mies.) |
| Po użyciu | – | po użyciu przez pogotowie: e-mail „sprawdź i przywróć gotowość” | brak | pomysł na „co dalej”: sygnał „użyto AED” z QR → prośba do zarządcy o kontrolę elektrod |

Wniosek do slajdu standardu: „Nasz wzorzec jest zgodny z kierunkiem Francji (Frictionless + `opening_hours` OSM) i modelem odpowiedzialności z Wielkiej Brytanii (opiekun urządzenia, cykliczne potwierdzenia), a dodaje profil zgłoszenia przy sprzedaży, którego nie ma żaden z nich.”

## Iteracja 63 (R40, R43). Ryzyka prawne w jednej tabeli i liczby do slajdów ze źródłami

**R40 – ryzyka prawne** (wszystkie do opinii prawnika; tu tylko to, co wynika z naszych ustaleń):

| Ryzyko | Co wiemy | Rekomendacja w prototypie |
|---|---|---|
| ODbL (OSM) w zbiorze ministerstwa | rekordy tylko z OSM poza eksportem; pól OSM nie przepisujemy (zasada 3) | bez zmian; slajd ograniczeń |
| Licencja zbioru krajowego | 715/781 rekordów CC BY 4.0; zasilanie daje dziś CC0 (it. 21) | warunek „podaj źródło” → CC BY 4.0 |
| Dane osobowe w danych otwartych | kontakty ukryte; `dysponent_nazwa` może być nazwą jednoosobowej działalności (it. 32) | warunek `personalData` w zasilaniu albo publikacja nazwy tylko z REGON osoby prawnej |
| Dane osobowe w rejestrze | położenie osoby zgłaszającej sygnał, pliki zgłoszeń z kontaktami (it. 32) | okresy retencji (90 dni / 30 dni / 12 mies.) |
| Odpowiedzialność za błędny wpis | dane „na dzień weryfikacji”, z datą i źródłem w każdym wierszu | opis zbioru: „stan na dzień weryfikacji, nie gwarancja działania”; pakiet dostawcy: FAQ „kto odpowiada” |
| Kody do szafek | nie publikujemy; `sposob_otwarcia` bez kodu (it. 60) | bez zmian |
| Brak obowiązku raportowania | dobrowolność; precedens: rozporządzenie o strukturze danych deweloperów (Dz.U. 2026 poz. 1489) | slajd „co dalej” |
| Promowanie firm przez państwo | publiczny ranking z linkami do ofert (it. 39) | neutralna lista dostawców |
| Prawa do znaku | logo rysuje człowiek; nie przerabiać znaku ISO 7010 E010 (brief) | bez zmian |

**R43 – liczby do slajdów z dokładnym źródłem** (zasada 10):

| Liczba | Źródło |
|---|---|
| 18 814 rekordów w rejestrze, 266 połączeń, 214 par do przeglądu, 781 w eksporcie | `datasets/out/raport.json` (budowa 21.11) |
| 708 z 781 rekordów eksportu z API Warszawy (91%) | `datasets/out/aed_dane_gov_pl.csv`, kolumna `zrodlo` |
| 715 z 781 rekordów na CC BY 4.0 | to samo, kolumna `licencja` |
| kompletność: najlepszy rekord otwarty 62, mediana 51; rekord po ścieżce QR 97 | to samo, kolumna `kompletnosc`; `wzorzec/przyklad-publikacja.csv` + `aed_standard.validate.completeness` |
| handel i usługi 0,3% rekordów (przybliżenie metodą słów kluczowych) | iteracja 37 – podać jako szacunek |
| OSM: 18 298 obiektów; godziny 37,1%; piętro 20,2%; `locked` 3 obiekty | `datasets/raw/openaedmap/PL.geojson` (pobranie 21.11) |
| InPost 95, ZUS 193 urządzeń w OSM | to samo, tag `operator` (zapis z OSM, nie dane firm) |
| Warszawa: 612 z 708 urządzeń z opisem godzin, 100 z „24/7” | `datasets/raw/warszawa_api/defibrylatory.json` |
| Géo'DAE 192 453 rekordy; The Circuit ok. 124 000 | `research_notes/.../europe_america_aed_systems.md` (źródła pierwotne podlinkowane tam) |
| interpelacja 20440 z 15.10.2026 do Ministra Cyfryzacji | `research_notes/.../poland_data_and_dane_gov_pl.md` → api.sejm.gov.pl |

Liczby, których **nie** używać bez źródła pierwotnego: przeżywalność, liczba zatrzymań krążenia, „do 70%” z komunikatu InPostu (`zachety.md` zaznacza to samo).

## Iteracja 64 (R42). Nazwa i hasło na naklejce – test długości według reguły z testów

Reguła z `tests/test_aed_service.py:153` (szerokość linii ≤ 320 jednostek przy naklejce 360; znaki × rozmiar × 0,75), czcionka minimum 15:

- Wszystkie nazwy-kandydaci (9–14 znaków: „Opiekun AED”, „AED na widoku”, „Pokaż AED”, „Minuta dla AED”…) mieszczą się w jednej linii nawet czcionką 22.
- Hasła: „AED widoczny w danych.” (22 znaki) – jedna linia czcionką 18; „Dbasz o AED? Pokaż to w danych.” (31) i „Twój AED musi być widoczny także w danych.” (42) – **tylko w dwóch liniach**. Na naklejce zmieści się nazwa, nie pełne hasło; hasło zostaje na stronie akcji, w panelu i materiałach.
- Napis bezpieczeństwa „W nagłym wypadku: 112” (21 znaków) mieści się czcionką 18; „Zadzwoń 112” (11) – czcionką 22. Na naklejce obecny podpis ma już dwie linie („Zeskanuj kod QR” / „i sprawdź lub zgłoś stan AED” – ta druga na granicy reguły przy czcionce 15). Dodanie „112” wymaga skrócenia podpisu, np. „Zeskanuj: sprawdź stan AED” albo przeniesienia „112” do nagłówka zamiast nazwy akcji.
- **Miejsce na logo** na naklejce: wysokość 50 z 360 jednostek (`STICKER_LOGO_H`) → przy naklejce ok. 57 mm szerokości ≈ **8 mm wysokości**. To konkretna minimalna wielkość do księgi znaku (strona 6) i potwierdzenie szacunku z briefu („do ok. 8 mm”).
- [x] R46 (it. 65). `docs/integracja-portal-backend.md` – sprawdzić zdania wobec nocnych ustaleń (licencja, e-mail raportów, typy kolumn, kto zakłada źródło).
- [x] R47 (it. 65). API Warszawy: znaczenie `device_specifications` (Tak/Nie/Brak informacji) – szukać w `api_przyklady.json` i opisach.
- [x] R48 (it. 65). `aed_service/README.md` – zdania nieaktualne po 21.11 (zasilanie, zmienne `AED_FEED_*`).
- [x] R49 (it. 65). Wszystkie miejsca w interfejsie i dokumentach ze słowem „ranking” – lista do zmiany (it. 2, 39).
- [x] R50 (podsumowanie końcowe). Odświeżenie podsumowania na górze pliku – ostatni przebieg przed 7:00.


## Iteracja 65 (R46–R49). Dokumenty i interfejs do poprawy po nocy – lista zmian

**R46 – `docs/integracja-portal-backend.md`:**
- rozdział o zasilaniu (dopisany 21.11) nie mówi o licencji – po poprawce z it. 21 dopisać „warunek podania źródła → CC BY 4.0”;
- dopisać: źródło danych zakłada redakcja portalu na prośbę dostawcy (it. 57); pole e-mail źródła to adres dla uwag do zbioru (it. 56); raporty importu e-mailem nie działają w 2.63.0 (it. 45);
- linia 69 („wymaga adresu HTTPS kończącego się na `.xml`”) – kod sprawdza tylko brak spacji w nazwie, *jeśli* adres kończy się na `.xml` (`harvester/utils.py:200`); wymóg HTTPS dotyczy adresów zasobów i dokumentów (`serializers.py:136`, `:177`). Doprecyzować.

**R47 – `device_specifications` w API Warszawy:** brak opisu w `api_parametry.json` i brak w `api_przyklady.json`. Znaczenie nieustalone (Tak 400 / Nie 179 / Brak informacji 129). Hipoteza: elektrody/tryb pediatryczny albo „specyfikacja dostępna” – **do zapytania miasta**; nie mapować, dopóki znaczenie nie jest znane (zgodnie z regułą „nie zgadujemy” z `aed-hours.ts`).

**R48 – `aed_service/README.md`:** nie opisuje zasilania XML ani zmiennych `AED_FEED_DIR`/`AED_FEED_URL` (są tylko w docstringu `__main__.py`). Dopisać krótki akapit i ostrzeżenie z it. 45 (publiczny prototyp nie może zasilać prawdziwego portalu).

**R49 – słowo „ranking” w interfejsie i dokumentach** (do zmiany, jeśli zespół przyjmie neutralną listę):
- interfejs: `aed.component.html:59` (zakładka „Ranking firm”), `aed-home.component.ts:65` („Ranking firm”), `aed-company.component.html:66` („Zobacz ranking firm”), `aed-sellers.component.html:19-22, 70` (podpis tabeli i komunikat pustej listy); komentarze w `aed-sellers.component.ts`, `aed-company.component.ts`, `aed-api.service.ts`;
- dokumenty: `docs/instrukcja-dla-jury.md:135`, `docs/prezentacja-konspekt.md:93, 126`, `kampania/zachety.md:36, 77`, `CLAUDE.md:170, 180, 192` (podział zadań i kolejność cięcia – tam „ranking” jest pierwszy do cięcia, co ułatwia decyzję);
- `kampania/nazwa-i-haslo.md:83` („Ranking top 3” nazw) – inny sens, bez zmian.

## Iteracja 66 (R36). Scenariusz demo – 5 minut, kwestie mówione

Zasady: zdania krótkie, bez obietnic zdrowotnych (zasada 9), liczby tylko z naszych danych (zasada 10). Osoba A mówi, osoba B klika. W nawiasach – ekran.

**0:00–0:40 (rejestr, mapa z filtrem „dostępne teraz”)**
A: „3 marca w centrum Warszawy świadkowie szukali defibrylatora i trafiali na zamknięte szafki. Dziś żaden otwarty zbiór nie powie, który AED jest dostępny o tej godzinie. Zebraliśmy wszystkie otwarte źródła: 18 814 urządzeń. Żadne nie jest potwierdzone przez kogoś, kto za nie odpowiada. Zbiór, który można opublikować, to w 91% Warszawa.”

**0:40–1:30 (panel firmy, wgranie `przyklad-sprzedawca-bledy.csv`)**
A: „Zaczynamy od tego, kto zna urządzenie najlepiej – od sprzedawcy. Wgrywa plik z dnia sprzedaży. Walidator mówi po polsku, w którym wierszu i polu jest błąd: data w złym formacie, zamienione współrzędne. Poprawne wiersze dostają identyfikator i naklejkę z kodem QR.”

**1:30–2:30 (naklejka → telefon: strona potwierdzenia)**
A: „Naklejka jedzie z urządzeniem do zarządcy. Zarządca skanuje kod: miejsce z lokalizacji telefonu, godziny bez znajomości żadnej składni, stan urządzenia. Trzy kroki. Rekord dostaje status «aktywny» i kompletność 97 na 100. Najlepszy otwarty rekord w Polsce ma dziś 62.”
(Jeśli wdrożono blok 112: „Ktoś, kto zeskanuje kod w nagłym wypadku, najpierw widzi «Zadzwoń 112».”)

**2:30–3:30 (panel ministerstwa)**
A: „Ministerstwo prowadzi rejestr. Mapper codziennie dokłada dane z otwartych źródeł i scala powtórzenia; człowiek decyduje tylko tam, gdzie zmienia to publikowany zbiór. System sam prosi zarządców o potwierdzenie i przypomina o bateriach i elektrodach.”

**3:30–4:30 (lokalny portal: DATA SOURCES → raport importu → zbiór z tabelą i mapą)**
A: „Publikacja nie wymaga zmian w portalu. Rejestr wystawia plik zasilania w schemacie portalu, a portal pobiera go codziennie tym samym mechanizmem, którego używają deweloperzy. Zbiór ma stały identyfikator, licencję, kategorię Zdrowie i mapę.”

**4:30–5:00 (propozycja nowych danych z głosami / strona akcji)**
A: „Na koniec akcja dla dostawców: [nazwa akcji]. Dostawcy deklarują udział tam, gdzie już pracują – w panelu portalu. W zamian dostają przypomnienia serwisowe i widoczność swoich urządzeń na równych zasadach. Dziękujemy.”

Rezerwa na pytania: tabela z iteracji 18.

## Iteracja 67 (R37). Instrukcja dla jury – tabela na jeden ekran (gotowa do wklejenia na górę `docs/instrukcja-dla-jury.md`)

Cel z `tips.txt`: „gdzie sprawdzić realizację każdego wymagania” – jedno wymaganie, jedno miejsce, jeden oczekiwany wynik. Szczegóły zostają niżej w obecnej instrukcji.

| # | Wymaganie (treść zadania) | Gdzie sprawdzić | Co powinno być widać |
|---|---|---|---|
| 1 | Prototyp | [adres publiczny] albo `docker compose up --build` → `/pl/aed` | strona „Jeden rejestr defibrylatorów AED dla Polski” |
| 2 | Wzorcowy zakres danych (XLSX) | `wzorzec/wzorzec-aed.xlsx` | arkusze: Dane (38 kolumn), Słownik pól, Słowniki, Mapowanie źródeł, Instrukcja |
| 3 | Dane z wielu źródeł ze wskazaniem zakresu | `datasets/raw/manifest.json`, `datasets/out/raport.json` → `rekordy_na_zrodlo`, `pokrycie_pol` | 6 źródeł, liczba rekordów przed/po, pokrycie pól na źródło |
| 4 | Integracja w jednym zbiorze (deduplikacja) | `raport.json` → `polaczenia`; panel ministerstwa → „Możliwe duplikaty” | 266 połączeń, 214 par do przeglądu |
| 5 | Format maszynowy | `datasets/out/aed_dane_gov_pl.csv` | UTF-8, przecinek, daty `RRRR-MM-DD`, dwie kolumny współrzędnych |
| 6 | Zgodność z zasadami dane.gov.pl | `docs/integracja-portal-backend.md`, rozdz. „Zasilanie XML przez harwester” + zrzuty portalu | zbiór ministerstwa zaimportowany przez źródło danych XML, raport importu OK, tabela i mapa |
| 7 | Proces od sprzedawcy do zbioru | prototyp: Panel firmy → naklejka → strona potwierdzenia → Rejestr | rekord ze statusem „aktywny”, kompletność 97 |
| 8 | Okresowe potwierdzenia i przypomnienia | Panel ministerstwa → „Zadania cykliczne” → „Uruchom przypomnienia” | wiadomości w skrzynce (dane demo: bateria ważna 30 dni, weryfikacja sprzed 200 dni) |
| 9 | WCAG i responsywność | [raport `docs/dostepnosc.md`] + strona potwierdzenia przy 320 px, samą klawiaturą | przejście bez myszy, stan tekstem i ikoną |
| 10 | Nazwa, hasło, logo, księga znaku | `kampania/logo/`, `kampania/ksiega-znaku.pdf` | pięć formatów logo; księga: koncepcja, kolory, pole ochronne, minimalna wielkość, niedozwolone użycia |
| 11 | Prezentacja | [plik prezentacji] | min. 5 slajdów ze zrzutami, kroki użytkownika, ograniczenia |
| 12 | Kod źródłowy i testy | repozytorium; `uv run … --with xmlschema python -m unittest` | wszystkie testy przechodzą (po poprawce `.gitattributes`, it. 31) |
| 13 | Użycie AI | `docs/uzycie-ai.md` | co zrobiło AI, co zweryfikował człowiek |

Pola w nawiasach kwadratowych – do uzupełnienia przed oddaniem (decyzje i pliki ludzi).

## Iteracja 68 (R44). Zrzuty: co już jest (więcej, niż zakładały dokumenty) i czego brakuje

**Sprostowanie do iteracji 6, 16, 28, 41 i podsumowania:** dowody dostępności **już istnieją** – `frontend/aed-zrzuty/DOSTEPNOSC.md` (commit `ed40736`, 21.11 19:13): axe-core 4.10.2 (WCAG 2.0/2.1 A/AA i 2.2 AA) na 9 widokach obszaru AED – po poprawkach **0 naruszeń** (przed: 1, `target-size`); przejście samą klawiaturą (Playwright); układ 320 px i 640 px; trzy tryby wysokiego kontrastu portalu. Pozostałe naruszenia są w nagłówku i stopce portalu (fork, CMS). Raport sam wymienia luki: brak czytnika ekranu i prawdziwego telefonu, filtr „dostępny teraz” tylko na mapie, teksty tylko po polsku.

Mój wniosek o kontraście `#c25400` (it. 28) zostaje jako uwaga: axe zgłaszał kontrast tylko „do ręcznej oceny” na tekstach błędów i podpowiedzi; status `nieaktualny` najpewniej nie występował w danych demo podczas testu – do sprawdzenia jednym zrzutem z rekordem `nieaktualny`.

**Dokumenty nie znają tych plików:** `docs/instrukcja-dla-jury.md:191` nadal wpisuje raport dostępności do „Do uzupełnienia”, a konspekt prezentacji wymienia tylko zrzuty 01–05. Poprawka (S): podlinkować `frontend/aed-zrzuty/DOSTEPNOSC.md` w sekcji 4B instrukcji i w slajdzie 9.

Inwentarz zrzutów (stan 22.11, 00:56) i przypisanie do slajdów:

| Slajd | Jest | Brakuje |
|---|---|---|
| 1 teza | `15-start-sciezki-dla-jury.jpg`, `01-rejestr-lista.jpg` | logo i nazwa akcji |
| 2–3 problem i pomiar | `04-panel-ministerstwa.jpg` | wykres pokrycia pól / „91% Warszawa” (z `raport.json`) |
| 4 proces | `09-raport-walidacji-bledy.jpg`, `10-wynik-zgloszenia-naklejki-linki.jpg`, `11-naklejka.jpg`, `07-naklejki-wydruk-a4.jpg`, `08-…godziny…`, `18-…bateria…`, `14-qr-potwierdzone-telefon.jpg`, `17-…problem…`, `16-…osoba postronna…`, `12-…wiadomości…`, `13-…historia zadań…` | – (komplet) |
| 5 standard | – | arkusz `wzorzec-aed.xlsx` („Słownik pól”), walidator w terminalu |
| 6 zgodność z portalem | – | **lokalny portal**: źródło danych + raport importu, zbiór z tabelą, mapa zasobu, „Umieść na swojej stronie”, propozycja nowych danych, `zasilanie.xml` w przeglądarce |
| 7 kampania | `06-ranking-firm.jpg` | logo na naklejce; strona akcji; (po decyzji: „Dostawcy danych” zamiast rankingu) |
| 9 ograniczenia i dostępność | `320px-*.jpg` (9), `kontrast-*.jpg` (9), `klawiatura-mapa-opis-urzadzenia.jpg`, `DOSTEPNOSC.md` | – |

Kolejność robienia zrzutów rano (największy brak – 30% oceny): (1) portal: źródło danych i raport importu; (2) zbiór z mapą; (3) „Umieść na swojej stronie”; (4) propozycja nowych danych; (5) `zasilanie.xml`; (6) arkusz XLSX; (7) logo/naklejka po decyzji ludzi.

## Iteracja 69 (R45). Plan od 7:00 do oddania (godzina oddania nieustalona – `CLAUDE.md`, otwarte decyzje)

Założenie: 3–4 godziny pracy zespołu. Kolejność według wpływu na ocenę i ryzyka; w nawiasie koszt i kto.

**7:00–7:30 – decyzje (ludzie, wszyscy razem)**
1. Nazwa i hasło akcji (`kampania/nazwa-i-haslo.md`), status logo.
2. Publiczny adres prototypu: tak/nie, gdzie (it. 10).
3. Ranking firm → lista dostawców: tak/nie (it. 2, 39, 65).
4. Godzina oddania – potwierdzić u organizatora.

**7:30–9:00 – poprawki „bezpieczeństwa oceny” (kod, małe, każda z testem)**
5. Licencja w zasilaniu: `<conditions><source>true</source></conditions>` + test „licencja zbioru ≥ licencje rekordów” (S, it. 21).
6. Blok „Zadzwoń 112” na stronie QR i napis na naklejce (S, it. 42, 64).
7. `.gitattributes` z regułami `eol=lf`, renormalizacja, test na świeżym klonie (S, it. 31).
8. `wprowadzajacy_nazwa` dla importów z `sources.json` (S, it. 46) – po nim przebudowa `datasets/out/`.
9. Pola niepublikowane w `schema.json` zamiast `HIDDEN_PUBLIC` – jeden eksport publikacyjny (S, it. 43).
10. Wycofane rekordy w eksporcie ze statusem (S, it. 23) – **tylko jeśli** zespół się zgodzi (zmienia liczbę 781).

**8:00–9:30 – dowody do 30% (równolegle, osoba z portalem)**
11. Uruchomić lokalny portal (`docker-compose.aed-ports.yml`), wygenerować zasilanie, zrobić zrzuty z it. 68 (źródło danych, raport importu, zbiór z mapą, osadzanie, propozycja nowych danych, XML).
12. Arkusz XLSX i walidator w terminalu – dwa zrzuty.

**9:00–10:00 – dokumenty**
13. Instrukcja dla jury: tabela z it. 67 na górę; sprostowania z it. 29 i 68; link do `DOSTEPNOSC.md`.
14. Konspekt: zmiany z it. 8, liczby z it. 63, ograniczenia z it. 41, zrzuty z it. 68.
15. README – pierwszy ekran wg it. 40.
16. `docs/uzycie-ai.md` – wpis o nocnym researchu (co zrobiło AI, co zweryfikował człowiek).

**Ostatnie 30 min – kontrola**
17. Świeży klon → testy → `docker compose up` → ścieżka A–C z instrukcji przez osobę, która jej nie pisała (it. 29).
18. Lista „Co oddajemy” w `CLAUDE.md` – odhaczyć.

Tnij w tej kolejności, gdy brakuje czasu: 10 → 9 → 12 → 15. Nie tnij: 1, 5, 6, 11, 13.

Świadomie poza planem (slajd „co dalej”): nowe pola standardu (`sposob_otwarcia`, `kategoria_miejsca`, stan działania, piętro – it. 5, 60, 62), konwersja godzin Warszawy (it. 22), pakiet dostawcy w CMS (it. 34, 52, 61), monitor publikacji (it. 45), regiony TERYT (it. 55).
- [x] R51 (it. 70). Raport luk dla gminy – na przykładzie czterech gmin: które pola standardu każda mogłaby uzupełnić (z `pokrycie_pol`).
- [x] R52 (it. 71). Reguły w `schema.json` (`reguly`) a reguły zaimplementowane w walidatorze – spójność (jedno źródło prawdy).
- [x] R53 (it. 72). `wzorzec-aed.xlsx` – odczyt i porównanie ze schematem (kolumny, słowniki, metadane zbioru).
- [x] R54 (it. 73). Liczby i nazwy w interfejsie modułu AED (np. „sześć źródeł”) a `raport.json`.
- [x] R55 (it. 74). Bezpieczeństwo linków zarządcy (token w adresie, ważność, przechowywanie skrótu) – przegląd kodu.
- [x] R56 (it. 75). Konspekt prezentacji – slajdy 5, 8, 10 wobec nocnych ustaleń.
- [x] R57 (it. 76). „Otwarte decyzje” z `CLAUDE.md` – rekomendacje z dowodami z nocy.


## Iteracja 70 (R51). Raport luk dla gminy – co każdy dostawca mógłby uzupełnić

Pokrycie pól (≥ 50% rekordów, `raport.json` → `pokrycie_pol`, bez pól technicznych):

| Dostawca | Pola wypełnione | Czego nie ma w ogóle (najważniejsze dla ratownika) |
|---|---|---|
| Krosno (21) | 8: nazwa, współrzędne, adres | dostęp, godziny, opis miejsca, wewnątrz/na zewnątrz, data weryfikacji |
| Legionowo (24) | 10: jak wyżej + `kod_terc`, `kod_simc` | jak wyżej |
| Przemyśl (21) | 7: nazwa, współrzędne, adres (bez cechy ulicy) | jak wyżej |
| Marki (8) | 8: jak Krosno | jak wyżej |
| Warszawa (708) | 12: + opis miejsca, wewnątrz/na zewnątrz, dostęp, opis godzin, producent | godziny w składni maszynowej, data weryfikacji, terminy baterii/elektrod |

Wnioski:

- **Wszystkie cztery gminy publikują wyłącznie „gdzie” – żadna nie publikuje „kiedy dostępne” ani „czy sprawdzone”.** Dokładnie te pola, których brak opisuje historia z 3 marca.
- Pomysł (S–M, automatyzacja + kampania): **raport luk jako wiadomość do dostawcy**, generowany przez mapper dla każdego źródła z portalu: „Twój zbiór [tytuł] ma N urządzeń; brakuje godzin dostępu we wszystkich; plik ma przecinek dziesiętny / zamienione współrzędne w K wierszach (naprawy z `naprawy_danych`); oto wzorzec i trzy kroki uzupełnienia”. Kanał: „Zgłoś uwagi do zbioru” na portalu (iteracja 56 – trafia do dostawcy) albo pismo ministerstwa. Wysyłka za zgodą człowieka.
- To konkretna, mierzalna forma pomysłu C5 z researchu („gap report”) i odpowiedź na „dostawcy mają zgłaszać się sami” – dostają gotową listę, co poprawić.
- Na slajd 3: zamiast tabeli procentów – ta tabela „co jest / czego brak” jest czytelniejsza dla jury.

## Iteracja 71 (R52). Reguły w `schema.json` a walidator – spójne; trzy brakujące reguły

Każda z 5 reguł opisanych w `schema.json` → `reguly` ma implementację w `aed_standard/validate.py`:

| Reguła w schemacie | Kod problemu w walidatorze |
|---|---|
| status `aktywny` wymaga `dostep`, `godziny_dostepu`, `data_weryfikacji` | `wymagane_dla_statusu` (z klucza `wymagane_dla_statusu`, więc lista pól nie jest zdublowana) |
| współrzędne w granicach Polski, zamiana z podpowiedzią | `poza_polska`, `wspolrzedne_zamienione` (`validate.py:171-175`) |
| daty nie z przyszłości (oprócz terminów ważności) | `data_z_przyszlosci` (`:189`) |
| minięty termin elektrod/baterii = ostrzeżenie | `termin_minal` (`:185`) |
| para producent + numer seryjny unikalna | `duplikat_numeru_seryjnego` (`:204`) |

Pozostałe kody wynikają z `type` i `constraints` pól (format daty, liczby, e-maila, słownik, zakres, długość) – też ze schematu. Zasada 1 jest zachowana: reguły są opisane słowami w schemacie, a parametry (pola, słowniki, zakresy) czytane z niego.

Brakujące reguły, które wyszły w nocy (każda – ostrzeżenie, nie błąd):

1. składnia `godziny_dostepu` (it. 34, 60) – 96,9% realnych wpisów OSM przejdzie;
2. koniec żywotności urządzenia: `data_produkcji` starsza niż N lat (pkt „10/14 lat” z rozmowy z komisją, it. 5) – N do potwierdzenia;
3. termin ważności baterii lub elektrod w ciągu 60 dni – ostrzeżenie już przy zgłoszeniu (ten sam próg co przypomnienia usługi, `EXPIRY_WARNING_DAYS`), żeby sprzedawca od razu widział urządzenia z kończącymi się materiałami.

Każdą nową regułę dopisać zdaniem do `reguly` w schemacie – wtedy trafi też do arkusza „Instrukcja” w XLSX (jeśli generator czyta `reguly` – do sprawdzenia w R53).

## Iteracja 72 (R53). `wzorzec-aed.xlsx` a schemat – kolumny zgodne, reguły i metadane poza arkuszem

Odczyt pliku (`openpyxl`, bez zmian):

- 5 arkuszy (Dane, Słownik pól, Słowniki, Mapowanie źródeł, Instrukcja); **nagłówek „Dane” = 38 kolumn w tej samej kolejności co `schema.json`** – zgodne; 6 walidacji danych (listy rozwijane słowników); 1 wiersz przykładowy.
- **Reguły ze schematu nie trafiają do arkusza**: „Instrukcja” to 15 linii zapisanych na sztywno w `scripts/build_template.py:105-123` (`INSTRUCTIONS`), żadna z 5 reguł `schema.json` → `reguly` nie występuje w arkuszu. Dwie informacje są powielone w kodzie generatora zamiast czytane ze schematu (opis profili, zasady formatu). Wbrew zasadzie 1, choć skala mała.
- **Metadane zbioru (`zbior_dane_gov_pl`) nie są w XLSX** – plik wygenerowano przed ich dodaniem; generator ich nie czyta.

Propozycje (S, w ramach `build_template.py`):

1. Arkusz „Instrukcja”: po stałych krokach dopisać sekcję „Reguły sprawdzane przez walidator” generowaną z `reguly` (5 zdań, a z it. 71 – 8).
2. Nowy arkusz „Metadane zbioru” z `zbior_dane_gov_pl` (it. 14.1): tytuł, opis, kategoria, tagi, częstotliwość, flagi z wartościami, licencja.
3. Linia o publikacji w portalu: typy kolumn tekstowych i znaczniki mapy (it. 14.2) – jedno zdanie z odsyłaczem do pakietu dostawcy.
4. Zdanie w instrukcji „po wysłaniu… rekord trafia do zbioru na dane.gov.pl” jest prawdziwe dla kanału ministerstwa; dla samorządu publikującego samodzielnie (model federacyjny) dopisać drugą ścieżkę – „opublikuj plik jako zasób swojego zbioru z tagiem akcji”.

Wpływ: kryterium „Wzorcowy zakres danych” (10%) ocenia właśnie ten plik – arkusz metadanych i reguł to tani sposób, by był kompletnym wzorcem udostępniania, a nie tylko listą kolumn.

## Iteracja 73 (R54). Liczby zapisane na sztywno w interfejsie modułu AED

Interfejs bierze statystyki z API (panel ministerstwa: `stats.*`), więc liczby rejestru same się aktualizują. Na sztywno w tekstach są:

| Miejsce | Tekst | Źródło prawdy | Ryzyko |
|---|---|---|---|
| `aed-home.component.ts:61` | „dane z **sześciu** otwartych źródeł” | `sources.json` (dziś 6 wpisów) | po dodaniu źródła tekst się zestarzeje; po wdrożeniu odkrywania zbiorów po tagu (it. 2, 36) – na pewno |
| `aed-ministry.component.html:155` | „uruchamiają się same, **co 24 godziny**” | `AED_CYCLE_HOURS` (domyślnie 24) | rozjazd przy innej konfiguracji (np. `0` w prototypie publicznym) |
| `aed-ministry.component.html:162-163` | „po **6 miesiącach**… od **12 miesięcy**” | `REQUEST_AFTER_DAYS = 183`, `STALE_AFTER_DAYS = 365` (`aed_service/app.py`) | zgodne dziś; przy dwóch rytmach z it. 53 – do zmiany |
| `aed-qr.component.html:74` | „mija w ciągu **60 dni**” | `EXPIRY_WARNING_DAYS = 60` | zgodne |

Wnioski:

- Dziś wszystkie teksty są **zgodne** z konfiguracją – nic do poprawy przed oddaniem.
- Dobra praktyka (po hackathonie): progi i liczba źródeł w odpowiedzi `GET /api/aed/statystyki` (usługa już zwraca statystyki), a interfejs wstawia je do zdań – jedno źródło prawdy, jak dla schematu.
- Jedyne, co warto zmienić od razu przy publicznym prototypie: jeśli harmonogram zostanie wyłączony (`AED_CYCLE_HOURS=0`), zdanie „co 24 godziny” wprowadzi jury w błąd – w instrukcji wdrożenia zostawić 24.

## Iteracja 74 (R55). Linki zarządcy – bezpieczeństwo w kodzie i **niezgodność z dokumentami („jednorazowy”)**

Kod (`aed_service/app.py`):

- token zarządcy: `secrets.token_urlsafe(24)` (192 bity losowości), w bazie tylko skrót (`sha`), przypisany do jednego `id_aed`, ważny 90 dni (`TOKEN_DAYS`); przeterminowane są usuwane (`:788`); sprawdzenie w jednym zapytaniu (`manager_ok`, `:207`) – solidnie;
- hasła kont: sól + skrót, porównanie `hmac.compare_digest` także dla nieistniejącego konta (`:485-486`) – nie zdradza, czy konto istnieje; sesje też jako skróty tokenów;
- **token nie jest jednorazowy**: zostaje ważny po potwierdzeniu, a urządzenie może mieć kilka ważnych linków naraz (komentarz przy `TOKEN_DAYS` i `new_token`). To świadoma decyzja (zarządca może wrócić i poprawić dane z tego samego maila).

Niezgodność z dokumentami – w trzech miejscach link jest nazwany jednorazowym:

- `docs/instrukcja-dla-jury.md:53` („token jest jednorazowym uprawnieniem zarządcy”),
- `docs/prezentacja-konspekt.md:57` („link z jednorazowym tokenem”),
- `kampania/zachety.md:63` (obsługa tokenów jednorazowych w kolumnie kosztów).

Poprawka (S, tylko tekst): „link osobisty, ważny 90 dni, przypisany do jednego urządzenia”. Juror, który kliknie link drugi raz i zobaczy, że działa, uzna to za błąd, jeśli dokument mówi „jednorazowy”.

Uwagi do wdrożenia (na slajd „bezpieczeństwo”, nie do zmiany teraz):

- token jest w adresie (`?t=`) – trafi do historii przeglądarki i ewentualnie do logów serwera; nginx prototypu nie ma własnego `log_format` ani nagłówków (`docker/nginx.conf.template`), więc logi dostępu mają pełne adresy. Na produkcji: `Referrer-Policy: no-referrer` na stronie QR i maskowanie parametru `t` w logach;
- przeglądarki domyślnie wysyłają do innych domen tylko pochodzenie (`strict-origin-when-cross-origin`), a strona QR nie ładuje kafelków mapy – wyciek tokenu przez nagłówek Referer jest mało prawdopodobny;
- brak limitu prób logowania i limitu sygnałów – już na liście ograniczeń (it. 41, 53).

## Iteracja 75 (R56). Konspekt – slajdy 5, 8, 9, 10 wobec nocnych ustaleń

**Slajd 5 (standard):**
- „pola z rozmowy z komisją … kto wprowadził” – pole jest w schemacie, ale w zbiorze z importu `wprowadzajacy_nazwa` jest puste we wszystkich 781 rekordach (it. 46). Albo poprawić mapper (plan, pkt 8), albo nie pokazywać tego pola na zrzucie zbioru.
- Dodać jedno zdanie porównania (it. 62): „zgodny z kierunkiem Francji (Frictionless, godziny w składni OSM) i modelem opiekuna z Wielkiej Brytanii; profil zgłoszenia przy sprzedaży to nasz dodatek”.
- Dodać: „wzorzec obejmuje też metadane zbioru (tytuł, kategoria, tagi, flagi) – jeden plik `schema.json`” (it. 14, 72) – po dodaniu arkusza metadanych do XLSX.

**Slajd 8 (wynik):** liczby zgodne z `raport.json` (it. 30). Dopisać dwa fakty: „zbiór do publikacji to w 91% Warszawa” i „najlepszy otwarty rekord: kompletność 62/100; po ścieżce sprzedawca → zarządca: 97/100” (it. 47). Brakujący wykres „ile odpadło z eksportu i dlaczego” można zastąpić tabelą „co jest / czego brak” z it. 70.

**Slajd 9 (ograniczenia) – dwa punkty są nieaktualne:**
- „w interfejsie nie znaleziono osobnego widoku mapy sprzedawców `[do sprawdzenia]`” – widok jest (`!sellers`, zrzut `06-ranking-firm.jpg`);
- „formalny audyt … `[do sprawdzenia: raportu nie ma w repozytorium]`” i `[BRAK: raport audytu dostępności]` – raport jest: `frontend/aed-zrzuty/DOSTEPNOSC.md` (axe 0 naruszeń w obszarze AED, klawiatura, 320 px, wysoki kontrast) i 19 zrzutów `320px-*`/`kontrast-*` (it. 68);
- „pełna integracja w backendzie portalu to plan” – doprecyzować: „publikacja przez harwester sprawdzona na lokalnej kopii portalu bez zmian w kodzie”;
- dopisać z it. 41: licencja zbioru (po poprawce – CC BY 4.0), raporty importu bez e-maila, zbiór w 91% z Warszawy, brak informacji o szafkach w źródłach, link zarządcy ważny 90 dni (nie „jednorazowy”, it. 74).

**Slajd 10 (AI):** `[BRAK: fragment docs/uzycie-ai.md]` – zrzut tabeli z dziennika sesji; dopisać w `uzycie-ai.md` noc 21/22.11: research i analiza kodu portalu przez AI, wyniki w `docs/burza-mozgow.md`, weryfikacja przez człowieka przed użyciem na slajdach (każda liczba ma źródło – it. 63).

## Iteracja 76 (R57). Otwarte decyzje z `CLAUDE.md` – rekomendacje z dowodami z nocy (decydują ludzie)

| Decyzja | Rekomendacja | Dowody |
|---|---|---|
| Publiczny adres prototypu | **tak** – sam `docker-compose.yml` z katalogu głównego (usługa AED + nginx z frontendem, bez portalu), dane demo, `AED_CYCLE_HOURS=24`, **bez** `AED_FEED_*` wskazujących na prawdziwy portal | `tips.txt`: „jury nie będzie miało czasu na samodzielną konfigurację” (it. 10); ryzyko zasilenia prawdziwego portalu danymi jurorów (it. 45); tekst „co 24 godziny” w panelu (it. 73) |
| Godzina i sposób oddania | potwierdzić u organizatora rano; plan zakłada 3–4 h (it. 69) | – |
| Nazwa i hasło | decyzja ludzi; kryteria z nocy: nazwa ≤ 14 znaków mieści się w jednej linii naklejki czcionką 22, hasło ≤ 22 znaki – jedną linią czcionką 18 (it. 64); nazwa powinna nadawać rolę dostawcy (odpowiedzialność, it. 9); „Opiekun AED” spełnia oba | it. 9, 64; `kampania/nazwa-i-haslo.md` |
| Numer seryjny w zbiorze otwartym | **nie publikować** (zostaje w rejestrze); decyzję zapisać w `schema.json` jako atrybut pola, nie w kodzie usługi | Géo'DAE (Francja) wyłącza numer seryjny, producenta, model i kontakty z danych otwartych na mocy aneksów rozporządzenia (it. 62); dziś lista ukrytych pól jest w kodzie usługi i nie działa w `aed_standard build` (it. 43) |
| Podstawa prawna raportowania | dobrowolność + zachęty teraz; na slajd „co dalej”: rozporządzenie o strukturze danych na wzór deweloperów (Dz.U. 2026 poz. 1489) oraz warunek wpisu przy AED kupowanych ze środków publicznych | precedens ministerstwa (it. 34); Francja ma obowiązek, ale i tak ok. 1/3 rynku zadeklarowane (`zachety.md`) – prawo nie wystarcza bez procesu |

Nowe decyzje, które wyszły w nocy (do dopisania do „Otwartych decyzji”):

1. ranking firm → neutralna lista dostawców (it. 2, 39, 65);
2. wycofane rekordy w zbiorze otwartym – tak/nie i jak długo (it. 23);
3. licencja zbioru krajowego: CC BY 4.0 (wynika z danych, it. 21) – formalność, ale wymaga zgody;
4. `dysponent_nazwa` przy jednoosobowej działalności – publikować czy nie (it. 32);
5. flagi zbioru (dane dynamiczne – nie; wysokiej wartości – nie) – potwierdzić u mentora (it. 7).
- [x] R58 (it. 77). Kraków i Koszalin (listy na stronach WWW) – czy da się je pozyskać jako źródło bez scrapingu; co zaproponować miastom.
- [x] R59 (it. 78). Sprawdzić `docs/dodawanie-zrodla.md` – czy dodanie źródła z innego portalu CKAN/XML jest opisane; luki wobec kanałów z it. 54.
- [x] R60 (it. 79). Ostatnie przejście po podsumowaniu na górze – sprostowania z it. 68 (dostępność) i 74 (token) – przed R50.
- [x] R61 (it. 80). `naprawy_danych` w `raport.json` – pełna lista napraw plików z portalu jako dowód „walidacja działa na danych już opublikowanych”.
- [x] R62 (it. 81). Testy a punkty rozmowy z komisją – które punkty mają test automatyczny, które nie.
- [x] R63 (it. 82). Strona „konta portalu wyłączone” (`!portal-accounts`) w trybie z lokalnym backendem portalu (`start:aed-local`) – czy komunikat nie przeczy temu, co pokazujemy jury.
- [x] R64 (it. 83). Przemyśl (GeoJSON, „codziennie”) – jakość pliku i metadanych; czy deklarowana codzienna aktualizacja jest prawdą (daty w manifeście).
- [x] R65 (it. 84). Pilotaż z InPostem – konkretna propozycja (co InPost publikuje, którym kanałem, co z tego ma) na podstawie `zachety.md` i danych OSM.
- [x] R66 (it. 85). Hasła mentorów → iteracje → działanie → status: jedna tabela syntezy (przed R50).


## Iteracja 77 (R58). Kraków i Koszalin – listy na stronach WWW: pozyskać czy zaprosić

Ustalenia:

- **Koszalin**: w OSM 31 węzłów AED ma `source = „Urząd Miejski w Koszalinie”`, a 36 – operatora związanego z Koszalinem (biuro zarządzania kryzysowego urzędu miasta). Miasto już raz przekazało swoją listę – do społeczności, która przepisała ją do OSM (licencja ODbL). Na portalu dane.gov.pl zbioru Koszalina o AED nie ma.
- **Kraków** („Krakowski IMPULS ŻYCIA AED”, lista na stronie miasta, podobno aktualizowana 1.04.2026 – notatki, źródło wtórne): w OSM tylko 2 węzły powołują się na `bip.krakow.pl`.

Wnioski:

- **Nie scrapować** stron WWW do zbioru ministerstwa: lista HTML nie ma licencji ani zadeklarowanego dostawcy (diagnoza z `tips.txt`: brak odpowiedzialności), a zbiór oparty na scrapingu byłby kruchy. Zgodne z dotychczasową decyzją w `CLAUDE.md` („publikują tylko listy na stronach WWW” – nie są źródłem).
- **Zaprosić – to najtańsze „szybkie wygrane” kampanii**: oba miasta mają już gotową listę urządzeń i jednostkę odpowiedzialną. Wystarczy, że opublikują ją na dane.gov.pl w standardzie (arkusz XLSX → CSV) jako własny zbiór; mapper ministerstwa dołoży go automatycznie (wpis w `sources.json` albo odkrywanie po tagu – it. 36). Koszalin: ok. 30–36 urządzeń, Kraków: urządzenia miejskie z listy.
- Argument w zaproszeniu (raport luk, it. 70): „Wasza lista jest już w OpenStreetMap, ale na licencji, która nie pozwala jej użyć w zbiorze państwowym; opublikujcie ją sami na dane.gov.pl – będzie w zbiorze krajowym z Waszym urzędem jako dostawcą”.
- Wzorzec dla kampanii samorządowej: miasta, których dane trafiły do OSM z „source = urząd” (`source` wypełnione w 8% obiektów OSM; it. 22 / research 3.2), to gotowa lista adresatów pierwszej fali – one już raz zdecydowały się dane udostępnić.

## Iteracja 78 (R59). `docs/dodawanie-zrodla.md` a kanały z iteracji 54 – co działa bez kodu, czego brakuje

Stan (instrukcja i kod):

- Wpis w `sources.json` obsługuje **pliki CSV i GeoJSON** z mapowaniem kolumn i naprawami; źródła niestandardowe (Warszawa, OSM) mają osobny kod (`"mapper"`).
- Pobieranie (`scripts/download_aed_data.py:30-50`) obsługuje automatycznie **tylko zbiory z dane.gov.pl** (klucz `dane_gov_pl.dataset_id`); OSM i API Warszawy mają stałe funkcje.
- Wpis wskazuje **konkretny plik zasobu** (`"file": "dane_gov_pl/krosno/resource_54632.csv"`). Gdy gmina podmieni zasób (nowy zasób = nowy identyfikator), źródło przestanie się wczytywać – usługa je pominie bez wycofywania urządzeń (bezpiecznie, it. 35), ale dane przestaną się odświeżać, dopóki ktoś nie poprawi wpisu.

Luki wobec kanałów z iteracji 54:

| Kanał | Obsługa w mapperze | Luka | Propozycja |
|---|---|---|---|
| zbiór gminy na dane.gov.pl w standardzie (przypadek 1) | jest, bez kodu | sztywny identyfikator zasobu | wybierać **najnowszy zasób CSV zbioru** zgodny z nagłówkiem standardu zamiast stałego `resource_id` – odporność na podmianę pliku (tak samo działa harwester u dużych dostawców: nowa wersja = nowy plik, it. 21) |
| duży dysponent z własnym zasilaniem XML | zbiór i tak trafia na dane.gov.pl → przypadek 1 | brak | – (wystarczy, że zbiór jest na portalu) |
| miasto z CKAN | zbiór trafia na dane.gov.pl jako zasób-link → przypadek 1 tylko, jeśli link prowadzi do pliku CSV | link do API (jak Warszawa) wymaga kodu | w pakiecie dostawcy: „link do pliku CSV w standardzie, nie do API” (it. 36) |
| odkrywanie zbiorów po tagu akcji | brak | ręczna lista | zadanie cykliczne: wyszukiwanie w API portalu po tagu → lista kandydatów do zatwierdzenia przez człowieka (it. 2) |

Wniosek: dzięki temu, że **każdy kanał dostawcy kończy się zbiorem na dane.gov.pl**, mapper ministerstwa potrzebuje tylko jednego mechanizmu wejścia (zbiory z portalu w standardzie). To mocny argument architektoniczny na slajd: „portal jest szyną danych – dostawcy publikują u siebie, ministerstwo składa całość”. Dwie poprawki z tabeli (najnowszy zasób, odkrywanie po tagu) czynią to automatycznym.

## Iteracja 79 (R60). Sprostowania naniesione

Naniesiono w miejscu (bez kasowania historii): it. 6 (pozycja 10 – audyt już jest), it. 16 (nagłówek sekcji), it. 41 (ograniczenie 17), podsumowanie (blok „Sprostowania nocy”). Liczba poprawionych miejsc: 4.

## Iteracja 80 (R61). Naprawy danych z portalu – i odkrycie: **Marki skopiowały plik Krosna razem z jednym punktem**

`raport.json` → `naprawy_danych` (cztery wpisy, wszystkie dla Marek):

1. 8 wierszy ujętych w jedną parę cudzysłowów – rozpakowane;
2. w 7 z 8 rekordów zamienione szerokość i długość – poprawione;
3. rekord 7 (Szkoła Podstawowa nr 5) – punkt 293 km od reszty – współrzędne usunięte;
4. rekordy 5 i 6 – różne adresy, te same współrzędne – zostawione do sprawdzenia u dostawcy.

**Nowe ustalenie (porównanie surowych plików):** współrzędne „szkoły w Markach” (`21.72034402175176, 49.718809346153336`) są **identyczne do ostatniej cyfry** z pierwszym wierszem zbioru Krosna (Zespół Krytych Pływalni, ul. Jasna, Krosno – `datasets/raw/dane_gov_pl/krosno/resource_54632.csv:2`). Oba pliki mają też identyczny nagłówek („Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id”, ze spacjami po przecinkach). Wniosek: Marki użyły pliku Krosna jako szablonu, wpisały swoje dane – ale w kolumnie „Długość” podały szerokość (stąd zamienione współrzędne w 7 rekordach) i zostawiły jeden punkt z Krosna.

Dlaczego to ważne (slajd 2–3, nasze dane, zasada 10):

- To najkrótsza możliwa ilustracja tezy zadania „bez wzorcowego zakresu danych każda gmina publikuje inaczej”: **gminy już dziś kopiują pliki sąsiadów jako nieformalny wzorzec – razem z ich układem i błędami.** Skoro i tak kopiują, trzeba im dać wzorzec, który da się bezpiecznie skopiować (XLSX z listami rozwijanymi, walidator, pakiet dostawcy).
- Walidator z mapperem wykrył wszystkie trzy klasy błędów automatycznie (format CSV, zamiana współrzędnych, punkt odstający) – dowód, że kontrola działa także na danych **już opublikowanych na portalu**.
- Raport luk dla Marek (it. 70) ma gotową treść: „rekord 7 ma współrzędne pływalni w Krośnie; rekordy 5 i 6 – te same współrzędne przy różnych adresach; kolumny współrzędnych zamienione”.

## Iteracja 81 (R62). Testy automatyczne a punkty rozmowy z komisją i nocne ustalenia

66 testów Pythona (`tests/`) i 3 pliki testów frontendu (`aed-hours.spec.ts`, `aed-ministry.component.spec.ts`, `aed-qr.component.spec.ts`).

| Punkt / ustalenie | Testy | Stan |
|---|---|---|
| 1. ministerstwo publikuje jeden zbiór | `test_publication_export`, `test_export_has_records_and_http_export_is_the_same`, `test_xml_matches_portal_xsd`, `test_ids_stable_and_csv_name_follows_data`, `test_write_feed_keeps_old_versions_and_md5_matches` | pokryte; **brak testu licencji zbioru** (it. 21) |
| 2. jedna struktura zgodna z portalem | `test_legionowo_is_subset_of_standard`, `test_real_registry_is_valid`, `test_example_seller_files`, `test_file_level_checks` | pokryte |
| 3. zgłoszenie przez sprzedawcę | `test_full_path`, `test_roles_and_upload_limits`, `test_single_device_and_seller_ranking`, `test_submission_zrodlo_is_reserved` | pokryte |
| 4. QR i potwierdzenie zarządcy | `test_full_path`, `test_manager_links_are_independent`, `test_problem_report_is_validated_but_may_be_incomplete`, `test_signal_does_not_change_record`, `test_sticker_text_fits_and_logo_placeholder`; frontend: `aed-qr.component.spec.ts` | pokryte; **brak testu „112 na stronie QR”** (it. 42) – dopisać razem z poprawką |
| 5. okresowe potwierdzenia, bateria, elektrody | `test_reminders_idempotent_and_stale`, `test_manager_can_replace_battery_and_reminder_stops` | pokryte |
| 6. mapper cykliczny i deduplikacja | `test_same_source_never_merges`, `test_serial_number_merge`, `test_different_serials_never_merge_spatially`, `test_mapper_*` (4), `test_duplicate_decisions_survive_mapper_runs`, `test_confirmation_queues_spatial_match_with_imported_record`, `test_jobs_do_not_overlap`, `test_typo_in_registry_entry_retires_nothing_end_to_end` | pokryte bardzo dobrze |
| 7. kompletność | pośrednio (`test_full_path`) | brak testu wartości (np. „pełna ścieżka daje 97”) – opcjonalnie |
| zasada 3 (ODbL) | `test_osm_values_never_leak`, `test_odbl_source_never_copies_values_whatever_the_flag` | pokryte |
| zasada 6 (bez danych osobowych) | `test_serial_never_in_public_output` | pokryte dla usługi; **`aed_standard build` publikuje kontakty** (it. 43) – test przejdzie dopiero po przeniesieniu listy pól do schematu |
| naprawy danych z portalu | `test_marki_repair`, `test_swapped_coordinates`, `test_broken_csv_detector_on_real_marki` | pokryte (na prawdziwym pliku Marek – zgodne z konwencją „test na prawdziwym pliku”) |
| godziny „dostępne teraz” | `aed-hours.spec.ts` | pokryte we frontendzie; brak reguły i testu w walidatorze (it. 71) |

Testy, które warto dopisać razem z poprawkami z planu (it. 69): licencja zbioru ≥ licencje rekordów; blok 112 na stronie QR (spec frontendu); pola niepubliczne puste w każdym eksporcie (także `aed_standard build`); `wprowadzajacy_nazwa` wypełnione dla importów. Każdy to kilka linii obok istniejących testów.

## Iteracja 82 (R63). Tryb prototypu blokuje logowanie do portalu – także z lokalnym backendem

Ustalenia (`frontend/src/app/pages/aed/aed-prototype.ts`):

- `AED_PROTOTYPE = !environment.production` – każda kompilacja poza produkcyjną portalu jest prototypem; pokazuje żółty pasek „Prototyp hackathonowy… to nie jest serwis dane.gov.pl” i **blokuje trasy logowania i rejestracji portalu** (`aedPortalAccountsOff`, `app-routing.module.ts:100`) – przekierowanie na stronę „Logowanie do portalu jest tu wyłączone”.
- Uzasadnienie jest dobre dla prototypu publicznego (frontend rozmawia z produkcyjnym API dane.gov.pl i nie może przyjmować prawdziwych haseł).
- **Konflikt z trybem `start:aed-local`** (frontend z lokalnym backendem portalu, konfiguracja `dev`): też jest prototypem, więc nie da się zalogować do lokalnego portalu przez frontend. Skutki dla nocnych planów:
  - zrzut „Propozycje nowych danych” z głosami pełnomocników (it. 3.1, 25) – głos oddaje się z frontendu portalu po zalogowaniu; w trybie `aed-local` to niemożliwe;
  - przycisk „Panel administracyjny” w „Moim koncie” (o który pytałeś wczoraj) też nie jest osiągalny przez frontend.
- Obejścia na rano (bez zmiany kodu): głosy i propozycję przygotować w panelu administracyjnym (`localhost:8001`) albo przez API lokalnego portalu (`localhost:8000`, logowanie `POST /auth/login`), a zrzut listy propozycji zrobić niezalogowanym (lista publiczna, `is_published_for_all`). Zmiana kodu (osobna konfiguracja, w której `AED_PROTOTYPE` jest fałszywe tylko dla lokalnego backendu) – mała, ale dotyka zabezpieczenia; tylko jeśli zespół uzna zrzut z głosowaniem za konieczny.
- Na slajd i do instrukcji: rozdzielić „prototyp publiczny (portal tylko do odczytu, konta demo AED)” od „lokalna kopia portalu (dowody mechanizmów portalu, zrzuty z panelu administracyjnego)”.

## Iteracja 83 (R64). Przemyśl – „codziennie” w metadanych, dane sprzed dwóch lat

Z `datasets/raw/manifest.json` i `dataset_metadata.json` zbioru 4581:

- deklarowana częstotliwość: **„Codziennie”**; zbiór utworzony i ostatnio zmieniony **06.11.2024**, zasoby z datą danych 06.11.2024 i 20.11.2024 – czyli **dwa lata bez aktualizacji** przy deklaracji codziennej (stan pobrania: 21.11.2026);
- **5 zasobów z tą samą treścią** (GML ×2, GeoJSON, JSON, CSV), wszystkie jako linki do eksportu z miejskiego CMS (`przemysl.skycms.com.pl/open-data/…`); w pliku: opis-ulotka o AED zamiast opisu miejsca, galeria zdjęć, pola `www`, `youtube_url`, `panorama_url` puste – to eksport „punktów na mapie” systemu CMS, nie zbiór danych o urządzeniach.

Wnioski:

- **Metadana „częstotliwość” na portalu nie mówi, czy dane są aktualne** – trzy gminy deklarują brak regularności (it. 46), a czwarta deklaruje „codziennie” i nie aktualizuje od dwóch lat. Wskaźnik aktualności musi pochodzić z danych (`data_weryfikacji` w każdym rekordzie), nie z deklaracji zbioru – to argument za naszym polem i za statusem `nieaktualny` po 12 miesiącach.
- Przypomnienia portalu o aktualizacji (it. 19) nie obejmują częstotliwości „codziennie” – dlatego Przemyśl nie dostał żadnego przypomnienia przez dwa lata. Rekomendacja w pakiecie dostawcy: deklarować częstotliwość, którą da się utrzymać (miesięczną albo kwartalną), wtedy portal sam przypomni.
- **Dostawca CMS jako dźwignia** (pomysł B6 z researchu, teraz z dowodem): Przemyśl publikuje dane AED eksportem z SkyCMS. Jeśli ten sam system obsługuje inne gminy, jeden eksport „AED w standardzie” u dostawcy CMS dałby wiele zbiorów naraz [do sprawdzenia, ile gmin używa tego CMS]. Do kampanii: dostawcy systemów dla samorządów jako partnerzy (obok producentów AED).
- Zasoby-linki do CMS (`availability` zdalna) to także powód, dla którego na portalu nie ma tabeli i mapy dla tego zbioru [do sprawdzenia na produkcji] – rekomendacja z it. 36 („plik CSV w standardzie, nie link do systemu”) dotyczy też Przemyśla.

## Iteracja 84 (R65). Pilotaż z InPostem – propozycja oparta na danych

Profil urządzeń InPostu w OSM (operator „InPost”, 96 obiektów, 21.11.2026):

- wszystkie `access = yes`, 95 z 96 `opening_hours = 24/7`, wszystkie na zewnątrz (`indoor = no`), opis miejsca „w kapsule na paczkomacie”;
- **92 z 96 bez daty weryfikacji**, żaden bez `source`, żaden z nazwą miejsca – czyli to najlepsze możliwe urządzenia dla świadka (całodobowe, na ulicy), opisane przez społeczność, bez odpowiedzialnego dostawcy w danych.
- `zachety.md` (źródła InPostu): ok. 188 aktywnych stacji Helpbox 365 (liczba niepotwierdzona), Centrum Ratownictwa monitoruje i serwisuje urządzenia. OSM zna ok. połowę.

Propozycja pilotażu (na slajd zachęt, jako przykład „co ma firma, która kupuje AED i utrzymuje dane” – pkt 8 rozmowy z komisją):

| Co | Jak |
|---|---|
| Kanał | InPost ma własny system i mapę stacji → **zasilanie XML** we wzorcu (zbiór na portalu pod instytucją `private` InPost) albo, prościej na start, plik CSV raz dziennie do rejestru ministerstwa |
| Zakres | identyfikator stacji, nazwa (np. numer i adres Paczkomatu), współrzędne, `dostep = publiczny`, `godziny_dostepu = 24/7`, `sposob_otwarcia = otwarta`, producent i model AED, terminy baterii i elektrod, `data_weryfikacji` z monitoringu Centrum Ratownictwa |
| Wartość dodana dla zbioru | od razu ok. 100–190 urządzeń całodobowych z odpowiedzialnym dostawcą i weryfikacją – to dziś więcej niż wszystkie cztery gminy razem (74) |
| Pierwsze „dane dynamiczne” | monitoring stanu stacji (Centrum Ratownictwa) mógłby codziennie aktualizować stan działania – kandydat na flagę `hasDynamicData` w przyszłości (it. 5, 62) |
| Co ma InPost | obecność stacji w państwowym zbiorze i aplikacjach na równych zasadach (bez reklamy – it. 9), dowód do raportu CSR, zgodność z inicjatywą Helpbox, przy okazji raport luk: które stacje są już w OSM, a których brak |
| Ryzyko | zbiór pod marką komercyjną – zgodnie z „nie premiować” InPost jest jednym z dostawców, bez wyróżnienia w portalu (it. 39) |

Zastrzeżenie: liczby z OSM to obserwacja społeczności, nie dane InPostu; przed rozmową z firmą sprawdzić aktualną liczbę stacji u źródła.

## Iteracja 85 (R66). Hasła mentorów – synteza: interpretacja, dowód w kodzie, działanie, status

| Hasło | Najlepsza interpretacja | Dowód (kod/dane) | Działanie | Status |
|---|---|---|---|---|
| Metody zbierania danych / portal zbiera od różnych dostawców | 12 kanałów, dane tylko z kanałów z odpowiedzialnością; portal jako szyna danych | it. 54, 78; harwester XML i CKAN w `harvester/` | slajd z tabelą kanałów; szablon zasilania dla dostawców; odkrywanie po tagu | ustalone; szablon i odkrywanie – plan |
| „Prasowanie” danych, żeby id się nie powtórzyło | stałe `id_aed` i `extIdent`; id z naklejki wygrywa | `dedup.py:171`, `app.py:763`, test `test_id_stable_across_builds` | wycofane rekordy w zbiorze z powiązaniem | ustalone; zmiana eksportu do decyzji |
| Nie zaburzać stylistyki, nie premiować danych | moduł na tokenach portalu; bez publicznego rankingu firm i bez `is_promoted`; priorytet źródeł = odpowiedzialność | `aed.scss`, `datasets/models.py:394`, it. 28, 53 | „Ranking firm” → „Dostawcy danych” (lista miejsc w it. 65) | do decyzji |
| Dane stare mają pozostać | nie zastępujemy zbiorów gmin; wersje CSV zostają; wycofane rekordy widoczne | it. 2, 23, 35; `feed.py` | wycofane w eksporcie | częściowo (wersje – jest) |
| Flaga, która nie jest fakultatywna / kategorie | flagi i kategoria zbioru obowiązkowe w formularzu portalu; szablon ministerstwa ustala je dla dostawców | `datasets/forms.py:92-150`, it. 34 | podane jawnie w `zbior_dane_gov_pl`; arkusz metadanych w XLSX | jest w zasilaniu; XLSX – plan |
| Dostęp do panelu administratora / adres panelu | dwie role w panelu: redakcja (instytucja, źródło danych, propozycje, CMS) i pełnomocnik dostawcy; instrukcja panelu jak w programach ministerstwa | it. 24, 34, 57, 82 | pakiet dostawcy z instrukcją panelu; zrzuty z `localhost:8001` | panel działa lokalnie; instrukcja – plan |
| Zautomatyzowanie procesów | dobowy łańcuch: mapper → przypomnienia → zasilanie → import portalu; człowiek tylko przy zaufaniu | it. 13, 35, 45 | monitor publikacji (raporty e-mail portalu nie działają) | łańcuch jest; monitor – plan |
| 2 słowa capslockiem (DATA SOURCES) | harwester portalu | `backend/mcod/harvester/`, it. 21–23 | zasilanie XML ministerstwa | **zrobione i sprawdzone** (z poprawką licencji do zrobienia) |
| Wykaz, gdzie można zmobilizować rozwiązanie | „Propozycje nowych danych” – głosują pełnomocnicy instytucji | `suggestions/views.py:136`, it. 25 | propozycja „Dane o AED” + zrzuty (przez panel/API – it. 82) | do zrobienia rano |

Wniosek końcowy syntezy: wszystkie hasła mentorów wskazują **mechanizmy, które portal już ma** (harwester, propozycje, flagi, panel, CMS). Najsilniejsza odpowiedź na kryterium 30% to pokazać, że nasze rozwiązanie korzysta z każdego z nich – bez zmian w kodzie portalu.

---

## Podsumowanie końcowe nocy (22.11, 7:00)

85 iteracji, 66 tematów z kolejki; wszystko bez zmian w kodzie i bez commitów. Najważniejsze w kolejności działania:

**Poprawić przed oddaniem (małe, z testami – plan w it. 69):**

1. Licencja zbioru z harwestera: dziś CC0, a 715 z 781 rekordów jest na CC BY 4.0 → `<conditions><source>true</source></conditions>` (it. 21).
2. „Zadzwoń 112” na górze strony QR i na naklejce – dziś brak (it. 42, 64).
3. `.gitattributes` ze składnią atrybutów – dziś test nie przechodzi przy `autocrlf=true` (it. 31).
4. `wprowadzajacy_nazwa` dla importów – pole wymienione przez komisję jest puste we wszystkich 781 rekordach (it. 46).
5. Pola niepubliczne w `schema.json` zamiast w kodzie usługi – jeden eksport publikacyjny (it. 43).
6. Dokumenty: link zarządcy „jednorazowy” → „ważny 90 dni” (it. 74); podlinkować istniejący raport dostępności `frontend/aed-zrzuty/DOSTEPNOSC.md` (it. 68); nieaktualne punkty instrukcji i konspektu (it. 29, 75).

**Pokazać (dowody do 30% – zrzuty z lokalnego portalu, it. 68):** źródło danych z raportem importu, zbiór z tabelą i mapą, „Umieść na swojej stronie”, propozycja nowych danych (głosy przez panel/API, bo frontend prototypu blokuje logowanie – it. 82), `zasilanie.xml`.

**Decyzje ludzi (it. 76):** nazwa i hasło, publiczny adres prototypu, ranking firm → lista dostawców, wycofane rekordy w zbiorze, `dysponent_nazwa` przy jednoosobowej działalności, licencja CC BY 4.0, flagi zbioru.

**Narracja (fakty z naszych danych, it. 63):** zbiór otwarty to w 91% Warszawa; sklepy, stacje i hotele – 0,3%; najlepszy otwarty rekord ma kompletność 62/100, rekord po ścieżce sprzedawca → zarządca 97/100; gminy publikują tylko „gdzie”, nie „kiedy” i „czy sprawdzone” (it. 70); Marki skopiowały plik Krosna razem z jednym punktem (it. 80); Przemyśl deklaruje „codziennie”, a dane są sprzed dwóch lat (it. 83); InPost ma 96 całodobowych AED w OSM i żadnego w zbiorze z odpowiedzialnym dostawcą (it. 84); interpelacja 20440 do Ministra Cyfryzacji pyta dokładnie o to, co rozwiązujemy (it. 34).

**Mechanizmy portalu, na których stoi rozwiązanie (it. 85):** instytucja-dostawca, harwester XML (DATA SOURCES), flagi i kategorie, walidacja tabelaryczna i mapa, propozycje nowych danych, „Zgłoś uwagi do zbioru”, osadzanie mapy, CMS (baza wiedzy, strona akcji) – wzorem pakietów ministerstwa dla starostów i deweloperów.

Plan na „co dalej” (poza oddaniem): nowe pola standardu (stan działania, `sposob_otwarcia`, piętro, kategoria miejsca), reguła składni godzin w walidatorze, konwersja opisów godzin Warszawy, pakiet dostawcy w CMS, monitor publikacji, regiony TERYT, odkrywanie zbiorów po tagu, pilotaż z InPostem i dużymi dysponentami (ZUS, sieci handlowe, uczelnie).
