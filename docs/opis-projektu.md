# Tytuł i opis projektu (formularz zgłoszeniowy)

Nazwa akcji jest jeszcze niewybrana (kandydaci: `kampania/nazwa-i-haslo.md`). Po wyborze dopisz ją przed tytułem roboczym, np. „[NAZWA AKCJI]: …”. Liczby pochodzą z `datasets/out/raport.json`.

## Tytuł roboczy

Wykaz AED w dane.gov.pl: jeden standard, wielu dostawców, jeden zbiór ministerstwa

## Opis szczegółowy

Dane o defibrylatorach AED są dziś rozproszone po kilku bazach i nikt nie bierze za nie odpowiedzialności. Zebraliśmy sześć dostępnych źródeł: cztery zbiory samorządowe z dane.gov.pl, API Warszawy i OpenStreetMap. Po scaleniu powstał rejestr 18 814 urządzeń. Żadne z nich nie ma potwierdzenia od zarządcy, średnia kompletność rekordu wynosi 39 na 100, a w czterech zbiorach samorządowych żaden rekord nie ma godzin dostępu.

Proponujemy rozwiązanie zbudowane na mechanizmach portalu dane.gov.pl, a nie obok niego. W kodzie portalu znaleźliśmy wykaz zasobów chronionych danych (DGA). To jedyny mechanizm, który zbiera zasoby wielu dostawców i scala je w jeden zasób zbiorczy. Na jego wzór dodaliśmy do forka portalu wykaz AED. Dostawca, czyli samorząd, instytucja albo firma, publikuje w swoim zbiorze zasób CSV oznaczony jako „Wykaz AED”. Portal sprawdza plik przy zapisie i podaje błędy po polsku na poziomie wiersza i pola. Raz dziennie scala wszystkie wykazy: usuwa duplikaty i zostawia tylko rekordy spełniające profil publikacji. Wynik to zasób zbiorczy w zbiorze Ministerstwa Cyfryzacji. Jest dostępny bez logowania jako tabela, mapa i API, razem z publicznym raportem przyjętych i odrzuconych wykazów.

Podstawą jest jeden standard danych: jeden wiersz to jedno urządzenie, dwa profile wymagalności (sprzedaż i publikacja), nazwy kolumn adresu zgodne z istniejącym zbiorem Legionowa. Ze standardu generujemy wzorzec XLSX, walidator i formularze.

Drugi kanał odpowiada na brak właściciela danych. Producent lub sprzedawca zgłasza urządzenie przy sprzedaży z konta firmy. System nadaje identyfikator i naklejkę z kodem QR, a zarządca obiektu skanuje ją telefonem i potwierdza miejsce, godziny dostępu i stan urządzenia. Rejestr przypomina o terminach baterii i elektrod i prosi o okresowe potwierdzenie danych. Potwierdzone rekordy trafiają do portalu jako wykaz ministerstwa albo przez harvester XML. Dane z OpenStreetMap (ODbL) zostają poza zbiorem otwartym, a numer seryjny i kontakty nie są publikowane.

Akcja promocyjna jest skierowana do dostawców danych. Zachęty to jedno miejsce raportowania, przypomnienia o terminach, obecność na mapie sprzedawców i odznaka za aktualne dane.

## Wersja krótka (do 500 znaków)

Wykaz AED w forku dane.gov.pl, wzorem wykazu DGA. Samorządy, instytucje i firmy publikują wykazy AED w jednym standardzie, a portal waliduje je i codziennie scala w zbiór zbiorczy ministerstwa, otwarty do odczytu (tabela, mapa, API). Drugi kanał: sprzedawca zgłasza urządzenie, zarządca potwierdza miejsce i godziny przez naklejkę QR, rejestr przypomina o bateriach i elektrodach. Do tego wzorzec XLSX i akcja dla dostawców danych.
