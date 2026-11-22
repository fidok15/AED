# Panel portalu krok po kroku: zbiór „Krajowy rejestr AED”

Instrukcja dla osoby, u której działa lokalny fork portalu (`backend/`, panel `http://localhost:8001`, API `http://localhost:8000`, uruchomione z `docker-compose.aed-ports.yml`). Na serwerze pod domeną (`docs/wdrozenie-serwer.md`) panel to `https://admin.<domena>`, API `https://api.<domena>`, a obejście HTTPS z rozdziału 3 jest niepotrzebne. Cel: zrobić zrzuty, które pokazują, że zbiór krajowy trafia do portalu jego własnymi mechanizmami. Dostawcą zbioru jest ministerstwo.

Odwołania `plik:linia` dotyczą katalogu `backend/mcod/`, chyba że podano inaczej. Na końcu jest lista tego, co sprawdzono uruchomieniem, a co tylko w kodzie.

Potrzebne: konto `admin@mcod.local` / `testadmin123!`, działający kontener Celery (`mcod-local-celery`) – bez niego plik nie zostanie przetworzony, a przycisk sprawdzania XML nie odpowie.

## 0. Przygotowanie (2 min)

1. W katalogu głównym repozytorium uruchom prototyp z aktualnego kodu: `docker compose up --build -d`. Zasilanie XML jest tylko w nowej wersji usługi.
2. Sprawdź: `curl -s http://localhost:8080/api/aed/eksport/dane-gov-pl.md5` zwraca 32 znaki.

## 1. Instytucja i zbiór (4 min)

### Instytucja „Ministerstwo Cyfryzacji”

Panel → Instytucje → Dodaj. Wymagane pola formularza (`organizations/forms.py:15-66`, `organizations/models.py:65-112`):

| Pole | Wartość | Uwagi |
|---|---|---|
| Nazwa | Ministerstwo Cyfryzacji | maks. 110 znaków (`forms.py:16`) |
| Rodzaj instytucji | Administracja rządowa (`state`) | `organizations/models.py:34-40` |
| Kod pocztowy, Miasto, Ulica, Typ ulicy | dane siedziby | kod w formacie `00-000` (`forms.py:53`) |
| E-mail | adres instytucjonalny | `forms.py:66` |
| Telefon | 7–9 cyfr bez spacji | `lib/forms/fields.py:16-19` |
| REGON | prawdziwy REGON ministerstwa z BIR GUS; na lokalne demo dowolny z poprawną sumą kontrolną, np. `123456785` | `forms.py:54` (walidacja sumy kontrolnej) |
| Status | opublikowany | zbioru nie da się opublikować w instytucji „szkic” (`datasets/forms.py:276-293`) |

EPUAP, faks, skrót, strona WWW są opcjonalne (`forms.py:38`, `55`, `73-78`).

### Zbiór (tylko wariant A)

W wariancie B zbiór zakłada harvester – nie twórz go ręcznie, bo powstałyby dwa zbiory. Panel → Zbiory danych → Dodaj. Wymagane (`datasets/forms.py:30-178`):

| Pole | Wartość |
|---|---|
| Tytuł | Krajowy rejestr AED |
| Opis | min. 20 znaków (`forms.py:43-55`); można skopiować `FEED_DESCRIPTION` z `aed_service/app.py` |
| Instytucja | Ministerstwo Cyfryzacji |
| Kategorie | Zdrowie (kod `HEAL`, `categories/migrations/0011_datamigration_create_basic_dcat_categories.py:56-58`); pole wymagane (`forms.py:150`) |
| Słowa kluczowe (PL) | AED, defibrylator, pierwsza pomoc, zdrowie; wymagane (`forms.py:161`) |
| Częstotliwość aktualizacji | Codziennie (`daily`); „Nie dotyczy” jest odrzucane (`forms.py:295-303`) |
| E-mail do powiadomień o aktualizacji | adres redaktora; wymagany (`forms.py:164`) |
| Dane dynamiczne / wysokiej wartości / z wykazu KE / badawcze | Nie (pola wymagane, `forms.py:92-138`) |
| Warunki: informacja o źródle i o przetworzeniu | zaznaczone |
| Status | opublikowany |

Licencja: portal nie ma pola „licencja” do wyboru wprost. Zaznaczenie warunku źródła albo przetworzenia daje CC BY 4.0 (`datasets/models.py:569-583`). Tego chcemy, bo rekordy z Warszawy są na CC BY 4.0, a reszta na CC0 1.0 (kolumna `licencja`).

## 2. Wariant A – ręcznie: zasób z pliku (5 min)

