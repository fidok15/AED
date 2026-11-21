# Misja AED – Dane na ratunek: research i pomysły na rozwiązanie

> Dokument roboczy zespołu. Stan wiedzy na 21.11.2026. Liczby z API (OpenAEDMap, dane.gov.pl) pobrane tego dnia.
> Fakty oznaczone **[do weryfikacji]** pochodzą ze źródeł nieoficjalnych albo wymagają potwierdzenia w kodzie portalu.

## Spis treści

1. [TL;DR](#1-tldr)
2. [Analiza zadania, regulaminu i wskazówek](#2-analiza-zadania-regulaminu-i-wskazówek)
3. [Stan obecny – research](#3-stan-obecny--research)
4. [Jak działa dane.gov.pl – mechanika, którą trzeba uszanować](#4-jak-działa-danegovpl--mechanika-którą-trzeba-uszanować)
5. [Wzorcowy zakres danych – szkic](#5-wzorcowy-zakres-danych--szkic)
6. [Pomysły na rozwiązanie](#6-pomysły-na-rozwiązanie)
7. [Rekomendowany kierunek (MVP na hackathon)](#7-rekomendowany-kierunek-mvp-na-hackathon)
8. [Ryzyka i ograniczenia](#8-ryzyka-i-ograniczenia)
9. [Checklista oddania](#9-checklista-oddania)
10. [Źródła](#10-źródła)

---

## 1. TL;DR

- **Problem nie jest techniczny, tylko organizacyjny:** dane o AED istnieją (OpenAEDMap ma ich w Polsce 18 297), ale nikt formalnie za nie nie odpowiada, a 67% rekordów nigdy nie było weryfikowanych. Na dane.gov.pl jest dziś zaledwie 5 lokalnych zbiorów o AED – każdy w innym schemacie, jeden wręcz uszkodzony.
- **Nie ma ustawowego rejestru AED.** MSWiA (kwiecień 2026) przerzuca standard ewidencji na Ministra Zdrowia, a operatorzy 112 korzystają z danych społecznościowych OpenAEDMap.
- **dane.gov.pl ma już gotowy wzorzec masowego, jednolitego zasilania:** harvester XML używany od 2025 r. przez tysiące deweloperów (ceny mieszkań). Identyczny mechanizm można zastosować do AED – to najmocniejszy argument w kryterium „zgodność z zasadami portalu” (30%).
- **Rekomendacja:** model federacyjny – każdy dysponent (gmina, szpital, uczelnia, firma) publikuje własny zbiór na dane.gov.pl zgodnie z naszym wzorcem i przez harvester XML, a wskazana instytucja publiczna publikuje codziennie zbiór zagregowany (z deduplikacją i statusem weryfikacji). Do tego narzędzia obniżające próg wejścia: kreator, walidator, konwertery, QR na urządzeniu.
- **Kampania (25% punktów!)** musi być skierowana do *dysponentów danych*, nie do jury – komunikat „opublikuj swój AED”, nie „znajdź AED”.

---

## 2. Analiza zadania, regulaminu i wskazówek

### 2.1. Co dokładnie trzeba oddać

| Artefakt | Wymóg | Uwagi |
|---|---|---|
| Tytuł i szczegółowy opis projektu | obowiązkowy | |
| Prezentacja | min. 5 slajdów z dowodami (zrzuty ekranu), opis funkcji i kroków użytkownika, lista ograniczeń | |
| Prototyp rozwiązania | obowiązkowy | jury nie będzie konfigurować środowiska → link do klikalnej wersji |
| Wzorcowy zakres danych | tabela **.xlsx** | dodatkowo warto dać wersję maszynową (CSV + JSON Table Schema) |
| Kod źródłowy | obowiązkowy | |
| Logotyp | .jpg, .png, .pdf + dowolny format otwarty (np. .svg) | |
| Księga znaku | .pdf | min.: kolorystyka, pole ochronne, minimalna wielkość, niedozwolone użycia, 3–5 zdań koncepcji |
| Deklaracja użycia AI | §2 pkt 8 regulaminu – **obowiązkowa** | łatwo o tym zapomnieć |

### 2.2. Wymagania techniczne

- Dane udostępniane przez rozwiązanie w formacie **odczytywalnym maszynowo** (CSV, JSON, GeoJSON, XML, XLSX – nie PDF/DOC).
- **Zgodność z zasadami działania dane.gov.pl** – patrz rozdział 4.
- **WCAG** w aktualnej wersji (2.2, poziom AA jako standard administracji), responsywność (desktop + mobile), zasady UX.
- AI dozwolone, ale praca ma być efektem analizy i pracy człowieka; trzeba wskazać zakres użycia AI.

### 2.3. Kryteria oceny – gdzie są punkty

| Kryterium | Waga | Co z tego wynika |
|---|---|---|
| Zgodność z zasadami działania dane.gov.pl | **30%** | Pokazać, że rozwiązanie *korzysta* z mechanizmów portalu (dostawcy, zbiory, zasoby, harvester, API, metadane, licencje), a nie je obchodzi. Najlepiej udowodnić na lokalnie uruchomionym portalu. |
| Logotyp i hasło | **25%** | Prawie tyle co technika. Kampania potrzebuje osobnej osoby w zespole. |
| Kreatywność i innowacyjność | 15% | Elementy wyróżniające: QR + weryfikacja społeczna, raport luk, dostępność „teraz”, analiza pokrycia. |
| Zgodność z tematem | 15% | Zbieranie danych z wielu źródeł + wskazanie zakresu referencyjnego + integracja w jednym zbiorze. |
| Wzorcowy zakres danych | 10% | Dobrze uzasadniony, porównany z OSM i Géo'DAE, z regułami walidacji. |
| Prezentacja | 5% | Kompletność. |

Wniosek: **55% punktów to zgodność z portalem i kampania.** Rozbudowana aplikacja mapowa dla obywateli to w tym konkursie rzecz drugorzędna – użytkownikiem docelowym jest de facto *dysponent danych* i *portal*.

### 2.4. Wnioski z `tips.txt`

1. **Instrukcja dla jury** w ponumerowanych krokach: który plik otworzyć, jak go odczytać, gdzie sprawdzić każde wymaganie. → Zrobić tabelę „wymaganie → plik/ekran → jak sprawdzić”.
2. **Klikalny prototyp** przechodzący cały proces od początku do końca bez konfiguracji. → Hosting (GitHub Pages/Vercel/Netlify) + dane demonstracyjne.
3. **Uruchomić portal we własnym środowisku** z otwartego kodu i pokazać, że rozwiązanie działa z jego mechanizmami. → To jest wprost podpowiedź, jak zdobyć 30%.
4. **Właściwy problem:** dane są rozproszone i *niezweryfikowane – nikt nie bierze za nie odpowiedzialności*. → Kluczowe pole w schemacie: dysponent + data weryfikacji + status.
5. **Logo i hasło** są do akcji promocyjnej skierowanej do *potencjalnych dostawców danych*, nie do pitchu.
6. **Nie można przebudować portalu tak, by każdy publikował.** Potrzebny jest dostawca (instytucja, firma), który bierze odpowiedzialność za zbiór. → Crowdsourcing tylko jako *sygnał* do dysponenta, nigdy jako bezpośrednia publikacja.

### 2.5. Prawa autorskie – konsekwencje

- Zwycięzcy przenoszą autorskie prawa majątkowe na Ministra Cyfryzacji (kod, dokumentacja, logo). Wszystko musi być wolne od wad prawnych.
- **Kod dane.gov.pl jest na licencji GPL‑3.0** – modyfikacje portalu muszą pozostać na GPL. Bezpieczniej: nasze narzędzia jako osobne aplikacje korzystające z API/harvestera, a ewentualne zmiany w mcod jako osobny, jasno opisany patch.
- **Dane OpenStreetMap są na ODbL (share-alike)** – nie można ich po prostu wgrać do zbioru na CC0/CC BY. Patrz rozdział 8.
- Fonty, ikony i zdjęcia w logo/prototypie – tylko na licencjach pozwalających na przeniesienie i użycie komercyjne (np. OFL dla fontów).

---

## 3. Stan obecny – research

### 3.1. Kontekst prawny i instytucjonalny w Polsce

- **Brak ustawowego, krajowego rejestru AED** i brak obowiązku rejestracji urządzeń. Jedyna „rejestracja” to techniczna rejestracja u producenta (serwis, elektrody, bateria).
- **Interpelacja nr 16205** (poseł P. Jaskulski, 26.03.2026, do MSWiA) – pyta m.in. o:
  - AED kupowane w ramach **Programu Ochrony Ludności i Obrony Cywilnej (OLiOC)** trafiające do zamkniętych szaf pancernych i magazynów („gotowość na godzinę W”) zamiast do miejsc ogólnodostępnych,
  - ogólnopolski **standard oznakowania i ewidencji AED** oraz integrację z dyspozytorami 112.
- **Odpowiedź MSWiA** (podsekretarz stanu W. Leśniakiewicz, 15.04.2026):
  - operatorzy numerów **112, 997 i 998 mają podkład mapowy z lokalizacjami AED – dane pobierane z openaedmap.org**, importowane na stanowiska operatorów i cyklicznie aktualizowane,
  - standard oznakowania i ewidencji AED oraz integracja z **Systemem Wspomagania Dowodzenia PRM (SWD PRM)** „wykraczają poza kompetencje” MSWiA – należą do **Ministra Zdrowia**,
  - tworzenie lokalnych sieci AED to inicjatywa JST,
  - wspomniano aplikację **Pierwszy Ratownik** (Związek OSP RP) – powiadamianie wolontariuszy, lokalizacja AED.
- W 2024 r. na **geoportal.gov.pl** dodano warstwę „Defibrylatory” (w „Obiekty użyteczności publicznej”) – na bazie porozumienia Głównego Geodety Kraju ze Stowarzyszeniem OpenStreetMap Polska, czyli również dane OSM.
- W 2023 r. Centrum e-Zdrowia objęło patronatem mapę AED opartą na OSM i zapowiadało ją w mojeIKP **[do weryfikacji – brak działającej mapy w mojeIKP wg cardiomedico]**.

**Wniosek:** państwo już *de facto* opiera ratownictwo na danych społecznościowych bez gwarancji jakości i bez odpowiedzialnego dysponenta. Nasze rozwiązanie wypełnia dokładnie tę lukę: dane z odpowiedzialnością, publikowane przez instytucje na dane.gov.pl.

### 3.2. OpenAEDMap / OpenStreetMap – analiza jakości danych

OpenAEDMap (openaedmap.org) prowadzi Stowarzyszenie OpenStreetMap Polska; dane z OSM, licencja ODbL, eksport `https://openaedmap.org/api/v1/countries/PL.geojson`.

Analiza eksportu z 21.11.2026 (**18 297 AED w Polsce**):

| Atrybut OSM | Wypełnione | Brak | Komentarz |
|---|---|---|---|
| `access` | 16 917 (92,5%) | 1 380 (7,5%) | `yes` 7 806, `customers` 4 683, **`private` 3 045**, `permit` 1 198, `permissive` 132, `no` 47 |
| `indoor` | 15 969 (87%) | 2 328 | `yes` 10 481, `no` 5 488 |
| `defibrillator:location` | 12 317 (67%) | 5 980 | opis „gdzie dokładnie wisi” |
| `opening_hours` | 6 781 (37%) | **11 516 (63%)** | `24/7` – 4 136 |
| `operator` | 6 007 (33%) | 12 290 | brak wskazania dysponenta w 2/3 przypadków |
| `check_date` | 5 981 (33%) | **12 316 (67%)** | najwięcej weryfikacji w 2026 (2 980) i 2025 (1 672) |
| `phone` | 4 481 (24%) | 13 816 | |
| `image` | 2 168 (12%) | 16 129 | |
| `source` | 1 445 (8%) | 16 852 | m.in. „email od ZUS” (174), „API UM Warszawa” (94), Koszalin (31) |
| `locked` | 3 | ~100% | informacja o zamknięciu szafki praktycznie nie istnieje |

Inne obserwacje:
- tylko 40% obiektów było edytowanych więcej niż raz (`@osm_version > 1`),
- ~3 000 urządzeń jest oznaczonych jako prywatne (`access=private`) – w nagłym zdarzeniu bezużyteczne lub o niejasnym statusie,
- ponad 600 obiektów ma tag `fixme` (ktoś zgłosił problem).

**Wniosek:** OSM świetnie sprawdza się jako *źródło porównawcze i wykrywacz luk*, ale nie jako zbiór referencyjny – brak dysponenta, dostępności czasowej, weryfikacji i statusu technicznego.

### 3.3. Inne istniejące źródła danych o AED w Polsce

| Źródło | Prowadzący | Charakter | Uwagi |
|---|---|---|---|
| OpenAEDMap / OSM | OSM Polska | społecznościowe, ODbL | używane przez 112/997/998, geoportal |
| Pierwszy Ratownik (1R) | Związek OSP RP + PZU | aplikacja, wolontariusze | dodawanie AED przez użytkowników obecnie niedostępne **[do weryfikacji]** |
| Ratuj z Sercem | prywatne | własna baza | niezsynchronizowana z OSM, ograniczenia licencyjne |
| Staying Alive | stowarzyszenie (FR) | aplikacja, zgłoszenia użytkowników | |
| aedmapa.pl / „Mapa AED – defibrylatory” | autor niezależny | aplikacja, dane z OSM | |
| Warszawa 19115 + API UM Warszawa | Urząd m.st. Warszawy | formularz zgłoszeń, dane otwarte | też na dane.gov.pl (zbiór 39512) |
| Kraków „Krakowski IMPULS ŻYCIA AED” | UM Krakowa | lista urządzeń miejskich | brak formularza dla prywatnych |
| BIP-y i strony gmin, powiatów, PSP | JST, KM/KP PSP | listy HTML/PDF | rozproszone, nienadające się do maszynowego odczytu |
| Producenci/dystrybutorzy AED | firmy | rejestracje serwisowe | najlepsza wiedza o datach ważności elektrod/baterii |
| Właściciele dużych sieci | ZUS, PKP, uczelnie, sieci handlowe, stacje paliw | wewnętrzne ewidencje | potencjalni „duzi dostawcy” jednym zbiorem |

### 3.4. Zbiory o AED już opublikowane na dane.gov.pl

Wyszukane przez `https://api.dane.gov.pl/1.4/search?q=defibrylator` i `?q=AED`:

| Dysponent | Zbiór (ID) | Format | Licencja | Częstotliwość | Problemy |
|---|---|---|---|---|---|
| Urząd Miasta Krosna | 3624 | CSV | CC0 1.0 | „Nie dotyczy” | kolejność lon, lat; spacje w nagłówkach; brak dostępności i dat |
| Urząd Miasta Marki | 4955 | CSV + XLSX | CC BY 4.0 | jednorazowo | **CSV uszkodzony**: każdy wiersz w całości w cudzysłowie, a współrzędne w kolejności lat, lon mimo nagłówka „Długość, Szerokość” |
| Urząd Miejski w Przemyślu | 4581 | CSV, JSON, GeoJSON, GML | CC0 1.0 | codziennie | separator `;`, geometria jako GeoJSON wklejony do kolumny CSV, długi opis-ulotka zamiast danych, zasób jako link do CMS |
| Urząd m.st. Warszawy | 39512 | JSON (link zewnętrzny) | CC BY 4.0 | brak | zasób to odnośnik do katalogu miejskiego |
| Legionowo | 40593 | CSV | – | – | **najlepszy przykład**: adres rozbity na pola, `kod_terc`, `kod_simc`, osobne kolumny współrzędnych |

Przykładowe nagłówki (dosłownie z plików):

```text
Krosno:     Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id
Marki:      "Długość geograficzna,Szerokość geograficzna, Nazwa, Lokalizacja, Adres, Numer Id"
            "52.326697, 21.107557,""Defibrylator"",""Urząd Miasta Marki "",..."
Przemyśl:   id;name;description;category;city;street;home_number;postcode;phone;email;www;youtube_url;panorama_url;geometry;gallery;attachments;links
Legionowo:  nazwa,cecha_ulicy,nazwa_ulicy,nr_budynku,nr_lokalu,kod_pocztowy,miejscowosc,kod_terc,kod_simc,szerokosc_geograficzna,dlugosc_geograficzna
```

**Wniosek:** 5 dysponentów = 5 różnych schematów, 2 różne kolejności współrzędnych, 2 separatory, 1 plik niepoprawny. Żaden nie zawiera dostępności czasowej, daty weryfikacji ani statusu technicznego. To idealny materiał do slajdu „dlaczego potrzebny jest wzorzec” i do demonstracji walidatora/konwerterów.

### 3.5. Wzorce zagraniczne

**Francja – Géo'DAE (najbliższy wzorzec)**
- Podstawa prawna: ustawa nr 2018-527, dekret 2018-1259, rozporządzenie z 29.10.2019 → **obowiązek deklarowania** publicznie dostępnych AED przez operatorów.
- Prowadzi Direction Générale de la Santé (odpowiednik MZ); deklaracja bezpośrednio lub przez platformę GéoDAE (atlasante.fr).
- **Oficjalny schemat danych** `atlasante/schema-dae` opublikowany na schema.data.gouv.fr (specyfikacja pliku wymiany), z szablonami CSV/XLSX; walidacja przez narzędzie Validata.
- Publikacja na data.gouv.fr jako open data (CSV + JSON); publikowane są tylko AED w dostępie publicznym.
- Wiele gmin publikuje własne zbiory zgodne ze schematem → dokładnie model federacyjny, który proponujemy.

**Wielka Brytania – The Circuit (National Defibrillator Network)**
- Prowadzi British Heart Foundation z NHS England, Resuscitation Council UK, St John Ambulance, AACE.
- **Wszystkie 14 służb pogotowia** korzysta z rejestru; publiczna wyszukiwarka Defib Finder.
- Model „opiekuna” (guardian): osoba/organizacja odpowiedzialna za urządzenie; konta pojedyncze i organizacyjne (import Excel).
- Dane: adres i opis miejsca, producent, model, numer seryjny, dni i godziny dostępności (także okresy niedostępności), daty ważności elektrod, potwierdzenie gotowości, kod do szafki (tylko dla dyspozytora), punkt na mapie, kontakt do opiekuna.
- **Przypomnienia co 3 miesiące** o kontroli gotowości, e-maile przed wygaśnięciem elektrod, eskalacja przy braku kontroli, status „wycofany z użytku”.
- Po użyciu AED przez dyspozytora opiekun dostaje e-mail i musi przywrócić status „Emergency Ready”.
- Statusy rekordu: szkic, wymaga działania, **potencjalny duplikat (ten sam kod pocztowy)**, oczekujący, zarejestrowany. Tylko „zarejestrowane” widzą pogotowia.

**Dania – Hjertestarter.dk (TrygFonden)**
- Rejestracja dobrowolna, a mimo to ~21 150 AED (2022); od 2011 powiązanie z dyspozytorniami medycznymi.
- Walidacja zgłaszanych informacji, publiczna mapa, rejestr wykorzystywany w badaniach naukowych (dostępność AED a przeżywalność).

**Wytyczne ERC 2025 / Resuscitation Council UK 2025**
- Systemy dyspozytorskie i systemy powiadamiania pierwszych ratowników powinny być **zintegrowane z rejestrami AED**.
- AED powinny być w **niezamykanych** szafkach, dostępne 24/7.
- ERC zaleca zgłaszanie każdego publicznego AED do lokalnego systemu ratunkowego.

### 3.6. Tagowanie OSM `emergency=defibrillator` – punkt odniesienia

| Tag | Znaczenie |
|---|---|
| `emergency=defibrillator` | tag główny (tylko węzeł) |
| `access` | ograniczenia dostępu (`yes`, `customers`, `private`, `permit`…) |
| `opening_hours` | godziny dostępności (składnia opening_hours) |
| `indoor` | wewnątrz/na zewnątrz budynku |
| `level`, `level:ref` | piętro |
| `defibrillator:location` (+ `:pl`, `:en`) | opis miejsca słowami |
| `locked` | czy szafka/urządzenie zamknięte |
| `defibrillator:cabinet` | typ szafki |
| `defibrillator:code` | kod do szafki (dyskusyjne publikowanie) |
| `phone`, `emergency:phone` | telefon odpowiedzialnego / alarmowy |
| `operator`, `manufacturer`, `model`, `description`, `check_date`, `image` | pozostałe |

Nasz schemat powinien mieć **jednoznaczne mapowanie** do tych tagów (ułatwia konwersję w obie strony i współpracę z OpenAEDMap, z którego korzysta 112).

---

## 4. Jak działa dane.gov.pl – mechanika, którą trzeba uszanować

### 4.1. Model danych portalu

```text
Dostawca (instytucja)  ──<  Zbiór danych (dataset)  ──<  Zasób (resource: plik / API / link)
```

- **Dostawca** to zarejestrowana instytucja: podmiot publiczny albo **dostawca prywatny** (firma), weryfikowany np. Profilem Zaufanym osoby reprezentującej. To on odpowiada za zbiór – dokładnie to, czego brakuje danym o AED.
- **Zbiór danych** ma metadane: tytuł i opis (PL/EN), kategorię (np. *Zdrowie*), słowa kluczowe, licencję (CC0 / CC BY 4.0 / inne), częstotliwość aktualizacji, warunki użycia, flagi: dane dynamiczne, dane wysokiej wartości (w tym z wykazu KE), dane badawcze.
- **Zasób** ma: format, `dataDate` (data aktualności danych), dostępność (plik kopiowany do portalu albo serwowany zdalnie), znaki umowne (puste wartości w widoku tabelarycznym), flagę „zawiera dane chronione (DGA)”. Portal potrafi generować widok tabelaryczny i mapę oraz pochodne formaty (CSV, JSON‑LD).
- Metadane w profilu **DCAT‑AP‑PL 2.1** (polska aplikacja DCAT‑AP) – portal jest harwestowany przez data.europa.eu.
- Funkcje dla użytkowników: wyszukiwarka, **„Zgłoś uwagi”** do zbioru, propozycje nowych danych, przykłady wykorzystania (showcase), subskrypcje/powiadomienia.

### 4.2. Harvester XML – precedens „deweloperski”

Od 2025 r. (ustawa z 21.05.2025 o zmianie ustawy o ochronie praw nabywcy lokalu…) **każdy deweloper w Polsce musi codziennie publikować ceny mieszkań na dane.gov.pl**. Centralny Ośrodek Informatyki wydał „Instrukcję przygotowania pliku XML” (v1.0.6, 18.11.2025). Mechanizm:

1. Deweloper rejestruje się jako dostawca prywatny.
2. Udostępnia na swoim serwerze **plik XML (manifest)** opisujący zbiory i zasoby; zasoby to linki do plików CSV/XLSX.
3. Harvester portalu cyklicznie pobiera manifest, **waliduje go względem XSD** i tworzy/aktualizuje zbiory i zasoby.

Struktura (wg instrukcji COI):

```xml
<p:datasets>
  <dataset status="published">
    <extIdent>…stały identyfikator, max 36 znaków…</extIdent>
    <title><polish>…</polish><english>…</english></title>
    <description><polish>…</polish><english>…</english></description>
    <url>…strona opisująca zbiór…</url>
    <categories><category>HEAL</category></categories>
    <conditions>…</conditions>
    <resources>
      <resource status="published">
        <extIdent>…</extIdent>
        <url>https://…/aed-gmina-xyz-2026-11-21.csv</url>
        <title><polish>…</polish><english>…</english></title>
        <description><polish>…</polish><english>…</english></description>
        <availability>local</availability>   <!-- local | remote -->
        <dataDate>2026-11-21</dataDate>
        <specialSigns><specialSign>X</specialSign></specialSigns>
        <hasDynamicData>false</hasDynamicData>
        <hasHighValueData>true</hasHighValueData>
        <hasHighValueDataFromEuropeanCommissionList>false</hasHighValueDataFromEuropeanCommissionList>
        <hasResearchData>false</hasResearchData>
        <containsProtectedData>false</containsProtectedData>
      </resource>
    </resources>
    <tags>…</tags>
    <updateFrequency>daily</updateFrequency>
    <hasDynamicData>false</hasDynamicData>
    <hasHighValueData>true</hasHighValueData>
    <hasHighValueDataFromEuropeanCommissionList>false</hasHighValueDataFromEuropeanCommissionList>
    <hasResearchData>false</hasResearchData>
  </dataset>
</p:datasets>
```

Istotne reguły z instrukcji:
- `extIdent` zbioru i zasobu **nie może się zmieniać** – zmiana = nowy obiekt i ponowne pobranie pliku.
- Nowe dane = nowy `<resource>` z nowym `extIdent` (np. z datą) albo aktualizacja pliku pod tym samym URL.
- Opisy do 1000 znaków, tytuły do 300, obowiązkowo PL i EN.

Wg bloga AD Software **[do weryfikacji w kodzie mcod]**: namespace `urn:otwarte-dane:harvester:1.13`, `licenseId` wymagane od v1.13, harvest codziennie ok. 04:00, przy niezgodności z XSD zbiór nie zostaje aktywowany, walidacja lokalna `xmllint --schema otwarte_dane_latest.xsd feed.xml --noout`.

**Dlaczego to kluczowe:** udowadnia, że portal *już* obsługuje scenariusz „wielu dostawców, jeden ustandaryzowany typ danych, codzienna automatyczna aktualizacja”. Proponując ten sam mechanizm dla AED, nie przebudowujemy portalu – używamy go zgodnie z przeznaczeniem.

### 4.3. Pozostałe kanały zasilania i odczytu

- Ręczne dodawanie zbiorów/zasobów w panelu dostawcy (pliki, linki, API).
- Harvester CKAN i DCAT (RDF) – dla instytucji z własnymi portalami (np. Warszawa, Wrocław) **[do weryfikacji]**.
- **Publiczne API** `https://api.dane.gov.pl/1.4/` (bez klucza, JSON:API) – zweryfikowane w tej sesji: `/search?q=`, `/datasets/{id}`, `/datasets/{id}/resources`, `/resources/{id}`, `/institutions/{id}`. Dokumentacja Swagger: `https://api.dane.gov.pl/doc`.
- **Kod źródłowy**: `https://dane.gov.pl/source-code/` (backend 2.63.0, frontend 3.6.1, wydanie z 17.11.2026; GPL‑3.0, opracowany przez KPRM). Mirror: `gitlab.dane.gov.pl/otwarte-dane` (mcod-backend, mcod-frontend). Backend w Pythonie, frontend w TypeScript/Angular **[stos do weryfikacji po pobraniu]**.
- Standard techniczny i Baza wiedzy dla dostawców: `https://dane.gov.pl/pl/knowledgebase/useful-materials`.

### 4.4. Co wolno, a czego nie (wnioski)

| Wolno / warto | Nie wolno / ryzykowne |
|---|---|
| Dostawca = instytucja odpowiedzialna za dane | Publikowanie na dane.gov.pl danych zebranych od „każdego” bez dysponenta |
| Wspólny wzorzec (schemat) + harvester XML | Zmiana modelu uprawnień portalu |
| Zbiór zagregowany publikowany przez wskazaną instytucję, z polem `dysponent` w każdym rekordzie | Agregat bez wskazania źródła i odpowiedzialności |
| Crowdsourcing jako *zgłoszenie do dysponenta* (np. przez „Zgłoś uwagi” albo nasz formularz) | Crowdsourcing jako bezpośrednia publikacja |
| Narzędzia zewnętrzne korzystające z API portalu | Scraping portalu zamiast API |
| Metadane zgodne z DCAT‑AP‑PL, licencja otwarta (CC0 rekomendowana) | Licencje niekompatybilne (np. ODbL w zbiorze CC0) |

---

## 5. Wzorcowy zakres danych – szkic

Zasada nadrzędna: **jeden wiersz = jedno urządzenie AED**, UTF‑8, separator `,`, kropka dziesiętna, daty ISO 8601, WGS84 (EPSG:4326). Nazwy kolumn bez polskich znaków i spacji (snake_case). Wersja maszynowa schematu: **Frictionless Table Schema (JSON)** – pozwala walidować pliki automatycznie i jest standardem m.in. we Francji.

Legenda wymagalności: **W** – wymagane, **Z** – zalecane, **O** – opcjonalne.

### 5.1. Identyfikacja i odpowiedzialność

| Kolumna | Typ | Wym. | Opis | Przykład | OSM / Géo'DAE |
|---|---|---|---|---|---|
| `aed_id` | string | W | trwały identyfikator nadany przez dysponenta, niezmienny przez cały cykl życia urządzenia | `PL-1408011-0001` | `ref` / `gid` |
| `aed_uuid` | uuid | Z | globalny UUID (do deduplikacji między źródłami) | `0f6c…` | – |
| `dysponent_nazwa` | string | W | instytucja odpowiedzialna za urządzenie i dane | `Urząd Miasta Legionowo` | `operator` |
| `dysponent_regon` | string(9/14) | Z | REGON dysponenta | `013268929` | – |
| `dysponent_typ` | enum | Z | `jst`, `administracja_rzadowa`, `podmiot_leczniczy`, `szkola_uczelnia`, `sluzby`, `ngo`, `firma`, `inny` | `jst` | `operator:type` |
| `kontakt_telefon` | string | Z | telefon **instytucjonalny** (nie prywatny) | `+48 22 766 40 00` | `phone` |
| `kontakt_email` | string | O | e-mail instytucjonalny | `aed@um.legionowo.pl` | `email` |

### 5.2. Lokalizacja

| Kolumna | Typ | Wym. | Opis | Przykład | OSM / Géo'DAE |
|---|---|---|---|---|---|
| `szerokosc` | number | W | WGS84, zakres 49.0–54.9 | `52.395198` | lat |
| `dlugosc` | number | W | WGS84, zakres 14.1–24.2 | `20.931382` | lon |
| `nazwa_obiektu` | string | W | budynek/miejsce | `Urząd Miasta Legionowo` | `name` |
| `miejscowosc` | string | W | | `Legionowo` | `addr:city` |
| `ulica` | string | Z | z cechą (ul., al.) | `ul. Piłsudskiego` | `addr:street` |
| `nr_budynku` | string | Z | | `41` | `addr:housenumber` |
| `kod_pocztowy` | string | Z | `NN-NNN` | `05-120` | `addr:postcode` |
| `kod_teryt_gminy` | string(7) | W | TERYT TERC gminy z rodzajem – klucz do statystyk i raportu luk | `1408011` | – |
| `kod_simc` | string(7) | Z | identyfikator miejscowości | `0920806` | – |
| `kod_ulic` | string(5) | O | identyfikator ulicy | | – |
| `opis_lokalizacji` | string | W | gdzie dokładnie wisi, słowami | `Hol główny, przy portierni, na lewo od wejścia` | `defibrillator:location` |
| `opis_lokalizacji_en` | string | O | wersja angielska | `Main hall, next to reception` | `defibrillator:location:en` |
| `wewnatrz_budynku` | boolean | W | | `true` | `indoor` |
| `pietro` | string | O | | `0` | `level` |

### 5.3. Dostępność

| Kolumna | Typ | Wym. | Opis | Przykład | OSM |
|---|---|---|---|---|---|
| `dostepnosc` | enum | W | `publiczna` (każdy), `klienci`, `pracownicy`, `ograniczona` | `publiczna` | `access` |
| `godziny_dostepnosci` | string | W | składnia **opening_hours** (maszynowo przetwarzalna) | `24/7` / `Mo-Fr 07:30-15:30` | `opening_hours` |
| `szafka_zamknieta` | boolean | W | czy dostęp wymaga kodu/klucza | `false` | `locked` |
| `sposob_otwarcia` | enum | Z | `brak`, `kod_od_dyspozytora_112`, `klucz_na_portierni`, `inne` – **samego kodu nie publikujemy** | `brak` | – |
| `szafka_alarm` | boolean | O | szafka z alarmem/powiadomieniem | `true` | – |
| `dostepny_dla_niepelnosprawnych` | boolean | O | dostęp bez barier | `true` | `wheelchair` |
| `okres_niedostepnosci` | string | O | np. sezonowo, remont: `2026-12-24/2026-12-26` | | – |

### 5.4. Urządzenie i stan techniczny

| Kolumna | Typ | Wym. | Opis | Przykład |
|---|---|---|---|---|
| `producent` | string | Z | | `Philips` |
| `model` | string | Z | | `HeartStart FRx` |
| `elektrody_pediatryczne` | boolean | Z | dostępne elektrody/tryb dziecięcy | `true` |
| `data_waznosci_elektrod` | date | Z | | `2028-03-31` |
| `data_waznosci_baterii` | date | Z | | `2030-01-31` |
| `status_gotowosci` | enum | W | `gotowy`, `serwis`, `wycofany` | `gotowy` |

### 5.5. Weryfikacja i pochodzenie

| Kolumna | Typ | Wym. | Opis | Przykład |
|---|---|---|---|---|
| `data_weryfikacji` | date | W | kiedy dysponent fizycznie sprawdził obecność i gotowość | `2026-11-15` |
| `data_aktualizacji` | date | W | ostatnia zmiana rekordu | `2026-11-20` |
| `data_instalacji` | date | O | | `2024-05-10` |
| `zrodlo` | enum | Z | `dysponent`, `agregator`, `import_osm`, `import_bip` – w zbiorze krajowym obowiązkowe | `dysponent` |
| `zdjecie_url` | url | O | zdjęcie lokalizacji (bez wizerunku osób) | |
| `uwagi` | string | O | | |

### 5.6. Reguły walidacji (do walidatora)

- współrzędne w granicach Polski; ostrzeżenie, gdy punkt leży poza gminą z `kod_teryt_gminy` (porównanie z PRG),
- **wykrywanie zamienionych lat/lon** (przypadek Marki),
- `aed_id` unikalne w pliku; ostrzeżenie o duplikatach przestrzennych (< 25 m),
- `godziny_dostepnosci` parsowalne jako opening_hours,
- `data_weryfikacji` nie starsza niż 12 miesięcy (ostrzeżenie), nie z przyszłości (błąd),
- `data_waznosci_elektrod` w przeszłości → ostrzeżenie „urządzenie może nie być gotowe”,
- `dostepnosc=publiczna` + `szafka_zamknieta=true` + `sposob_otwarcia=brak` → niespójność,
- kodowanie UTF‑8, nagłówek zgodny ze wzorcem, brak cudzysłowów wokół całego wiersza.

### 5.7. Metadane zbioru (rekomendacje)

- Tytuł: `Defibrylatory AED – {nazwa dysponenta}`; EN: `AED defibrillators – {name}`.
- Kategoria: Zdrowie (HEAL); tagi: `AED`, `defibrylator`, `ratownictwo`, `zdrowie`, `{nazwa gminy}`, oraz **wspólny tag kampanii** (np. `aed-wzorzec-v1`), po którym agregator wyszukuje zbiory przez API.
- Licencja: **CC0 1.0** (rekomendowana – pozwala bezkonfliktowo zasilać OSM i aplikacje ratownicze), alternatywnie CC BY 4.0.
- Częstotliwość aktualizacji: co najmniej kwartalnie; zalecane codziennie przy harvesterze.
- `hasHighValueData=true` (dane geoprzestrzenne o znaczeniu dla bezpieczeństwa) – do decyzji Ministerstwa.

---

## 6. Pomysły na rozwiązanie

Każdy pomysł: opis, na które kryteria wpływa, trudność (S – mała, M – średnia, L – duża).

### A. Architektura i model odpowiedzialności

**A1. Agregator-dostawca krajowy.** Jedna instytucja publiczna (np. Ministerstwo Zdrowia, Centrum e-Zdrowia, Lotnicze Pogotowie Ratunkowe lub urzędy wojewódzkie) publikuje na dane.gov.pl codziennie zbiór „Defibrylatory AED w Polsce”. Każdy rekord ma pola `dysponent_*`, `zrodlo` i `data_weryfikacji`, więc odpowiedzialność jest jawna na poziomie wiersza. *Kryteria: zgodność 30%, temat. Trudność: M.*

**A2. Federacja (rekomendowane).** Każdy dysponent publikuje *własny* zbiór zgodny ze wzorcem (gmina, szpital, uczelnia, PKP, sieć handlowa). Agregator odnajduje je przez API dane.gov.pl (tag kampanii + walidacja schematu), łączy, deduplikuje i publikuje zbiór krajowy. Odpowiedzialność zostaje u źródła, portal działa dokładnie jak zaprojektowano. Wzorowane na Francji (schemat + wiele zbiorów gminnych + baza krajowa). *Kryteria: zgodność, temat, zakres danych. Trudność: M.*

**A3. „Model deweloperski” – harvester XML dla AED.** Dokładne odwzorowanie mechanizmu z cen mieszkań: dysponent wystawia manifest XML + CSV, portal pobiera codziennie. Dajemy gotowy szablon XML, przykład i instrukcję w stylu instrukcji COI. *Kryteria: zgodność (bardzo mocny argument). Trudność: S–M.*

**A4. Pośrednicy dla małych gmin.** Powiat, związek gmin lub urząd wojewódzki publikuje jeden zbiór w imieniu wielu małych gmin, które nie mają konta dostawcy (np. na podstawie porozumienia). Rozwiązuje problem 2 477 gmin, z których większość nie publikuje nic na dane.gov.pl. *Kryteria: temat, realizm. Trudność: S (organizacyjne).*

**A5. Prywatni dysponenci.** Firmy rejestrują się jako „dostawcy prywatni” (tak jak deweloperzy) albo przekazują dane gminie/agregatorowi przez formularz (z oświadczeniem o odpowiedzialności). Duże sieci (stacje paliw, markety, ZUS, PKP) – jeden zbiór ogólnokrajowy. *Trudność: S.*

**A6. Rekomendacja legislacyjna.** Projekt zapisu w rozporządzeniu MZ / ustawie o PRM: obowiązek zgłaszania publicznie dostępnych AED zgodnie ze wzorcem (jak Francja 2018), oraz warunek w programie OLiOC: AED kupione z programu muszą być publikowane. Część „dokumentacyjna” rozwiązania. *Kryteria: temat, kreatywność. Trudność: S.*

### B. Narzędzia dla dysponentów (obniżenie progu wejścia)

**B1. Kreator „AED Publisher Kit”.** Prosta aplikacja web (WCAG 2.2, mobile): dysponent klika na mapie, wypełnia formularz z podpowiedziami (adres → automatyczne TERYT/SIMC i współrzędne z geokodera, edytor godzin w stylu „od–do” zamiast składni opening_hours), a na końcu pobiera gotowy CSV/XLSX + manifest XML i instrukcję „jak wgrać na dane.gov.pl w 5 krokach”. Bez backendu – dane zostają u dysponenta. *Kryteria: temat, UX, kreatywność. Trudność: M.*

**B2. Walidator online.** Przeciągnij plik → raport błędów i ostrzeżeń po polsku z podpowiedzią naprawy (reguły z 5.6). Demonstracja na realnym, wadliwym pliku z Marek („wykryto zamienione współrzędne w 100% wierszy”). Odpowiednik francuskiego Validata. *Kryteria: zgodność, zakres danych, kreatywność. Trudność: S–M.*

**B3. Konwertery istniejących formatów.** Moduły ETL: Krosno, Marki, Przemyśl, Legionowo, Warszawa, OSM/OpenAEDMap, generyczny „mapuj kolumny” → wzorzec. Pokazuje „zbieranie danych z wielu rozproszonych źródeł ze wskazaniem zakresu referencyjnego” – dosłownie zdanie z treści zadania. *Kryteria: temat 15%. Trudność: S.*

**B4. Import masowy z Excela.** Szablon XLSX z listami rozwijanymi (enumy), walidacją danych i instrukcją w arkuszu. Dla instytucji, które pracują wyłącznie w Excelu. Ten sam plik może być załącznikiem „wzorcowy zakres danych”. *Trudność: S.*

**B5. Asystent pozyskiwania danych z BIP.** Scraper list AED z BIP/stron gmin i komend PSP + LLM do strukturyzacji tekstu/PDF → plik „wstępnie wypełniony – do zatwierdzenia przez gminę”. Gmina tylko sprawdza i publikuje. Człowiek zawsze zatwierdza (zgodne z podejściem do AI w regulaminie). *Kryteria: kreatywność. Trudność: M.*

**B6. Wtyczki do CMS-ów gminnych.** Moduł eksportu „AED wg wzorca” dla popularnych systemów BIP/CMS (np. SkyCMS używany przez Przemyśl, WordPress). Jedno wdrożenie = setki gmin. *Trudność: M–L (poza MVP).*

**B7. Gotowy „pakiet startowy dla gminy”.** ZIP: szablon XLSX, szablon XML, instrukcja PDF/HTML, wzór zarządzenia wójta o wyznaczeniu osoby odpowiedzialnej, wzór naklejki QR. *Kryteria: kampania, temat. Trudność: S.*

### C. Jakość i aktualność danych

**C1. Deduplikacja i łączenie rekordów.** Algorytm: kandydaci w promieniu 25 m + podobieństwo nazwy/adresu (np. Jaro‑Winkler) + zgodność TERYT → wynik pewności. Rekord z dysponentem wygrywa z OSM; konflikty do ręcznego przeglądu. Stosowane w agregatorze krajowym. *Trudność: M.*

**C2. Wskaźnik świeżości.** Każdy rekord ma kolor: zielony (weryfikacja < 3 mies.), żółty (< 12 mies.), czerwony (> 12 mies.). Statystyka świeżości per dysponent i per gmina. *Trudność: S.*

**C3. Przypomnienia dla dysponentów.** Wzorem The Circuit: co 3 miesiące e-mail „potwierdź, że AED jest na miejscu i gotowy” (jeden klik aktualizuje `data_weryfikacji` w pliku dysponenta) oraz alert przed wygaśnięciem elektrod/baterii. Usługa zewnętrzna wobec portalu. *Trudność: M.*

**C4. QR na urządzeniu → weryfikacja społeczna.** Naklejka z kodem QR na szafce AED prowadzi do strony urządzenia: „AED jest na miejscu i działa / brak / zamknięty / uszkodzony”. Zgłoszenie trafia **do dysponenta** (nie na portal), a dysponent aktualizuje dane. Dodatkowo link do mechanizmu „Zgłoś uwagi” na dane.gov.pl. Pozytywne potwierdzenia od obywateli mogą zasilać pole „ostatnio widziany”. *Kryteria: kreatywność, temat, zgodność. Trudność: M.*

**C5. Raport luk dla gminy („gap report”).** Porównanie: ile AED w gminie jest w OSM, a ile w zbiorze dysponenta na dane.gov.pl. „W OSM jest 42 AED w Twojej gminie, w Twoim zbiorze 0 – pobierz wstępnie wypełniony plik”. Świetne narzędzie kampanii. *Kryteria: kreatywność, kampania. Trudność: S–M.*

**C6. Wersjonowanie i wycofywanie.** Urządzenia nie znikają z pliku – dostają `status_gotowosci=wycofany`. Dzięki temu konsumenci (112, aplikacje) wiedzą, że AED usunięto, a nie że rekord zginął przez błąd. Historia przez kolejne zasoby z `dataDate`. *Trudność: S.*

**C7. Monitor jakości zbiorów na dane.gov.pl.** Codzienny job przez API portalu: wyszukuje zbiory o AED, sprawdza zgodność ze wzorcem, publikuje ranking jakości i automatycznie zgłasza problemy przez „Zgłoś uwagi”. *Trudność: M.*

### D. Wykorzystanie danych (pokazanie wartości)

**D1. Mapa „AED dostępne teraz”.** Filtr na podstawie `godziny_dostepnosci` (parser opening_hours) i `dostepnosc` – w nocy pokazuje tylko te AED, do których faktycznie da się dostać. Wprost odpowiada na scenariusz z treści zadania (zamknięte AED). *Kryteria: temat, kreatywność. Trudność: S–M.*

**D2. Eksport dla 112 / SWD PRM.** Feed GeoJSON/CSV w formacie zgodnym z tym, co dziś importują CPR z OpenAEDMap – ale z danymi od dysponentów, statusem gotowości i informacją o sposobie otwarcia szafki. *Trudność: S.*

**D3. Dane dynamiczne – inteligentne szafki.** Szafki z czujnikiem otwarcia/temperatury i łącznością (IoT) raportują status w czasie rzeczywistym → zasób oznaczony `hasDynamicData=true` (API). Pomysł rozwojowy, ale pokazuje świadomość mechanizmu danych dynamicznych portalu. *Trudność: L.*

**D4. Analiza pokrycia.** Izochrony pieszo 3–5 minut wokół AED (OSRM/Valhalla na sieci dróg OSM) nałożone na siatkę gęstości ludności GUS 1 km → mapa „białych plam” i lista rekomendowanych lokalizacji nowych AED dla gmin. *Kryteria: kreatywność. Trudność: M.*

**D5. Widget/embed dla stron gmin.** Fragment HTML wyświetlający mapę AED gminy bezpośrednio z jej zbioru na dane.gov.pl. Nagroda za publikację: gmina dostaje gotową mapę na swoją stronę. *Kryteria: kampania. Trudność: S.*

**D6. PWA „najbliższy AED” z trybem offline.** Lekka aplikacja z kafelkami danych w pamięci podręcznej, nawigacją pieszą, przyciskiem „zadzwoń 112” i instrukcją RKO. Dodatek – nie rdzeń oceny. *Trudność: M.*

**D7. Zwrotne zasilanie OSM.** Dane na CC0 z dane.gov.pl mogą (po uzgodnieniu ze społecznością OSM i wg zasad importu) uzupełniać OSM, a przez to OpenAEDMap i podkład 112. Odwrotny kierunek tylko jako porównanie (ODbL). *Trudność: M (organizacyjnie).*

**D8. Showcase na dane.gov.pl.** Zgłoszenie naszej mapy/walidatora jako „przykład wykorzystania danych” na portalu – pokazuje znajomość funkcji portalu. *Trudność: S.*

### E. Kampania promocyjna (25% punktów)

Odbiorca: **dysponenci AED** – wójtowie, burmistrzowie, dyrektorzy szkół i szpitali, zarządcy obiektów, firmy. Komunikat: „masz AED – opublikuj dane, żeby ktoś mógł go znaleźć w 3 minuty”.

**E1. Propozycje nazw akcji i haseł**

| Nazwa akcji | Hasło | Idea |
|---|---|---|
| **Pokaż AED** | „AED, którego nie widać, nie ratuje.” | prosta, imperatywna, łatwa w hashtagu `#PokażAED` |
| **Mapa Serca** | „Jeden wpis. Jedno uratowane życie.” | emocjonalna, łatwa do zapamiętania |
| **Minuta dla danych** | „Poświęć minutę, żeby ktoś jej nie stracił.” | gra słów: minuta pracy urzędnika vs. minuta przy NZK |
| **AED na mapie** | „Opublikuj. Zaznacz. Uratuj.” | bardzo opisowa |
| **Zaznacz Życie** | „Twój defibrylator na dane.gov.pl to czyjeś życie na mapie.” | zaznaczenie punktu = ratunek |
| **Dane na ratunek** | „Dane, które ratują.” | spójna z nazwą wyzwania |
| **Puls Danych** | „Daj sygnał, gdzie jest Twój AED.” | rytm serca + przepływ danych |
| **Widoczny AED** | „Zamknięty i nieznany AED to tylko pudełko.” | odnosi się do problemu zamkniętych szaf |

**E2. Koncepcje logo**
- Serce połączone z pinezką mapy, wewnątrz błyskawica (symbol AED) – najbardziej czytelne.
- Serce zbudowane z kratek tabeli/pikseli – połączenie „danych” i „życia”.
- Pinezka, której ostrze tworzy linię EKG.
- Tarcza zegara z sercem – „minuty”.
- Znak odwołujący się do międzynarodowego symbolu AED (zielony, ILCOR) – rozpoznawalność, ale bez kopiowania znaku 1:1.
- Kolorystyka: zieleń AED (rozpoznawalna z oznakowania) + czerwień serca + neutralny granat „urzędowy”; sprawdzić kontrast WCAG i wersję monochromatyczną.

**E3. Elementy księgi znaku (minimum z zadania + dobre praktyki)**: koncepcja (3–5 zdań), kolorystyka (HEX/RGB/CMYK/Pantone), pole ochronne, minimalna wielkość (px i mm), wersje (pełna, pozioma, sygnet, mono, negatyw), typografia, niedozwolone użycia (zniekształcenia, zmiana kolorów, cienie, tło o niskim kontraście, obracanie), przykłady aplikacji (naklejka QR na szafkę, baner na stronę gminy, post social media, odznaka „Gmina z AED na mapie”).

**E4. Grywalizacja i ranking.** Publiczny licznik „opublikowanych AED” w Polsce i ranking gmin/województw (% pokrycia, świeżość danych). Odznaka/certyfikat „Gmina z AED na mapie” do umieszczenia na stronie. *Trudność: S.*

**E5. Materiały do akcji.** Pismo przewodnie Ministerstwa do JST, checklista „5 kroków do publikacji”, krótki film instruktażowy, szablon posta, naklejka z QR na szafkę AED, webinar dla urzędników. *Trudność: S.*

**E6. Kanały i partnerzy.** Związek OSP RP (Pierwszy Ratownik), PCK, WOŚP (która przekazywała AED), PSP, OSM Polska, Związek Miast Polskich, Związek Gmin Wiejskich, NFZ, ZUS, PKP, sieci handlowe i stacje paliw. Momenty kampanii: Europejski Dzień Przywracania Czynności Serca (16 października), Światowy Dzień Serca (29 września).

**E7. Wpięcie w program OLiOC.** Rekomendacja: AED zakupione z programu ochrony ludności muszą być zgłoszone wg wzorca i opublikowane – kampania ma natychmiastową, dużą grupę docelową. *Trudność: S (rekomendacja).*

### F. Prototyp, dowody i prezentacja

**F1. Lokalny dane.gov.pl z harvesterem AED.** Uruchomienie mcod (backend + frontend z `dane.gov.pl/source-code/`, prawdopodobnie Docker Compose) i pokazanie na zrzutach: konto dostawcy „Gmina Demo”, harvester pobiera nasz manifest XML, zbiór AED pojawia się w portalu z widokiem tabeli/mapy, a API zwraca dane. Bezpośrednio realizuje wskazówkę nr 3 z `tips.txt` i kryterium 30%. *Trudność: M–L (zależy od kodu).*

**F2. Klikalny prototyp bez instalacji.** Statyczna strona (GitHub Pages/Vercel) z: kreatorem, walidatorem, podglądem zbioru zagregowanego, mapą „dostępne teraz”, raportem luk. Dane demonstracyjne z prawdziwych zbiorów (Krosno, Marki, Przemyśl, Legionowo, Warszawa) po konwersji. *Trudność: M.*

**F3. Instrukcja dla jury.** Tabela: wymaganie z treści → plik/ekran → jak sprawdzić (ponumerowane kroki). Plus nagranie 2–3 min ścieżki od początku do końca. *Trudność: S.*

**F4. Dowody WCAG 2.2 i RWD.** Raport z narzędzi (axe, Lighthouse, WAVE), test klawiaturą i czytnikiem ekranu, zrzuty z telefonu i desktopu – na slajdach jako „dowody realizacji wymagań technicznych”. *Trudność: S.*

**F5. Deklaracja użycia AI.** Osobny plik/slajd: do czego użyto AI (research, szkic kodu, tłumaczenia), co zrobił człowiek (decyzje, weryfikacja, projekt, logo). *Trudność: S.*

---

## 7. Rekomendowany kierunek (MVP na hackathon)

**Koncepcja:** „Wzorzec + harvester + narzędzia + kampania”.

1. **Wzorcowy zakres danych** (rozdział 5) → `wzorzec-aed.xlsx` (z arkuszami: pola, słowniki, przykład, instrukcja) + `aed-schema.json` (Table Schema) + przykładowy `aed-przyklad.csv`.
2. **Szablon manifestu XML** dla harvestera dane.gov.pl + instrukcja w stylu COI (A3).
3. **Konwertery** 5 istniejących zbiorów z dane.gov.pl + OSM do wzorca (B3) – dowód „zbierania z rozproszonych źródeł”.
4. **Agregator** (A2 + C1): pobiera zbiory przez API dane.gov.pl, waliduje, deduplikuje, oznacza źródło i świeżość, generuje zbiór krajowy CSV/GeoJSON + manifest XML dla instytucji-agregatora.
5. **Aplikacja web** (F2): kreator (B1), walidator (B2), raport luk (C5), mapa „dostępne teraz” (D1), strona urządzenia z QR (C4).
6. **Lokalny dane.gov.pl** (F1) – próba uruchomienia i pokazania harvestowania; jeśli się nie uda w czasie, zrzuty z API produkcyjnego + makieta i uczciwy wpis w „ograniczeniach”.
7. **Kampania** (E): nazwa, hasło, logo (SVG → PNG/JPG/PDF), księga znaku PDF, 2–3 materiały aplikacyjne (naklejka QR, baner, odznaka).
8. **Prezentacja + instrukcja dla jury + deklaracja AI** (F3–F5).

Proponowany podział ról: (1) dane i schemat + konwertery, (2) agregator + API, (3) frontend WCAG, (4) mcod lokalnie + harvester, (5) grafik/kampania + prezentacja.

---

## 8. Ryzyka i ograniczenia

| Ryzyko | Opis | Mitygacja |
|---|---|---|
| Licencja ODbL (OSM) | Dane z OSM nie mogą trafić do zbioru CC0/CC BY | OSM tylko do porównań, raportu luk i podpowiedzi dla dysponenta, który sam weryfikuje i publikuje własne dane |
| Licencja GPL‑3.0 (mcod) | Zmiany w kodzie portalu muszą być na GPL; prawa przechodzą na MC | Nasze narzędzia jako osobne aplikacje; zmiany w mcod jako osobny patch |
| RODO | Telefony/e-maile opiekunów to dane osobowe | Tylko kontakty instytucjonalne; brak imion i nazwisk w danych otwartych |
| Bezpieczeństwo | Publikacja kodów do szafek = ryzyko kradzieży | Publikujemy tylko `sposob_otwarcia` (np. „kod od dyspozytora 112”), kody poza danymi otwartymi |
| Brak podstawy prawnej | Bez obowiązku dysponenci mogą nie publikować | Kampania + rekomendacja legislacyjna (wzór FR) + warunek w OLiOC; Dania pokazuje, że dobrowolność też działa przy dobrej kampanii |
| Jakość danych od dysponentów | Pliki jak z Marek | Walidator, szablony, harvester z XSD, monitor jakości |
| Odpowiedzialność prawna dysponenta | Obawa przed odpowiedzialnością za „zły” wpis | Jasna informacja: dane z datą weryfikacji; to stan na dzień, nie gwarancja |
| Uruchomienie mcod | Duży kod (~84 MB backend), zależności (bazy, wyszukiwarka) | Zarezerwować czas; plan B: dowody z API produkcyjnego |
| Wybór agregatora | Nie wiadomo, kto (MZ, CeZ, LPR, wojewodowie) | Rozwiązanie neutralne – dowolna instytucja może być agregatorem |
| Niezgodność z mechaniką portalu | Pokusa „każdy publikuje” | Crowdsourcing wyłącznie jako zgłoszenia do dysponentów |

---

## 9. Checklista oddania

- [ ] Tytuł i szczegółowy opis projektu (README / PDF)
- [ ] Prezentacja ≥ 5 slajdów: zrzuty ekranu jako dowody, opis funkcji i kroków użytkownika, lista ograniczeń
- [ ] Link do klikalnego prototypu (bez konfiguracji)
- [ ] `wzorzec-aed.xlsx` – wzorcowy zakres danych (+ CSV przykład, JSON Table Schema, szablon XML)
- [ ] Kod źródłowy (repozytorium, licencja, instrukcja uruchomienia)
- [ ] Logo: `.svg` (otwarty), `.png`, `.jpg`, `.pdf`
- [ ] Księga znaku `.pdf` (kolorystyka, pole ochronne, min. wielkość, niedozwolone użycia, 3–5 zdań koncepcji)
- [ ] Instrukcja dla jury: wymaganie → plik → jak sprawdzić
- [ ] Deklaracja zakresu użycia AI
- [ ] Dowody WCAG 2.2 i responsywności
- [ ] Dowód zgodności z dane.gov.pl (lokalny portal / API / harvester)

---

## 10. Źródła

Oficjalne:
- Treść zadania i regulamin – `docs/MC DZD - Pełna treść zadania konkursowego-1.pdf`, `docs/MC DZD - Regulamin zadania konkursowego-1.pdf`, wskazówki – `docs/tips.txt`
- [Interpelacja nr 16205 – treść](https://api.sejm.gov.pl/sejm/term10/interpellations/16205/body)
- [Odpowiedź MSWiA na interpelację 16205 (DT7HSX)](https://api.sejm.gov.pl/sejm/term10/interpellations/16205/reply/DT7HSX/body)
- [Kod źródłowy dane.gov.pl](https://dane.gov.pl/source-code/)
- [Baza wiedzy dane.gov.pl – materiały](https://dane.gov.pl/pl/knowledgebase/useful-materials)
- [DCAT-AP-PL 2.1](https://dane.gov.pl/dcat-ap-pl/)
- [Standard techniczny dane.gov.pl](https://dane.gov.pl/media/ckeditor/2020/06/16/standard-techniczny.pdf)
- [API dane.gov.pl – dokumentacja](https://api.dane.gov.pl/doc)
- [COI – Instrukcja przygotowania pliku XML (deweloperzy), v1.0.6](https://assets.basehub.com/9f5f0c1c/c1aa71c8f576c4373a5fb048d901eaff/dane.gov.plinstrukcjazasilaniaxmldladeweloperow1.0.620251121v2.pdf)
- [Monitor Polski 2021 poz. 290 – Program otwierania danych](https://monitorpolski.gov.pl/M2021000029001.pdf)
- Zbiory AED na dane.gov.pl: [Krosno](https://api.dane.gov.pl/1.4/datasets/3624), [Marki](https://api.dane.gov.pl/1.4/datasets/4955), [Przemyśl](https://api.dane.gov.pl/1.4/datasets/4581), [Warszawa](https://api.dane.gov.pl/1.4/datasets/39512), [Legionowo](https://api.dane.gov.pl/1.4/datasets/40593)
- [Géo'DAE – baza krajowa (data.gouv.fr)](https://www.data.gouv.fr/datasets/geodae-base-nationale-des-defibrillateurs)
- [Schemat DAE (schema.data.gouv.fr)](https://schema.data.gouv.fr/atlasante/schema-dae/)
- [The Circuit – National Defibrillator Network (UK)](https://www.thecircuit.uk/) i [FAQ](https://www.thecircuit.uk/frequently-asked-questions)
- [Hjertestarter.dk (DK)](https://www.hjertestarter.dk/english)
- [Resuscitation Council UK – Systems saving lives 2025](https://www.resus.org.uk/professional-library/2025-resuscitation-guidelines/systems-saving-lives-guidelines)
- [ERC Guidelines 2025 – Systems Saving Lives (wersja do konsultacji)](https://cprguidelines.eu/assets/other-documents/ERC-Guidelines-2025-Systems-Saving-Lives_final-for-public-comments.pdf)

Społecznościowe / techniczne:
- [OpenAEDMap – eksport PL (GeoJSON)](https://openaedmap.org/api/v1/countries/PL.geojson)
- [OpenAEDMap – Software Design Document](https://github.com/openstreetmap-polska/openaedmap-sdd)
- [OSM Polska – Mapa defibrylatorów](https://openstreetmap.org.pl/2022/mapa-defibrylatorow-aed-na-terenie-polski/)
- [OSM Wiki – Tag:emergency=defibrillator](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator)
- [Forum OSM – Mapa AED, nakładka dla Polski](https://community.openstreetmap.org/t/mapa-aed-defibrylatory-drobna-nakladka-tematyczna-dla-polski/94736)
- [Badania nad duńskim rejestrem AED (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9374329)

Nieoficjalne (traktować ostrożnie):
- [cardiomedico.com – Mapa AED w Polsce (blog sprzedawcy, 30.09.2026)](https://cardiomedico.com/Mapa-AED-jak-znalezc-defibrylator-i-jak-zglosic-wlasny-AED-na-mape-blog-pol-1790894995.html)
- [AD Software – rejestracja zbioru deweloperskiego na dane.gov.pl (blog)](https://adsoftware.pl/dane-gov-pl-rejestracja-deweloper/)
- [Mirror mcod-backend (GitHub, ecosyste.ms)](https://repos.ecosyste.ms/hosts/GitHub/repositories/olekstomek%2Fmcod-backend-dane.gov.pl)
