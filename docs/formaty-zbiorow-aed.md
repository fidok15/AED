# Formaty polskich zbiorów AED i co z nimi robi konwerter

Przegląd z 22.11.2026. Wszystkie liczby pochodzą z plików i odpowiedzi usług, które faktycznie otwarliśmy (zasada 10); czego nie dało się otworzyć – piszemy wprost.

## Skąd wziąć dane do testu

Adresy sprawdzone 22.11.2026 (adresy plików dane.gov.pl – z odpowiedzi API `api.dane.gov.pl/1.4/resources/<id>`, pole `file_url`). Pobrany plik wrzuć do konwertera (`/pl/aed/konwerter`) bez zmiany nazwy – format rozpoznajemy po treści.

| Instytucja | Adres | Co kliknąć / wpisać | Co przyjdzie |
|---|---|---|---|
| Urząd Miejski w Koszalinie (mapa „Punkty Życia”) | https://www.google.com/maps/d/kml?mid=1AQwJAfeZsGGB7fhz0-yBSxab83DwyIw&forcekml=1 | otwórz adres – przeglądarka pobierze plik | KML, 35 punktów (bez `&forcekml=1` – KMZ). W konwerterze ustaw wartość stałą „Miejscowość” = Koszalin |
| Miasto Kraków | https://krakow.pl/3992,artykul,gdzie-znalezc-defibrylator-.html | w przeglądarce „Zapisz stronę jako…” (HTML) | tabela HTML, 20 wierszy na stronie 1 (stron jest więcej), adresy bez współrzędnych |
| BIP Miasta Krakowa | https://www.bip.krakow.pl/zalaczniki/dokumenty/n/298628/karta | „zobacz załącznik” | DOCX z tabelą 31 lokalizacji, bez współrzędnych; wartość stała „Miejscowość” = Kraków |
| Przemyśl (dane.gov.pl, zbiór 4581) | https://api.dane.gov.pl/media/resources/20241106/1730818801_b50R6UVxPgoVdBbq.gml (zamień `.gml` na `.geojson`, `.json`, `.csv`) | otwórz adres | ten sam wykaz 21 AED jako GML, GeoJSON, JSON i CSV (`;`) |
| Krosno (dane.gov.pl, zbiór 3624) | https://api.dane.gov.pl/media/resources/20240219/Defibrylator_jAmxQcp.csv | otwórz adres | CSV z kolumną pełnego adresu |
| Marki (dane.gov.pl, zbiór 4955) | https://api.dane.gov.pl/media/resources/20250710/Defibrylator_GminaMiastoMarki_1.xlsx | otwórz adres | XLSX z całym wierszem CSV w jednej komórce |
| Legionowo (dane.gov.pl, zbiór 40593) | https://api.dane.gov.pl/media/resources/20260914/aed.csv | otwórz adres | CSV zgodny ze standardem |
| Esri Polska – kopia danych Warszawy | https://services.arcgis.com/zg6BBB0wvjzrRBLk/arcgis/rest/services/AED/FeatureServer/0/query?where=1%3D1&outFields=*&f=json | otwórz adres, zapisz jako `.json` | ArcGIS JSON, 708 urządzeń, współrzędne w EPSG:3857 (z `&f=geojson` – GeoJSON) |
| Warstwa ArcGIS z Mikołowa (konto prywatne, bez licencji – tylko do testu) | https://services9.arcgis.com/E1ZsJFZqsk2tR9yK/arcgis/rest/services/Defibrylatory_AED/FeatureServer/0/query?where=1%3D1&outFields=*&f=json | jw. | ArcGIS JSON, 21 punktów w PUWG 2000 strefa 6 (EPSG:2177), adres w jednym polu „Mikołów, Gliwicka 3” |
| Koszalin – strona urzędu (wersja do druku) | https://www.koszalin.pl/en/printpdf/9480 | otwórz | PDF – konwerter odpowie, że PDF nie jest formatem odczytywalnym maszynowo |

## Przegląd źródeł

