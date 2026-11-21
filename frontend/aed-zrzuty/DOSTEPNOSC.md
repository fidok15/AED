# Dostępność obszaru AED – co sprawdzono

Stan na 21.11.2026, serwer deweloperski `http://localhost:4200`, usługa AED na porcie 8085 z danymi demonstracyjnymi.
Zakres: strony obszaru AED (`/pl/aed/...`) i pasek prototypu. Nagłówek i stopka portalu należą do forka dane.gov.pl i nie były poprawiane.

## Narzędzia

| Co | Czym |
|---|---|
| Test automatyczny | axe-core 4.10.2, reguły WCAG 2.0 A/AA, 2.1 A/AA i 2.2 AA |
| Przeglądarka | Chromium 157 sterowany przez Playwright |
| Klawiatura | skrypt Playwright naciskający wyłącznie klawisze (Tab, Shift+Tab, Enter, spacja, strzałki, Escape) |
| Układ | okno 320 px oraz 640 px, czyli powiększenie 200% okna 1280 px |
| Kontrast | trzy tryby wysokiego kontrastu portalu (klasy `black-white`, `black-yellow`, `yellow-black` na `<body>`) |

Nie użyto czytnika ekranu ani prawdziwego telefonu – patrz „Co zostało”.

## Wyniki axe według widoku

Liczba naruszeń w obszarze AED przed poprawkami i po nich. Pełne wyniki: `axe-4.10.2-przed-poprawkami.json` i `axe-4.10.2-po-poprawkach.json` (klucz `obszarAed` – nasz kod, `calaStrona` – razem z nagłówkiem i stopką portalu).

| Widok | Adres | Przed | Po |
|---|---|---|---|
| Start ze ścieżkami | `/pl/aed` | 0 | 0 |
| Rejestr: lista i mapa | `/pl/aed/registry` | 1 | 0 |
| Ranking firm | `/pl/aed/sellers` | 0 | 0 |
| Panel firmy, po zalogowaniu | `/pl/aed/company` | 0 | 0 |
| Arkusz naklejek | `/pl/aed/company/stickers` | 0 | 0 |
| Formularz urządzenia z błędami | `/pl/aed/company/device` | 0 | 0 |
| Strona z naklejki – dysponent, z błędami | `/pl/aed/qr/{id}?t=…` | 0 | 0 |
| Strona z naklejki – bez uprawnień | `/pl/aed/qr/{id}` | 0 | 0 |
| Panel ministerstwa, po zalogowaniu | `/pl/aed/ministry` | 0 | 0 |

Jedyne naruszenie: `target-size` (WCAG 2.5.8) – odnośnik stronicowania z komponentu portalu miał 23 × 28 px.

Pozycje „do ręcznej oceny” (`color-contrast`, od 1 do 8 elementów na formularzach) to teksty błędów i podpowiedzi z ikoną w tle. Kolory pochodzą z tokenów w `aed.scss`: tekst błędu `#a91e2c` i tekst pomocniczy `#5e5e5e` na białym lub jasnoszarym tle – oba powyżej 4,5:1.

Naruszenia poza obszarem AED, obecne na każdej stronie portalu: `aria-required-parent` (24), `listitem` (19), `aria-required-children` (3), `aria-allowed-attr` (1), `aria-progressbar-name` (1). Dotyczą stopki z CMS, menu „Więcej” i paska postępu forka.

## Przejście samą klawiaturą

Ścieżka firma → naklejka → dysponent, wszystko na danych demonstracyjnych:

1. Panel firmy: 26 naciśnięć Tab przez nagłówek portalu (portal ma na początku odnośnik „Przejdź do treści”), potem nawigacja AED, pola logowania, „Zaloguj się”, „Wypełnij”. Enter na „Wypełnij”, Shift+Tab, Enter na „Zaloguj się”. Fokus trafia na wiersz „Zalogowano: …”.
2. Tab do pola pliku, Enter otwiera systemowy wybór pliku. Po wybraniu `przyklad-sprzedawca-bledy.csv` pojawia się raport: 10 wierszy, 2 poprawne, 8 do poprawy; tabela błędów jest przewijalnym regionem z fokusem.
3. Ponowny wybór pliku (poprawny, 3 urządzenia), Tab do „Wyślij zgłoszenie”, Enter. Fokus trafia na nagłówek „Zgłoszenie wysłane”.
4. Tab do „Otwórz arkusz naklejek do wydruku (3)”, Enter – arkusz z trzema naklejkami, Tab do „Drukuj naklejki”.
5. Strona dysponenta (okno 390 px): Tab do „Użyj lokalizacji telefonu”, Enter – położenie zapisane. Dalej Tab przez pola; wpisane nazwa, miejscowość i opis; spacja na „tak”, „Publiczny”, „Jest na miejscu…”; strzałka w dół przełącza godziny na „W wybranych dniach i godzinach”, spacja zaznacza sobotę. Enter na „Potwierdź dane” – ekran „Dane potwierdzone”, fokus na jego nagłówku, rekord ma status `aktywny`.