1. Zbiór „Krajowy rejestr AED” → Dodaj zasób. Źródło danych: plik `datasets/out/aed_dane_gov_pl.csv` (albo eksport usługi, patrz uwaga niżej). Tytuł, opis (min. 20 znaków, `settings/base.py:2055`), „Dane na dzień”, „Zawiera wykaz chronionych danych” = Nie (wymagane, `resources/forms.py:253-265`). Zapisz.
2. Poczekaj, aż Celery przetworzy plik (zakładki „Walidacja pliku” i „Walidacja danych”). Zakładki „Zmiana typu” i „Mapy i wykresy” pojawiają się dopiero po wykryciu schematu (`resources/admin.py:256-283`).
3. **Zakładka „Walidacja danych” pokaże błędy – to oczekiwane.** Ustaw typy w zakładce **„Zmiana typu”** (widżet `lib/widgets.py:218-257`, typy `settings/base.py:1820-1829`):

   | Kolumna | Wykryty typ | Ustaw |
   |---|---|---|
   | `nr_budynku` | Liczba całkowita | Dane tekstowe |
   | `kod_terc` | Liczba całkowita | Dane tekstowe |
   | `kod_simc` | Liczba całkowita | Dane tekstowe (inaczej zginie zero wiodące, np. `0920806`) |
   | `zrodlo_id` | Liczba całkowita | Dane tekstowe |
   | `kompletnosc` | Liczba całkowita | bez zmian albo Dane tekstowe (liczba całkowita przechodzi – sprawdzone 22.11 na pliku 0.3.0) |
   | `szerokosc_geograficzna`, `dlugosc_geograficzna` | Liczba zmiennoprzecinkowa | bez zmian – wymagane dla mapy |
   | `data_aktualizacji` | Data | bez zmian (wypełniona w każdym wierszu) |

   Standard 0.3.0 (42 kolumny) nie zmienia tej listy dla obecnego pliku: typ wykrywany przez portal (`mcod/resources/type_guess.py`, ten sam kod co w Celery) uruchomiony 22.11 w kontenerze `mcod-admin` na wykazie krajowym 0.3.0 dał liczby całkowite w `nr_budynku`, `kod_terc`, `kod_simc`, `zrodlo_id`, `kompletnosc` i datę w `data_aktualizacji`; walidacja goodtables tym schematem zgłosiła błędy tylko w `nr_budynku`, `kod_terc`, `kod_simc` i `zrodlo_id`. Nowe kolumny są dziś puste albo tekstowe (`sposob_ustalenia_polozenia` = `import`), więc portal daje im typ dowolny lub tekst. **Gdy zaczną być wypełniane rzadko**, zmień na „Dane tekstowe” także: `pietro` (w standardzie liczba całkowita), `data_stanu`, `data_weryfikacji` oraz `data_produkcji`, `data_waznosci_elektrod`, `data_waznosci_baterii` (w 0.3.0 przyjmują też `RRRR-MM`, więc i tak nie są typem „Data”) – pusta komórka w kolumnie liczbowej albo datowej to błąd walidacji. Pozycje kolumn zmieniły się w 0.3.0 (np. `nr_budynku` to kolumna 9, `kod_terc` 12, `kod_simc` 13, `zrodlo_id` 39), więc komunikaty „kolumna N” z wcześniejszych zrzutów nie pasują do nowych plików. Zasobu zbiorczego to nie dotyczy: scalanie ustawia mu schemat (wszystko tekstem poza współrzędnymi).

   Sprawdzone 22.11 na lokalnym stosie: po zmianie tych pięciu kolumn na tekst i kliknięciu „Zmień typ” walidacja danych po ok. 20 s ma status SUCCESS (zrzut `docs/zrzuty/portal-11-typy-kolumn.png`). Dlaczego tak jest – patrz sekcja „CSV a walidacja portalu”. Zapis zmienionego schematu uruchamia ponowną walidację (`resources/admin.py:888-912`).
4. Zakładka **„Mapy i wykresy”** – zestaw „współrzędne geograficzne” (`resources/forms.py:131-158`, opisy ról w `settings/base.py:1840-1861`):

   | Kolumna | Rola (znacznik) |
   |---|---|
   | `nazwa` | Etykieta (`label`) |
   | `szerokosc_geograficzna` | Szerokość geograficzna (`b`) |
   | `dlugosc_geograficzna` | Długość geograficzna (`l`) |

   Reguły formularza: każda rola najwyżej raz (`forms.py:94-109`), role tylko z jednego zestawu (`forms.py:111-129`), zestaw kompletny (`forms.py:131-158`), `l` i `b` muszą mieć typ liczbowy (`forms.py:160-168`). Kolumny adresu (`kod_pocztowy`, `miejscowosc`) zostaw bez roli, bo mieszanie zestawów jest błędem.
