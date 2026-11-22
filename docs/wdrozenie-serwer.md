# Wdrożenie pełnego forka portalu pod domeną

Cel: na serwerze kolegi, pod kupioną domeną, działa fork dane.gov.pl (frontend, API, panel administracyjny, CMS, Celery) razem z usługą AED. Jury otwiera adresy w przeglądarce bez żadnej konfiguracji.

**Stan: przygotowana i sprawdzona składniowo konfiguracja, nieuruchomiona.** `docker compose ... config` przechodzi, skrypt `.env` sprawdzono na kopii `env.sample`. Żadnego kontenera z tego wariantu nie uruchomiono. Miejsca, które wynikają z kodu, ale nie były sprawdzone w działaniu, mają oznaczenie **[nie uruchomiono]**.

Pliki:

| Plik | Rola |
|---|---|
| `backend/docker-compose.aed-domain.yml` | nakładka na `docker-compose.local.yml`: Caddy (HTTPS), usługa AED, build frontendu, serwery produkcyjne, bez portów infrastruktury na zewnątrz |
| `backend/aed-domain/init-env.sh` | tworzy `backend/.env` z `env.sample` i generuje nowe sekrety |
| `backend/aed-domain/settings.py` | ustawienia Django dla domeny (ciasteczka, CSRF, bez trybu debug); dziedziczy po `mcod/settings/local.py` |
| `backend/aed-domain/Caddyfile` | cztery nazwy hostów, certyfikaty Let's Encrypt, pliki statyczne i media |
| `backend/aed-domain/web.conf.template` | nginx frontendu: `/api/aed` → usługa AED, `/api` i `/cms` → portal z forka (zamiast publicznego dane.gov.pl) |

W kodzie `backend/mcod/` nie ma zmian.

## Dwa warianty – który wybrać

| | Lekki (`docker-compose.prod.yml` w katalogu głównym) | Pełny fork (ten dokument) |
|---|---|---|
| Co pokazuje | moduł AED; reszta portalu czytana z publicznego API dane.gov.pl | cały portal z forka: strona główna, zbiory, panel administracyjny, wykaz AED, harvester |
| Kontenery | 3 | 14 |
| Pamięć | ok. 1 GB | ok. 8 GB (szacunek) |
| Zgodność ze wskazówką prowadzącego („postawcie środowisko”, „panel administracyjny”, „wykazy”) | nie pokazuje mechanizmów portalu | pokazuje |

Oba warianty zajmują porty 80 i 443, więc na jednym serwerze działa tylko jeden. Pełny wariant zawiera moduł AED, więc zastępuje lekki.

## 1. Serwer

- **System:** Linux na procesorze amd64 (x86_64) – **założenie do potwierdzenia u kolegi**. Obrazy aplikacji portalu są przypięte do `linux/amd64` (`backend/docker-compose.local.yml`). Na ARM natywna budowa nie przechodzi: według notatki w `backend/docker-compose.aed-mac.yml` dla Pythona 3.8 na arm64 nie ma gotowego pakietu gevent, a budowa ze źródeł się nie udaje. Zostaje wtedy emulacja amd64, która jest bardzo wolna.
- **Sieć Dockera:** portal używa podsieci `172.18.18.0/24` ze stałymi adresami. Jeśli na serwerze inna sieć Dockera już ją zajmuje, dodaj `-f docker-compose.aed-mac.yml` (podsieć `172.30.18.0/24`). Zmienną `COMPOSE_FILE` w `.env` trzeba wtedy rozszerzyć o ten plik. **[nie uruchomiono]**
- **Docker Engine** z wtyczką Compose. Nakładka używa znacznika `!reset` (zerowanie portów), więc Compose musi go znać. Sprawdzone na Compose 5.7.0. Najstarszej wersji, która go obsługuje, nie sprawdzaliśmy.
- **Pamięć:** 8 GB RAM, minimum 6 GB z plikiem wymiany. Szacunek: Elasticsearch ma stałą stertę 1 GB, a cztery kontenery aplikacji mają limit 2 GB każdy (`mem_limit` w `docker-compose.local.yml`).
- **Dysk:** 40 GB wolnego miejsca, także szacunek. Obraz aplikacji portalu zawiera Pythona, Node.js, Firefoksa i ffmpeg, do tego dochodzi build frontendu z `node_modules`.
- **Procesor:** 4 vCPU. Pierwsza budowa obrazów potrwa od kilkunastu do kilkudziesięciu minut (szacunek).
- **Porty otwarte z internetu:** 22, 80, 443. Na hoście nic więcej nie nasłuchuje: nakładka zeruje porty bazy, RabbitMQ, Redis, Elasticsearch, poczty testowej, Fuseki i wewnętrznego nginx.
- Elasticsearch 6.8 na Linuksie może wymagać `sysctl -w vm.max_map_count=262144` (przy `discovery.type=single-node` zwykle nie). **[nie uruchomiono]**