Na każdym elemencie interaktywnym w obszarze AED był widoczny obrys fokusu. Nagłówki i wiersze, na które fokus przenosi kod (wynik logowania, wysłania, potwierdzenia), obrysu celowo nie mają. Na stronie dysponenta żadne pole z fokusem nie chowało się pod przyklejonym paskiem z przyciskiem (pomiar położenia po przewinięciu, 9 kolejnych pól).

Mapa rejestru:

1. Tab na mapę, Tab na grupę „686 urządzeń w tym miejscu mapy – przybliż”, Enter przybliża, fokus zostaje na mapie.
2. Tab do znacznika urządzenia (65 naciśnięć – po drodze są inne grupy), Enter otwiera opis z tekstem: nazwa, status, dostęp, godziny, dostępność teraz, kompletność, identyfikator. Fokus przechodzi do opisu.
3. Escape zamyka opis, fokus wraca na mapę; plus i strzałki zmieniają widok.

Panel ministerstwa: po „Pomiń tę parę” i „Uruchom przypomnienia” fokus zostaje na użytym przycisku. „To samo urządzenie – połącz” uruchomiono klawiszem Enter raz, jeszcze przed tą poprawką (fokus wtedy przepadał); po poprawce nie klikano go ponownie, żeby nie łączyć kolejnej pary – korzysta z tego samego mechanizmu.

## 320 px i powiększenie 200%

Dziewięć widoków z tabeli w oknie 320 px i 640 px: strona nie przewija się w poziomie i żaden element obszaru AED nie wychodzi poza krawędź. Wyjątkiem z założenia są przewijalne regiony tabel (raport błędów, porównanie duplikatów, ranking, historia zadań) i sama mapa. Zrzuty: `320px-*.jpg`.

## Tryby wysokiego kontrastu portalu

Rejestr, panel ministerstwa i strona dysponenta w trzech trybach – dziewięć zrzutów `kontrast-*.jpg`. Trzy z nich obejrzano w całości (rejestr czarno-żółty, strona dysponenta żółto-czarna, panel ministerstwa czarno-biały): tekst, obramowania, przyciski i znaki statusu przejmują kolory trybu. Tryby włączano klasą na `<body>`, a nie przyciskami portalu, dlatego na zrzutach nagłówek portalu nie jest w pełni przełączony. Pasek prototypu celowo zostaje żółto-czarny we wszystkich trybach.

## Co poprawiono w tej rundzie

- Odnośniki stronicowania w rejestrze mają co najmniej 44 × 44 px (tylko w obszarze AED, bez zmiany komponentu portalu).
- Po zalogowaniu, wysłaniu zgłoszenia i zgłoszeniu jednego urządzenia fokus przechodzi na wynik; wcześniej wracał na początek strony.
- Przyciski w trakcie działania nie są wyłączane atrybutem `disabled` (przeglądarka zabierała im fokus), tylko oznaczane `aria-disabled` i ignorują ponowne użycie.
- Mapa: znacznik z fokusem nie przesuwa już mapy (przesunięcie odrysowywało znaczniki i gubiło fokus, przez co do znaczników urządzeń nie dało się dojść klawiszem Tab); po przybliżeniu grupy i po zamknięciu opisu fokus wraca na mapę; opis zamyka się klawiszem Escape także wtedy, gdy fokus jest w opisie; pod filtrem jest opis obsługi klawiaturą.
- Wskaźnik kompletności ma obrys, więc w trybach wysokiego kontrastu widać, jaka część jest wypełniona.
- Odnośniki „Naklejka z kodem QR” i „Strona potwierdzenia dla dysponenta” mają w nazwie identyfikator urządzenia (dla czytników ekranu), bo na liście powtarzały się bez rozróżnienia.

## Co zostało

- Nie sprawdzono czytnikiem ekranu (VoiceOver, NVDA) ani na prawdziwym telefonie; geolokalizacja była podstawiona przez przeglądarkę testową.
- Na mapie do znacznika urządzenia prowadzi wiele naciśnięć Tab, gdy w widoku jest dużo grup. Pełnoprawną drogą dla klawiatury i czytnika pozostaje lista nad mapą.
- Filtr „dostępny teraz” działa tylko na mapie; lista podaje ten stan w każdym wierszu, ale nie filtruje po nim.
- W wysokim kontraście pasek udziału statusów nad filtrem rejestru jest jednobarwny. Jest ozdobnikiem ukrytym przed czytnikami; te same liczby są w filtrze pod nim.
- Naruszenia w nagłówku i stopce portalu (lista wyżej) wymagają zmian w kodzie forka i treściach CMS.
- Teksty obszaru AED są tylko po polsku; w angielskiej wersji portalu obszar ma ustawiony `lang="pl"`.