5. Zapisz i odczekaj na ponowne przetworzenie. Na stronie zasobu w portalu pojawia się widok tabeli i mapa.

Uwaga do pliku: od PR #16 `datasets/out/aed_dane_gov_pl.csv` i eksport usługi (`http://localhost:8080/api/aed/eksport/dane-gov-pl.csv`) mają tę samą regułę – kolumny `numer_seryjny`, `dysponent_email` i `dysponent_telefon` są puste (`HIDDEN_PUBLIC` w `aed_standard/build.py`). Można wgrać którykolwiek z nich.

## 3. Wariant B – automatycznie: harvester XML (5 min)

### Adres i wymagania harvestera (ustalone w kodzie)

| Wymaganie | Gdzie | Jak spełnia usługa |
|---|---|---|
| Adres XML kończy się na `.xml`, bez spacji w nazwie | `harvester/utils.py:200-204` | `…/api/aed/eksport/dane-gov-pl.xml` |
| `HEAD` na adres XML zwraca 2xx | `harvester/utils.py:182-188`, `47-55` | trasa obsługuje `HEAD` |
| `Content-Type` zawiera `text/xml` lub `application/xml` | `harvester/utils.py:191-197` | `application/xml; charset=utf-8` |
| Suma pod adresem XML z `.xml` zamienionym na `.md5` (`os.path.splitext`), w treści 32 znaki szesnastkowe | `harvester/utils.py:168-179` | `…/eksport/dane-gov-pl.md5` (nie `.xml.md5`) |
| MD5 pobranego pliku = suma z `.md5` | `harvester/utils.py:216-224` | obie trasy liczą z tych samych bajtów |
| Wersja schematu z przestrzeni nazw korzenia, walidacja XSD | `harvester/utils.py:68-86`, `153-165` | `urn:otwarte-dane:harvester:1.13`, `backend/data/harvester/xml_import_otwarte_dane_1_13.xsd` |
| Adres **zasobu** musi być `https://` | XSD 1.13 linie 578-588 (`pattern https://.*`), `harvester/serializers.py:133-141`, `resources/link_validation.py:92-93` | linki z `AED_BASE_URL` – trzeba ustawić adres `https://` |
| Certyfikat nie jest sprawdzany | `settings/base.py:316-322` (`verify: False`), `resources/link_validation.py:82-89` | wystarczy certyfikat samopodpisany |
| Sam adres XML może być `http://` | `harvester/models.py:192`, `335-351`, `harvester/forms.py:18-19` (zwykłe `URLField`) | – |

`extIdent` zbioru (`aed-krajowy-rejestr`) i zasobu (`aed-krajowy-rejestr-csv`) są stałe. Obiekt, którego `extIdent` zniknie z pliku, harvester usuwa (`harvester/models.py:369-390`, `1207-1215`).

Plik zasobu jest pobierany ponownie tylko przy zmianie linku (`resources/models.py:1287-1295`, `1966-1970`; harvester zapisuje zasób tylko przy zmianie pól, `harvester/models.py:638-653`). Dlatego link do CSV ma parametr `wersja` – skrót zawartości pliku.

### HTTPS lokalnie – najmniejsze obejście (ograniczenie demonstracji)

Prototyp działa po `http://localhost:8080`, a XSD wymaga `https://` w adresie zasobu. Na czas demonstracji stawiamy przed prototypem tymczasowy serwer TLS z certyfikatem samopodpisanym. Kontenery portalu na Docker Desktop (Mac) widzą komputer gospodarza pod nazwą `host.docker.internal`. Na Linuksie trzeba dodać `extra_hosts: ["host.docker.internal:host-gateway"]` do usług `mcod-local-admin` i `mcod-local-celery`.

```sh
mkdir -p /tmp/aed-tls && cd /tmp/aed-tls
openssl req -x509 -newkey rsa:2048 -nodes -days 7 -subj "/CN=host.docker.internal" -keyout key.pem -out cert.pem
cat > tls.conf <<'EOF'
server {
    listen 443 ssl;
    ssl_certificate     /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    location / { proxy_pass http://host.docker.internal:8080; proxy_set_header Host $host; }
}
EOF
docker run --rm -d --name aed-tls -p 8443:443 \
  -v "$PWD/cert.pem:/etc/nginx/certs/cert.pem:ro" -v "$PWD/key.pem:/etc/nginx/certs/key.pem:ro" \
  -v "$PWD/tls.conf:/etc/nginx/conf.d/default.conf:ro" nginx:1.27-alpine
# w katalogu repozytorium: linki w XML budowane z tego adresu
AED_BASE_URL=https://host.docker.internal:8443 docker compose up --build -d
curl -sk https://localhost:8443/api/aed/eksport/dane-gov-pl.md5
```

