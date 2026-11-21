# Instrukcja dla jury (szkielet)

Organizator prosi o: (1) ponumerowane kroki wskazujące, który plik otworzyć i gdzie sprawdzić każde wymaganie, (2) klikalny prototyp bez konfiguracji, (3) uruchomienie portalu we własnym środowisku (`docs/tips.txt`). Poniżej tabela wymagań z treści zadania. Uzupełnić pola **[WSTAW]** tuż przed oddaniem; adresy i ścieżki nieznane dziś są oznaczone.

## Szybki start (3 minuty)

1. Otwórz prototyp: **[WSTAW: adres URL klikalnego prototypu]**. Logowanie: **[WSTAW: konto demonstracyjne firmy i zarządcy lub „bez logowania”]**. Hasła i dane demonstracyjne nie zawierają danych osobowych.
2. Jeśli prototyp jest niedostępny: nagranie i zrzuty (plan B): **[WSTAW: ścieżka lub adres]**.
3. Prezentacja: **[WSTAW: `docs/prezentacja.pdf` lub adres]**; konspekt w `docs/prezentacja-konspekt.md`.
4. Kod źródłowy: **[WSTAW: adres repozytorium]**; uruchomienie lokalne: **[WSTAW: polecenia]**.
5. Zbiór i wzorzec: `datasets/out/` i `wzorzec-aed.xlsx` **[WSTAW: ścieżka]**.

## Tabela: wymaganie → plik lub ekran → kroki sprawdzenia

### A. Wymagania formalne (sekcja 4 treści zadania)

| Wymaganie z treści zadania | Plik lub ekran | Kroki sprawdzenia |
|---|---|---|
| Szczegółowy opis i tytuł projektu | **[WSTAW: `README.md` lub `docs/opis-projektu.md`]** | 1. Otwórz plik. 2. Sprawdź tytuł na pierwszej stronie. 3. Sprawdź opis: cel, proces, standard danych, akcja. |
| Prezentacja, min. 5 slajdów | **[WSTAW: `docs/prezentacja.pdf`]**; konspekt: `docs/prezentacja-konspekt.md` | 1. Otwórz plik. 2. Policz slajdy (proponowane: 10). 3. Przejdź slajdy 4–6 jako dowody. |
| Dowody na realizację wymagań technicznych (zrzuty ekranu) | slajdy 4, 5, 6, 8, 9 prezentacji | 1. Na każdym z tych slajdów sprawdź podpisany zrzut ekranu z datą. 2. Porównaj z działaniem prototypu (kroki z sekcji C). |
| Opis funkcjonalności, w tym kroki użytkownika | slajd 4 (proces), sekcja „Ścieżki jury” poniżej | 1. Otwórz slajd 4. 2. Wykonaj ścieżkę 1 i 2 z sekcji „Ścieżki jury”. |
| Lista ewentualnych ograniczeń | slajd 9 prezentacji; **[WSTAW: `docs/ograniczenia.md`, jeśli wyodrębniona]** | 1. Otwórz slajd 9. 2. Sprawdź listę ograniczeń. |
| Prototyp rozwiązania | **[WSTAW: adres]** | 1. Otwórz adres. 2. Wykonaj ścieżki jury. |
| Plik z wzorcowym zakresem danych (xlsx) | **[WSTAW: `wzorzec-aed.xlsx`]** | 1. Otwórz plik w arkuszu kalkulacyjnym. 2. Sprawdź kartę z polami (nazwa, typ, wymagalność w profilach `sprzedaz` i `publikacja`). 3. Sprawdź kartę ze słownikami i przykładowymi wierszami. |
| Kod źródłowy | **[WSTAW: adres repozytorium]**; katalogi `aed_standard/`, `scripts/`, `backend/`, `frontend/` | 1. Otwórz repozytorium. 2. Sprawdź `aed_standard/schema.json` jako źródło prawdy. 3. Uruchom test: **[WSTAW: polecenie testu]**. |
| Logotyp w .jpg, .png, .pdf i formacie otwartym (.svg) | **[WSTAW: `kampania/logo/` – pliki]** | 1. Otwórz katalog. 2. Sprawdź pięć plików: `.svg`, `.png`, `.jpg`, `.pdf` oraz warianty (kolor, jednobarwny, negatyw). |
| Księga znaku w .pdf | **[WSTAW: `kampania/ksiega-znaku.pdf`]**; szkielet: `kampania/ksiega-znaku-szablon.md` | 1. Otwórz PDF. 2. Sprawdź sekcje: koncepcja, kolorystyka, pole ochronne, minimalna wielkość, niedozwolone użycia (patrz sekcja D). |

### B. Wymagania techniczne (sekcja 5 treści zadania)

