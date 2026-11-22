## A. Ocena ekranów

1. **Start — do poprawy.** Umieść nad instrukcją demonstracyjną główny przycisk „Znajdź najbliższy AED”, prowadzący do sekcji wyszukiwania w rejestrze.
2. **Potwierdzenie przez dysponenta po zeskanowaniu QR, 390 px — do poprawy.** W pierwszym kroku zastąp przyklejone „Potwierdź dane” przyciskiem „Dalej” i pokaż „Potwierdź dane AED” dopiero po przejściu wszystkich trzech kroków. Przewijanie musi pozwalać odsłonić każde pole także po przeniesieniu na nie fokusu.
3. **Rejestr, lista i mapa — do poprawy.** W wynikach wyróżnij „Wyznacz trasę”, a kompletność rekordu przenieś do szczegółów. Obecnie pasek procentowy konkuruje z działaniem potrzebnym użytkownikowi.
4. **Mapa kraju — dobrze.** Zachowaj czytelne granatowe klastry i dodaj nad mapą krótką instrukcję „Liczba na mapie oznacza grupę urządzeń. Wybierz grupę, aby przybliżyć mapę”.
5. **Najbliższe AED, 390 px — do poprawy.** Wyróżnij dostępność bezpośrednio pod nazwą i odległością. Pierwszy wynik jest oddalony o 107 m, ale z rejestru nie wynika, czy można teraz wejść do budynku.
6. **Zakładki, 320 px — słabo.** Zastąp przewijaną nawigację modułu przyciskiem „Sekcje AED”, który pokazuje wszystkie pięć pozycji i wskazuje bieżącą. Na zrzucie widać trzy pozycje i brakuje wyraźnej wskazówki, że są kolejne.
7. **Ranking firm z mapą — do poprawy.** Pokaż nazwę firmy po wybraniu znacznika zarówno kliknięciem, jak i klawiaturą. Sama litera i objaśnienie nad mapą utrudniają powiązanie siedziby z rankingiem.
8. **Wynik konwertera — słabo.** Pokaż nad pobraniem, że plik zawiera odrzucony wiersz, i usuń podpowiedź zamiany niejednoznacznej daty „03/04/2028” na konkretny dzień bez potwierdzenia.
9. **Formularz administracyjny, pole „Wykaz AED” — do poprawy.** Zastosuj dwa wzajemnie wykluczające się przyciski radiowe „Tak” i „Nie”. Obecne pola wyglądają jak niezależne checkboxy.
10. **Błędy walidacji w panelu — słabo.** Pokaż nad formularzem komunikat „Nie zapisano wykazu AED” z linkiem do pola i krótką listą wymaganych poprawek. Czerwony blok w środku długiego formularza łatwo przeoczyć.
11. **Mapa krajowego wykazu w portalu — dobrze.** Dodaj krótkie objaśnienie pod zakładkami, czego dotyczą liczby w klastrach i jak przejść od grupy do urządzenia.
12. **E-mail o odrzuconym wykazie — do poprawy.** Dodaj przed tabelą błędów link „Otwórz zasób i popraw plik CSV”, prowadzący do edycji konkretnego zasobu.

## B. 10 poprawek według wpływu na wrażenie jurora

1. **Pokaż wartość modułu na pierwszym ekranie — S.** Pod tytułem umieść przycisk „Znajdź najbliższy AED”, a trzy kroki demonstracyjne zgrupuj niżej pod nagłówkiem „Jak urządzenie trafia do rejestru”.
2. **Uczyń pierwszy wynik na telefonie możliwym do oceny jednym spojrzeniem — M.** Ułóż go w kolejności: miejsce, odległość w linii prostej, dostępność teraz, „Wyznacz trasę”. Identyfikator i kompletność przenieś do szczegółów.
3. **Dopasuj główną akcję QR do etapu — M.** W krokach 1 i 2 pokaż „Dalej”, w kroku 3 „Potwierdź dane AED”. Zapewnij miejsce pod ostatnim polem i sprawdź, czy pasek akcji nie zasłania fokusu przy nawigacji klawiaturą. Zrzut statyczny nie rozstrzyga zgodności z WCAG 2.2 AA w tym zakresie.
4. **Odsłoń wszystkie sekcje przy szerokości 320 px — M.** Wprowadź rozwijane „Sekcje AED” z nazwą bieżącej sekcji i pięcioma linkami łamiącymi się w obrębie ekranu. Sprawdź kolejność fokusu i aktywną pozycję przy obsłudze klawiaturą.
5. **Pokaż wynik konwersji językiem decyzji — S.** Nad przyciskiem pobrania umieść „2 z 3 wierszy przeszły sprawdzenie. Plik nadal zawiera 1 odrzucony wiersz”. Przy niejednoznacznej dacie poproś o sprawdzenie jej w danych źródłowych.
6. **Pokaż odrzucenie po zapisie w miejscu, gdzie administrator go oczekuje — M.** Dodaj na górze formularza „Nie zapisano wykazu AED”, link do pola oraz pogrupowane komunikaty „Brak wymaganych kolumn” i „Kolumny spoza standardu”. Podawaj konkretne nazwy nagłówków do dodania lub zmiany.
7. **Ujednolić obsługę klastrów na obu mapach urządzeń — M.** Użyj tego samego granatowego stylu i tej samej akcji przybliżenia. Zadbaj o widoczny fokus i nazwę dostępną w rodzaju „739 urządzeń. Przybliż mapę”. Z obrazu można ocenić wygląd klastrów, a obsługę klawiaturą i nazwy trzeba sprawdzić w działającym interfejsie.
8. **Rozróżnij potwierdzenie danych od dostępności urządzenia — S.** Oznacz te informacje osobno jako „Status danych” i „Dostępność teraz”. Przy braku godzin pokaż „Nie wiadomo, czy AED jest teraz dostępny” także wtedy, gdy dostęp jest publiczny.
9. **Uczyń ustawienie „Wykaz AED” jednoznacznym — S.** Zmień checkboxy na grupę radiową i skróć opis do „Wybierz «Tak», jeśli plik jest wykazem AED zgodnym ze standardem. Portal sprawdzi go przy zapisie”.
10. **Zamknij ścieżkę naprawy w e-mailu — S.** Zacznij od „Odrzucono 21 z 21 wierszy. Żadne urządzenie z tego pliku nie trafiło do krajowego wykazu AED”, a zaraz pod spodem umieść link do edycji zasobu.