Skutek uboczny: `AED_BASE_URL` trafia też do kodów QR na naklejkach, więc naklejki wygenerowane w tym czasie nie zadziałają na telefonie. Po zrzutach: `docker stop aed-tls` i `docker compose up -d` bez zmiennej. Alternatywa z prawdziwym certyfikatem to tunel (np. `cloudflared tunnel --url http://localhost:8080`), ale wystawia prototyp publicznie – to otwarta decyzja zespołu.

### Źródło danych w panelu

Panel → Źródła danych (`/harvester/datasource/`) → Dodaj. Pola (`harvester/admin.py:238-322`, `harvester/models.py:120-200`):

| Pole | Wartość |
|---|---|
| Nazwa | Krajowy rejestr AED – zasilanie XML |
| Opis | wymagany (`models.py:130`) |
| Typ źródła | XML |
| XML url | `https://host.docker.internal:8443/api/aed/eksport/dane-gov-pl.xml` |
| Instytucja | Ministerstwo Cyfryzacji (dla XML wymagana, `models.py:335-338`) |
| Częstotliwość | codziennie (`models.py:103-108`) |
| Status | aktywny |
| E-mail | adres redaktora (wymagany, `models.py:142`) |

1. Kliknij **„Sprawdź poprawność pliku”**. Uruchamia to zadanie Celery `validate_xml_url_task` (`harvester/tasks.py:42-69`, `harvester/views.py:28-39`), które przechodzi 7 kroków walidacji i wpisuje „hash źródła” (`templates/admin/harvester/datasource/change_form.html:39-45`). Zrzut okna z wynikiem.
2. Zapisz. **Import rusza od razu**: zapis ze zmianą statusu na „aktywny” uruchamia `import_data_task(force=True)` i pokazuje komunikat „Zadanie importu danych zostało uruchomione!” (`harvester/admin.py:227-236`). Że to działa także przy tworzeniu nowego źródła, wnioskujemy z działania `FieldTracker`; nie było to uruchamiane.
3. Ponowny import bez czekania do 03:00 (harmonogram `celeryapp.py:78-82`; lokalnie Celery beat i tak jest wyłączony, `backend/docker-compose.local.yml:197-199`):
   - w panelu: status „nieaktywny” → Zapisz → „aktywny” → Zapisz, albo
   - z konsoli: `docker exec mcod-admin python manage.py shell -c "from mcod.harvester.models import DataSource; from mcod.harvester.tasks import import_data_task; import_data_task.delay(DataSource.objects.get(name='Krajowy rejestr AED – zasilanie XML').id, force=True)"` (`harvester/tasks.py:22-28`).
4. Zakładka „Importy” źródła pokaże wynik: liczbę zbiorów i zasobów utworzonych, zmienionych i usuniętych oraz opis błędu (`harvester/models.py:1197-1230`).
5. Powstały zbiór i zasób trzeba raz poprawić ręcznie jak w wariancie A (kroki 3–4: typy kolumn i mapa). Harvester nie ustawia typów ani mapy. Przy kolejnych importach zapisany schemat powinien zostać zachowany, bo `_resolve_tabular_data_schema` wylicza go od nowa tylko przy zmianie znaków umownych (`resources/tasks/process_resource_file_data.py:24-36`) – wniosek z kodu, nie sprawdzony.

## 4. Zrzuty do prezentacji

1. Strona zbioru „Krajowy rejestr AED” w portalu: dostawca Ministerstwo Cyfryzacji, kategoria Zdrowie, licencja CC BY 4.0, częstotliwość codziennie.
2. Widok tabeli zasobu (frontend portalu, zakładka danych).
3. Mapa zasobu (ta sama strona, widok mapy) – punkty AED.
4. API zasobu: `http://localhost:8000/resources/<id>/data` i `http://localhost:8000/resources/<id>/geo` (`routes.py:133`, `146`).
5. Poziom otwartości zasobu (gwiazdki na stronie zasobu; dla CSV spodziewamy się 3 – nie sprawdzono).
6. Panel: zakładka „Zmiana typu” i „Mapy i wykresy” z ustawionymi znacznikami.
7. Panel: źródło danych XML – okno „Sprawdź poprawność pliku” z przejściem 7 kroków i zakładka „Importy” z wynikiem `OK`.
8. Dla kontekstu: `https://localhost:8443/api/aed/eksport/dane-gov-pl.xml` w przeglądarce.

