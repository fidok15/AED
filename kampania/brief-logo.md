# Brief kreatywny: logo akcji (dla osoby rysującej znak)

**Status:** dokument roboczy. Nie zawiera gotowego logo. Znak ma narysować człowiek (wymóg zadania: praca autorska zespołu, wszystkie prawa po stronie zespołu, następnie przeniesienie praw na Ministra Cyfryzacji; zasady użycia AI w `docs/uzycie-ai.md`). Poniżej trzy kierunki opisane słowami, żeby skrócić drogę do szkicu.

Nazwa akcji: **[wstaw po decyzji; rekomendacja: Opiekun AED]**, hasło: **[wstaw; rekomendacja: „Dbasz o AED? Pokaż to w danych.”]**. Patrz `kampania/nazwa-i-haslo.md`.

## 1. Zadanie w jednym akapicie

Zrobić prosty, nowoczesny, kreatywny znak o potencjale promocyjnym (kryteria z treści zadania, 25% oceny razem z hasłem), który zachęca **dostawców danych** (producentów i sprzedawców AED, zarządców, samorządy) do udostępniania danych o defibrylatorach w portalu dane.gov.pl. Znak nie służy do pitchu rozwiązania. Będzie drukowany na naklejce z kodem QR na urządzeniu, na odznace dostawcy, na banerze na stronie gminy i jako pinezka na mapie sprzedawców.

## 2. Odbiorcy i sytuacje użycia

| Odbiorca | Co ma zobaczyć | Gdzie widzi znak |
|---|---|---|
| Producent / sprzedawca AED | „Rejestruję urządzenie przy sprzedaży, jestem na liście partnerów” | pismo od Ministerstwa, panel firmy, mapa sprzedawców |
| Zarządca / właściciel | „To urządzenie jest zgłoszone, mam je potwierdzić” | naklejka z QR na szafce, e-mail z prośbą o potwierdzenie |
| Samorząd | „Moja gmina ma aktualne dane, mogę to pokazać mieszkańcom” | baner na stronie BIP / urzędu, odznaka |
| Pośrednio: ratownik, przechodzień | „Ten sygnał oznacza zgłoszone i zweryfikowane urządzenie” | naklejka na szafce |

Ton: rzeczowy, ciepły, nie alarmowy. Bez obietnic uratowanych istnień (twarda zasada 9 w `CLAUDE.md`).

## 3. Ograniczenia twarde

1. **Bez orła, bez biało-czerwonych form narodowych, bez znaku Ministerstwa w środku logo.** Logo ma stać obok znaku Ministerstwa Cyfryzacji i dane.gov.pl (pasek partnerski), nie wchodzić w jego pole ochronne i nie udawać go. Wspólna identyfikacja administracji rządowej (rozporządzenie z 30.09.2022, Dz.U. 2022 poz. 2102) opiera się na orle; pełnego tekstu i zasad współużycia z logo kampanii **nie czytano** [do sprawdzenia].
2. **Bez zmodyfikowanego znaku ISO 7010 E010.** Nie przerysowywać, nie przekolorowywać, nie dekorować znaku AED. Dopuszczalne jest nawiązanie do jego słownika (zieleń, serce, błyskawica lub linia EKG) w nowej, własnej formie. Nie układać białego serca z błyskawicą na zielonym kwadracie z krzyżykiem, bo to właśnie jest E010. Czy sam znak ISO podlega ograniczeniom licencyjnym w logo: [do sprawdzenia].
3. Tylko własnoręcznie narysowane kształty. Tekst zamieniony na krzywe w pliku głównym. Czcionki wyłącznie na otwartych licencjach (sekcja 6).
4. Bez gradientów, cieni, efektów 3D, rastrów w pliku głównym.
5. Działa czarno-biało i w negatywie (nie opiera się wyłącznie na kolorze).
6. Nie podpisuje się obietnicą medyczną ani liczbą uratowanych osób.
7. Nie kopiuje znaków istniejących w Polsce (patrz lista zajętych nazw w `kampania/nazwa-i-haslo.md`; Staying Alive: zielone serce z białym piorunem; Géo'DAE: niebieska pinezka z czerwonym EKG; Défib'Action: pismo odręczne z pomarańczowym sercem w „o” – wg `campaigns_and_branding.md`, sekcja 1, obserwacja wizualna z PDF-a prasowego).

Powód zakazu „samego serca”: w AED serce jest wszędzie („z sercem”, „porusz serce”, zielone serce Staying Alive). Wyróżnikiem tej akcji ma być **sygnał danych** (punkt, komórka tabeli, pinezka, nawias, potwierdzenie), połączony z sygnałem pierwszej pomocy.

