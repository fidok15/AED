# Prezentacja – konspekt slajd po slajdzie

Wymóg zadania: min. 5 slajdów z dowodami na realizację wymagań technicznych (zrzuty ekranu), opis funkcjonalności z krokami użytkownika, lista ograniczeń. Proponujemy 10 slajdów. Kryterium „Prezentacja” to 5% oceny, ale jest też nośnikiem dowodów dla pozostałych (zgodność z dane.gov.pl 30%).

Narracja sprzedażowa: **problem → dlaczego obecne dane zawodzą → proces → standard danych → dowód zgodności z dane.gov.pl → kampania i zachęty → ograniczenia → deklaracja użycia AI.** Logo i hasło dotyczą akcji dla dostawców, więc na slajdzie 7 pokazujemy je jako część rozwiązania „jak pozyskać dostawców”, nie jako ozdobę pitchu.

Zasady: liczby tylko ze źródła pierwotnego albo z naszych danych (`datasets/out/raport.json`, twarda zasada 10); bez obietnic uratowanych istnień (zasada 9); w przykładzie stan źródeł na 21.11 podany w `CLAUDE.md` (pięć zbiorów z dane.gov.pl, API Warszawy 708 urządzeń, OpenAEDMap 18 297 obiektów) – przed użyciem odświeżyć z raportu.

---

## Slajd 1. Tytuł i teza

- **Nagłówek:** „[NAZWA AKCJI]: jeden zbiór o AED, za który ktoś odpowiada”
- Punkty:
  - zadanie: ogólnopolski, otwarty, aktualny zbiór AED na dane.gov.pl;
  - nasza odpowiedź: proces, w którym dane wprowadza podmiot odpowiedzialny, a Ministerstwo publikuje jeden zbiór;
  - w pakiecie: standard danych, prototyp portalu, akcja dla dostawców z logo i księgą znaku.
- **Zrzut dowodowy:** `[WSTAW: ekran startowy prototypu z logo akcji]`
- **Notatki mówcy:** Zaczynamy od tezy, nie od technologii: dziś nikt nie odpowiada za dane o AED, a my pokazujemy, jak to zmienić. W ciągu kilku minut przejdziemy przez proces od sprzedaży urządzenia do publikacji zbioru. Na końcu pokażemy, jak sprawić, żeby dostawcy zgłosili się sami.

## Slajd 2. Problem

- **Nagłówek:** „Dane są rozproszone i nikt za nie nie odpowiada”
- Punkty:
  - sytuacja z zadania: 3 marca w centrum Warszawy świadkowie szukali AED, część urządzeń była zamknięta na klucz (opis z treści zadania, bez własnych szczegółów);
  - nie istnieje kompletna mapa; kilka baz, mniej lub bardziej kompletnych (treść zadania);
  - diagnoza organizatora: dane niezweryfikowane, „nikt nie bierze za nie odpowiedzialności” (`docs/tips.txt`);
  - nasz pomiar: **[WSTAW: liczba źródeł i rekordów z raportu, np. 5 zbiorów z dane.gov.pl + API Warszawy + OpenAEDMap, z `datasets/out/raport.json`]**.
- **Zrzut dowodowy:** `[WSTAW: tabela źródeł z manifestu `datasets/raw/` lub wykres z raportu]`
- **Notatki mówcy:** Problem to nie tylko brak danych, ale brak właściciela danych. Sam zbiór sklejony przez zespół nie rozwiąże sprawy, bo dane.gov.pl wymaga dostawcy, który bierze odpowiedzialność za zbiór. Dlatego budujemy proces, nie jednorazowy plik.

## Slajd 3. Dlaczego obecne dane zawodzą

- **Nagłówek:** „Pięć zbiorów, trzy schematy, brak potwierdzenia”
- Punkty:
  - istniejące zbiory na dane.gov.pl (Krosno, Marki, Przemyśl, Legionowo, Warszawa) mają różne struktury kolumn; najczystszy jest Legionowo i to jemu dopasowaliśmy nazwy pól adresu (`CLAUDE.md`);
  - samorządy, które nie publikują maszynowo: Kraków („Impuls Życia”) i Koszalin („Punkty Życia”) – tylko listy na stronach WWW (`CLAUDE.md`);
  - OpenStreetMap: dużo obiektów, ale bez odpowiedzialnego dostawcy i na licencji ODbL, więc nie mieszamy z danymi otwieranymi przez ministerstwo (zasada 3);
  - braki: **[WSTAW: kompletność pól kluczowych w źródłach z raportu, np. % rekordów z godzinami dostępu]**.
- **Zrzut dowodowy:** `[WSTAW: porównanie kolumn zbiorów lub raport jakości z `datasets/out/`]`
- **Notatki mówcy:** Pokazujemy, że różne zbiory opisują to samo różnym językiem, więc nie da się ich połączyć bez wspólnego standardu. Dodatkowo żaden z nich nie mówi, kto i kiedy potwierdził dane. To wskazanie braków jest podstawą naszego procesu potwierdzeń.

## Slajd 4. Proces od sprzedaży do zbioru