## 2. DNS

Cztery rekordy A (i AAAA, jeśli serwer ma IPv6) na adres serwera albo jeden rekord wieloznaczny `*.<domena>` plus rekord dla samej domeny:

| Nazwa | Co tam jest |
|---|---|
| `<domena>` | frontend portalu (fork) z modułem AED: `https://<domena>/pl`, `https://<domena>/pl/aed` |
| `api.<domena>` | API portalu, w tym `GET /aed-aggregated` i pliki zasobów (`/media`) |
| `admin.<domena>` | panel administracyjny portalu (Django) |
| `cms.<domena>` | CMS portalu (Wagtail); jury go nie potrzebuje, ale frontend czyta z niego treści stron |

Caddy dostaje certyfikat dla każdej nazwy przy pierwszym wejściu, więc rekordy DNS muszą działać **przed** startem. Forum (`forum.`) i poczta testowa (`mail.`) nie są wystawiane.

## 3. HTTPS i ruch

Jeden punkt wejścia: Caddy z automatycznym certyfikatem Let's Encrypt, tak samo jak w lekkim wariancie. Certyfikaty leżą w wolumenie `caddy-data`, więc ponowne uruchomienie nie pobiera ich od nowa (Let's Encrypt ma limity).

```
internet ─► Caddy :443 ─┬─ <domena>        ─► aed-web (nginx: build frontendu)
                        │                        ├─ /api/aed ─► aed-service:8085
                        │                        ├─ /api     ─► mcod-local-api:8000/1.4/
                        │                        ├─ /cms     ─► mcod-local-cms:8002
                        │                        └─ /media   ─► pliki z backend/media
                        ├─ api.<domena>    ─► mcod-local-api:8000   (/media z dysku)
                        ├─ admin.<domena>  ─► mcod-local-admin:8001 (/static, /media z dysku)
                        └─ cms.<domena>    ─► mcod-local-cms:8002   (/static, /media z dysku)
```

Ustalone z kodu:

- frontend w buildzie `aed` (`environment.production = false`) woła `/api`, `/cms` i `/media` względnie, z własnego adresu (`frontend/src/app/services/rest.service.ts:96`, `cms.service.ts:49`). Dlatego wystarczy jeden nginx przed frontendem i nie trzeba ustawiać CORS. Cele są takie jak w `frontend/proxy.aed-local.conf.json`;
- linki do plików zasobów portal buduje z `API_URL` (`resources/models.py:810`), więc potrzebna jest nazwa `api.<domena>`;
- Django rozpoznaje HTTPS po nagłówku `X-Forwarded-Proto` (`settings/base.py:512`), który Caddy dokłada sam;
- `mcod/settings/local.py` ustawia ciasteczka na sztywno na `mcod.local` i bez `Secure`. Na innej domenie przeglądarka by je odrzuciła i logowanie do panelu nie działałoby. Poprawia to `aed-domain/settings.py`. Ten sam plik ustawia też domenę dla ciasteczka CSRF API i listy zaufanych adresów (`core/api/middlewares.py:459–469`).

Uproszczenie: Caddy podaje `/media` prosto z dysku. Lokalny nginx portalu sprawdza wcześniej w Django, czy plik należy do opublikowanego zasobu (`X-Accel-Redirect`, `docker/nginx/config-templates/03-admin.conf.template`). Na demonstracji to sprawdzenie pomijamy. Pliki zasobów i tak są publiczne pod `api.<domena>/media`.

Panel, API i CMS działają pod gunicornem zamiast `runserver` i `werkzeug --debug`. Debugger werkzeuga wystawiony do internetu pozwalałby wykonać kod na serwerze. Polecenia są takie jak w `docker/app/start-api.sh` i `start-django.sh`. **[nie uruchomiono]**

## 4. Zmienne środowiskowe

Wszystko ustawia skrypt `sh aed-domain/init-env.sh <domena>`. Bierze `backend/env.sample` (szablon portalu), podmienia w nim znane sekrety i dopisuje kilka zmiennych. Ręcznie nie trzeba ustawiać nic. Adresy (`BASE_URL`, `API_URL`, `ADMIN_URL`, `CMS_URL`, `FRONTEND_BASE_URL`, `API_URL_INTERNAL`) nakładka wylicza z `AED_DOMAIN`.