Ponieważ ok. 20% badanych poprawnie rozpoznaje sam znak ISO AED (badanie z 2024 r., [Resuscitation Plus, DOAJ](https://doaj.org/article/42e6a62b0c174571a381ed5ac71a01f3), źródło ze snippetu), **znak bez słów jest ryzykowny**. Wymagana jest wersja z nazwą akcji (lockup).

## 4. Trzy kierunki koncepcyjne

Opisy to wskazówki dla rysującego, nie rysunki. Każdy kierunek da się zrealizować jednym kolorem.

### Kierunek A. „Pinezka z rytmem”

- **Idea kształtu:** klasyczna pinezka mapy, w której zamiast okrągłego otworu znajduje się pojedyncza linia o rytmie EKG (jeden „skok”), albo której dolne ostrze przechodzi w krótki zygzak linii EKG.
- **Co komunikuje:** „to miejsce na mapie” + „to jest urządzenie ratunkowe”. Wprost wiąże dane (położenie) z celem.
- **Przy 16 px:** zostaje sama sylwetka pinezki z jednym ostrym załamaniem w środku (grubość kreski co najmniej 2 px przy 16 px, [do sprawdzenia] w teście na ikonie przeglądarki). Zygzak z ostrza usunąć w wersji uproszczonej.
- **Na naklejce 3 cm:** pinezka może stanowić ramę/nagłówek nad kodem QR (do ok. 8 mm wysokości, [do sprawdzenia] przy próbnym druku); linia EKG jest wystarczająco gruba, żeby nie zniknąć w druku.
- **Ryzyko:** pinezka + EKG jest blisko Géo'DAE (niebieska pinezka z czerwoną linią EKG). Rysujący musi odejść od tego układu (np. pinezka pełna w kolorze, linia negatywowa, inny stosunek proporcji, brak „kropki trójbarwnej”) i udokumentować różnicę w księdze znaku.

### Kierunek B. „Serce z komórek”

- **Idea kształtu:** serce zbudowane z kwadratowych komórek siatki (jak komórki tabeli lub piksele), np. rozkład 3×3 (górny rząd: komórka, przerwa, komórka; środkowy: trzy; dolny: jedna środkowa), albo 5×5 z wyraźnym zaokrągleniem narożników. Jedna komórka może mieć inny kolor lub znak potwierdzenia (ptaszek), co symbolizuje „zweryfikowano”.
- **Co komunikuje:** dane (tabela, siatka rekordów) tworzą coś żywego; kompletność zbioru jako „wypełnianie” serca. Wskaźnik kompletności rekordu (0–100) z `CLAUDE.md` można pokazać jako stopień wypełnienia komórek (wariant dla ekranu, opcjonalny).
- **Przy 16 px:** wersja 3×3 (komórka około 4 px z przerwą 1 px) pozostaje czytelna jako serce; wersja 5×5 jest zbyt drobna i nie wchodzi do favicony.
- **Na naklejce 3 cm:** forma blokowa, dobrze reprodukuje się w druku jednobarwnym i obok kodu QR (kwadratowe moduły harmonizują z QR, ale trzeba upewnić się, że nie zakłócają skanowania: znak poza strefą ciszy kodu, [do sprawdzenia] próbny skan).
- **Ryzyko:** serce z pikseli to częsty motyw „heart + tech”; wyróżnik trzeba zbudować przez sposób podziału (np. przesunięta jedna komórka) i kolor.

### Kierunek C. „Pieczęć potwierdzenia” (pierścień i punkt)

- **Idea kształtu:** punkt otoczony jednym lub dwoma koncentrycznymi pierścieniami, z których jeden jest przerwany (jak sygnał rozchodzący się z punktu i jak pieczęć), przerwa w pierścieniu formuje ptaszek lub ostrze pinezki. Opcjonalnie punkt w środku to maleńki kwadrat (komórka danych).
- **Co komunikuje:** „tu jest punkt, który ktoś potwierdził”; przekaz o odpowiedzialności zarządcy (potwierdzenie przez skan QR) i o cykliczności (kolejne pierścienie = kolejne potwierdzenia, np. lata).
- **Przy 16 px:** najodporniejszy ze wszystkich: pierścień i punkt przeżywają redukcję; wystarczy jeden pierścień (grubość 2 px).
- **Na naklejce 3 cm:** pasuje jako okrągła odznaka „potwierdzone” obok lub zamiast QR na małym urządzeniu; sprawdza się też jako stempel z rokiem potwierdzenia w środku.
- **Ryzyko:** abstrakcyjny; bez kontekstu nie kojarzy się z AED. Rysujący musi dodać wyraźny sygnał pierwszej pomocy (np. subtelne wcięcie w kształt serca lub linia EKG w przerwie pierścienia) albo opierać się na lockupie z nazwą.

### Skrót porównawczy

| | A pinezka z rytmem | B serce z komórek | C pieczęć potwierdzenia |
|---|---|---|---|
| Czytelność „to AED / pierwsza pomoc” | wysoka | średnia | niska bez lockupu |
| Czytelność „to dane / lokalizacja” | wysoka | średnia | wysoka |
| Odporność na 16 px | średnia | średnia (tylko 3×3) | wysoka |
| Ryzyko podobieństwa do istniejących znaków | wysokie (Géo'DAE) | średnie | niskie |
| Rozbudowa w system (pin, odznaka, wskaźnik) | pin, baner | wskaźnik kompletności | odznaka z rokiem |

Rekomendacja robocza do szkiców: **zacząć od C i B**, A dorysować jako wariant pinezki do mapy sprzedawców. Decyzja należy do osoby rysującej i zespołu.

## 5. Paleta kolorów – propozycja (kontrasty obliczone)

Kontrast WCAG 2.x liczony ze wzoru z definicji luminancji względnej (skrypt w sesji, wartości zaokrąglone do 0,01). Progi: tekst normalny 4,5:1, duży tekst i elementy graficzne 3:1 (kryteria 1.4.3 i 1.4.11, [do sprawdzenia] na https://www.w3.org/TR/WCAG22/; logotypy są z 1.4.3 wyłączone, ale paletę stosujemy też w interfejsie).

| Rola | Nazwa | HEX | Uwagi |
|---|---|---|---|
| Główny | Zieleń pierwszej pomocy | `#0B6E4F` | zieleń nawiązuje do oznaczeń AED, ale celowo ciemniejsza i nie jest „zielenią ISO” (wartości zieleni bezpieczeństwa z ISO 3864 nie sprawdzono, nie powoływać się na nią) |
| Podstawowy ciemny | Granat | `#14274E` | tekst, wersja mono ciemna |
| Akcent | Bursztyn | `#F28C28` | tylko elementy graficzne i duże napisy, **nie** tekst na bieli |
| Tło jasne | Mięta | `#E6F4EC` | tło odznak i banerów |
| Neutralny tekst | Szary | `#5B6770` | opisy, podpisy |
| Neutralny ciemny | Grafit | `#0D1B1E` | czerń zastępcza dla druku |
| Tło / negatyw | Biel | `#FFFFFF` | |

Czerwień celowo pominięta: koliduje z czerwienią znaku państwowego obok i kojarzy się z zakazem lub pożarem; zieleń + granat + bursztyn wyróżniają akcję na tle zielono-czerwonych znaków AED (wnioski z `campaigns_and_branding.md`, sekcja 4, jako rozumowanie, nie ustalenie).

### Obliczone współczynniki kontrastu

| Para (przód / tło) | Współczynnik | Wniosek |
|---|---|---|
| Zieleń `#0B6E4F` / biel | 6,25:1 | AA dla tekstu (≥4,5) |
| Granat `#14274E` / biel | 14,69:1 | AAA |
| Granat `#14274E` / mięta `#E6F4EC` | 12,95:1 | AAA |
| Zieleń `#0B6E4F` / mięta `#E6F4EC` | 5,51:1 | AA dla tekstu |
| Szary `#5B6770` / biel | 5,80:1 | AA dla tekstu |
| Szary `#5B6770` / jasny `#F3F5F4` | 5,30:1 | AA dla tekstu |
| Bursztyn `#F28C28` / granat `#14274E` | 5,98:1 | AA dla tekstu na granacie |
| Bursztyn `#F28C28` / grafit `#0D1B1E` | 7,18:1 | AAA |
| Bursztyn `#F28C28` / biel | 2,45:1 | **poniżej 3:1**: nie używać do tekstu ani samotnego znaku na bieli; tylko z obrysem/obwódką lub na ciemnym tle |
| Biel / grafit `#0D1B1E` | 17,61:1 | AAA (negatyw) |
| Zieleń `#0B6E4F` / granat `#14274E` | 2,35:1 | **nie stykać** zieleni z granatem bez białego odstępu |
| Zieleń `#0B6E4F` / bursztyn `#F28C28` | 2,55:1 | **nie stykać** bez białego odstępu |
| Żółty `#FFC53D` / granat `#14274E` | 9,31:1 | alternatywny akcent na ciemnym tle (jeśli bursztyn nie działa w druku) |
| Żółty `#FFC53D` / biel | 1,58:1 | nie używać na bieli |

Wartości CMYK, Pantone, RGB do druku: **[wstaw po kalibracji próbnego wydruku naklejki; nie podawać przeliczeń z HEX bez sprawdzenia]**.

## 6. Typografia – propozycje (wyłącznie otwarte licencje)

| Rola | Krój | Licencja | Uwagi |
|---|---|---|---|
| Logotyp (napis akcji) | Lexend (Google Fonts) | SIL Open Font License 1.1 | zaprojektowany pod czytelność; użyty też w materiałach Défib'Action 2026 (wg metadanych PDF-a, `campaigns_and_branding.md`) |
| Tekst, interfejs | Atkinson Hyperlegible (Braille Institute) | SIL Open Font License 1.1 | projektowany pod słabowidzenie, dobry dla WCAG |
| Alternatywa uniwersalna | Inter lub Source Sans 3 | SIL Open Font License 1.1 | pełne polskie znaki |

Licencje podane z pamięci i potwierdzone jedynie dla Lexend w kontekście materiałów kampanii; **[do sprawdzenia]** na stronach źródłowych kroju (https://fonts.google.com, https://github.com/googlefonts/atkinson-hyperlegible) oraz obecność wszystkich polskich znaków (ą ć ę ł ń ó ś ź ż) przed użyciem. W logotypie napis zamienić na krzywe, w księdze znaku podać nazwę kroju i licencję.

## 7. Wymagany zestaw plików

| Plik | Format | Uwagi |
|---|---|---|
| Logo główne (kolor, lockup poziomy: znak + nazwa + hasło) | `.svg` | źródło główne, tekst na krzywych, bez rastrów |
| Logo główne | `.png` | przezroczyste tło, min. 2000 px dłuższego boku |
| Logo główne | `.jpg` | na białym tle |
| Logo główne | `.pdf` | wektorowy |
| Sygnet (sam znak) | `.svg`, `.png`, `.pdf` | do favikony, pinezki, odznaki |
| Księga znaku | `.pdf` | na bazie `kampania/ksiega-znaku-szablon.md` |

Zadanie wymaga co najmniej: `.jpg`, `.png`, `.pdf` i jednego formatu otwartego (`.svg` spełnia ten warunek) oraz księgi znaku w `.pdf`.

### Wymagane warianty (każdy w pełnym zestawie formatów)

1. kolorowy na jasnym tle,
2. kolorowy na ciemnym tle (granat lub grafit),
3. jednobarwny czarny (grafit),
4. jednobarwny biały (negatyw, na tło ciemne lub kolor),
5. sygnet bez napisu (do 16–24 px),
6. lockup pionowy i poziomy,
7. wariant do naklejki (znak w układzie z kodem QR).

Nazwy plików: `[nazwa-akcji]_logo_poziome_kolor.svg`, `..._mono-czarne.svg`, `..._negatyw.svg`, `..._sygnet.svg` (bez polskich znaków).

## 7a. Wymagania testowe dla gotowego znaku

- czytelny w skali szarości i jednobarwnie (druk jednokolorowy),
- test na 16 px i 24 px (favicona, pinezka),
- test 3 cm (naklejka): próbny wydruk z kodem QR i skanowanie telefonem w różnych warunkach światła [do sprawdzenia]; strefa ciszy kodu QR nie może być naruszana przez znak,
- test negatywu na kolorze `#14274E` i `#0D1B1E`,
- test obok znaków Ministerstwa Cyfryzacji i dane.gov.pl w układzie paska partnerskiego (pliki tych znaków: [do sprawdzenia, pozyskać u organizatora]).

## 8. Czego brakuje do decyzji (pytania do człowieka)

1. Wybór nazwy i hasła (patrz `nazwa-i-haslo.md`).
2. Czy sygnet ma zawierać słowo „AED”, czy tylko lockup.
3. Rozmiar naklejki: „3 cm” z zadania to średnica odznaki czy cała naklejka z QR? Przy kodzie QR 3 cm jest bardzo mało miejsca na znak [do sprawdzenia].
4. Narzędzie do rysowania (np. Inkscape lub Penpot, oba otwarte; **nie zweryfikowano** w tej sesji ich funkcji eksportu, [do sprawdzenia]) oraz osoba odpowiedzialna za oświadczenie o autorstwie i przeniesieniu praw.