- **Nagłówek:** „Sprzedawca → naklejka QR → zarządca → zbiór Ministerstwa”
- Punkty (kroki użytkownika):
  1. Producent lub sprzedawca rejestruje urządzenie przy sprzedaży (CSV lub formularz), rekord ma status `zgloszony`.
  2. Do urządzenia trafia naklejka z kodem QR.
  3. Zarządca skanuje kod, uzupełnia lokalizację i godziny dostępu, potwierdza stan: `aktywny`.
  4. Rejestr krajowy Ministerstwa publikuje rekordy w profilu `publikacja` jako zbiór na dane.gov.pl; brak potwierdzenia w terminie: `nieaktualny`.
  - równolegle: mapper cyklicznie dokłada dane z innych źródeł, z deduplikacją; rekordy bez odpowiedzialnego podmiotu: `niepotwierdzony`.
- **Zrzuty dowodowe:** `[WSTAW: panel firmy: wgranie CSV z raportem walidacji]`, `[WSTAW: strona QR na telefonie]`, `[WSTAW: widok rejestru ze statusami]`
- **Notatki mówcy:** To jest sedno rozwiązania: rolę wprowadzającego ma ten, kto zna urządzenie (sprzedawca), a miejsce potwierdza ten, kto je zna (zarządca). Ministerstwo jest dostawcą zbioru i agreguje to, co potwierdzone. Cykliczne przypomnienia utrzymują dane przy życiu.

## Slajd 5. Standard danych i wzorzec

- **Nagłówek:** „Jedna struktura dla wszystkich źródeł”
- Punkty:
  - jeden wiersz = jedno urządzenie; CSV UTF-8, daty `RRRR-MM-DD`, współrzędne WGS84 w osobnych kolumnach (warunek mapy na portalu);
  - pola z rozmowy z komisją: identyfikator, producent, model, numer seryjny, data produkcji, daty ważności elektrod i baterii, współrzędne, godziny dostępu, kto wprowadził;
  - dwa profile wymagalności: `sprzedaz` i `publikacja`; kompletność rekordu 0–100;
  - źródłem prawdy jest `aed_standard/schema.json`, z niego generujemy `wzorzec-aed.xlsx`, walidator i formularze.
- **Zrzut dowodowy:** `[WSTAW: arkusz `wzorzec-aed.xlsx` – karta pól i słownik]`, `[WSTAW: wynik walidatora dla przykładowego pliku]`
- **Notatki mówcy:** Standard jest zgodny z istniejącym zbiorem Legionowa, więc stanowi jego rozszerzenie, a nie konkurencję. Walidator mówi po polsku, co poprawić w wierszu i polu. Nie dublujemy listy pól w kodzie ani w dokumentach, bo wszystko wynika ze schematu.

## Slajd 6. Dowód zgodności z dane.gov.pl

- **Nagłówek:** „Publikujemy tak, jak pozwala portal”
- Punkty:
  - dostawcą zbioru krajowego jest Ministerstwo; firmy mają własne konta instytucji (typ konta zainspirowany istniejącym typem `developer`, `backend/mcod/organizations/models.py`);
  - obywatel nie publikuje; skan QR bez uprawnień jest sygnałem dla właściciela (zasada 2);
  - formaty maszynowe: CSV i XLSX, GeoJSON, XML do zasilania (zasada 5);
  - łatka do kodu portalu wydzielona (osobna aplikacja Django, moduł Angular), prawa przechodzą na Ministra Cyfryzacji (zasada 4);
  - środowisko: **[WSTAW: czy portal działa lokalnie (Docker Compose) czy dowód z API produkcyjnego i osobna usługa; plan B z `CLAUDE.md`]**.
- **Zrzut dowodowy:** `[WSTAW: lokalny portal: zbiór krajowy opublikowany jako zasób dostawcy „ministerstwo”, ustawiona mapa w „Mapy i wykresy”]` albo `[WSTAW: plan B]`
- **Notatki mówcy:** To odpowiedź na uwagę organizatora, że nie można przebudować mechaniki portalu tak, żeby każdy publikował. Dostawcą jest instytucja, a my tworzymy narzędzia, które mu to ułatwiają. Pokazujemy dowód uruchomienia, nie deklarację.

## Slajd 7. Kampania i zachęty dla dostawców

- **Nagłówek:** „[NAZWA AKCJI]: co ma firma, która zgłasza AED”
- Punkty:
  - cel: zgłaszają się producenci i sprzedawcy AED, zarządcy, samorządy (nie opinia publiczna);
  - zachęty: jedno miejsce raportowania, mapa sprzedawców, odznaka, darmowe przypomnienia o bateriach i elektrodach, ranking kompletności (pakiet w `kampania/zachety.md`);
  - punkt odniesienia: InPost „Helpbox 365” na Paczkomatach (komunikat z 13.08.2025); pożyczamy widoczny znak w przestrzeni publicznej i narrację o „białych plamach”;
  - naklejka z QR niesie znak akcji na każdym urządzeniu.
