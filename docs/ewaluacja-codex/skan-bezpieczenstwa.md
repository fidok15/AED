# Skan bezpieczeństwa całego systemu (22.11.2026, ok. 04:15)

Przegląd w trybie „łowcy błędów": tylko ścieżki osiągalne z sieci, sterowane przez użytkownika, z dowodem na osobnej instancji usługi (port 8091, świeża baza). Zakres: `aed_service/`, `aed_standard/`, zmiany w forku portalu (`backend/mcod/aed/`, zaczepy), moduł `frontend/src/app/pages/aed/`, konfiguracje wdrożenia. Jawne hasła kont demo są świadomą decyzją zespołu i nie są zgłaszane. Znaleziska wcześniejszych audytów (`audyt-uslugi.md`, `przeglad-forka-portalu.md`) pominięto.

## Znalezione i naprawione

### 1. Wgrany plik HTML albo SVG uruchamiał się jako strona naszej domeny (stored XSS, CWE-79)

- **Ścieżka:** portal przyjmuje zasoby w formacie HTML (`backend/mcod/settings/base.py`, `SUPPORTED_CONTENT_TYPES`; `resources/file_validation.py:222`). Nakładka domenowa serwuje `/media/resources/` z dysku pod domeną frontendu (`backend/aed-domain/web.conf.template`) oraz pod `api.`, `admin.`, `cms.` (`Caddyfile`).
- **Kto może:** każdy redaktor, czyli także konto `jury@aed.example` z jawnym hasłem.
- **Skutek:** skrypt z wgranego pliku działa w domenie frontendu: odczyt tokenu sesji modułu AED z `sessionStorage` (także konta ministerstwa), żądania do API portalu w imieniu zalogowanego użytkownika (wspólna domena ciasteczka sesji).
- **Lekki prototyp:** to samo przez `location /media/` przekazywane z dane.gov.pl – plik HTML dowolnego dostawcy prawdziwego portalu otwierałby się w naszej domenie.
- **Poprawka:** wszystkie trzy serwery pośredniczące wysyłają dla plików z `/media/` nagłówki `Content-Security-Policy: sandbox; default-src 'none'; …` i `X-Content-Type-Options: nosniff`. Plik da się pobrać i wyświetlić jako obraz, ale nie wykona skryptu ani nie ma dostępu do domeny. Sprawdzone na przebudowanym prototypie (nagłówki obecne); nakładka domenowa – tylko walidacja `caddy validate` i `nginx -t`.

### 2. Naklejka SVG bez ograniczeń dokumentu

- `GET /api/aed/urzadzenia/{id}/naklejka.svg` zwraca dokument SVG w naszej domenie, a identyfikator trafiał do treści bez kodowania. Dziś nie do wykorzystania (identyfikator musi istnieć w rejestrze, a nadaje go usługa), ale jedna zmiana reguły nadawania identyfikatorów otwierałaby XSS.
- **Poprawka:** kodowanie identyfikatora w SVG, `Content-Security-Policy: sandbox` na odpowiedzi, `X-Content-Type-Options: nosniff` na wszystkich odpowiedziach usługi. Test: `tests/test_audyt.py::HardeningTest`.

## Sprawdzone próbą – bez znalezisk

| Próba | Wynik |
|---|---|
| Firma ustawia w CSV pola systemowe (`id_aed`, `status=aktywny`, `zrodlo`, `licencja`, `data_weryfikacji`, `kompletnosc`) | zignorowane: rekord dostaje własny identyfikator, `zgloszony`, `zgloszenie`, CC0; nie trafia do eksportu |
| Zarządca przy potwierdzeniu dosyła `status`, `zrodlo`, `licencja`, `numer_seryjny`, `producent`, `id_aed` | zignorowane (lista dozwolonych pól) |
| Token zarządcy urządzenia A użyty na urządzeniu B (w adresie i w treści) | 403 `zly_token` |
| Druga firma czyta rekord i historię zgłoszeń pierwszej | bez numeru seryjnego i kontaktu; historia rozdzielona |
| Operacje ministerstwa bez logowania i z konta firmy | 401 / 403 na każdej trasie |
| Wstrzyknięcia w `q`, `status`, `zrodlo`, stronicowaniu | zapytania parametryzowane; znaki `%` i `_` kodowane |
| Błędne treści żądań (lista, `null`, obiekt zamiast tekstu) | 400 / 401, bez 500 |
| CORS z obcej domeny | brak nagłówka zezwolenia |
| Zgłoszenie osoby postronnej 300 kB i 40 zgłoszeń z rzędu | treść obcinana, wiadomości do dysponenta nie mnożą się |
| Nazwa pliku ze ścieżką (`../../etc/passwd.csv`) w konwerterze | bez wpływu, plik nie jest zapisywany |
| `<script>` w nazwie urządzenia | zapisany jako tekst; Angular koduje przy wyświetlaniu; dymki map budowane przez `textContent` |
| Wykonywanie poleceń | jedno `subprocess.run` ze stałą listą argumentów, bez danych użytkownika |
| Tokeny | sesja 32 bajty, token zarządcy 24 bajty z `secrets`; w bazie skróty; porównanie stałoczasowe |

## Zostaje jako ryzyko (nie błąd do naprawy w prototypie)

- **Jawne hasła demo** (decyzja zespołu): każdy może zalogować się jako firma i dodać punkt o dowolnej nazwie na publiczną mapę (ze statusem „zgłoszony"), a jako ministerstwo – czytać pełne rekordy i uruchamiać zadania. Prototyp publiczny ma zawierać wyłącznie dane otwarte i fikcyjne.
- **Brak limitu prób logowania i limitu żądań** – bez znaczenia przy jawnych hasłach; do zrobienia przed prawdziwym wdrożeniem.
- **Usługa jednowątkowa** – jedno ciężkie żądanie wstrzymuje API; limity konwertera to ograniczają.
- **Token zarządcy w adresie** (`?t=`) – dzienniki usługi i nginx nie zapisują parametrów; docelowo jednorazowa wymiana na sesję.
- **Token sesji modułu AED w `sessionStorage`** – po poprawce nr 1 nie ma znanej drogi do jego odczytu; docelowo ciasteczko `HttpOnly` wspólne z logowaniem portalu.
- **Nakładka domenowa** po zmianach bezpieczeństwa nie była uruchomiona od początku do końca (tylko walidacja składni).
