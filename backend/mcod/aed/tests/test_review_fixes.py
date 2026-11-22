"""Fixes after the portal maintainer's review (docs/ewaluacja-codex/przeglad-forka-portalu.md).
Needs the portal test stack (Postgres, Redis cache)."""
import os
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile

from mcod.aed import constants as C
from mcod.aed.aed_utils import (
    acquire_run_lock,
    build_main_aed_list,
    clean_up_after_main_aed_resource_creation,
    get_all_aed_list_resources,
    key_generator_for_create_main_aed_resource,
    keep_last_list_after_failed_sources,
    public_report,
    read_resource_bytes,
    release_run_lock,
    REMOTE_DISABLED,
    TransientError,
)
from mcod.aed.models import AggregatedAEDInfo
from mcod.aed.tasks import create_main_aed_resource_task
from mcod.datasets.factories import DatasetFactory
from mcod.organizations.factories import OrganizationFactory
from mcod.resources.factories import ResourceFactory
from mcod.resources.forms import ChangeResourceForm
from mcod.resources.models import Resource
from mcod.users.factories import UserFactory

GOOD_LIST = (
    "nazwa,miejscowosc,szerokosc_geograficzna,dlugosc_geograficzna,dostep\n"
    "Urząd Miasta Legionowo,Legionowo,52.395198,20.931382,publiczny\n"
).encode("utf-8")


def _files_in_work_dir():
    return set(os.listdir(C.FILE_CREATION_ROOT)) if os.path.isdir(C.FILE_CREATION_ROOT) else set()


# P1 SSRF: links are not fetched unless MAIN_AED_ALLOW_REMOTE_LISTS
def test_link_list_rejected_without_flag():
    resource = ResourceFactory.create(contains_aed_list=True, status="published", link="https://example.org/aed.csv")
    with patch("mcod.aed.aed_utils.requests.get") as get:
        data, error = read_resource_bytes(resource)
    assert data is None and "nie pobiera wykazów z linków" in error
    get.assert_not_called()


def test_link_list_with_flag_does_not_follow_redirects():
    resource = ResourceFactory.create(contains_aed_list=True, status="published", link="https://example.org/aed.csv")
    response = MagicMock(status_code=302)
    response.__enter__.return_value = response
    with patch("mcod.aed.constants.ALLOW_REMOTE_LISTS", True), patch(
        "mcod.aed.aed_utils.requests.get", return_value=response
    ) as get, patch.object(Resource, "main_file", None), patch.object(Resource, "csv_converted_file", None):
        data, error = read_resource_bytes(resource)
    assert data is None and "302" in error
    assert get.call_args.kwargs["allow_redirects"] is False and get.call_args.kwargs["stream"] is True


# P1 foreign dataset: an editor marks an AED list only in their own institution
def test_editor_cannot_mark_aed_list_in_other_institution():
    own, other = OrganizationFactory.create(), OrganizationFactory.create()
    editor = UserFactory.create(is_staff=True, is_superuser=False, state="active")
    editor.organizations.set([own])
    for dataset, allowed in ((DatasetFactory.create(organization=other), False), (DatasetFactory.create(organization=own), True)):
        form = ChangeResourceForm(instance=ResourceFactory.create(dataset=dataset))
        form.aed_user = editor
        form.cleaned_data = {"contains_aed_list": True, "file": SimpleUploadedFile("w.csv", GOOD_LIST)}
        form._errors = {}
        form._validate_aed_list_file(form.cleaned_data, dataset)
        errors = form.errors.get("contains_aed_list", [])
        assert (errors == []) is allowed, errors
        assert allowed or "swojej instytucji" in errors[0]


