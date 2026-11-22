"""National AED list: merge of all AED lists ("wykaz AED") published as resources on the portal.

Modelled step by step on the DGA list (mcod/resources/dga_utils.py, mcod/resources/tasks/dga.py):
provider resources flagged `contains_aed_list` -> one file -> one resource in the ministry's dataset ->
validation by the portal's own tasks -> AggregatedAEDInfo points at it, the old one is deleted.
Structure, validation and deduplication come from aed_standard (aed_standard/schema.json).
"""
import datetime
import hashlib
import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import requests
import sentry_sdk
from django.apps import apps
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.db.models import QuerySet

from aed_standard import schema as S
from aed_standard.build import to_csv
from aed_standard.validate import ERROR, LAT, LON
from aed_standard.wykaz import merge_wykazy, read_wykaz
from mcod.aed import constants as C
from mcod.aed.notifications import PENDING_KEY, notify_aed_list_providers, public_problem

if TYPE_CHECKING:
    from mcod.datasets.models import Dataset
    from mcod.resources.models import Resource

logger = logging.getLogger("mcod")

PORTAL_TO_STANDARD_LICENCE = {"CC0 1.0": "CC0 1.0", "CC BY 4.0": "CC BY 4.0"}  # Dataset.LICENSES names


def get_aggregated_aed_info():
    return apps.get_model("aed", "AggregatedAEDInfo").objects.last()


def get_main_aed_resource() -> Optional["Resource"]:
    info = get_aggregated_aed_info()
    return info.main_aed_resource if info else None


def get_main_aed_dataset() -> Optional["Dataset"]:
    info = get_aggregated_aed_info()
    return info.main_aed_dataset if info else None


def source_for_resource(resource: "Resource", dataset: Optional["Dataset"] = None) -> Dict[str, Any]:
    """aed_standard.wykaz source description of a portal resource (also used by the admin form)."""
    dataset = dataset or resource.dataset
    data_date = getattr(resource, "data_date", None) or datetime.date.today()
    return {
        "zrodlo": "dane.gov.pl/%s" % dataset.pk,
        "zasob": resource.pk,
        "tytul": resource.title or "",
        "instytucja": dataset.organization.title,
        "licencja": PORTAL_TO_STANDARD_LICENCE.get(dataset.license_name, dataset.license_name),
        "data_aktualizacji": data_date.isoformat(),
        # Lists published by the dataset owner (ministry register of sellers' submissions) win on merge.
        "priority": 0 if dataset.organization_id == C.OWNER_ORGANIZATION_PK else 1,
    }


