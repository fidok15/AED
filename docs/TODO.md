# Do zrobienia

Stan na 22.11.2026, ok. 04:00, gałąź `feat/nocna-runda`. Plan i zasady: `CLAUDE.md`. Kontrakt API: `docs/api-aed.md`. Ocena Codexa (juror, audyt usługi, fork, UI): `docs/ewaluacja-codex/`.

Co działa i ma dowód:

- prototyp lekki (`docker compose up --build`, `http://localhost:8080/pl/aed`), ścieżki A–D i K przeklikane od zera na Dockerze;
- pełny fork portalu lokalnie: migracje, testy Django `mcod/aed` (8) i regresji DGA, panelu i Celery (148), scalanie przez Celery uruchomione ręcznie, zasób zbiorczy z tabelą i mapą, `/aed-aggregated`, e-mail do dostawcy o odrzuconym wykazie w MailHog (`docs/wykaz-aed-w-portalu.md`);
- nakładka domenowa uruchomiona lokalnie pod `aed.localhost` (`docs/wdrozenie-serwer.md`, rozdz. 11);
- XSD harvestera 1.14 z `containsAedList` w forku (test parsera i serializera); usługa wystawia 1.13;
- prezentacja `docs/prezentacja/misja-aed.pptx` (14 slajdów) ze wszystkimi zrzutami, w tym render karty „Słownik pól” (`docs/zrzuty/wzorzec-slownik-pol.png`);
- liczby zbioru: stan z `datasets/out/raport.json` (rejestr z mappera, eksport, pary do przeglądu) – nie przepisujemy ich tutaj.

Nakład: S – do godziny, M – kilka godzin, L – dzień albo więcej.

## Dla agenta

- [ ] **Widok publikacyjny w XLSX** (S): w `wzorzec-aed.xlsx` arkusz z polami dopuszczonymi do udostępnienia (bez kontaktu dysponenta i numeru seryjnego) i przykładowym wierszem; generator `scripts/build_template.py`.
- [ ] **Jeden identyfikator od QR do portalu** (M): zgłoszenie → naklejka → potwierdzenie → eksport usługi → wykaz ministerstwa w forku → scalanie → ten sam `id_aed` w zasobie zbiorczym; zapis kroków i zrzut.
- [ ] **Stały adres zasobu zbiorczego** (M): ponowne scalanie dziś tworzy nowy zasób, stary zwraca 404; zachować identyfikator zasobu albo stały adres do bieżącego wyniku; test po dwóch scaleniach.
- [ ] **Ponowne wgranie identycznego wykazu zawyża wynik** (M): ten sam plik Legionowa jako drugi zasób dał 805 zamiast 781; wykrywać duplikat wykazu tego samego dostawcy po skrócie znormalizowanej treści (urządzenia z jednego budynku zostają osobno).
- [ ] **Test Celery Beat** (S): w środowisku testowym ustawić porę scalania na najbliższą minutę, zachować log Beat, wykonanie przez worker i odczyt zaktualizowanego zasobu.
- [ ] **Pliki robocze zasobów serwowane z dysku** (M): Caddy podaje `/media/resources/` bez sprawdzenia stanu publikacji; przywrócić kontrolę (`X-Accel-Redirect` jak w nginx portalu) i sprawdzić anonimowy odczyt zasobu opublikowanego i roboczego. Do tego czasu nie wgrywać na serwer niczego, co nie ma być jawne.
- [ ] Uwagi UI A6–A8 (S–M): tabele błędów, duplikatów i mapowania na wąskich ekranach.
- [ ] Mapa w buildzie produkcyjnym frontendu (`build:aed`) w pełnym forku – sprawdzono tylko `ng serve --no-prebundle` (S).

## Dla człowieka

