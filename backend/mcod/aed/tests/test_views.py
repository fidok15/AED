import pytest

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
    assert response.json["report"] == {"wykazy_przyjete": 1}


def test_aed_aggregated_view_404_without_list(client14):
    assert client14.simulate_get("/aed-aggregated").status_code == 404