| Wymaganie | Plik lub ekran | Kroki sprawdzenia |
|---|---|---|
| Format odczytywalny maszynowo dla udostępnianych danych (nie pdf, doc) | `datasets/out/` (CSV, GeoJSON); `wzorzec-aed.xlsx`; **[WSTAW: zasób na dane.gov.pl lub w lokalnym portalu]** | 1. Otwórz `datasets/out/` i sprawdź rozszerzenia plików danych (CSV, GeoJSON, XLSX, XML). 2. Pobierz CSV i sprawdź: UTF-8, jeden wiersz nagłówka, daty `RRRR-MM-DD`, współrzędne w osobnych kolumnach. 3. Potwierdź brak PDF i DOC wśród plików danych. |
| Zgodność z zasadami działania portalu dane.gov.pl | slajd 6; **[WSTAW: adres lokalnego portalu]**; kod w `backend/` (łatka wydzielona) | 1. Otwórz portal lokalny. 2. Zaloguj się jako firma **[WSTAW: konto]**. 3. Wgraj plik CSV **[WSTAW: ścieżka pliku przykładowego]**. 4. Sprawdź, że rekordy trafiają do zbioru jako zasób dostawcy „ministerstwo”. 5. Sprawdź, że obywatel bez uprawnień nie może publikować (skan QR jest sygnałem). |
| Zgodność z aktualną wersją WCAG | **[WSTAW: raport audytu, np. `docs/dostepnosc.md`]**; ekrany prototypu | 1. Otwórz raport. 2. Przejdź ścieżkę jury samą klawiaturą (Tab, Enter, Esc). 3. Sprawdź, że stan jest podany tekstem i ikoną, nie samym kolorem. 4. Sprawdź kontrasty tekstu (min. 4,5:1). Używana wersja: WCAG 2.2 AA **[do sprawdzenia: czy to „aktualna wersja” w dniu oceny]**. |
| Responsywność (komputery i urządzenia mobilne) | **[WSTAW: zrzuty 320 px i szeroki ekran]**; prototyp | 1. Otwórz prototyp na telefonie lub zawęź okno do 320 px. 2. Sprawdź stronę QR i listę rejestru. 3. Sprawdź, że lista działa bez mapy (mapa jest dodatkiem). |
| Zgodność z zasadami UX | prototyp | 1. Wykonaj ścieżkę 1 i 2. 2. Sprawdź komunikaty błędów walidatora po polsku. 3. Sprawdź jasny stan procesu (zgłoszony, aktywny, nieaktualny). |
| Użycie AI dozwolone pod warunkiem autorskiej pracy zespołu | `docs/uzycie-ai.md`; slajd 10 | 1. Otwórz plik. 2. Sprawdź listę: co wygenerowano, co zweryfikował człowiek. 3. Sprawdź oświadczenie o autorstwie logo **[WSTAW]**. |

### C. Wymagania funkcjonalne (sekcja 2 i 3 treści zadania)

| Wymaganie | Plik lub ekran | Kroki sprawdzenia |
|---|---|---|
| Zbiór ogólnopolski, otwarty, możliwie aktualny | `datasets/out/` (zbiór krajowy); **[WSTAW: widok na dane.gov.pl lub lokalnie]** | 1. Otwórz zbiór krajowy. 2. Sprawdź liczbę rekordów w `datasets/out/raport.json`. 3. Sprawdź znacznik czasu ostatniej aktualizacji **[WSTAW: pole]**. |
| Zebranie danych z wielu rozproszonych źródeł ze wskazaniem ich referencyjnego zakresu | `datasets/raw/` (manifest), raport, slajd 8 | 1. Otwórz manifest źródeł. 2. Sprawdź tabelę: źródło → zakres (terytorialny/typ), liczba rekordów **[WSTAW]**. 3. Uruchom mapper: **[WSTAW: polecenie]**; drugie uruchomienie dokłada tylko różnice. |
| Integracja informacji od wszystkich dysponentów w jednym zbiorze (deduplikacja) | `datasets/out/` – lista duplikatów do przeglądu, pole „źródło” w rekordach | 1. Otwórz listę duplikatów. 2. Sprawdź regułę: ten sam producent i numer seryjny = to samo urządzenie; do 15 m z różnych źródeł = łączenie automatyczne; dwa rekordy z tego samego źródła nigdy automatycznie. 3. Sprawdź, że rekordy tylko z OSM mają status `niepotwierdzony` i nie trafiają do eksportu na dane.gov.pl. |
| Wzorcowy zakres danych, jednolity sposób udostępniania | `aed_standard/schema.json`; `wzorzec-aed.xlsx` | 1. Otwórz schemat. 2. Sprawdź pola: identyfikator, producent, model, numer seryjny, data produkcji, daty ważności elektrod i baterii, współrzędne, godziny dostępu, kto wprowadził. 3. Uruchom walidator na pliku **[WSTAW: przykład poprawny i błędny]**; sprawdź komunikaty po polsku. |
| Proces: sprzedawca → naklejka QR → zarządca → zbiór ministerstwa | prototyp: panel firmy, strona QR, rejestr | Patrz „Ścieżki jury” poniżej. |
| Przypomnienia o potwierdzeniu i terminach baterii i elektrod | **[WSTAW: lokalna skrzynka testowa portalu lub zrzut]** | 1. Wywołaj przypomnienie **[WSTAW: krok]**. 2. Otwórz wiadomość w skrzynce testowej. 3. Kliknij link jednorazowy i potwierdź. |
| Dostawcy zgłaszają się sami: akcja, zachęty | `kampania/zachety.md`, slajd 7 | 1. Otwórz plik. 2. Sprawdź trzy grupy: sprzedawcy, zarządcy, samorządy (korzyść, koszt, pokazanie w produkcie, hasło). |