| Zmienna | Wartość | Po co |
|---|---|---|
| `AED_DOMAIN` | domena bez `https://` | jedyna wartość podawana przez człowieka |
| `COMPOSE_FILE` | `docker-compose.local.yml:docker-compose.aed-domain.yml` | samo `docker compose …` w `backend/` używa obu plików |
| `DJANGO_SECRET_KEY`, `JWT_SECRET_KEY` | losowe | domyślne wartości są wpisane w `settings/base.py:61` i `:325`, czyli publicznie znane |
| `POSTGRES_PASSWORD`, `SPARQL_PASSWORD`, `FIELD_ENCRYPTION_KEYS` | losowe | w `env.sample` są znane wartości |
| `DISCOURSE_FORUM_ENABLED` | `false` | obraz forum jest w prywatnym rejestrze |
| `AED_DEMO_PASSWORD` | losowe | hasło trzech kont demo usługi AED |
| `MAIN_AED_DATASET_OWNER_ORGANIZATION_PK` | `2838` | właściciel zbioru „Krajowy wykaz AED”: instytucja z danych startowych portalu (w kroku 6 zmieniamy jej nazwę na ministerstwo) |
| `AED_CELERY_OPTS` (opcjonalna) | `-l INFO -B --scheduler django_celery_beat.schedulers:DatabaseScheduler` | włącza harmonogram: scalanie wykazów AED o 03:45, harvester o 03:00 i pozostałe zadania dzienne portalu. Domyślnie wyłączony, zadania uruchamiamy ręcznie |
| `AED_DEBUG` (opcjonalna) | `yes` | strony błędów Django; tylko na czas diagnozy |

### Domyślne hasła i klucze, które trzeba zmienić przed wystawieniem

| Co | Domyślnie | Kto zmienia |
|---|---|---|
| sekret Django, sekret JWT | wpisane w `settings/base.py` | skrypt |
| hasło PostgreSQL `mcod`, hasło Fuseki `Britenet.1`, klucz szyfrowania pól | `env.sample` | skrypt (hasło bazy działa tylko przy **pierwszym** starcie wolumenu) |
| konto panelu `admin@mcod.local` / `testadmin123!` (superużytkownik) | dane startowe `mcod/core/fixtures/basic_data.json` | **człowiek**, krok 5 |
| konto panelu `pelnomocnik@mcod.local` / `User123!` | jw. | **człowiek**, krok 5 |
| konta demo usługi AED (`…-demo`) | `aed_service/README.md` | skrypt (`AED_DEMO_PASSWORD`); działa tylko przy pierwszym utworzeniu bazy usługi |
| RabbitMQ `guest`, Redis i Elasticsearch bez hasła, Flower bez logowania | obrazy | nie zmieniamy: porty nie są wystawione, Flower jest wyłączony |
| klucze Discourse w `env.sample` | `env.sample` | bez znaczenia, forum wyłączone |

**Znany problem:** karty „Konta demonstracyjne” na ekranie logowania AED pokazują stałe hasła `…-demo` z `frontend/src/environments/environment.aed.ts`. Po ustawieniu `AED_DEMO_PASSWORD` karty podają złe hasło. Przycisk „Wypełnij” nadal uzupełnia e-mail, ale hasło trzeba wpisać ręcznie. Jest to decyzja do podjęcia i poprawka we frontendzie (pytanie w sekcji 10).

## 5. Od czystego serwera do działającej strony

W katalogu `backend/` repozytorium:

```sh
git clone <repozytorium> aed && cd aed/backend
sh aed-domain/init-env.sh aed.example.pl                 # 1. .env z sekretami; wypisze hasło kont demo AED
cp mcod/settings/local.py.sample mcod/settings/local.py  # 2. lokalne ustawienia portalu (plik jest w .gitignore)
docker compose up -d --build                             # 3. budowa i start (pierwszy raz długo)
docker compose exec mcod-local-admin python manage.py init_mcod_db            # 4. migracje + dane startowe
docker compose exec mcod-local-admin python manage.py search_index --rebuild -f  # 5. indeksy wyszukiwarki
docker compose exec mcod-local-admin python manage.py compilemessages          # 6. polskie tłumaczenia panelu
docker compose exec mcod-local-admin python manage.py changepassword admin@mcod.local
docker compose exec mcod-local-admin python manage.py changepassword pelnomocnik@mcod.local
```

Uwagi:

- `init_mcod_db` wykonuje `migrate`, więc zakłada też tabele AED (`resources.0076_resource_contains_aed_list`, `aed.0001_initial`) i ładuje `basic_data.json` (`core/management/commands/init_mcod_db.py`). **[nie uruchomiono]**
- Krok 6 jest potrzebny, bo `docker-compose.local.yml` montuje katalog `translations/` z repozytorium, a w nim nie ma plików `.mo`. Bez tego panel może być po angielsku (wniosek z `docs/integracja-portal-backend.md`).
- Kontrola: `docker compose ps` (wszystkie `running`, `aed-service` `healthy`), potem `curl -sI https://<domena>/pl/aed`, `curl -s https://api.<domena>/aed-aggregated`, `curl -s https://<domena>/api/aed/eksport/dane-gov-pl.md5`.
- Logi: `docker compose logs -f caddy` (certyfikaty), `docker compose logs -f mcod-local-celery` (przetwarzanie plików, scalanie).
- Aktualizacja kodu: `git pull && docker compose up -d --build`.

## 6. Dane do demonstracji

Szczegóły kroków i oczekiwane komunikaty: `docs/wykaz-aed-w-portalu.md` i `docs/panel-portalu-krok-po-kroku.md`. Poniżej kolejność dla serwera (adres panelu: `https://admin.<domena>`).

1. **Ministerstwo.** Instytucje → „Pierwsza instytucja” (nr 2838, typ `state`) → zmień nazwę na „Ministerstwo Cyfryzacji”. Jest właścicielem zbioru zbiorczego (`MAIN_AED_DATASET_OWNER_ORGANIZATION_PK=2838`), więc nie trzeba restartować kontenerów.
2. **Dostawcy wykazów.** Dodaj instytucje, np. „Urząd Miasta Legionowo” (`local`) i „Urząd Miasta Krosna” (`local`), status opublikowany. Wymagane pola: tabela w `docs/panel-portalu-krok-po-kroku.md`, rozdział 1.
3. **Wykaz przyjęty.** W instytucji Legionowa: zbiór + zasób z pliku `datasets/raw/dane_gov_pl/legionowo/resource_2625221.csv`, „Wykaz AED: TAK”.
4. **Wykaz odrzucony.** W instytucji Krosna: zasób z `datasets/raw/dane_gov_pl/krosno/resource_54632.csv`, „Wykaz AED: TAK”. Formularz pokaże błędy po polsku. Zapisz z „NIE”.
5. **Wykaz z usługi AED (kanał sprzedawca → QR → zarządca).** W ministerstwie: zbiór „Rejestr zgłoszeń AED” i zasób typu **link** `https://<domena>/api/aed/eksport/dane-gov-pl.csv`, „Wykaz AED: TAK”. Link jest czytany przy scalaniu (`mcod/aed/aed_utils.py:69–92`), z weryfikacją certyfikatu, więc potrzebny jest prawdziwy certyfikat. Ten wariant to zapewnia. Zamiast linku można wgrać plik `datasets/out/aed_dane_gov_pl.csv`.
6. **Scalanie.**
   ```sh
   docker compose exec mcod-local-admin python manage.py create_main_aed_resource --dry-run   # raport bez zapisu
   docker compose exec mcod-local-admin python manage.py create_main_aed_resource
   ```
   Wynik: zbiór „Krajowy wykaz defibrylatorów AED – wykaz zbiorczy” w ministerstwie oraz `https://api.<domena>/aed-aggregated` z raportem wykazów przyjętych i odrzuconych. Liczby dla wariantu z plikiem z kroku 5 (z testu `tests/test_wykaz.py`): 805 rekordów z wykazów, 24 połączenia, 781 w wykazie krajowym. **[nie uruchomiono w portalu]**
7. **Zasilanie XML (opcjonalnie, drugi mechanizm portalu).** Panel → Źródła danych → XML, adres `https://<domena>/api/aed/eksport/dane-gov-pl.xml`, instytucja ministerstwo. Na serwerze nie trzeba obchodzić HTTPS: certyfikat jest prawdziwy, a `AED_BASE_URL` to `https://<domena>`. Powstaje osobny zbiór bez flagi wykazu, więc rekordy nie liczą się w scalaniu podwójnie.
8. **Ścieżka sprzedawca → QR → zarządca** w `https://<domena>/pl/aed` (instrukcja dla jury, ścieżki A–C). Po potwierdzeniu urządzenia przez zarządcę ponowne scalanie (krok 6) dołącza je do wykazu krajowego przez link z kroku 5.

Skrót (w toku u innego agenta, jeszcze nie w repozytorium): polecenie `python manage.py seed_aed_demo` w `backend/mcod/aed/management/commands/` zakłada instytucje, zbiory i trzy wykazy z prawdziwych plików (ministerstwo, Legionowo, Krosno). Nakładka montuje do jego użytku `../datasets` jako `/usr/src/mcod_backend/aed_datasets`. Polecenie jest opisane jako „tylko lokalne demo”, więc przed użyciem na serwerze trzeba sprawdzić, czy nie nadpisuje danych. **[nie uruchomiono]**

