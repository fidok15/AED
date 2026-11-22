import pytest
from django.conf import settings

from mcod.aed.models import AggregatedAEDInfo
from mcod.resources.factories import ResourceFactory

pytestmark = [pytest.mark.depends_on_component, pytest.mark.component_api]


def test_aed_aggregated_view_is_public(client14):
    resource = ResourceFactory.create(status="published")
    AggregatedAEDInfo.objects.create(resource=resource, report={"wykazy_przyjete": 1})
    response = client14.simulate_get("/aed-aggregated")
    assert response.status_code == 200, response.text
    assert response.json["resource_id"] == resource.pk, response.json
    assert response.json["dataset_id"] == resource.dataset.pk
    report = response.json["report"]
    assert report.pop("stale_adresy") == {
        "resource": settings.API_URL + "/aed-aggregated/resource", "file": settings.API_URL + "/aed-aggregated/file"}
    assert report == {"wykazy_przyjete": 1, "wykazy": []}  # public_report, not the raw JSON


def test_aed_aggregated_view_404_without_list(client14):
    assert client14.simulate_get("/aed-aggregated").status_code == 404


def test_aed_aggregated_view_404_when_dataset_not_published(client14):
    resource = ResourceFactory.create(status="published")
    AggregatedAEDInfo.objects.create(resource=resource, report={})
    resource.dataset.status = "draft"
    resource.dataset.save()
    assert client14.simulate_get("/aed-aggregated").status_code == 404


def test_aed_aggregated_permanent_addresses_follow_the_current_resource(client14):
    """Each merge creates a new resource; the permanent addresses keep pointing at the current one."""
    first, second = ResourceFactory.create(status="published"), ResourceFactory.create(status="published")
    info = AggregatedAEDInfo.objects.create(resource=first, report={})
    for current in (first, second):
        info.resource = current
        info.save()
        response = client14.simulate_get("/aed-aggregated/resource")
        assert response.status_code == 302, response.text
        assert response.headers["location"] == "%s/resources/%s" % (settings.API_URL, current.pk)
        response = client14.simulate_get("/aed-aggregated/file")
        assert response.status_code == 302
        assert response.headers["location"] == "%s/resources/%s/file" % (settings.API_URL, current.pk)
    second.dataset.status = "draft"
    second.dataset.save()
    assert client14.simulate_get("/aed-aggregated/file").status_code == 404