## C. Mikrocopy

| Ekran | Jest → powinno być |
|---|---|
| 1. Start | „Dysponent potwierdza urządzenie z naklejki” → „Opiekun AED potwierdza dane urządzenia po otwarciu linku”. |
| 2. QR | „Data ważności elektrod: 2026-12-20 – termin bliski.” → „Elektrody są ważne do 20 grudnia 2026 r.” |
| 2. QR | „Potwierdź dane” → „Dalej” w krokach 1 i 2 oraz „Potwierdź dane AED” w kroku 3. |
| 3. Rejestr | „Pokaż urządzenia o statusie” → „Filtruj według statusu danych”. |
| 3 i 5. Lista | „Dostępność nieznana” → „Nie wiadomo, czy AED jest teraz dostępny”. |
| 4. Mapa kraju | „Urządzenia w widocznym obszarze mapy: 15 777.” → „W tym obszarze mapy jest 15 777 urządzeń”. |
| 5. Najbliższe AED | „Odległość liczona od: Twojej lokalizacji (w linii prostej, nie wzdłuż drogi).” → „Podajemy odległość od Ciebie w linii prostej”. |
| 7. Ranking | „Te same firmy co na liście powyżej. Firma to biały kwadrat z pierwszą literą nazwy; zielony znak ✓ w rogu oznacza firmę z odznaką.” → „Wybierz znacznik, aby zobaczyć nazwę firmy. Zielony znak ✓ oznacza firmę z odznaką”. |
| 8. Konwerter | „Wykaz jest częściowo zgodny ze standardem” → „2 z 3 wierszy przeszły sprawdzenie”. |
| 8. Konwerter | „Otrzymano: „03/04/2028”. Zamień na 2028-04-03.” → „Sprawdź, czy chodzi o 3 kwietnia czy 4 marca 2028 r. Wpisz właściwą datę w formacie RRRR-MM-DD”. |
| 10. Walidacja | „Brakuje kolumny „miejscowosc” wymaganej w profilu publikacja. Dodaj ją do nagłówka.” → „Dodaj kolumnę „miejscowosc” w pierwszym wierszu pliku CSV”. |
| 12. E-mail | „Wykaz AED odrzucony przy scalaniu” → „Wykaz AED nie trafił do krajowego rejestru”. |

## D. Pierwsze 30 sekund demo

- **0–10 s.** Zacznij od mobilnej listy z ustawioną lokalizacją demonstracyjną. Powiedz „Szukam AED. Najbliższy jest 107 metrów stąd w linii prostej. Rejestr pokazuje, czy wiemy, że jest teraz dostępny”. Wskaż dostępność i „Wyznacz trasę”.
- **10–20 s.** Otwórz na telefonie link dla opiekuna z demonstracyjnego zgłoszenia. Pokaż „Użyj lokalizacji telefonu” i powiedz „Tak opiekun potwierdza, gdzie rzeczywiście znajduje się urządzenie”.
- **20–30 s.** Pokaż wcześniej przygotowany, potwierdzony rekord tego samego AED na mapie. Wskaż status i godziny dostępu. Na jednym urządzeniu połącz wyszukanie, aktualizację danych przez opiekuna i efekt widoczny w rejestrze.