Kontener Celery łączy się z adresem publicznym domeny (kroki 5 i 7). Na typowym serwerze VPS to działa. Jeśli serwer nie widzi sam siebie pod adresem publicznym (NAT bez hairpinu), trzeba dodać `extra_hosts` z adresem wewnętrznym. **[nie uruchomiono]**

## 7. Usługa AED

W nakładce działa jako `aed-service`, w sieci portalu. Przy pierwszym starcie zakłada konta demo i importuje rejestr z `datasets/raw/` zapisanych w obrazie. `AED_BASE_URL` to `https://<domena>`, więc kody QR na naklejkach, linki aktywacyjne i linki w zasilaniu XML prowadzą pod publiczny adres i działają z telefonu. Baza leży w wolumenie `aed-data`.

## 8. Czego potrzebuje jury

| Co | Adres | Konto |
|---|---|---|
| prototyp AED (rejestr, panel firmy, strona QR, panel ministerstwa) | `https://<domena>/pl/aed` | konta demo AED, hasło `AED_DEMO_PASSWORD` przekazane osobno |
| portal z forka (strona główna, zbiory, zbiór zbiorczy, tabela, mapa) | `https://<domena>/pl` | bez logowania |
| wykaz AED do odczytu | `https://api.<domena>/aed-aggregated`, `https://api.<domena>/resources/<id>/data` | bez logowania |
| panel administracyjny (oznaczanie wykazów, źródła harvestera) | `https://admin.<domena>` | konto redaktora (propozycja niżej) |

Odczyt nie wymaga żadnego konta, a to odpowiada wskazówce prowadzącego („cenniejsze będzie rozwiązanie do odczytu”). Do panelu proponujemy osobne konto redaktora (`is_staff`) przypisane do jednej instytucji demonstracyjnej, np. „Gmina Demo”. Juror może wtedy sam dodać wykaz AED, ale nie zmieni danych ministerstwa ani kont. Superużytkownika zostawiamy zespołowi. Nie sprawdziliśmy, czy redaktor instytucji może uruchomić „Sprawdź poprawność pliku” w źródle harvestera. **[do sprawdzenia w panelu]**

Logowanie do kont portalu we frontendzie jest wyłączone w buildzie `aed` (`frontend/src/app/pages/aed/aed-prototype.ts`). Portal ma pasek „to nie jest serwis dane.gov.pl”. Panel administracyjny działa normalnie.

## 9. Wyłączenie i zerowanie

```sh
docker compose stop                       # zatrzymanie, dane zostają
docker compose start                      # ponowny start
docker compose down                       # usunięcie kontenerów, wolumeny zostają
docker volume rm backend_aed-data         # tylko usługa AED od nowa (najpierw: docker compose rm -sf aed-service)
docker compose down -v                    # WSZYSTKO od nowa: baza portalu, indeksy, usługa AED, certyfikaty
```

Po `down -v` trzeba powtórzyć kroki 4–6 z sekcji 5 i dane z sekcji 6. Pliki wgrane do portalu leżą na dysku hosta w `backend/media/` (montowany katalog). Przy pełnym zerowaniu usuń też `backend/media/resources/` i `backend/media/main_aed/`. Wolumen z certyfikatami (`backend_caddy-data`) najlepiej zostawić ze względu na limity Let's Encrypt. Nazwy wolumenów mają przedrostek `backend_` od katalogu projektu. **[nie uruchomiono]**

## 10. Pytania do zespołu

1. Serwer: amd64 czy ARM, ile RAM i dysku, jaki system, czy działa na nim coś na portach 80 i 443?
2. Domena: jaka nazwa? Czy można dodać rekordy `api.`, `admin.` i `cms.` albo rekord wieloznaczny?
3. Hasła kont demo AED: losowe hasło z `AED_DEMO_PASSWORD` (jury dostaje je w instrukcji; karty logowania wymagają wtedy poprawki we frontendzie) czy znane hasła `…-demo` (każdy z internetu może wejść do panelu ministerstwa prototypu)?
4. Konto jury w panelu portalu: redaktor jednej instytucji demonstracyjnej (propozycja) czy tylko odczyt bez logowania?
5. Harmonogram Celery: włączyć (`AED_CELERY_OPTS`), żeby scalanie szło samo o 03:45, czy pokazywać ręczne uruchomienie?
6. Do kiedy serwer ma działać po hackathonie i kto go wyłączy?
