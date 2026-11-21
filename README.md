# Misja AED – Dane na ratunek

Prototyp na HackNation 2026 (zadanie Ministerstwa Cyfryzacji): proces i narzędzia, dzięki którym ministerstwo zbiera w dane.gov.pl jeden, ujednolicony zbiór danych o defibrylatorach AED.

Jak to działa: producent lub sprzedawca zgłasza urządzenie z konta firmy (plik CSV albo formularz) → system nadaje identyfikator i naklejkę z kodem QR → zarządca obiektu skanuje kod, uzupełnia i potwierdza miejsce oraz godziny dostępu → rekord trafia do zbioru krajowego. Równolegle mapper pobiera istniejące otwarte źródła, sprowadza je do wspólnego standardu i usuwa duplikaty.

## Uruchomienie jedną komendą

Wymaga Dockera.

```
docker compose up --build
```

Potem otwórz `http://localhost:8080/pl/aed`. Pierwsza budowa trwa kilka minut. Konta demonstracyjne są w `aed_service/README.md`.

Strony portalu poza obszarem AED pobierają dane tylko do odczytu z publicznego API dane.gov.pl. Nie loguj się w nich kontem portalu.

## Co jest w repozytorium

| Katalog | Zawartość |
|---|---|
| `aed_standard/` | standard danych (`schema.json`), walidator, mapper źródeł, deduplikacja – czysty Python bez zależności |
| `aed_service/` | usługa API: konta firm, zgłoszenia CSV, naklejki QR, potwierdzenia, rejestr (`docs/api-aed.md`) |
| `frontend/` | fork frontendu dane.gov.pl z modułem AED (`src/app/pages/aed/`) |
| `backend/` | fork backendu dane.gov.pl (niezmieniony; notatka integracyjna w `docs/integracja-portal-backend.md`) |
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

# testy
uv run --python 3.13 --with-requirements aed_service/requirements.txt python -m unittest
```

Plan pracy, zasady i podział zadań: `CLAUDE.md`.
