"""Settings of the national AED list, kept out of settings/base.py so the patch stays in mcod/aed.
Counterparts of the MAIN_DGA_* settings."""
import os

from django.conf import settings

# Owner of the national AED dataset: the ministry, by default the same institution as for the DGA list.
OWNER_ORGANIZATION_PK = int(
    os.environ.get("MAIN_AED_DATASET_OWNER_ORGANIZATION_PK", settings.MAIN_DGA_DATASET_OWNER_ORGANIZATION_PK)
)

FILE_CREATION_ROOT = os.path.join(settings.MEDIA_ROOT, "main_aed")
FILE_NAME_PREFIX = "Krajowy wykaz AED – Ministerstwo Cyfryzacji"
FILE_CREATION_CACHE_TIMEOUT = getattr(settings, "MAIN_DGA_RESOURCE_XLSX_CREATION_CACHE_TIMEOUT", 60 * 60)
RESOURCE_CREATION_CACHE_TIMEOUT = getattr(settings, "MAIN_DGA_RESOURCE_CREATION_CACHE_TIMEOUT", None)

RESOURCE_TITLE = "Krajowy wykaz AED"
RESOURCE_DESC = (
    "Wykaz zbiorczy defibrylatorów AED w Polsce, tworzony codziennie przez portal z wykazów AED, które "
    "instytucje i firmy publikują jako zasoby w swoich zbiorach. Każdy wykaz jest sprawdzany według "
    "standardu AED, a to samo urządzenie zgłoszone w kilku wykazach występuje raz. Struktura pliku: "
    "jeden wiersz to jedno urządzenie, CSV UTF-8, współrzędne WGS84 w kolumnach szerokosc_geograficzna "
    "i dlugosc_geograficzna. Raport z ostatniego scalania: " + settings.API_URL + "/aed-aggregated"
)
DATASET_TITLE = "Krajowy wykaz defibrylatorów AED – wykaz zbiorczy"
DATASET_DESC = (
    "Zbiór zawiera wykaz zbiorczy defibrylatorów AED scalony z wykazów AED publikowanych w portalu przez "
    "samorządy, instytucje i firmy. Aby Twoje urządzenia znalazły się w wykazie, opublikuj w swoim zbiorze "
    "zasób CSV w strukturze standardu AED i zaznacz w nim „Wykaz AED: TAK”."
)
DATASET_UPDATE_NOTIFICATION_EMAIL = getattr(settings, "MAIN_DGA_DATASET_UPDATE_NOTIFICATION_EMAIL", "")
DATASET_CATEGORIES_TITLES = ["Zdrowie"]
DATASET_TAGS_NAMES = ["AED", "defibrylator", "wykaz zbiorczy"]

FORM_MAX_MESSAGES = 10  # as goodtables' error_limit in the portal's tabular validation