# P1 limits: one list over the limit is rejected, the others still merge
def test_list_over_size_limit_rejected_others_merge():
    big = ResourceFactory.create(contains_aed_list=True, status="published", format="csv")
    good = ResourceFactory.create(contains_aed_list=True, status="published", format="csv")
    sizes = {big.pk: C.MAX_LIST_BYTES + 1, good.pk: len(GOOD_LIST)}

    def fake_file(resource):
        f = MagicMock(size=sizes[resource.pk])
        f.open.return_value.__enter__.return_value.read.return_value = GOOD_LIST
        return f

    with patch.object(Resource, "main_file", property(fake_file)), patch.object(Resource, "csv_converted_file", None), \
            patch("mcod.aed.aed_utils.is_remote_link", return_value=False):
        _, report = build_main_aed_list(get_all_aed_list_resources())
    statuses = {w["zasob"]: w["status"] for w in report["wykazy"]}
    assert statuses == {big.pk: "odrzucony", good.pk: "przyjety"}
    assert report["rekordy_w_wykazie_krajowym"] == 1


def test_list_over_row_limit_rejected():
    resource = ResourceFactory.create(contains_aed_list=True, status="published", format="csv")
    f = MagicMock(size=10)
    f.open.return_value.__enter__.return_value.read.return_value = GOOD_LIST
    with patch("mcod.aed.constants.MAX_LIST_ROWS", 1), patch.object(Resource, "main_file", f), \
            patch("mcod.aed.aed_utils.is_remote_link", return_value=False):
        data, error = read_resource_bytes(resource)
    assert data is None and "więcej niż 1 wierszy" in error


# P1 overlapping runs: a second run while the lock is held creates and deletes nothing
def test_second_run_with_lock_held_does_nothing():
    owner = OrganizationFactory.create()
    current = ResourceFactory.create(status="published")
    AggregatedAEDInfo.objects.create(resource=current)
    assert acquire_run_lock("first-run")
    before_resources, before_files = Resource.raw.count(), _files_in_work_dir()
    try:
        with patch("mcod.aed.constants.OWNER_ORGANIZATION_PK", owner.pk), \
                patch("mcod.aed.aed_utils.build_main_aed_list") as build:
            result = create_main_aed_resource_task.apply().get()
        assert result == "locked"
        build.assert_not_called()
        assert Resource.raw.count() == before_resources and _files_in_work_dir() == before_files
        assert AggregatedAEDInfo.objects.get().resource == current
        assert caches["default"].get(C.LOCK_KEY) == "first-run"  # the other run's lock is untouched
    finally:
        release_run_lock("first-run")


# P2 owner: checked before any list is read
def test_missing_owner_creates_nothing():
    ResourceFactory.create(contains_aed_list=True, status="published")
    before_resources, before_files = Resource.raw.count(), _files_in_work_dir()
    with patch("mcod.aed.constants.OWNER_ORGANIZATION_PK", None), \
            patch("mcod.aed.aed_utils.read_resource_bytes") as read:
        with pytest.raises(ImproperlyConfigured):
            create_main_aed_resource_task.apply().get()
    read.assert_not_called()
    assert Resource.raw.count() == before_resources and _files_in_work_dir() == before_files
    assert caches["default"].get(C.LOCK_KEY) is None


# P2 public report: no raw values, URLs or internal keys
def test_public_report_has_no_raw_values():
    report = {
        "wykazy_razem": 1,
        "wykazy": [{
            "zasob": 7, "tytul": "Wykaz", "instytucja": "Gmina", "zrodlo": "dane.gov.pl/1", "status": "czesciowo",
            "wiersze": 2, "przyjete": 1, "problemy_razem": 2, "powiadomienie_oczekuje": True,
            "problemy": [
                {"wiersz": 2, "pole": "dysponent_email", "poziom": "blad", "kod": "format_email",
                 "komunikat": "Otrzymano: „jan.kowalski@prywatny.pl”."},
                {"wiersz": None, "pole": "token=abc", "poziom": "blad", "kod": "odczyt",
                 "komunikat": "Adres zasobu https://x.example/a.csv?token=abc nie odpowiada."},
            ],
        }],
    }
    public = public_report(report)
    text = str(public)
    assert "jan.kowalski" not in text and "token" not in text and "https://" not in text
    assert "powiadomienie_oczekuje" not in text
    assert public["wykazy"][0]["problemy"][0] == {
        "wiersz": 2, "pole": "dysponent_email", "poziom": "blad", "kod": "format_email",
        "opis": C.PROBLEM_DESCRIPTIONS["format_email"],
    }
    assert public["wykazy"][0]["problemy"][1]["pole"] is None