def list_size_error(size: Optional[int]) -> Optional[str]:
    if size is not None and size > C.MAX_LIST_BYTES:
        return "Wykaz AED ma %.1f MB; największy dopuszczalny rozmiar to %d MB." % (
            size / 1048576.0, C.MAX_LIST_BYTES // 1048576)
    return None


def list_rows_error(data: bytes) -> Optional[str]:
    if data.count(b"\n") > C.MAX_LIST_ROWS:
        return "Wykaz AED ma więcej niż %d wierszy; podziel go na kilka zasobów." % C.MAX_LIST_ROWS
    return None


class TransientError(str):
    """A read failure that may pass by itself (I/O, network, server error) - unlike a rejection by rule
    (link switched off, over a limit, not a CSV). Only these keep the last national list (keep_last_list...)."""


REMOTE_DISABLED = (
    "Wykaz AED musi być plikiem zapisanym w portalu. Portal nie pobiera wykazów z linków - "
    "dodaj plik CSV jako zasób."
)


def is_remote_link(resource: "Resource") -> bool:
    return bool(resource.link) and not resource.is_link_internal


def _fetch_remote_list(url: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Only with MAIN_AED_ALLOW_REMOTE_LISTS: no redirects, size limit, limit of the whole download time."""
    deadline = time.monotonic() + C.REMOTE_TOTAL_TIMEOUT
    try:
        # Unlike DGA (verify=False): the content is republished as official data, so the certificate must be valid.
        with requests.get(url, timeout=(3.0, 5.0), allow_redirects=False, stream=True) as response:
            if response.status_code != 200:
                error = "Adres zasobu zwrócił kod %s zamiast 200." % response.status_code
                return None, TransientError(error) if response.status_code >= 500 else error
            chunks, size = [], 0
            for chunk in response.iter_content(64 * 1024):
                size += len(chunk)
                if size > C.MAX_LIST_BYTES:
                    return None, list_size_error(size)
                if time.monotonic() > deadline:
                    return None, "Pobieranie wykazu z adresu zasobu trwało dłużej niż %d s." % C.REMOTE_TOTAL_TIMEOUT
                chunks.append(chunk)
            return b"".join(chunks), None
    except requests.exceptions.SSLError:
        return None, "Adres zasobu ma nieprawidłowy certyfikat HTTPS."
    except requests.exceptions.RequestException:
        return None, TransientError("Adres zasobu nie odpowiada.")


def read_resource_bytes(resource: "Resource") -> Tuple[Optional[bytes], Optional[str]]:
    """-> (CSV bytes, None) or (None, Polish error). File kept by the portal (CSV or its CSV copy of XLSX);
    a link resource only with MAIN_AED_ALLOW_REMOTE_LISTS. Size and row limits before parsing."""
    if is_remote_link(resource) and not C.ALLOW_REMOTE_LISTS:
        return None, REMOTE_DISABLED
    io_failed = False
    for field_file in (resource.main_file if resource.format == "csv" else None, resource.csv_converted_file):
        if field_file:
            try:
                error = list_size_error(field_file.size)
                if error:
                    return None, error
                with field_file.open("rb") as f:
                    data = f.read()
                return (None, list_rows_error(data)) if list_rows_error(data) else (data, None)
            except Exception as exc:
                io_failed = True
                logger.error("Cannot read AED list file of resource %s: %s", resource.pk, exc)
    if io_failed:
        return None, TransientError("Nie udało się odczytać pliku zasobu z magazynu portalu.")
    if is_remote_link(resource):
        data, error = _fetch_remote_list(resource.link)
        if data is not None and list_rows_error(data):
            return None, list_rows_error(data)
        return data, error
    return None, (
        "Wykaz AED musi być plikiem CSV (UTF-8, przecinek) w strukturze standardu AED "
        "albo plikiem XLSX, z którego portal zrobił kopię CSV."
    )


def validate_aed_list_file(data: bytes, resource: "Resource", dataset: "Dataset") -> List[str]:
    """Polish error messages for the admin form ([] = the list can be saved)."""
    too_big = list_size_error(len(data)) or list_rows_error(data)
    if too_big:
        return [too_big]
    _, report = read_wykaz(data, source_for_resource(resource, dataset))
    errors = [p for p in report["problemy"] if p["poziom"] == ERROR]
    messages = []
    for p in errors[: C.FORM_MAX_MESSAGES]:
        where = "Wiersz %s" % p["wiersz"] if p["wiersz"] is not None else "Plik"
        messages.append("%s%s: %s" % (where, ", pole %s" % p["pole"] if p["pole"] else "", p["komunikat"]))
    if messages and report["problemy_razem"] > len(messages):
        messages.append("Pokazano %d z %d problemów w pliku." % (len(messages), report["problemy_razem"]))
    if messages and C.LIST_HELP_URL:
        messages.append("Plik można przekształcić do standardu AED w konwerterze: %s" % C.LIST_HELP_URL)
    return messages


def get_all_aed_list_resources() -> QuerySet:
    """Published AED lists, the current national list excluded. Unlike DGA, no prefilter on task statuses:
    every list is read and a rejected one is named, with the reason, in the public report."""
    Resource = apps.get_model("resources", "Resource")
    main = get_main_aed_resource()
    return (
        Resource.objects.filter(contains_aed_list=True, status="published")
        .exclude(id=main.pk if main else None)
        .select_related("dataset__organization")
        .order_by("dataset__organization__title", "id")
    )


def key_generator_for_create_main_aed_file(run_id: str = "", *args, **kwargs) -> str:
    return "main_aed_file_path_to_clean:%s" % run_id


def acquire_run_lock(run_id: str) -> bool:
    """One merge at a time (schedule and manual command share the queue). cache.add is atomic in Redis (SET NX);
    a retry of the same Celery task keeps its id and so its lock."""
    cache = caches["default"]
    return cache.add(C.LOCK_KEY, run_id, C.RUN_TIMEOUT) or cache.get(C.LOCK_KEY) == run_id


def release_run_lock(run_id: str) -> None:
    cache = caches["default"]
    if cache.get(C.LOCK_KEY) == run_id:
        cache.delete(C.LOCK_KEY)


def get_owner_organization():
    """The configured owner of the national AED dataset; checked before any list is read."""
    Organization = apps.get_model("organizations", "Organization")
    if C.OWNER_ORGANIZATION_PK is None:
        raise ImproperlyConfigured("MAIN_AED_DATASET_OWNER_ORGANIZATION_PK is not set (owner of the national AED list).")
    try:
        return Organization.objects.get(pk=C.OWNER_ORGANIZATION_PK)
    except Organization.DoesNotExist:
        raise ImproperlyConfigured("Main AED owner institution %s not found." % C.OWNER_ORGANIZATION_PK)


def get_or_create_main_aed_path(run_id: str = "") -> Path:
    directory = Path(C.FILE_CREATION_ROOT)
    os.makedirs(directory, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d")
    return directory / ("%s %s%s.csv" % (C.FILE_NAME_PREFIX, stamp, " " + run_id[:8] if run_id else ""))


def attribution(resource: "Resource") -> Dict[str, Any]:
    """CC BY 4.0 attribution of one list used in the national list (public report)."""
    dataset = resource.dataset
    return {
        "instytucja": dataset.organization.title,
        "zbior": dataset.title,
        "zasob": resource.title,
        "zasob_id": resource.pk,
        "link": resource.frontend_absolute_url,
        "licencja": dataset.license_name,
    }


REPEATED = "powtorzony"


def list_digest(data: bytes) -> str:
    """SHA-256 of a list's content after normalising the BOM, line endings and trailing newlines."""
    text = data[3:] if data.startswith(b"\xef\xbb\xbf") else data
    return hashlib.sha256(text.replace(b"\r\n", b"\n").replace(b"\r", b"\n").rstrip(b"\n")).hexdigest()


def repeated_list_entry(source: Dict[str, Any], first_resource_pk: int) -> Dict[str, Any]:
    """Report entry of a list identical to an earlier list of the same institution; it is not merged."""
    return {
        "zasob": source["zasob"], "tytul": source["tytul"], "instytucja": source["instytucja"],
        "zrodlo": source["zrodlo"], "status": REPEATED, "wiersze": 0, "przyjete": 0, "problemy": [],
        "problemy_razem": 0, "powtorzenie_zasobu": first_resource_pk,
    }


def build_main_aed_list(resources) -> Tuple[str, Dict[str, Any]]:
    """-> (CSV text of the national list, report). No database writes. The full report (with aed_standard's
    messages) stays in the database for the provider e-mail; the API shows public_report()."""
    items, used, repeated, first_by_content = [], {}, [], {}
    unreadable = 0
    for resource in resources:
        data, error = read_resource_bytes(resource)
        unreadable += isinstance(error, TransientError)  # rejections by rule do not count
        source = source_for_resource(resource)
        used[resource.pk] = resource
        if data is not None:
            # The same file published twice by one institution would double every device (rows of one source are
            # never merged automatically). Lists that only overlap stay: several devices in one building are fine.
            first = first_by_content.setdefault((resource.dataset.organization_id, list_digest(data)), resource.pk)
            if first != resource.pk:
                repeated.append(repeated_list_entry(source, first))
                continue
        items.append((source, data, error))
    national, pairs, report = merge_wykazy(items)
    report["wykazy"] += repeated
    report["wykazy_razem"] += len(repeated)
    report["wykazy_powtorzone"] = len(repeated)
    report["data_utworzenia"] = datetime.datetime.now().isoformat(timespec="seconds")
    report["wykazy_nieodczytane"] = unreadable
    report["wykorzystane_zasoby"] = [
        attribution(used[w["zasob"]]) for w in report["wykazy"]
        if w["status"] not in ("odrzucony", REPEATED) and w["zasob"] in used
    ]
    logger.info(
        "AED lists accepted: %s/%s, national list rows: %s",
        report["wykazy_przyjete"],
        report["wykazy_razem"],
        report["rekordy_w_wykazie_krajowym"],
    )
    return to_csv(national), report


PUBLIC_LIST_KEYS = (
    "zasob", "tytul", "instytucja", "zrodlo", "status", "wiersze", "przyjete", "problemy_razem", "powtorzenie_zasobu")
PUBLIC_REPORT_KEYS = (
    "wykazy_razem", "wykazy_przyjete", "wykazy_powtorzone", "wykazy_nieodczytane", "rekordy_z_wykazow",
    "rekordy_po_deduplikacji",
    "polaczenia", "do_przegladu", "rekordy_w_wykazie_krajowym", "pominiete_przy_publikacji", "kompletnosc_srednia",
    "data_utworzenia", "wykorzystane_zasoby", "ostatnie_nieudane_scalanie",
)


def public_report(report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Explicit public report: counters, per list status and coded problems; no raw values, URLs or internal keys."""
    report = report or {}
    result = {k: report[k] for k in PUBLIC_REPORT_KEYS if k in report}
    result["wykazy"] = [
        dict({k: w.get(k) for k in PUBLIC_LIST_KEYS}, problemy=[public_problem(p) for p in w.get("problemy", [])])
        for w in report.get("wykazy", [])
    ]
    return result


def create_main_aed_file(run_id: str = "") -> Tuple[str, Dict[str, Any]]:
    """Writes the national AED list CSV of this run. -> (path, report). Cached per run so that task retries
    reuse it (as DGA)."""
    cache = caches["default"]
    key = key_generator_for_create_main_aed_file(run_id)
    cached = cache.get(key) if run_id else None  # cache only serves retries of one task run
    if cached and os.path.exists(cached[0]):
        logger.info("Using cache for main AED file path.")
        return cached
    content, report = build_main_aed_list(get_all_aed_list_resources())
    file_path = get_or_create_main_aed_path(run_id)
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    result = (str(file_path), report)
    if run_id:
        cache.set(key, result, C.RUN_TIMEOUT)
    return result


def create_main_aed_dataset() -> int:
    Dataset = apps.get_model("datasets", "Dataset")
    Category = apps.get_model("categories", "Category")
    Tag = apps.get_model("tags", "Tag")
    institution = get_owner_organization()

    with transaction.atomic():
        dataset = Dataset.objects.create(
            title=C.DATASET_TITLE,
            notes=C.DATASET_DESC,
            organization=institution,
            update_notification_recipient_email=C.DATASET_UPDATE_NOTIFICATION_EMAIL,
            has_dynamic_data=False,
            has_high_value_data=False,
            has_high_value_data_from_ec_list=False,
            has_research_data=False,
            update_frequency="daily",
            status="published",
            # CC BY 4.0 (Dataset.license_code): merged lists may require attribution; source is kept in column zrodlo.
            license_condition_source=True,
            license_condition_modification=True,
        )
        categories = Category.objects.filter(title__in=C.DATASET_CATEGORIES_TITLES)
        tags = [Tag.objects.get_or_create(name=name, language="pl")[0] for name in C.DATASET_TAGS_NAMES]
        dataset.categories.set(categories)
        dataset.tags.set(tags)
        dataset.save()
    logger.info("Created main AED dataset %s.", dataset.pk)
    return dataset.pk


def key_generator_for_create_main_aed_resource(run_id: str = "", *args, **kwargs) -> str:
    return "main_aed_to_clean:%s" % run_id


def create_main_aed_resource_with_dataset(file_path: str, run_id: str = "") -> Tuple[int, Optional[int]]:
    """Creates the national AED list resource (and the dataset when missing). -> (resource pk, new dataset pk).
    Cached per run, so a retry of the task reuses the candidate instead of creating another."""
    cache = caches["default"]
    key = key_generator_for_create_main_aed_resource(run_id)
    cached = cache.get(key) if run_id else None
    if cached:
        logger.info("AED objects get from cache.")
        return cached
    Resource = apps.get_model("resources", "Resource")
    ResourceFile = apps.get_model("resources", "ResourceFile")
    Dataset = apps.get_model("datasets", "Dataset")

    old = get_main_aed_resource()
    dataset = get_main_aed_dataset()
    new_dataset_created = False
    with transaction.atomic():
        if dataset is None:
            dataset = Dataset.objects.get(pk=create_main_aed_dataset())
            new_dataset_created = True
        with open(file_path, "rb") as f:
            django_file = SimpleUploadedFile(name=os.path.basename(file_path), content=f.read(), content_type="text/csv")
        resource = Resource.objects.create(
            title=old.title if old else C.RESOURCE_TITLE,
            description=old.description if old else C.RESOURCE_DESC,
            dataset=dataset,
            has_dynamic_data=False,
            has_high_value_data=False,
            has_high_value_data_from_ec_list=False,
            has_research_data=False,
            contains_protected_data=False,
            contains_aed_list=False,  # the national list is not a source of itself
            status="published",
            data_date=datetime.date.today(),
            tabular_data_schema=main_aed_tabular_schema(),
        )
        # post_save runs the portal's file and tabular data validation tasks
        ResourceFile.objects.create(resource=resource, is_main=True, file=django_file)
    result = (resource.pk, dataset.pk if new_dataset_created else None)
    if run_id:
        cache.set(key, result, C.RUN_TIMEOUT)
    return result


def main_aed_tabular_schema() -> Dict[str, Any]:
    """Table schema of the national list with map markers, set before the portal processes the file, so the
    first indexing already has map points (same structure the "Mapy i wykresy" widget writes, mcod/lib/widgets.py).
    Columns from aed_standard; only the coordinates are numbers - the rest is text, so empty cells always pass
    the portal's goodtables check. missingValues == [] matches a resource without special signs, so
    _resolve_tabular_data_schema (resources/tasks/process_resource_file_data.py) keeps this schema."""
    markers = {LAT: "b", LON: "l", "nazwa": "label"}
    fields, geo = [], {}
    for index, name in enumerate(S.FIELD_NAMES):
        field = {"name": name, "type": "number" if name in (LAT, LON) else "string", "format": "default"}
        if name in markers:
            field["geo"] = markers[name]
            geo[markers[name]] = {"col_name": name, "col_index": index}
        fields.append(field)
    return {"fields": fields, "missingValues": [], "geo": geo}


def update_or_create_aggr_aed_info_and_delete_old_main_aed(new_resource: "Resource", report: Dict[str, Any]) -> None:
    AggregatedAEDInfo = apps.get_model("aed", "AggregatedAEDInfo")
    info = AggregatedAEDInfo.objects.last()
    old = info.main_aed_resource if info else None
    old_report = info.report if info else None
    with transaction.atomic():
        if info:
            info.resource = new_resource
            info.report = report
            info.save()
        else:
            AggregatedAEDInfo.objects.create(resource=new_resource, report=report)
        if old:
            old.delete()
            logger.info("Previous main AED resource %s deleted.", old.pk)
    notify_aed_list_providers(old_report, report)  # never raises; marks undelivered entries
    if any(w.get(PENDING_KEY) for w in report.get("wykazy", [])):  # undelivered messages are retried next time
        AggregatedAEDInfo.objects.filter(resource=new_resource).update(report=report)


def keep_last_list_after_failed_sources(report: Dict[str, Any]) -> bool:
    """Empty result while some lists could not be read for a transient reason (TransientError: I/O, network,
    server error): the last good national list stays; only a note goes to the report. A list rejected by rule
    (link off, over a limit, not the standard) does not count, so a withdrawn or excluded source does empty the
    national list. -> True when the run must stop here."""
    if report.get("rekordy_w_wykazie_krajowym") or not report.get("wykazy_nieodczytane"):
        return False
    note = {
        "data_utworzenia": report.get("data_utworzenia"),
        "wykazy_nieodczytane": report["wykazy_nieodczytane"],
        "komunikat": "Scalanie dało pusty wykaz, a części wykazów nie udało się odczytać; "
                     "pozostawiono poprzedni wykaz krajowy.",
    }
    logger.error("Main AED: empty result with %s unreadable lists; previous list kept.", report["wykazy_nieodczytane"])
    AggregatedAEDInfo = apps.get_model("aed", "AggregatedAEDInfo")
    info = AggregatedAEDInfo.objects.last()
    if info:
        info.report = dict(info.report or {}, ostatnie_nieudane_scalanie=note)
        info.save()
    return True


def clean_up_after_main_aed_resource_creation(exception_occurred: bool, run_id: str = "") -> None:
    """As clean_up_after_main_dga_resource_creation: on failure delete what this run created - never the resource
    the national list currently points at; always drop this run's cache entries and working file."""
    cache = caches["default"]
    objects_key = key_generator_for_create_main_aed_resource(run_id)
    file_key = key_generator_for_create_main_aed_file(run_id)
    resource_created, dataset_created = cache.get(objects_key, (None, None))
    cached_file = cache.get(file_key, None)
    try:
        info = get_aggregated_aed_info()
        published = info.resource_id if info else None
        if exception_occurred and resource_created and resource_created != published:
            apps.get_model("resources", "Resource").raw.filter(pk=resource_created).delete()
        if exception_occurred and dataset_created and resource_created != published:
            apps.get_model("datasets", "Dataset").raw.filter(pk=dataset_created).delete()
    except Exception as exc:
        logger.error("AED clean up failed. Reason: %s", exc)
        sentry_sdk.api.capture_exception(exc)
    finally:
        cache.delete(objects_key)
    try:
        if cached_file and os.path.exists(cached_file[0]):
            os.remove(cached_file[0])
    except Exception as exc:
        logger.error("Cannot delete main AED temp file %s: %s", cached_file, exc)
    finally:
        cache.delete(file_key)
