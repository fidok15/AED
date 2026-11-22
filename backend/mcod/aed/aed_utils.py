"""National AED list: merge of all AED lists ("wykaz AED") published as resources on the portal.

Modelled step by step on the DGA list (mcod/resources/dga_utils.py, mcod/resources/tasks/dga.py):
provider resources flagged `contains_aed_list` -> one file -> one resource in the ministry's dataset ->
validation by the portal's own tasks -> AggregatedAEDInfo points at it, the old one is deleted.
Structure, validation and deduplication come from aed_standard (aed_standard/schema.json).
"""
import datetime
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import requests
import sentry_sdk
from cache_memoize import cache_memoize
from django.apps import apps
from django.core.cache import caches
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.db.models import QuerySet

from aed_standard import schema as S
from aed_standard.build import to_csv
from aed_standard.validate import ERROR, LAT, LON
from aed_standard.wykaz import merge_wykazy, read_wykaz
from mcod.aed import constants as C
from mcod.aed.notifications import PENDING_KEY, notify_aed_list_providers

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


def read_resource_bytes(resource: "Resource") -> Tuple[Optional[bytes], Optional[str]]:
    """-> (CSV bytes, None) or (None, Polish error). File first (CSV or the portal's CSV copy of XLSX), then link."""
    for field_file in (resource.main_file if resource.format == "csv" else None, resource.csv_converted_file):
        if field_file:
            try:
                with field_file.open("rb") as f:
                    return f.read(), None
            except Exception as exc:
                logger.error("Cannot read AED list file of resource %s: %s", resource.pk, exc)
    if resource.link and not resource.is_link_internal:
        try:
            # Unlike DGA (verify=False): the content is republished as official data, so the certificate must be valid.
            response = requests.get(resource.link, timeout=(3.0, 5.0))
        except requests.exceptions.SSLError:
            return None, "Adres zasobu %s ma nieprawidłowy certyfikat HTTPS." % resource.link
        except requests.exceptions.RequestException:
            return None, "Adres zasobu %s nie odpowiada." % resource.link
        if response.status_code != 200:
            return None, "Adres zasobu %s zwrócił kod %s zamiast 200." % (resource.link, response.status_code)
        return response.content, None
    return None, (
        "Wykaz AED musi być plikiem CSV (UTF-8, przecinek) w strukturze standardu AED "
        "albo plikiem XLSX, z którego portal zrobił kopię CSV."
    )


def validate_aed_list_file(data: bytes, resource: "Resource", dataset: "Dataset") -> List[str]:
    """Polish error messages for the admin form ([] = the list can be saved)."""
    _, report = read_wykaz(data, source_for_resource(resource, dataset))
    errors = [p for p in report["problemy"] if p["poziom"] == ERROR]
    messages = []
    for p in errors[: C.FORM_MAX_MESSAGES]:
        where = "Wiersz %s" % p["wiersz"] if p["wiersz"] is not None else "Plik"
        messages.append("%s%s: %s" % (where, ", pole %s" % p["pole"] if p["pole"] else "", p["komunikat"]))
    if messages and report["problemy_razem"] > len(messages):
        messages.append("Pokazano %d z %d problemów w pliku." % (len(messages), report["problemy_razem"]))
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


def key_generator_for_create_main_aed_file(*args, **kwargs) -> str:
    return "main_aed_file_path_to_clean"


def get_or_create_main_aed_path() -> Path:
    directory = Path(C.FILE_CREATION_ROOT)
    os.makedirs(directory, exist_ok=True)
    return directory / ("%s %s.csv" % (C.FILE_NAME_PREFIX, datetime.datetime.now().strftime("%Y%m%d")))


def build_main_aed_list(resources) -> Tuple[str, Dict[str, Any]]:
    """-> (CSV text of the national list, public report). No database writes."""
    items = []
    for resource in resources:
        data, error = read_resource_bytes(resource)
        items.append((source_for_resource(resource), data, error))
    national, pairs, report = merge_wykazy(items)
    report["data_utworzenia"] = datetime.datetime.now().isoformat(timespec="seconds")
    logger.info(
        "AED lists accepted: %s/%s, national list rows: %s",
        report["wykazy_przyjete"],
        report["wykazy_razem"],
        report["rekordy_w_wykazie_krajowym"],
    )
    return to_csv(national), report


@cache_memoize(
    timeout=C.FILE_CREATION_CACHE_TIMEOUT,
    hit_callable=lambda *args, **kwargs: logger.info("Using cache for main AED file path."),
    key_generator_callable=key_generator_for_create_main_aed_file,
)
def create_main_aed_file() -> Tuple[str, Dict[str, Any]]:
    """Writes the national AED list CSV. -> (path, report). Cached so that task retries reuse it (as DGA)."""
    content, report = build_main_aed_list(get_all_aed_list_resources())
    file_path = get_or_create_main_aed_path()
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    return str(file_path), report


def create_main_aed_dataset() -> int:
    Organization = apps.get_model("organizations", "Organization")
    Dataset = apps.get_model("datasets", "Dataset")
    Category = apps.get_model("categories", "Category")
    Tag = apps.get_model("tags", "Tag")
    try:
        institution = Organization.objects.get(pk=C.OWNER_ORGANIZATION_PK)
    except Organization.DoesNotExist:
        logger.error("Can't create main AED dataset. Institution with pk %s not found.", C.OWNER_ORGANIZATION_PK)
        raise ObjectDoesNotExist("Main AED Owner Institution not found.")

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


def key_generator_for_create_main_aed_resource(*args, **kwargs) -> str:
    return "main_aed_to_clean"


@cache_memoize(
    timeout=C.RESOURCE_CREATION_CACHE_TIMEOUT,
    hit_callable=lambda *args, **kwargs: logger.info("AED objects get from cache."),
    key_generator_callable=key_generator_for_create_main_aed_resource,
)
def create_main_aed_resource_with_dataset(file_path: str) -> Tuple[int, Optional[int]]:
    """Creates the national AED list resource (and the dataset when missing). -> (resource pk, new dataset pk)."""
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
    return resource.pk, dataset.pk if new_dataset_created else None


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
    notify_aed_list_providers(old_report, report)  # never raises
    if any(w.get(PENDING_KEY) for w in report.get("wykazy", [])):  # undelivered messages are retried next time
        AggregatedAEDInfo.objects.filter(resource=new_resource).update(report=report)


def clean_up_after_main_aed_resource_creation(exception_occurred: bool) -> None:
    """As clean_up_after_main_dga_resource_creation: on failure delete what the task created; always drop caches
    and the temporary file."""
    cache = caches["default"]
    objects_key = key_generator_for_create_main_aed_resource()
    file_key = key_generator_for_create_main_aed_file()
    resource_created, dataset_created = cache.get(objects_key, (None, None))
    cached_file = cache.get(file_key, None)
    try:
        if exception_occurred and resource_created:
            apps.get_model("resources", "Resource").raw.filter(pk=resource_created).delete()
        if exception_occurred and dataset_created:
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
