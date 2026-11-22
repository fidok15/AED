"""Modelled on mcod/resources/tests/test_main_dga.py. Needs the portal test stack (Postgres, Docker)."""
import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from mcod.aed import constants as C
from mcod.aed.aed_utils import (
    build_main_aed_list,
    clean_up_after_main_aed_resource_creation,
    create_main_aed_file,
    create_main_aed_resource_with_dataset,
    get_all_aed_list_resources,
    main_aed_tabular_schema,
    update_or_create_aggr_aed_info_and_delete_old_main_aed,
    validate_aed_list_file,
)
from mcod.aed.models import AggregatedAEDInfo
from mcod.core.tests.helpers.tasks import run_on_commit_events
from mcod.datasets.factories import DatasetFactory
from mcod.datasets.models import Dataset
from mcod.organizations.factories import OrganizationFactory
from mcod.resources.dga_utils import check_all_resource_validations_status
from mcod.resources.factories import ResourceFactory
from mcod.resources.forms import ChangeResourceForm
from mcod.resources.models import Resource, ResourceFile

GOOD_LIST = (
    "nazwa,miejscowosc,szerokosc_geograficzna,dlugosc_geograficzna,dostep\n"
    "Urząd Miasta Legionowo,Legionowo,52.395198,20.931382,publiczny\n"
    "Starostwo Powiatowe,Legionowo,52.421807,20.939056,publiczny\n"
).encode("utf-8")
BAD_LIST = "Nazwa;Adres\nUrząd;ul. Jasna\n".encode("utf-8")


@pytest.fixture
def aed_owner():
    owner = OrganizationFactory.create()
    with patch("mcod.aed.constants.OWNER_ORGANIZATION_PK", owner.pk):
        yield owner


def test_build_main_aed_list_skips_bad_and_unreadable_lists():
    good = ResourceFactory.create(contains_aed_list=True, status="published")
    bad = ResourceFactory.create(contains_aed_list=True, status="published")
    gone = ResourceFactory.create(contains_aed_list=True, status="published")
    ResourceFactory.create(contains_aed_list=False, status="published")
    answers = {good.pk: (GOOD_LIST, None), bad.pk: (BAD_LIST, None), gone.pk: (None, "Adres zasobu nie odpowiada.")}

    with patch("mcod.aed.aed_utils.read_resource_bytes", side_effect=lambda r: answers[r.pk]):
        content, report = build_main_aed_list(get_all_aed_list_resources())

    statuses = {w["zasob"]: w["status"] for w in report["wykazy"]}
    assert statuses == {good.pk: "przyjety", bad.pk: "odrzucony", gone.pk: "odrzucony"}
    assert report["rekordy_w_wykazie_krajowym"] == 2
    assert content.splitlines()[0].startswith("id_aed,nazwa,szerokosc_geograficzna,dlugosc_geograficzna")


def test_identical_list_of_the_same_institution_is_not_merged_twice():
    """Real Legionowo file (BOM, LF) published twice by Legionowo, the copy without BOM and with CRLF: counted once,
    the copy is "powtorzony".
    The same file from another institution and a list that only overlaps are merged as before."""
    legionowo = (Path(__file__).parent / "data" / "legionowo_resource_2625221.csv").read_bytes()
    assert legionowo.startswith(b"\xef\xbb\xbf") and b"\r" not in legionowo
    copy = legionowo[3:].replace(b"\n", b"\r\n")
    partial = legionowo.rsplit(b"\n", 2)[0] + b"\n"  # without the last row
    dataset = DatasetFactory.create(organization=OrganizationFactory.create())
    first, second, overlap = (ResourceFactory.create(contains_aed_list=True, status="published", dataset=dataset)
                              for _ in range(3))
    other = ResourceFactory.create(contains_aed_list=True, status="published")
    answers = {first.pk: legionowo, second.pk: copy, overlap.pk: partial, other.pk: legionowo}

    with patch("mcod.aed.aed_utils.read_resource_bytes", side_effect=lambda r: (answers[r.pk], None)):
        _, report = build_main_aed_list(get_all_aed_list_resources())
        _, alone = build_main_aed_list([first])

    entries = {w["zasob"]: w for w in report["wykazy"]}
    assert entries[second.pk]["status"] == "powtorzony" and entries[second.pk]["powtorzenie_zasobu"] == first.pk
    assert entries[first.pk]["status"] == entries[overlap.pk]["status"] == entries[other.pk]["status"] == "przyjety"
    assert report["wykazy_powtorzone"] == 1 and report["wykazy_razem"] == 4
    rows = alone["rekordy_z_wykazow"]
    assert rows == 24 and report["rekordy_z_wykazow"] == rows + (rows - 1) + rows
    assert second.pk not in {u["zasob_id"] for u in report["wykorzystane_zasoby"]}


def test_create_main_aed_resource_with_dataset(aed_owner, tmp_path):
    path = tmp_path / "wykaz.csv"
    path.write_bytes(GOOD_LIST)
    resource_pk, dataset_pk = create_main_aed_resource_with_dataset(str(path))

    resource = Resource.objects.get(pk=resource_pk)
    assert dataset_pk == resource.dataset.pk
    assert resource.dataset.organization == aed_owner
    assert resource.title == C.RESOURCE_TITLE
    assert resource.contains_aed_list is False
    assert resource.tabular_data_schema["geo"]["b"]["col_name"] == "szerokosc_geograficzna"
    assert resource.status == "published"


def test_main_aed_tabular_schema_has_map_markers():
    tds = main_aed_tabular_schema()
    names = [f["name"] for f in tds["fields"]]
    assert tds["geo"]["b"] == {"col_name": "szerokosc_geograficzna", "col_index": names.index("szerokosc_geograficzna")}
    assert tds["geo"]["l"]["col_name"] == "dlugosc_geograficzna"
    assert tds["geo"]["label"]["col_name"] == "nazwa"
    assert {f["type"] for f in tds["fields"] if f.get("geo") in ("b", "l")} == {"number"}