## CSV a walidacja portalu

Portal najpierw wykrywa typy kolumn (`resources/indexed_data.py:575-590`, `resources/type_guess.py`), zapisuje schemat, a potem waliduje plik tym schematem w goodtables (`resources/tasks/process_resource_file_data.py:72-83`, `resources/indexed_data.py:610-639`). Uruchomiliśmy tę ścieżkę poza portalem, na wersjach bibliotek z `backend/Pipfile.lock` (tableschema 1.21.0, goodtables 2.1.4, tabulator 1.53.5) i z plikiem `type_guess.py` z forka. Wyniki dla `datasets/out/aed_dane_gov_pl.csv` i dla eksportu usługi są takie same:

- `szerokosc_geograficzna` i `dlugosc_geograficzna` są wykrywane jako liczba zmiennoprzecinkowa (`number`), więc znaczniki `l` i `b` przejdą;
- **walidacja nie przechodzi bez poprawki:** `nr_budynku` i `zrodlo_id` są wykrywane jako liczba całkowita, bo większość wartości to liczby, a część nie (`23/25`, `19A`, `2625221/7`). `kod_terc` i `kod_simc` są wypełnione tylko dla Legionowa, a puste komórki w kolumnie liczbowej to błąd. `type_guess.py:150-158` usuwa pusty napis z listy brakujących wartości, więc zapisany schemat ma `missingValues: []`;
- kolumny całkowicie puste dostają typ „Dowolny typ” i nie przeszkadzają; kolumny tekstowe z pustymi komórkami też nie;
- po zmianie typu czterech kolumn na „Dane tekstowe” plik waliduje się bez błędów.

Nie da się tego naprawić w samym pliku CSV bez zmiany danych: CSV nie niesie typów, a wartości są poprawne. To ryzyko dla każdej kolumny, która w przyszłości będzie rzadko wypełniona i liczbowa lub datowa, np. `data_weryfikacji` i daty ważności, gdy w eksporcie pojawią się potwierdzone urządzenia. Przy wgrywaniu sprawdź wtedy zakładkę „Zmiana typu”.

## Co zweryfikowano, a czego nie

Uruchomione (na tej maszynie, bez portalu):

- XML z pełnego rejestru (781 rekordów w eksporcie) waliduje się względem XSD 1.13 w `xmllint` i w `xmlschema` 3.4.4 (wersja z `Pipfile.lock`); wersja schematu jest odczytywana z przestrzeni nazw tak jak w `harvester/utils.py:68-86`;
- odtworzenie kroków `validate_xml_url` (nazwa, `HEAD`, typ treści, adres `.md5`, zgodność sumy, XSD) i sprawdzeń `download_file` dla linku zasobu (`https`, kod 200, typ treści, `Content-Disposition`) przez tymczasowy serwer TLS z certyfikatem samopodpisanym pod `https://host.docker.internal:8443`;
- walidatory adresów z portalu (marshmallow 3.9.1, Django 2.2.9) akceptują `https://host.docker.internal:8443/...`;
- wykrywanie typów i walidacja CSV jak w sekcji wyżej;
- test automatyczny `tests/test_aed_service.py::HarvesterFeedTest`: XSD, suma MD5, stabilność między pobraniami, zmiana linku po zmianie danych, brak rekordów OSM i prywatnych w pliku zasobu.

Uruchomione później w lokalnym pełnym stosie forka (22.11, `docs/wykaz-aed-w-portalu.md`): formularz zasobu w panelu (dodanie i edycja, pole „Wykaz AED”), przetwarzanie pliku przez Celery, walidacja danych, ocena otwartości, tabela i mapa zasobu we frontendzie, zmiana typów kolumn w zakładce „Zmiana typu” (po zmianie `nr_budynku`, `kod_terc`, `kod_simc`, `zrodlo_id`, `kompletnosc` na tekst walidacja danych wykazu ministerstwa przeszła).

Tylko w kodzie, nieuruchomione:

- formularze panelu dla instytucji i źródła danych (harvester) i ich komunikaty;
- zadania Celery harvestera: `validate_xml_url_task`, `import_data_task`;
- serializer `XMLDatasetSchema` (`harvester/serializers.py:680-796`) w całości, w tym zamiana `conditions` na licencję i dopasowanie kategorii `HEAL`;
- że kontener portalu u kolegi dosięgnie `host.docker.internal` – na Docker Desktop to standard, na Linuksie wymaga `extra_hosts`;
- zachowanie ręcznie ustawionych typów kolumn przy kolejnych importach harvestera.