- **Zrzuty dowodowe:** `[WSTAW: logo i hasło]`, `[WSTAW: makieta naklejki QR]`, `[WSTAW: odznaka dostawcy i baner dla samorządu]`, `[WSTAW: mapa sprzedawców lub ranking, jeśli zrobione]`
- **Notatki mówcy:** Akcja nie obiecuje skutków zdrowotnych, tylko pokazuje wartość dla dostawcy: widoczność, mniej pracy, uznanie. Logo trafia na urządzenia i do komunikacji z dostawcami. Mierzymy liczbę dostawców, kompletność i udział potwierdzonych rekordów.

## Slajd 8. Zakres i kompletność – wynik

- **Nagłówek:** „Zbiór krajowy z pierwszych źródeł”
- Punkty:
  - zbiór krajowy po deduplikacji: **[WSTAW: liczba rekordów z `datasets/out/raport.json`]**;
  - podział statusów: `zgloszony`, `aktywny`, `nieaktualny`, `niepotwierdzony`: **[WSTAW]**;
  - średnia kompletność (0–100): **[WSTAW]**; lista duplikatów do ręcznego przeglądu: **[WSTAW: liczba]**;
  - wskazany referencyjny zakres każdego źródła (wymóg zadania): **[WSTAW: tabela źródło → zakres terytorialny/typ]**.
- **Zrzut dowodowy:** `[WSTAW: raport kompletności, widok rejestru z filtrem statusu]`
- **Notatki mówcy:** Każda liczba na tym slajdzie pochodzi z naszego raportu, nie z internetu. Deduplikacja nigdy nie łączy automatycznie dwóch rekordów z tego samego źródła, bo w jednym budynku bywa kilka urządzeń. Rekordy bez potwierdzenia nie trafiają do eksportu na dane.gov.pl.

## Slajd 9. Dostępność, responsywność i ograniczenia

- **Nagłówek:** „Co działa, a czego jeszcze nie ma”
- Punkty:
  - WCAG 2.2 AA i responsywność od pierwszego ekranu; lista dowodów: **[WSTAW: wynik audytu, np. Lighthouse/axe, 320 px, nawigacja klawiaturą]**;
  - ograniczenia (lista roboczo, uzupełniać w miarę pracy): brak podstawy prawnej obowiązku raportowania dla sprzedawców (dobrowolność i zachęty); dane z OSM na ODbL wymagają opinii prawnika; niepewny status publikacji numeru seryjnego w zbiorze otwartym; „10/14 lat żywotności” rozumiemy jako żywotność urządzenia, do potwierdzenia z komisją; logo i księga znaku wymagają próbnych wydruków (QR i minimalne rozmiary); **[WSTAW: nowe ograniczenia z prac]**;
  - co dalej: rekomendacja powiązania zakupów ze środków publicznych z obowiązkiem wpisu; integracja z systemami dyspozytorskimi (do ustalenia ze służbami).
- **Zrzut dowodowy:** `[WSTAW: raport dostępności, widok mobilny 320 px]`
- **Notatki mówcy:** Mówimy otwarcie, co jest zrobione, a co jest rekomendacją. Jury lubi widzieć, że znamy granice rozwiązania. Ograniczenia nie są wstydem, tylko planem następnych kroków.

## Slajd 10. Deklaracja użycia AI i prawa

- **Nagłówek:** „Autorskie rozwiązanie zespołu; AI jako narzędzie”
- Punkty:
  - AI pomagało przy: **[WSTAW: z `docs/uzycie-ai.md`, np. badania źródeł, szkice tekstów, fragmenty kodu]**; każdy wynik zweryfikował człowiek **[WSTAW: kto i jak]**;
  - logo i księga znaku powstały ręcznie, **[WSTAW: autor/autorzy, narzędzie]**;
  - prawa do rozwiązania przechodzą na Ministra Cyfryzacji; kod OpenAEDMap (AGPL) nie został skopiowany (zasada 4);
  - zasoby: kod portalu dane.gov.pl (fork), dane z dane.gov.pl, API Warszawy, OSM (ODbL).
- **Zrzut dowodowy:** `[WSTAW: fragment `docs/uzycie-ai.md`]`
- **Notatki mówcy:** Zadanie dopuszcza AI pod warunkiem, że praca jest autorskim rozwiązaniem zespołu z prawami po jego stronie; tak to dokumentujemy. Pokazujemy, co wygenerowano i co sprawdził człowiek. Dziękujemy; instrukcja dla jury prowadzi krok po kroku przez dowody.

---

## Lista zrzutów do zrobienia (zbiorczo)

1. ekran startowy z logo, 2. porównanie źródeł, 3. arkusz `wzorzec-aed.xlsx`, 4. walidator, 5. panel firmy (CSV), 6. strona QR (telefon), 7. widok rejestru (statusy, kompletność), 8. portal: zbiór i mapa, 9. makieta naklejki i odznaki, 10. audyt dostępności i widok 320 px, 11. `docs/uzycie-ai.md`.

Każdy zrzut: podpisany, z datą i adresem ekranu; w razie braków na portalu lokalnym użyć planu B z `CLAUDE.md` i napisać to na slajdzie 6 i 9.
