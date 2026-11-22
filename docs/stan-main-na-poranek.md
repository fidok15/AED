## Zestawienie z `main` (22.11, rano; `main` = 9ff4b9e, PR #41)

Od wieczora `main` poszedł w stronę wskazaną przez prowadzącego: **wykaz AED w forku portalu wzorem wykazu DGA** (`backend/mcod/aed/`, `GET /aed-aggregated`), standard 0.3.0, logo i księga znaku „Opiekun AED”, prezentacja HTML, konwerter formatów, geokodowanie GUGiK. Nocna interpretacja „wykazu” jako „Propozycji nowych danych” (it. 3, 25) jest **nieaktualna** – prowadzący wskazał wykaz DGA.

**Zrobione w `main` (pokrywa się z nocnymi wnioskami):**

| Ustalenie | Stan w `main` |
|---|---|
| licencja zbioru z harwestera (it. 21) | `aed_service/app.py:1187` – `<conditions><source>true</source>` (CC BY 4.0); zasilanie przeniesione do usługi: `GET /api/aed/eksport/dane-gov-pl.xml` |
| pola niepubliczne w schemacie, jeden eksport (it. 43) | `"publiczne": false` w `schema.json`, `HIDDEN_FIELDS` w `schema.py`, `build.py` czyści je; w `datasets/out/` 0 kontaktów |
| reguła składni godzin (it. 34, 71) | `aed_standard/hours.py` + `validate.py:270` |
| stan urządzenia osobno od statusu, piętro (it. 5, 22, 62) | `stan_urzadzenia`, `data_stanu`, `pietro` (0.3.0) |
| dowody WCAG (it. 68) | podlinkowane w instrukcji dla jury |
| zrzuty z portalu (it. 44, 68) | `docs/zrzuty/portal-*.png`, panel krok po kroku |
| arkusz publikacyjny w XLSX (it. 72, część) | „Dane otwarte (publikacja)” |
| nazwa, logo, księga znaku | „Opiekun AED”, `kampania/logo/`, `naklejka-logo.svg` |

**Nadal wymaga uwagi:**

1. **„112” na stronie QR i naklejce** – w `main` brak (it. 42). Bezpieczeństwo i UX; mała zmiana.
2. **`wprowadzajacy_nazwa` puste we wszystkich 781 rekordach** eksportu – pole z listy komisji (it. 46).
3. **Test na końcach linii**: `main` usunął błędny `.gitattributes`, ale nie dodał poprawnego; przy `autocrlf=true` (Git for Windows) plik z `datasets/out/` ma CRLF i `test_committed_outputs_match_build` nie przejdzie (it. 31).
4. **Zasilanie XML z usługi nie było uruchomione na harwesterze** (`docs/wykaz-aed-w-portalu.md:307`). Nocny import na lokalnym portalu (gałąź `feat/zasilanie-xml`) przeszedł dla wersji z nazwą pliku zależną od treści; `main` używa adresu z `?wersja=` – nieprzetestowane. Do sprawdzenia też typy kolumn (`kod_terc`, `kod_simc`, `nr_budynku`, `zrodlo_id` → tekst), bo portal wnioskuje `integer` i odrzuca puste pola (it. 21–23 nocy, iteracja o walidacji tabelarycznej).
5. **„Link jednorazowy”** w `docs/instrukcja-dla-jury.md:96` i `kampania/zachety.md:63` – link jest ważny 90 dni, wielokrotnie (it. 74).
6. **Publiczny ranking firm** („Ranking firm” w zakładce, panelu i prezentacji) – do decyzji wobec „nie premiować danych” (it. 2, 39).
7. **Wycofane rekordy znikają z eksportu** – decyzja otwarta (it. 23).
8. **Instrukcja XLSX** nie zawiera reguł walidatora (0 z 5) ani metadanych zbioru (it. 72).
9. **Prezentacja** nie używa nocnych faktów: 91% Warszawa, 62 → 97, Marki skopiowały plik Krosna, Przemyśl „codziennie” sprzed 2 lat, interpelacja 20440, 96 AED InPostu bez dostawcy (it. 30, 47, 80, 83, 34, 84).
10. **Raporty importu harwestera nie idą e-mailem** w 2.63.0 – jeśli prezentacja lub instrukcja obiecuje powiadomienie, poprawić (it. 45).

**Gałąź `feat/zasilanie-xml`:** zasilanie jest już w `main` w innej formie (w usłudze), więc gałęzi nie scalać w całości. Warto przenieść tylko wnioski z próby na portalu (pkt 4) i ewentualnie wersjonowaną nazwę pliku.
