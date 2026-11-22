"""Settings of the national AED list, kept out of settings/base.py so the patch stays in mcod/aed.
Counterparts of the MAIN_DGA_* settings."""
import os

from django.conf import settings

# Owner of the national AED dataset (the ministry). Required, no fallback to the DGA owner: the task stops with a
# configuration error before reading any list when it is missing or the institution does not exist.
_owner = os.environ.get("MAIN_AED_DATASET_OWNER_ORGANIZATION_PK", "").strip()
OWNER_ORGANIZATION_PK = int(_owner) if _owner else None

# Working file of a merge run. Under MEDIA_ROOT like DGA's MAIN_DGA_RESOURCE_XLSX_CREATION_ROOT; the domain
# deployment serves only the public media folders, so this folder is not reachable over HTTP.
FILE_CREATION_ROOT = os.path.join(settings.MEDIA_ROOT, "main_aed")
FILE_NAME_PREFIX = "Krajowy wykaz AED – Ministerstwo Cyfryzacji"
# One lifetime for the run lock and both cache entries of a run (file path, created objects): longer than
# 1 + 5 retries x 20 s of the task. ponytail: run state lives in the cache as in DGA, not in the database.
RUN_TIMEOUT = 60 * 60
LOCK_KEY = "main_aed_run_lock"

# Only files kept by the portal are read. A link resource marked as an AED list is rejected unless this is on
# (the worker would fetch addresses chosen by the provider).
ALLOW_REMOTE_LISTS = os.environ.get("MAIN_AED_ALLOW_REMOTE_LISTS", "false").lower() in ("1", "true", "yes")
REMOTE_TOTAL_TIMEOUT = 30  # seconds for the whole download, not between chunks
# Limits of one provider's list, checked before parsing (form and merge); a list over a limit is rejected.
MAX_LIST_BYTES = 20 * 1024 * 1024
MAX_LIST_ROWS = 100000

RESOURCE_TITLE = "Krajowy wykaz AED"
RESOURCE_DESC = (
    "Wykaz zbiorczy defibrylatorów AED w Polsce, tworzony codziennie przez portal z wykazów AED, które "
    "instytucje i firmy publikują jako zasoby w swoich zbiorach. Każdy wykaz jest sprawdzany według "
    "standardu AED, a to samo urządzenie zgłoszone w kilku wykazach występuje raz. Struktura pliku: "
    "jeden wiersz to jedno urządzenie, CSV UTF-8, współrzędne WGS84 w kolumnach szerokosc_geograficzna "
    "i dlugosc_geograficzna. Raport z ostatniego scalania, z listą wykorzystanych wykazów (instytucja, zbiór, "
    "zasób, link, licencja) do uznania autorstwa: " + settings.API_URL + "/aed-aggregated"
)
DATASET_TITLE = "Krajowy wykaz defibrylatorów AED – wykaz zbiorczy"
DATASET_DESC = (
    "Zbiór zawiera wykaz zbiorczy defibrylatorów AED scalony z wykazów AED publikowanych w portalu przez "
    "samorządy, instytucje i firmy. Aby Twoje urządzenia znalazły się w wykazie, opublikuj w swoim zbiorze "
    "zasób CSV w strukturze standardu AED i zaznacz w nim „Wykaz AED: TAK”. Autorów wykazów, z których powstał "
    "wykaz zbiorczy, wraz z linkami do ich zasobów i licencjami podaje raport ze scalania: "
    + settings.API_URL + "/aed-aggregated (pole wykorzystane_zasoby). Kolumna zrodlo wskazuje źródło każdego rekordu."
)
DATASET_UPDATE_NOTIFICATION_EMAIL = getattr(settings, "MAIN_DGA_DATASET_UPDATE_NOTIFICATION_EMAIL", "")
DATASET_CATEGORIES_TITLES = ["Zdrowie"]
DATASET_TAGS_NAMES = ["AED", "defibrylator", "wykaz zbiorczy"]

FORM_MAX_MESSAGES = 10  # as goodtables' error_limit in the portal's tabular validation

# E-mail to the provider when the merge rejects its list or accepts it in part (mcod/aed/notifications.py).
NOTIFY_PROVIDERS = os.environ.get("MAIN_AED_NOTIFY_PROVIDERS", "true").lower() not in ("0", "false", "no")
# Page with the AED template and converter, linked in that e-mail; empty = no link.
LIST_HELP_URL = os.environ.get("MAIN_AED_LIST_HELP_URL", "")

# Fixed public description of each aed_standard problem code. The public report and the provider e-mail use these
# instead of aed_standard's messages, which quote the provider's raw values ("Otrzymano: ...").
PROBLEM_DESCRIPTIONS = {
    "brak_kolumny": "Brak kolumny wymaganej przez standard AED.",
    "brak_wierszy": "Plik nie zawiera wierszy z danymi.",
    "brak_wymaganego": "Brak wartości w polu wymaganym.",
    "dane_osobowe": "Pole może zawierać dane osobowe, których nie publikujemy.",
    "data_z_przyszlosci": "Data z przyszłości.",
    "format_csv": "Plik nie jest poprawnym plikiem CSV.",
    "format_daty": "Data nie jest w formacie RRRR-MM-DD.",
    "format_email": "Niepoprawny adres e-mail.",
    "format_liczby": "Wartość nie jest liczbą.",
    "format_liczby_calkowitej": "Wartość nie jest liczbą całkowitą.",
    "format_pola": "Wartość ma niepoprawny format.",
    "kod_do_szafki": "Pole może zawierać kod do szafki, którego nie publikujemy.",
    "kodowanie": "Plik nie jest zapisany w kodowaniu UTF-8.",
    "licencja": "Licencja zbioru nie pozwala włączyć wykazu do zbioru krajowego.",
    "liczba_kolumn": "Wiersz ma inną liczbę kolumn niż nagłówek.",
    "limit": "Wykaz przekracza dopuszczalny rozmiar.",
    "link_wylaczony": "Wykaz musi być plikiem w portalu, nie linkiem.",
    "nieznana_kolumna": "Kolumna spoza standardu AED.",
    "odczyt": "Nie udało się odczytać pliku wykazu.",
    "powtorzona_kolumna": "Kolumna występuje w pliku więcej niż raz.",
    "powtorzony_id_aed": "Identyfikator urządzenia powtarza się; nadano nowy.",
    "powtorzony_naglowek": "Nagłówek powtarza się w danych.",
    "poza_polska": "Współrzędne poza Polską.",
    "poza_zakresem": "Wartość poza dozwolonym zakresem.",
    "przecinek_dziesietny": "Liczba zapisana z przecinkiem zamiast kropki.",
    "pusta_nazwa_kolumny": "Kolumna bez nazwy.",
    "pusty_plik": "Plik jest pusty.",
    "separator": "Separatorem pól musi być przecinek.",
    "spoza_slownika": "Wartość spoza słownika standardu AED.",
    "termin_minal": "Termin ważności minął.",
    "wartosc_logiczna": "Niepoprawna wartość logiczna.",
    "wiersz_w_cudzyslowie": "Cały wiersz ujęty w cudzysłów.",
    "wspolrzedne_niepelne": "Podano tylko jedną ze współrzędnych.",
    "wspolrzedne_zamienione": "Szerokość i długość geograficzna są zamienione.",
    "wymagane_dla_aktywnego": "Brak pola wymaganego dla urządzenia aktywnego.",
    "znak_nul": "Plik zawiera niedozwolony znak NUL.",
}
PROBLEM_DESCRIPTION_DEFAULT = "Niezgodność ze standardem AED."
