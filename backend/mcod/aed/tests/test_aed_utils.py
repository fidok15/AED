"""Modelled on mcod/resources/tests/test_main_dga.py. Needs the portal test stack (Postgres, Docker)."""
from unittest.mock import patch

import pytest

from mcod.aed import constants as C
from mcod.aed.aed_utils import (
    build_main_aed_list,
    create_main_aed_resource_with_dataset,
    get_all_aed_list_resources,
    main_aed_tabular_schema,
    update_or_create_aggr_aed_info_and_delete_old_main_aed,
)
from mcod.aed.models import AggregatedAEDInfo
from mcod.organizations.factories import OrganizationFactory
from mcod.resources.factories import ResourceFactory
from mcod.resources.models import Resource

GOOD_LIST = (
    "nazwa,miejscowosc,szerokosc_geograficzna,dlugosc_geograficzna,dostep\n"
    "Urząd Miasta Legionowo,Legionowo,52.395198,20.931382,publiczny\n"
    "Starostwo Powiatowe,Legionowo,52.421807,20.939056,publiczny\n"
).encode("utf-8")
BAD_LIST = "Nazwa;Adres\nUrząd;ul. Jasna\n".encode("utf-8")


@pytest.fixture
def aed_owner():
    return OrganizationFactory.create(pk=C.OWNER_ORGANIZATION_PK)


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