# P2 empty result after unreadable sources keeps the last list
def test_empty_result_with_unreadable_lists_keeps_last_list():
    current = ResourceFactory.create(status="published")
    AggregatedAEDInfo.objects.create(resource=current, report={"rekordy_w_wykazie_krajowym": 781})
    assert keep_last_list_after_failed_sources({"rekordy_w_wykazie_krajowym": 0, "wykazy_nieodczytane": 2})
    info = AggregatedAEDInfo.objects.get()
    assert info.resource == current and info.report["rekordy_w_wykazie_krajowym"] == 781
    assert info.report["ostatnie_nieudane_scalanie"]["wykazy_nieodczytane"] == 2
    assert not keep_last_list_after_failed_sources({"rekordy_w_wykazie_krajowym": 0, "wykazy_nieodczytane": 0})


def test_only_transient_read_errors_count_as_unreadable():
    """A network or I/O failure keeps the last list; a link switched off or a list over a limit does not."""
    transient = ResourceFactory.create(contains_aed_list=True, status="published")
    by_rule = ResourceFactory.create(contains_aed_list=True, status="published")
    answers = {transient.pk: (None, TransientError("Adres zasobu nie odpowiada.")), by_rule.pk: (None, REMOTE_DISABLED)}
    with patch("mcod.aed.aed_utils.read_resource_bytes", side_effect=lambda r: answers[r.pk]):
        _, report = build_main_aed_list(get_all_aed_list_resources())
    assert report["wykazy_nieodczytane"] == 1 and report["rekordy_w_wykazie_krajowym"] == 0

    answers.pop(transient.pk)
    transient.delete()
    with patch("mcod.aed.aed_utils.read_resource_bytes", side_effect=lambda r: answers[r.pk]):
        _, report = build_main_aed_list(get_all_aed_list_resources())
    assert report["wykazy_nieodczytane"] == 0
    assert not keep_last_list_after_failed_sources(report)  # only rejected by rule: the empty list is published


def test_network_error_is_transient_disabled_link_is_not():
    resource = ResourceFactory.create(contains_aed_list=True, status="published", link="https://example.org/aed.csv")
    _, error = read_resource_bytes(resource)
    assert not isinstance(error, TransientError)
    with patch("mcod.aed.constants.ALLOW_REMOTE_LISTS", True), patch.object(Resource, "main_file", None), \
            patch.object(Resource, "csv_converted_file", None), \
            patch("mcod.aed.aed_utils.requests.get", side_effect=requests.exceptions.ConnectionError):
        _, error = read_resource_bytes(resource)
    assert isinstance(error, TransientError)


# P2 clean up never deletes the resource the national list points at
def test_clean_up_keeps_published_candidate():
    published = ResourceFactory.create(status="published")
    AggregatedAEDInfo.objects.create(resource=published)
    caches["default"].set(key_generator_for_create_main_aed_resource("run-x"), (published.pk, None), 60)
    clean_up_after_main_aed_resource_creation(exception_occurred=True, run_id="run-x")
    assert Resource.objects.filter(pk=published.pk).exists()
    assert caches["default"].get(key_generator_for_create_main_aed_resource("run-x")) is None


# P2 attribution: accepted lists with institution, dataset, resource, link and licence
def test_report_lists_used_resources_for_attribution():
    good = ResourceFactory.create(contains_aed_list=True, status="published")
    with patch("mcod.aed.aed_utils.read_resource_bytes", return_value=(GOOD_LIST, None)):
        _, report = build_main_aed_list(get_all_aed_list_resources())
    used = public_report(report)["wykorzystane_zasoby"]
    assert used == [{
        "instytucja": good.dataset.organization.title, "zbior": good.dataset.title, "zasob": good.title,
        "zasob_id": good.pk, "link": good.frontend_absolute_url, "licencja": good.dataset.license_name,
    }]