- [ ] **Adres publiczny dla jury** (L): serwer (amd64, min. 8 GB RAM), domena z rekordami `api.`, `admin.`, `cms.`, kroki `docs/wdrozenie-serwer.md` (rozdz. 5–6), dane demo zakładane na serwerze (`seed_aed_demo`), konto `jury@aed.example`; potem sprawdzić z zewnętrznej sieci zbiór, tabelę, mapę, CSV i `/aed-aggregated`, wpisać adres w sekcji 0 `docs/instrukcja-dla-jury.md`.
- [ ] **Przypomnienie dostarczone do skrzynki zarządcy** (M): dziś wiadomości zostają w skrzynce nadawczej usługi; pokazać wysyłkę do kontrolowanej skrzynki i ponowne potwierdzenie z linku z wiadomości.
- [ ] **Testy na telefonie** (M): QR z wydrukowanej naklejki (ok. 4 cm), geolokalizacja i odmowa geolokalizacji, rejestr przy 320 px; VoiceOver na ścieżce dysponenta i panelu firmy; prawdziwy zoom 200%.
- [ ] **Pilotaż spoza Warszawy** (L): wykaz potwierdzony przez dysponenta spoza Warszawy (dziś większość eksportu to API Warszawy, a cały rejestr z mappera jest `niepotwierdzony`); na slajdzie zasięg, data i udział rekordów zweryfikowanych.
- [ ] Obejrzeć `docs/prezentacja/misja-aed.pptx` po renderze w PowerPoincie albo Keynote, slajd po slajdzie (generator nie renderuje).
- [ ] Potwierdzić u organizatora godzinę i sposób oddania.

## Kampania – 25% oceny (zespół)

- [ ] Wybrać nazwę i hasło akcji (kandydaci: `kampania/nazwa-i-haslo.md`); sprawdzić domenę i rejestry znaków. „Misja AED – Dane na ratunek” to nazwa zadania, nie akcji.
- [ ] Narysować logo; eksport do `.svg`, `.png`, `.jpg`, `.pdf`; warianty kolorowy, monochromatyczny, negatyw (`kampania/brief-logo.md`).
- [ ] Zapisać znak jako `aed_service/naklejka-logo.svg` – usługa wstawi go na naklejkę QR.
- [ ] Księga znaku w PDF na podstawie `kampania/ksiega-znaku-szablon.md`.
- [ ] Wpisać nazwę, hasło i logo w `docs/prezentacja/slajdy.json` i przebudować prezentację; wstawić nazwę akcji i znak do interfejsu modułu AED i do tytułu w `docs/opis-projektu.md`.

## Decyzje

Podjęte 22.11 (wpisane w `CLAUDE.md`): hasła kont demo jawne na czas pokazu; konto `jury@aed.example` (redaktor instytucji demo) w panelu portalu; numer seryjny ukryty w danych publicznych; zasilanie XML z usługi w wersji 1.13; kto odpowiada za wykaz i ile wykazów na instytucję – odłożone do przepisów.

Otwarte:

- [ ] Czy wymagać `id_aed` albo `zrodlo_id` w wykazie (bez nich identyfikator zależy od kolejności wierszy)?
- [ ] Mapper ignoruje `id_aed` z plików źródłowych, a wykaz w portalu zachowuje identyfikator dostawcy – czy ta różnica ma zostać?
- [ ] Kto wystawia linki przejęcia punktu: dziś tylko ministerstwo; czy także firmy dla własnych urządzeń?
- [ ] Zgłoszenie „problem” dla punktu z OSM nie uruchamia przejęcia (rekord zostaje ODbL, poza eksportem) – czy ma?
- [ ] Zaproszenie z podanym e-mailem nie wpisuje go do pola „E-mail dysponenta” na ekranie QR – czy ma wpisywać?
- [ ] Harmonogram Celery na serwerze: scalanie samo o 03:45 (`AED_CELERY_OPTS`) czy ręcznie na pokazie?

Odłożone pomysły: kreator źródła w panelu ministerstwa; uzupełnianie `kod_terc` i `kod_simc` ze współrzędnych.
