# Próbki formatów dla konwertera

Pobrane 22.11.2026. Próbki służą testom konwertera (`tests/test_formaty.py`), nie są źródłami zbioru krajowego.

| Plik | Instytucja i adres | Licencja / status | Co to jest |
|---|---|---|---|
| `koszalin-mymaps.kml` | Urząd Miejski w Koszalinie, mapa „Punkty Życia” podlinkowana na stronie urzędu (otwarta wersja do druku: https://www.koszalin.pl/en/printpdf/9480, link „Punkty Życia na mapie Koszalina”); eksport `https://www.google.com/maps/d/kml?mid=1AQwJAfeZsGGB7fhz0-yBSxab83DwyIw&forcekml=1` | licencja niepodana; informacja publiczna urzędu | cały plik, 35 punktów |
| `koszalin-mymaps.kmz` | jw., ten sam adres bez `forcekml=1` | jw. | oryginalny KMZ (ZIP z `doc.kml` i ikonami) |
| `krakow-bip-impuls-zycia.docx` | BIP Miasta Krakowa, https://www.bip.krakow.pl/zalaczniki/dokumenty/n/298628/karta („zobacz załącznik”) | licencja niepodana; dokument BIP | cały plik; tabela 31 lokalizacji (stan 25.05.2020), bez współrzędnych |
| `krakow-lista.html` | Miasto Kraków, https://krakow.pl/3992,artykul,gdzie-znalezc-defibrylator-.html | licencja niepodana | fragment strony: tabela z 5 pierwszymi wierszami (z 20 na stronie 1) |
| `arcgis-warszawa-epsg3857.json` | Esri Polska (Esri_PL_Content), warstwa „Lokalizacje defibrylatorów AED w Warszawie”, https://services.arcgis.com/zg6BBB0wvjzrRBLk/arcgis/rest/services/AED/FeatureServer/0/query?where=1%3D1&outFields=*&resultRecordCount=3&f=json | dane Urzędu m.st. Warszawy z portalu Otwarte dane Warszawy (warunki ponownego wykorzystywania m.st. Warszawy) | 3 pierwsze rekordy, ArcGIS JSON w EPSG:3857 |
| `arcgis-warszawa.geojson` | jw., `f=geojson` | jw. | 3 pierwsze rekordy w GeoJSON |
| `arcgis-epsg2177-struktura.json` | **odtworzona struktura**: warstwa `Defibrylatory_AED` (Mikołów) na koncie prywatnym ArcGIS Online, https://services9.arcgis.com/E1ZsJFZqsk2tR9yK/arcgis/rest/services/Defibrylatory_AED/FeatureServer/0 | brak licencji i brak instytucji – treści nie kopiujemy | nazwy pól i układ EPSG:2177 jak w oryginale; wartości tekstowe zmyślone; 3 pary współrzędnych z oryginału (same liczby, do testu przeliczenia PUWG 2000) |

Przemyśl (GML, GeoJSON, JSON, CSV tych samych 21 urządzeń) i API Warszawy leżą już w `datasets/raw/` i testy czytają je stamtąd.