def test_update_aggr_aed_info_replaces_old_resource():
    old = ResourceFactory.create(status="published")
    AggregatedAEDInfo.objects.create(resource=old)
    new = ResourceFactory.create(status="published")
    update_or_create_aggr_aed_info_and_delete_old_main_aed(new, {"wykazy": []})

    info = AggregatedAEDInfo.objects.get()
    assert info.resource == new and info.report == {"wykazy": []}
    assert not Resource.objects.filter(pk=old.pk).exists()


DATA_DIR = Path(__file__).parent / "data"  # copies of real dane.gov.pl files from datasets/raw/dane_gov_pl/


def _aed_list_resource(file_name: str) -> Resource:
    resource = Resource.objects.create(
        title=file_name, description="Wykaz AED z prawdziwego pliku.", dataset=DatasetFactory.create(), format="csv",
        status="published", data_date=datetime.date.today(), contains_aed_list=True,
    )
    content = (DATA_DIR / file_name).read_bytes()
    ResourceFile.objects.create(resource=resource, is_main=True, file=SimpleUploadedFile(file_name, content))
    return resource


@pytest.mark.elasticsearch
def test_main_aed_resource_end_to_end_with_portal_validation(aed_owner):
    """The task's steps on real files, with the portal's own file and tabular data validation (eager Celery)."""
    legionowo = _aed_list_resource("legionowo_resource_2625221.csv")
    krosno = _aed_list_resource("krosno_resource_54632.csv")
    run_on_commit_events()

    file_path, report = create_main_aed_file()
    resource_pk, _ = create_main_aed_resource_with_dataset(file_path)
    run_on_commit_events()  # the portal processes the new file here
    resource = Resource.objects.get(pk=resource_pk)
    check_all_resource_validations_status(resource)  # raises if the portal rejected the file
    update_or_create_aggr_aed_info_and_delete_old_main_aed(resource, report)
    clean_up_after_main_aed_resource_creation(exception_occurred=False)

    statuses = {w["zasob"]: w["status"] for w in report["wykazy"]}
    assert statuses == {legionowo.pk: "przyjety", krosno.pk: "odrzucony"}
    resource.refresh_from_db()
    assert resource.format == "csv"
    assert resource.tabular_data_schema["geo"]["b"]["col_name"] == "szerokosc_geograficzna"
    assert {f["name"]: f["type"] for f in resource.tabular_data_schema["fields"]}["dlugosc_geograficzna"] == "number"
    assert AggregatedAEDInfo.objects.get().main_aed_resource == resource


def test_admin_form_rejects_bad_aed_list_with_polish_messages():
    resource = ResourceFactory.create()
    dataset = resource.dataset
    form = ChangeResourceForm(instance=resource)
    form.aed_user = None
    krosno = SimpleUploadedFile("krosno.csv", (DATA_DIR / "krosno_resource_54632.csv").read_bytes())
    form.cleaned_data = {"contains_aed_list": True, "file": krosno}
    form._errors = {}
    form._validate_aed_list_file(form.cleaned_data, dataset)
    messages = form.errors["contains_aed_list"]
    assert any("nie występuje w standardzie" in m for m in messages), messages


def test_form_messages_point_to_the_converter():
    resource = ResourceFactory.create(status="published")
    with patch("mcod.aed.constants.LIST_HELP_URL", "https://example.org/pl/aed/!konwerter"):
        messages = validate_aed_list_file(BAD_LIST, resource, resource.dataset)
    assert messages[-1] == "Plik można przekształcić do standardu AED w konwerterze: https://example.org/pl/aed/!konwerter"


def test_repeated_list_keeps_the_accepted_copy_not_the_lower_id():
    """Same file in two datasets of one institution: the lower-id copy is in a CC BY-NC dataset (rejected by licence),
    so the CC0 copy is kept and the rejected one is the repeat. With no accepted copy nothing is "powtorzony"."""
    legionowo = (Path(__file__).parent / "data" / "legionowo_resource_2625221.csv").read_bytes()
    organization = OrganizationFactory.create()
    nc = DatasetFactory.create(organization=organization, license_chosen=Dataset.LICENSE_CC_BY_NC,
                               license_condition_source=False, license_condition_modification=False)
    cc0 = DatasetFactory.create(organization=organization, license_chosen=None, license_condition_source=False,
                                license_condition_modification=False, license_condition_responsibilities=False,
                                license_condition_cc40_responsibilities=False, license_condition_default_cc40=False,
                                license_condition_custom_description=None)
    rejected = ResourceFactory.create(contains_aed_list=True, status="published", dataset=nc)
    accepted = ResourceFactory.create(contains_aed_list=True, status="published", dataset=cc0)
    assert rejected.pk < accepted.pk and nc.license_name == "CC BY-NC 4.0" and cc0.license_name == "CC0 1.0"

    with patch("mcod.aed.aed_utils.read_resource_bytes", return_value=(legionowo, None)):
        _, report = build_main_aed_list([rejected, accepted])
        _, only_rejected = build_main_aed_list([rejected, ResourceFactory.create(dataset=nc)])

    statuses = {w["zasob"]: (w["status"], w.get("powtorzenie_zasobu")) for w in report["wykazy"]}
    assert statuses == {accepted.pk: ("przyjety", None), rejected.pk: ("powtorzony", accepted.pk)}
    assert report["rekordy_w_wykazie_krajowym"] == 24
    assert {w["status"] for w in only_rejected["wykazy"]} == {"odrzucony"} and only_rejected["wykazy_powtorzone"] == 0
