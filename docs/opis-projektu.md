# Tytuł i opis projektu (formularz zgłoszeniowy)

„Misja AED – Dane na ratunek” to nazwa zadania konkursowego. Nazwa akcji to „Opiekun AED”, hasło: „Dbasz o AED? Pokaż to w danych.” (`kampania/nazwa-i-haslo.md`, znak i księga znaku w `kampania/`). Liczby: stan z `datasets/out/raport.json` (rejestr z mappera) z 22.11.

## Tytuł

Opiekun AED – wykaz AED w dane.gov.pl: jeden standard, wielu dostawców, jeden zbiór ministerstwa

## Opis szczegółowy

Dane o defibrylatorach AED są dziś rozproszone po kilku bazach i nikt nie bierze za nie odpowiedzialności. Zebraliśmy sześć dostępnych źródeł: cztery zbiory samorządowe z dane.gov.pl, API Warszawy i OpenStreetMap. Po scaleniu powstał rejestr z mappera: 18 814 urządzeń (stan z `raport.json`). Żadne z nich nie ma potwierdzenia od zarządcy, średnia kompletność rekordu wynosi 39,2 na 100, a w czterech zbiorach samorządowych żaden rekord nie ma godzin dostępu.

Proponujemy rozwiązanie zbudowane na mechanizmach portalu dane.gov.pl, a nie obok niego. W kodzie portalu znaleźliśmy wykaz zasobów chronionych danych (DGA). To jedyny mechanizm, który zbiera zasoby wielu dostawców i scala je w jeden zasób zbiorczy. Na jego wzór dodaliśmy do forka portalu wykaz AED. Dostawca, czyli samorząd, instytucja albo firma, publikuje w swoim zbiorze zasób CSV oznaczony jako „Wykaz AED”. Plik CSV portal sprawdza przy zapisie i podaje błędy po polsku na poziomie wiersza i pola; wykaz XLSX i wykaz-link sprawdza dopiero scalanie. Scalanie wszystkich wykazów (zadanie Celery, w harmonogramie codziennie o 03:45) usuwa duplikaty i zostawia tylko rekordy spełniające profil publikacji. Scalanie sprawdziliśmy ręcznym uruchomieniem zadania; samego harmonogramu w działaniu – jeszcze nie. Wynik to zasób zbiorczy w zbiorze Ministerstwa Cyfryzacji. Jest dostępny bez logowania jako tabela, mapa i API, razem z publicznym raportem przyjętych i odrzuconych wykazów. Pełny fork portalu uruchomiliśmy lokalnie; adres publiczny podamy po wdrożeniu na serwer.

Podstawą jest jeden standard danych: jeden wiersz to jedno urządzenie, dwa profile wymagalności (sprzedaż i publikacja), nazwy kolumn adresu zgodne z istniejącym zbiorem Legionowa. Ze standardu generujemy wzorzec XLSX, walidator i formularze.

Drugi kanał odpowiada na brak właściciela danych. Producent lub sprzedawca zgłasza urządzenie przy sprzedaży z konta firmy. System nadaje identyfikator i naklejkę z kodem QR, a zarządca obiektu skanuje ją telefonem i potwierdza miejsce, godziny dostępu i stan urządzenia. Zadanie przypomnień przygotowuje prośby o okresowe potwierdzenie danych i przypomnienia o terminach baterii i elektrod; w prototypie trafiają one do skrzynki nadawczej usługi, bez wysyłki e-mail. Potwierdzone rekordy trafiają do eksportu ministerstwa (CSV i zasilanie XML w wersji 1.13), który ministerstwo może opublikować w portalu jako swój wykaz. Pełnego importu harvesterem i przejścia jednego rekordu od naklejki do zasobu zbiorczego jeszcze nie pokazaliśmy. Dane z OpenStreetMap (ODbL) zostają poza zbiorem otwartym, a numer seryjny i kontakty nie są publikowane.

Akcja promocyjna jest skierowana do dostawców danych. Zachęty to jedno miejsce raportowania, przypomnienia o terminach, obecność na mapie sprzedawców i odznaka za aktualne dane.

## Wersja krótka (do 500 znaków)

Wykaz AED w forku dane.gov.pl, wzorem wykazu DGA. Samorządy, instytucje i firmy publikują wykazy AED w jednym standardzie, a portal waliduje je i scala (zadanie Celery) w zbiór zbiorczy ministerstwa, otwarty do odczytu (tabela, mapa, API); uruchomione lokalnie w forku. Drugi kanał: sprzedawca zgłasza urządzenie, zarządca potwierdza miejsce i godziny przez naklejkę QR, rejestr przygotowuje przypomnienia o bateriach i elektrodach. Do tego wzorzec XLSX i akcja dla dostawców danych.
