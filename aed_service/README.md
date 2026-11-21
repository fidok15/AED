# Usługa AED (prototyp)

Samodzielne API (Falcon 4 + SQLite) realizujące kontrakt z `docs/api-aed.md`. Walidacja, mapper, deduplikacja i eksport pochodzą z `aed_standard`.

## Start

Z katalogu głównego repozytorium (wymaga `uv`; Python 3.13, bo Falcon nie ma jeszcze wsparcia dla 3.15):

```
uv run --python 3.13 --with-requirements aed_service/requirements.txt python -m aed_service
```

- adres: `http://localhost:8085/api/aed` (zmiana portu: `AED_PORT=9000`),
- pierwszy start zakłada konta demo i importuje rejestr krajowy z `datasets/raw` (ok. 19 tys. rekordów, kilka sekund),
- baza: `aed_service/aed_service.db` (plik ignorowany przez git; inna ścieżka: `AED_DB=/ścieżka/plik.db`),
- CORS: dozwolony `http://localhost:4200` (zmiana: `AED_CORS_ORIGINS=http://a,http://b`),
- adres frontendu w kodzie QR naklejki: `AED_BASE_URL` (domyślnie `http://localhost:4200`).

## Konta demo (dane fikcyjne)

| Rola | E-mail | Hasło | Podmiot |
|---|---|---|---|
| ministerstwo | `ministerstwo@aed.example` | `ministerstwo-demo` | Ministerstwo Cyfryzacji (konto demo), Warszawa |
| firma (producent) | `pulsar@aed.example` | `pulsar-demo` | Pulsar Medical Sp. z o.o., Gdańsk |
| firma (sprzedawca) | `serwis@aed.example` | `serwis-demo` | Serwis Rytm Sp. z o.o., Poznań |

## Proxy w Angularze

W `frontend/proxy.*.conf.json` (dev) skieruj `/api/aed` na usługę, przed regułą dla `/api` portalu:

```json
{ "/api/aed": { "target": "http://localhost:8085", "secure": false, "changeOrigin": true } }
```

Bez proxy też działa (CORS dla `localhost:4200`), wtedy wołaj `http://localhost:8085/api/aed/...`.

## Odznaka sprzedawcy

`odznaka = tak`, gdy firma ma co najmniej jedno urządzenie oraz jednocześnie:

- średnia kompletność jej urządzeń >= `BADGE_MIN_COMPLETENESS` = 70,
- udział urządzeń ze statusem `aktywny` >= `BADGE_MIN_ACTIVE_SHARE` = 0,5.

Stałe są na górze `aed_service/app.py`; progi zwraca też `GET /api/aed/sprzedawcy` w polu `progi`.

## Reguły zadań cyklicznych

Stałe w `app.py`: prośba o potwierdzenie po 183 dniach bez weryfikacji, przypomnienie 60 dni przed końcem ważności baterii lub elektrod, `nieaktualny` po 365 dniach. Ten sam rodzaj wiadomości dla urządzenia nie jest powtarzany przez 30 dni (więc ponowne uruchomienie tego samego dnia niczego nie dubluje).

## Reset bazy

Zatrzymaj usługę i usuń plik: `rm aed_service/aed_service.db` (kolejny start zasieje dane od nowa). Przykładowy plik `wzorzec/przyklad-sprzedawca.csv` można wgrać raz; powtórne wgranie zgłosi duplikaty.

## Testy

```
uv run --python 3.13 --with-requirements aed_service/requirements.txt python -m unittest
```

## Uwagi prototypu

- Wiadomości nie są wysyłane; trafiają do skrzynki (`GET /api/aed/wiadomosci`, konto ministerstwa). Zawierają link z tokenem zarządcy (w bazie tylko hash tokenu).
- Eksport i widok publiczny nie zawierają `numer_seryjny`, `dysponent_email` i `dysponent_telefon`.
- Brak limitu prób logowania i serwer jednowątkowy (`wsgiref`) – do demonstracji, nie do produkcji.
