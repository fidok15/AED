# Prezentacja – konspekt

Plik prezentacji: **`docs/prezentacja/misja-aed.pptx`, 14 slajdów**. Treść slajdów (punkty, podpisy, notatki mówcy) jest tylko w `docs/prezentacja/slajdy.json`; plik PPTX powstaje z niej poleceniem `uv run --with python-pptx python scripts/build_presentation.py`. Ten konspekt nie powtarza treści, żeby nie rozjechała się z plikiem.

Wymóg zadania (rozdział 4): min. 5 slajdów z dowodami realizacji wymagań technicznych (zrzuty ekranu), opis funkcjonalności z krokami użytkownika, lista ograniczeń.

Narracja: **problem (dane rozproszone, bez odpowiedzialnego) → odpowiedź w mechanice portalu: wykaz AED wzorem DGA → jeden standard → kanał sprzedawcy i QR (odpowiedzialny podmiot) → wynik → zachęty i kampania → ograniczenia → co dalej.**

Zasady:

- Liczby wstawia generator z `datasets/out/raport.json`, `aed_standard/schema.json` i `datasets/out/aed_dane_gov_pl.csv` (pola `{…}` w `slajdy.json`; lista: `--liczby`). W tekście nie wpisujemy liczb z raportu na sztywno (zasada 10). Wyjątek: liczby ze zrzutów ekranu mają dopisek „w chwili zrzutu” z datą.
- Każda liczba ma etykietę zakresu: **rejestr z mappera** (`raport.json`), **widok publiczny usługi** (bez rekordów z dostępem prywatnym, z urządzeniami demo), **eksport do publikacji** (`aed_dane_gov_pl.csv`).
- Status wdrożenia: pełny fork portalu uruchomiony lokalnie (także próbnie pod `aed.localhost`); serwera publicznego nie ma. Scalanie sprawdzone ręcznym uruchomieniem zadania; harmonogram 03:45 skonfigurowany, niesprawdzony.
- Bez obietnic uratowanych istnień (zasada 9). Bez pól zastępczych poza logo i nazwą akcji (projektuje zespół).

## Slajdy

| # | Sekcja | Dowody na slajdzie |
|---|---|---|
| 1 | Tytuł (tytuł roboczy; „Misja AED – Dane na ratunek” to nazwa zadania konkursowego) | `docs/zrzuty/portal-01-zbior-zbiorczy.png`; miejsce na logo |
| 2 | Problem | `frontend/aed-zrzuty/04-panel-ministerstwa.jpg` (widok usługi) |
| 3 | Pomiar istniejących danych | tabela pokrycia pól z `raport.json` |
| 4 | Rozwiązanie: dwa kanały, jeden standard | schemat |
| 5 | Wykaz w portalu wzorem DGA | schemat DGA → AED; `portal-02-formularz-wykaz-aed.png` |
| 6 | Wykaz w działaniu (kroki użytkownika) | `portal-03`, `-04`, `-05`, `-06`, `-07`, `-08` |
| 7 | Standard danych i wzorzec XLSX | `docs/zrzuty/wzorzec-slownik-pol.png` (render arkusza, nie zrzut z Excela); `09-raport-walidacji-bledy.jpg` |
| 8 | Kanał sprzedawcy i QR (kroki użytkownika) | `11-naklejka.jpg`, `05-`, `18-`, `14-qr-…-telefon.jpg` |
| 9 | Mapper i deduplikacja | wykres powodów wykluczenia z `raport.json`; `03-rejestr-mapa.jpg` |
| 10 | Zachęty i kampania | `06-ranking-firm.jpg`; miejsce na logo i hasło |
| 11 | Dostępność | `320px-qr-dysponent.jpg`, `kontrast-black-yellow-rejestr.jpg` |
| 12 | Ograniczenia | lista |
| 13 | Co dalej | lista |
| 14 | Użycie AI i prawa | tabela z `docs/uzycie-ai.md` |

## Zrzuty z portalu (`docs/zrzuty/`)

Ekrany przeglądarki z lokalnego pełnego stosu forka (22.11): `portal-01`, `-02`, `-03`, `-06`, `-07`, `-08`, `-10`, `-11`, `-12` (skrzynka testowa MailHog). `portal-04` i `-05` to wyjście terminala wyrenderowane do PNG. `portal-09` (harvester XML) nie powstał – pełnego importu harvesterem nie uruchomiono.

| Plik | Co | Slajd |
|---|---|---|
| `portal-01-zbior-zbiorczy.png` | strona zbioru „Krajowy wykaz defibrylatorów AED – wykaz zbiorczy” we frontendzie forka | 1 |
| `portal-02-formularz-wykaz-aed.png` | formularz zasobu w panelu z polem „Wykaz AED” | 5 |
| `portal-03-bledy-wykazu-krosno.png` | błędy po polsku po wgraniu pliku z Krosna | 6 |
| `portal-04-dry-run-raport.png` | `create_main_aed_resource --dry-run` (terminal) | 6 |
| `portal-05-aed-aggregated.png` | `GET /aed-aggregated` (terminal) | 6 |
| `portal-06-tabela.png` | tabela zasobu zbiorczego | 6 |
| `portal-07-mapa.png` | mapa zasobu zbiorczego | 6 |
| `portal-08-api-i-otwartosc.png` | poziom otwartości, CSV, JSON, API | 6 |
| `portal-10-aed-aggregated-przegladarka.png` | `GET /aed-aggregated` w przeglądarce | – (instrukcja dla jury) |
| `portal-11-typy-kolumn.png` | zakładka „Zmiana typu” zwykłego zasobu CSV | – (instrukcja dla jury) |
| `portal-12-mail-odrzucony-wykaz.png` | e-mail do dostawcy o odrzuconym wykazie (MailHog) | – (instrukcja dla jury) |
