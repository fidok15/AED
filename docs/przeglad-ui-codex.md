# Przegląd UI/UX – Codex (22.11.2026, ok. 02:15)

Jedno uruchomienie na 9 zrzutach ekranu (`docs/zrzuty/`, `frontend/aed-zrzuty/`), bez czytania kodu i bez klikania aplikacji; ok. 37 tys. tokenów. Zrzut rejestru pochodzi sprzed dodania filtra „Dostępny teraz” do listy, więc pierwsza uwaga jest już częściowo zrealizowana (filtr jest, sortowania po odległości nie ma). Uwagi nie były weryfikowane w aplikacji – to lista do wyboru, nie lista zadań.

## A. Uwagi do interfejsu

1. Rejestr – lista nie pokazuje, który AED jest najbliżej, a filtr dostępności działa tylko na mapie – nad listą dodaj wspólny filtr „Dostępny teraz”, pole lokalizacji i przycisk „Użyj mojej lokalizacji”; po wskazaniu punktu sortuj listę po odległości i pokaż ją przy nazwie – L.
2. Potwierdzenie po QR – przyklejony przycisk zasłania pola i ich opisy – dodaj dolny odstęp formularza równy wysokości paska z `safe-area-inset-bottom` oraz `scroll-padding-bottom`, żeby przewijanie do pola z fokusem lub błędem odsłaniało je w całości – S.
3. Potwierdzenie po QR – opcjonalne daty baterii i elektrod odsuwają pierwszy wymagany krok o kilka ekranów – przenieś edycję dat pod krok 3, a ostrzeżenie o terminie pokaż w jednej krótkiej linii w karcie urządzenia – S.
4. Rejestr przy 320 px – zakładki zajmują trzy rzędy i spychają tytuł poza pierwszy ekran – poniżej 480 px zastąp zakładki przyciskiem z nazwą bieżącej sekcji i rozwijaną listą sekcji; etykietę „prototyp” usuń z tego wiersza, bo informacja jest w żółtym banerze – M.
5. Rejestr – „Dostępny teraz” przy niepotwierdzonym urządzeniu może wyglądać jak potwierdzenie jego gotowości – umieść status przy nazwie, a pod godzinami pokaż „Według harmonogramu: dostępny teraz”; kompletność danych przenieś do szczegółów rekordu – S.
6. Panel firmy i konwerter – długie tabele błędów ściskają instrukcje, szczególnie na telefonie – poniżej 640 px ułóż każdy błąd pionowo: numer wiersza i typ u góry, pole i poprawka poniżej; zachowaj czytelne etykiety oraz powiązania semantyczne – M.
7. Panel ministerstwa – długa tabela duplikatów rozdziela porównanie od decyzji – pokaż domyślnie różniące się pola, dodaj „Pokaż wszystkie pola”, a pod tabelą umieść pasek decyzji z zawijaniem przycisków na wąskich ekranach – M.
8. Konwerter – przy przypisywaniu kolumn trzeba jednocześnie śledzić trzy szerokie kolumny tabeli – na wąskich ekranach ułóż nazwę kolumny, pole wyboru i zwijane próbki wartości pionowo; zastosuj `min-width: 0` i zawijanie długich wartości – M.

## B. Mapa

1. **Znaczniki.** Aktywny – zielona pinezka z haczykiem. Niepotwierdzony – szary romb z pytajnikiem. Zgłoszony – niebieski kwadrat z zegarem. Nieaktualny – pomarańczowy trójkąt z wykrzyknikiem. Wycofany – czerwone przekreślone koło, widoczne po wybraniu tego statusu. Każdy symbol ma nazwę dostępną dla czytnika.
2. **Klastry.** Granatowe koła z liczbą i białym obrysem. Na widoku kraju grupuj szerzej, a przy zbliżaniu rozbijaj klastry na mniejsze grupy. Aktywacja klastra myszą lub klawiaturą przybliża jego obszar. Dla punktów o tych samych współrzędnych otwiera listę urządzeń.
3. **Podkład i legenda.** Wycisz kolory podkładu oraz drobne etykiety na widoku kraju. Zachowaj czytelne nazwy miast i główne drogi. Nad mapą daj zwijaną legendę z rzeczywistymi symbolami, nazwami statusów i przykładem klastra.
4. **„Jesteś tutaj”.** Po użyciu przycisku lokalizacji pokaż niebieską kropkę z białą obwódką i półprzezroczystym okręgiem dokładności. Obok przycisku daj opcję ręcznego wskazania lokalizacji.
5. **Szczegóły punktu.** Pokaż nazwę, odległość po ustaleniu lokalizacji, opis dojścia, status, godziny i warunki dostępu. Na telefonie otwieraj szczegóły w panelu pod mapą. Po zamknięciu przywróć fokus na znacznik.
6. **Lista i mapa.** Wspólne filtry statusu i dostępności, lista jako pierwszy widok. „Pokaż na mapie” przy rekordzie zaznacza punkt, a „Pokaż na liście” w szczegółach przenosi fokus do rekordu. Przesunięcie mapy zawęża listę dopiero po użyciu „Szukaj w tym obszarze”.

## C. Co zachować

1. Żółty baner wyraźnie oznacza prototyp i dane demonstracyjne, a oprawa portalu pozostaje spójna.
2. Raport walidacji CSV przed wysłaniem wskazuje wiersz, pole i sposób poprawy oraz pozwala wysłać poprawne wiersze.
3. Formularz po QR ma duże pola i klikalne etykiety opcji. Pozwala użyć lokalizacji telefonu lub wpisać współrzędne ręcznie.