### D. Akcja, logotyp i księga znaku (sekcja 2, 3 i 8)

| Wymaganie | Plik lub ekran | Kroki sprawdzenia |
|---|---|---|
| Nazwa akcji i hasło | `kampania/nazwa-i-haslo.md`; **[WSTAW: wybrana nazwa i hasło]** | 1. Otwórz plik. 2. Sprawdź wybraną nazwę i wyniki sprawdzenia kolizji. |
| Logotyp: proste i zrozumiałe, zgodne z tematem, nowoczesne, kreatywne, potencjał promocyjny | **[WSTAW: `kampania/logo/`]**; zastosowania: strona 11 księgi znaku | 1. Otwórz logo. 2. Sprawdź czytelność przy 16 px i na naklejce. 3. Sprawdź makiety: naklejka QR, odznaka, baner, pinezka. |
| Księga znaku: kolorystyka | strona 7 księgi | 1. Otwórz stronę. 2. Sprawdź HEX/RGB/CMYK/Pantone i kontrasty. |
| Księga znaku: pole ochronne | strona 5 | 1. Otwórz stronę. 2. Sprawdź rysunek z polem w jednostkach X. |
| Księga znaku: minimalna wielkość | strona 6 | 1. Otwórz stronę. 2. Sprawdź wartości w mm i px. |
| Księga znaku: niedozwolone wykorzystanie znaku | strona 10 | 1. Otwórz stronę. 2. Sprawdź listę rysunków z przekreśleniem. |
| Księga znaku: opis koncepcji 3–5 zdań | strona 2 | 1. Otwórz stronę. 2. Policz zdania (3–5). |
| Prawa autorskie i oświadczenie o autorstwie | strona 12; `docs/uzycie-ai.md` | 1. Sprawdź oświadczenie **[WSTAW]**. |

### E. Kryteria oceny (sekcja 8) – gdzie szukać dowodów

| Kryterium (waga) | Gdzie |
|---|---|
| Zgodność z zasadami działania portalu dane.gov.pl (30%) | sekcja B, wiersz „Zgodność z zasadami działania portalu”; slajd 6 |
| Logotyp i hasło (25%) | sekcja D |
| Kreatywność i innowacyjność (15%) | slajdy 4, 7; kanał sprzedawcy, QR, potwierdzenia, kompletność, zachęty |
| Zgodność z tematem wyzwania (15%) | sekcja C |
| Wzorcowy zakres danych (10%) | sekcja C, wiersz „Wzorcowy zakres danych”; `wzorzec-aed.xlsx` |
| Prezentacja (5%) | sekcja A, wiersz „Prezentacja” |

## Ścieżki jury (kroki użytkownika)

### Ścieżka 1: sprzedawca rejestruje urządzenia

1. Otwórz **[WSTAW: adres panelu firmy]** i zaloguj się kontem **[WSTAW: demo firmy]**.
2. Pobierz szablon **[WSTAW: przycisk lub plik `wzorzec-aed.xlsx`]**.
3. Wgraj plik z błędami **[WSTAW: `przyklady/blad.csv`]** i sprawdź raport walidacji (komunikaty po polsku, wiersz i pole).
4. Wgraj plik poprawny **[WSTAW: `przyklady/ok.csv`]**.
5. Sprawdź listę urządzeń: status `zgloszony`.

### Ścieżka 2: zarządca potwierdza przez QR

1. Otwórz **[WSTAW: adres strony QR dla przykładowego urządzenia]** (lub zeskanuj kod z makiety **[WSTAW: obraz]**).
2. Wpisz lokalizację (użyj „Użyj mojej lokalizacji” lub ręcznie), godziny dostępu, potwierdź stan.
3. Sprawdź komunikat potwierdzenia i zmianę statusu na `aktywny`.
4. Sprawdź w rejestrze, że rekord ma pole „kto wprowadził” i kompletność **[WSTAW: wartość]**.
5. Powtórz samą klawiaturą (Tab, Enter) i w oknie 320 px.

### Ścieżka 3: zbiór w portalu

1. Otwórz **[WSTAW: adres zbioru w portalu]**.
2. Sprawdź dostawcę zbioru (ministerstwo), opis i metadane.
3. Pobierz zasób CSV; sprawdź tylko rekordy w profilu `publikacja`.
4. Otwórz widok mapy **[WSTAW: widok „Mapy i wykresy”]**.

## Jak odtworzyć dane (opcjonalnie)

1. `[WSTAW: polecenie budowy zbioru krajowego z surowych źródeł]`
2. `[WSTAW: polecenie testów]`
3. Dane źródłowe: `datasets/raw/` (nie edytować ręcznie; manifest opisuje pochodzenie).

## Znane ograniczenia dla jury

Patrz slajd 9 i `[WSTAW: docs/ograniczenia.md]`.