| Instytucja | Format i dostęp | Zapis położenia | Rekordów | Licencja | Pola |
|---|---|---|---|---|---|
| Krosno (dane.gov.pl 3624) | CSV, UTF-8, `,` | 2 kolumny WGS84, część zamieniona | w repo | CC0 1.0 (portal) | Numer Id, Nazwa, Lokalizacja, Adres (jedno pole), szer., dł. |
| Marki (dane.gov.pl 4955) | CSV i XLSX (wiersz CSV w komórce) | 2 kolumny WGS84, nagłówki zamienione | 8 | jw. | jak Krosno |
| Przemyśl (dane.gov.pl 4581) | **GML** (`gml:pos` „szer. dł.”), GeoJSON, JSON (tablica obiektów, `geometry` jako obiekt), CSV `;` z kolumną punktu GeoJSON | WGS84; w GML kolejność szer., dł. | 21 | jw. | id, name, description (długi tekst), category, city, street, home_number, postcode, phone, email, www… |
| Legionowo (dane.gov.pl 40593) | CSV w standardzie | 2 kolumny WGS84 | w repo | jw. | standard |
| m.st. Warszawa (API, dane.gov.pl 39512 = odnośnik) | JSON: **tablica obiektów GeoJSON bez FeatureCollection**, `coordinates` jako `[[dł., szer.]]` | WGS84 zagnieżdżone | 708 | warunki m.st. Warszawy | defibrillator_id, location_*, device_* |
| Esri Polska – kopia Warszawy (ArcGIS Online) | **ArcGIS FeatureServer**: `f=json` (attributes + geometry x/y), `f=geojson`; eksport także csv, kml, excel, shapefile | **EPSG:3857** w geometrii + kolumny `latitude`/`longitude` | 708 (`returnCountOnly`) | „Dane pochodzą z portalu Otwarte dane Warszawy…” | object_name, street, building_no, postcode, city, access_desc, availability… |
| Mikołów – warstwa na koncie prywatnym ArcGIS Online | ArcGIS FeatureServer `f=json` | **PUWG 2000 strefa 6 (EPSG:2177)** | 21 | brak; nie instytucja | Lokalizacja, adres („Mikołów, Gliwicka 3”), Pietro, Położenie |
| Koszalin, Urząd Miejski („Punkty Życia”) | **Google Moje Mapy → KML/KMZ** (link z PDF strony urzędu) | KML `lon,lat,0` | 35 punktów (strona mówi o 40 urządzeniach, w tym 8 mobilnych) | niepodana | name („Punkt Życia #1”), description (opis miejsca z ulicą), warstwa |
| Kraków, krakow.pl | **tabela HTML** na stronie, stronicowana (20 na stronę) | brak – tylko adres „ul. Totus Tuus 34 30-610 Kraków” | ok. 20 × liczba stron (nie liczyliśmy) | niepodana | Nazwa (nazwa + adres w jednej komórce), Kategoria, Mapa (pusta) |
| Kraków, BIP | **DOCX** z tabelą (wiersz tytułowy nad nagłówkiem) | brak; adres bez miejscowości („ul. Bosacka 18”) | 31 wierszy (kolumna „Liczba AED” – wiersz może oznaczać kilka urządzeń; konwerter jej nie rozwija) | niepodana | LP., MIEJSCE, ADRES, Liczba AED |
| Chełm (samorzad.gov.pl) | lista punktowana na stronie | brak | 10 | niepodana | nazwa i adres w tekście |
| Koszalin, strona urzędu | PDF (wersja do druku) | brak | – | – | opis + link do mapy |
| OpenAEDMap / OSM | CSV, GeoJSON, ODS (według wyszukiwarki: `aed_poland.ods`) | WGS84 | 18 298 (w repo) | ODbL – nie wchodzi do zbioru (zasada 3) | tagi OSM |

Nie znaleźliśmy: zbiorów AED w CKAN Gdyni (`package_search?q=defibrylator` → 0 wyników); portale Gdańska, Wrocławia, Poznania i Lublina nie odpowiedziały na zapytania API (przekroczony czas albo 403); warstwy „Defibrylatory” na geoportal.gov.pl nie udało się namierzyć (wyszukiwarka wskazuje tylko komunikat o niej, bez adresu usługi WMS/WFS). Strona Wrocławia o mapie AED (2013) nie zawiera mapy ani pliku. Wyszukiwarka dane.gov.pl (`api.dane.gov.pl/1.4/search?q=AED|defibrylator`) zwraca tylko znane zbiory: Krosno, Marki, Przemyśl, Legionowo, Warszawa.

### Wnioski: co występuje naprawdę

Formaty, od najczęstszych w tym, co otwarliśmy: CSV (Krosno, Marki, Przemyśl, Legionowo, eksport ArcGIS) → JSON/GeoJSON (Przemyśl, Warszawa, ArcGIS) → strona WWW z listą lub tabelą (Kraków, Chełm, Koszalin) → PDF i DOCX z BIP (Kraków, Koszalin) → XLSX (Marki) → KML/KMZ z Google Moje Mapy (Koszalin) → ArcGIS FeatureServer (2 warstwy) → GML (Przemyśl).

Położenie: dwie kolumny WGS84 (Krosno, Marki, Legionowo, ArcGIS-atrybuty) → geometria GeoJSON/KML w WGS84 (Przemyśl, Warszawa, Koszalin) → **brak współrzędnych, sam adres** (Kraków ×2, Chełm) → układy płaskie w usługach ArcGIS (EPSG:3857, EPSG:2177). Nie spotkaliśmy w prawdziwych plikach stopni-minut-sekund ani WKT – obsługujemy je, bo kosztują kilka linii, ale to przypuszczenie, nie obserwacja.

Gotowe do dodania do `sources.json`: **brak**. Koszalin (KML) i Kraków (HTML/DOCX) nie mają podanej licencji, a Kraków nie ma współrzędnych – to kandydaci do rozmowy z urzędem (zachęta: konwerter i publikacja na dane.gov.pl), nie źródła otwarte. Warstwa Esri Polska to kopia API Warszawy, które już mamy; warstwa z Mikołowa nie ma instytucji ani licencji.

## Jak konwerter czyta dowolny plik

Jedna ścieżka: `formaty.detect` rozpoznaje format **po treści** (sygnatury ZIP i jego zawartość, `%PDF`, OLE2 starego XLS/DOC, PNG/JPEG, `<kml`, `<gpx`, `FeatureCollection`/`featureMember`, `{`/`[`, `<table`, BOM), czytnik formatu zamienia plik na tę samą tabelę (kolumny + wiersze tekstu + ewentualny punkt), potem wspólny krok położenia i istniejąca propozycja mapowania, normalizacja, `sources.map_rows` i `wykaz.read_wykaz`. Żadnych osobnych gałęzi mapowania per format.

| Format | Czytnik | Uwagi |
|---|---|---|
| CSV / TXT / TSV | bez zmian | UTF-8, UTF-16 z BOM, Windows-1250; `,` `;` tab |
| XLSX | `xlsx.py` (bez zmian) | + pomijanie wierszy tytułowych nad nagłówkiem |
| ODS | `formaty.read_ods` | `number-columns-repeated` puste nie są rozwijane; limit komórek |
| JSON | `formaty.read_json` | tablica obiektów; obiekt z listą pod `features`/`data`/`result`/`records`/`items`… (do 3 poziomów, CKAN); spłaszczanie `a.b` |
| GeoJSON | jw. | FeatureCollection albo tablica Feature (Warszawa), Point/MultiPoint/`[[x,y]]` |
| ArcGIS JSON | jw. | `features[].attributes` + `geometry.x/y` + `spatialReference` → układ z EPSG |
| KML / KMZ | `formaty.read_xml_format` | Placemark: name, description (HTML → tekst), ExtendedData, SimpleData, nazwa folderu jako „warstwa”; KMZ: limit po rozpakowaniu 50 MB |
| GPX | jw. | `wpt`/`rtept`: lat/lon, name, desc, cmt, link |
| GML / WFS | jw. | `featureMember`/`member`: liście jako kolumny, `gml:pos`/`gml:coordinates` + `srsName` |
| Tabela HTML | `formaty.read_html` (`html.parser`) | największa tabela; komórka z kilkoma blokami (nazwa + adres) dzielona na kolumny |
| Tabela DOCX | `formaty.read_docx` | największa tabela z `word/document.xml`; wiersz tytułowy pomijany |
| PDF, obraz, XLS/DOC, Shapefile w ZIP | – | komunikat po polsku: format nieodczytywalny maszynowo / „zapisz jako XLSX/CSV” / „wyeksportuj jako GeoJSON” |

Położenie (wspólny krok `konwerter._positions`, moduł `uklady.py`):

- dwie kolumny WGS84, także z przecinkiem dziesiętnym i zamienione (było);
- stopnie-minuty-sekundy w kolumnie (`52°13'47"N`) → stopnie dziesiętne;
- jedna kolumna z całym punktem: GeoJSON, WKT `POINT(x y)` z opcjonalnym `SRID=2180;`, „52.2297, 21.0122”, „21,0122 52,2297”, para DMS z literami N/E; kolejność rozstrzyga zakres Polski, pojedynczy odwrócony wiersz jest obracany;
- dwie kolumny płaskie: PUWG 1992 (EPSG:2180), PUWG 2000 strefy 5–8 (EPSG:2176–2179, strefa z cyfry milionów), Web Mercator (EPSG:3857) – rozpoznawane po zakresie, przeliczane odwrotnym odwzorowaniem Gaussa-Krügera (szereg Krügera do n³, GRS80; źródło w komentarzu `uklady.py`). **Dokładność**: na 5 punktach przeliczonych przez serwer ArcGIS (EPSG:2180, 2177, 2178, 3857) błąd < 1 mm (test `test_planar_systems_within_a_millimetre`). Różnicę WGS84–ETRF2000 (poniżej 1 m) pomijamy.
- Ograniczenie: w PUWG 1992 para (X, Y) i (Y, X) często obie wypadają w Polsce. Rozstrzyga nazwa kolumny (szer/lat/north → północna), w braku – kolejność GIS (pierwsza kolumna = wschodnia). Raport każe sprawdzić kilka punktów na mapie.

Adres bez współrzędnych: konwersja się udaje, raport mówi „N wierszy ma adres bez współrzędnych – nie trafią do wykazu, dopóki nie uzupełnisz położenia”, plik w standardzie zawiera te wiersze z pustymi współrzędnymi. Nie geokodujemy usługą zewnętrzną (prywatność, zależność).

Proponowana bezpieczna ścieżka geokodowania (do wdrożenia po hackathonie, nie zaimplementowana): adresy z PRG (Państwowy Rejestr Granic – punkty adresowe, GUGiK, otwarte dane, aktualizowane), pobrane jako plik i trzymane lokalnie w portalu; dopasowanie po `kod_terc`/`kod_simc` z TERYT, nazwie ulicy (ULIC) i numerze; zapis `sposob_weryfikacji = geokodowanie PRG` i status `niepotwierdzony` do czasu potwierdzenia przez zarządcę przy naklejce QR. Żaden adres nie opuszcza serwera ministerstwa.

Zabezpieczenia obejmują nowe formaty: limit 5 MB pliku; limit 50 MB po rozpakowaniu (XLSX, ODS, DOCX, KMZ; odczyt ograniczony, rozmiar z nagłówka ZIP nie jest ufany); XML z DOCTYPE/ENTITY odrzucany; 300 kolumn (także przy spłaszczaniu JSON i w ODS), 50 000 wierszy, 1 mln komórek, 20 mln znaków – sprawdzane przed analizą kolumn; reguła OSM/ODbL, ukrywanie kontaktu i numeru seryjnego, neutralizacja formuł – bez zmian, bo działają na wspólnej tabeli.

## Od pliku do wykazu – wyniki

Każda próbka: analiza → zaproponowane mapowanie przyjęte bez zmian (+ wartość stała, gdzie podano) → konwersja → `read_wykaz` (test `tests/test_formaty.py`).

| Źródło | Format | Wierszy | Przyjętych | Ręcznie |
|---|---|---|---|---|
| Koszalin, Moje Mapy | KML | 35 | 35 | stała „Miejscowość” = Koszalin |
| Koszalin, Moje Mapy | KMZ | 35 | 35 | jw. |
| Przemyśl | GML | 21 | 21 | nic |
| Przemyśl | JSON | 21 | 21 | nic |
| Przemyśl | CSV z punktem GeoJSON | 21 | 21 | nic |
| Przemyśl | GeoJSON | 21 | 21 | nic (te same pozycje we wszystkich 4 formatach) |
| Warszawa, API | JSON (tablica Feature) | 708 | 706 | 2 wiersze z opisem położenia innym niż „Wewnątrz/Na zewnątrz budynku” – walidator je nazywa |
| Esri Polska / Warszawa | ArcGIS JSON, EPSG:3857 | 3 | 3 | nic |
| Esri Polska / Warszawa | GeoJSON | 3 | 3 | nic |
| Mikołów (odtworzona struktura) | ArcGIS JSON, EPSG:2177 | 3 | 3 | stała „Miejscowość” (adres „Mikołów, Gliwicka 3” nie ma kodu pocztowego) |
| Kraków, krakow.pl | tabela HTML | 5 | 0 | brak współrzędnych: 4 wiersze z adresem do uzupełnienia, 1 adres bez kodu |
| Kraków, BIP | DOCX | 31 | 0 | brak współrzędnych i miejscowości: stała „Miejscowość”, 31 wierszy do uzupełnienia położenia |
