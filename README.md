# Misja AED – Dane na ratunek

Prototyp na HackNation 2026 (zadanie Ministerstwa Cyfryzacji): proces i narzędzia, dzięki którym ministerstwo zbiera w dane.gov.pl jeden, ujednolicony zbiór danych o defibrylatorach AED.

Jak to działa – dwa kanały, jeden standard (`aed_standard/schema.json`):

1. **Wykaz AED w portalu** (wzorem wykazu DGA): samorząd, instytucja lub firma publikuje w swoim zbiorze na dane.gov.pl zasób „Wykaz AED”. Portal sprawdza plik przy zapisie i codziennie scala wszystkie wykazy w jeden zasób zbiorczy ministerstwa, publicznie do odczytu (`GET /aed-aggregated`, tabela, mapa, API). Kod: `backend/mcod/aed/`, opis: `docs/wykaz-aed-w-portalu.md`.
2. **Usługa AED**: producent lub sprzedawca zgłasza urządzenie z konta firmy (CSV albo formularz) → identyfikator i naklejka z kodem QR → zarządca skanuje kod i potwierdza miejsce oraz godziny dostępu → rekord trafia do rejestru ministerstwa, który wraca do portalu jako wykaz ministerstwa albo zasilanie XML dla harvestera.

Stan początkowy daje mapper istniejących otwartych źródeł z deduplikacją.

## Uruchomienie jedną komendą

Wymaga Dockera.

```
docker compose up --build
```

Potem otwórz `http://localhost:8080/pl/aed`. Pierwsza budowa trwa kilka minut. Konta demonstracyjne są w `aed_service/README.md`.

Strony portalu poza obszarem AED pobierają dane tylko do odczytu z publicznego API dane.gov.pl. Nie loguj się w nich kontem portalu.

Pełny fork portalu (frontend, API, panel administracyjny, wykaz AED) z usługą AED pod domeną z HTTPS: `docs/wdrozenie-serwer.md`.

## Co jest w repozytorium

| Katalog | Zawartość |
|---|---|
| `aed_standard/` | standard danych (`schema.json`), walidator, mapper źródeł, deduplikacja – czysty Python bez zależności |
| `aed_service/` | usługa API: konta firm, zgłoszenia CSV, naklejki QR, potwierdzenia, rejestr (`docs/api-aed.md`) |
| `frontend/` | fork frontendu dane.gov.pl z modułem AED (`src/app/pages/aed/`) |
| `backend/` | fork backendu dane.gov.pl; zmiany wydzielone w `mcod/aed/` (wykaz AED) plus pole zasobu `contains_aed_list` (model, formularz, migracja); wdrożenie pod domeną: `docker-compose.aed-domain.yml`, `aed-domain/` |
| `wzorzec/` | `wzorzec-aed.xlsx` – wzorcowy zakres danych – oraz przykładowe pliki CSV |
| `datasets/` | surowe źródła (`raw/`) i wynik mappera (`out/`) |
| `kampania/` | materiały akcji promocyjnej |
| `docs/` | treść zadania, kontrakt API, instrukcja dla jury, konspekt prezentacji |

## Praca bez Dockera

```
# zbiór krajowy z surowych źródeł (ok. 2 s)
python3 -m aed_standard build

# walidacja pliku firmy
python3 -m aed_standard validate wzorzec/przyklad-sprzedawca-bledy.csv --profil sprzedaz

# usługa API na porcie 8085
uv run --python 3.13 --with-requirements aed_service/requirements.txt python -m aed_service

# frontend na porcie 4200
cd frontend && npm ci && npm run start:aed

# frontend z lokalnym backendem portalu (mcod: API :8000, CMS :8002, nginx :443) zamiast publicznego API;
# porty publikuje backend/docker-compose.aed-ports.yml
cd backend && docker compose -f docker-compose.local.yml -f docker-compose.aed-ports.yml up mcod-local-api mcod-local-admin mcod-local-cms mcod-local-celery
cd frontend && npm run start:aed-local

# testy
uv run --python 3.13 --with-requirements aed_service/requirements.txt python -m unittest
```

Plan pracy, zasady i podział zadań: `CLAUDE.md`.
