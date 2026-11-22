import falcon
from django.apps import apps
from django.conf import settings

from mcod.aed.aed_utils import public_report
from mcod.core.api import fields
from mcod.core.api.handlers import BaseHdlr
from mcod.core.api.hooks import login_optional
from mcod.core.api.schemas import ExtSchema
from mcod.core.api.views import JsonAPIView
from mcod.core.versioning import versioned


class AggregatedAEDInfoApiResponse(ExtSchema):
    dataset_id = fields.Int(attribute="resource.dataset.id", data_key="dataset_id")
    dataset_slug = fields.Str(attribute="resource.dataset.slug", data_key="dataset_slug")
    resource_id = fields.Int(attribute="resource.id", data_key="resource_id")
    resource_slug = fields.Str(attribute="resource.slug", data_key="resource_slug")
    updated_at = fields.DateTime(data_key="updated_at")
    report = fields.Method("get_public_report", data_key="report")

    def get_public_report(self, obj):
        # Permanent addresses that keep working after the next merge (AggregatedAEDRedirectView).
        permanent = {name: settings.API_URL + "/aed-aggregated/" + name for name in AggregatedAEDRedirectView.PATHS}
        return dict(public_report(obj.report), stale_adresy=permanent)


class AggregatedAEDInfoView(JsonAPIView):
    """Public, no login: where the national AED list is and which provider lists went into it (and why not)."""

    @falcon.before(login_optional)
    @versioned
    def on_get(self, request, response, *args, **kwargs):
        self.handle(request, response, self.GET, *args, **kwargs)

    class GET(BaseHdlr):
        database_model = apps.get_model("aed", "AggregatedAEDInfo")
        serializer_schema = AggregatedAEDInfoApiResponse

        def _get_data(self, cleaned, *args, **kwargs):
            data = self.database_model.objects.select_related("resource", "resource__dataset").first()
            if not data or data.main_aed_resource is None or data.main_aed_dataset is None:
                raise falcon.HTTPNotFound
            return data

        def serialize(self, *args, **kwargs):
            self.prepare_context(*args, **kwargs)
            return self.serializer.dump(self.response.context.data)


class AggregatedAEDRedirectView:
    """Permanent public address of the national AED list: every merge creates a new resource (as DGA), so external
    links point here and get a 302 to the current resource (`resource`) or its file (`file`, through the portal's
    own /resources/<id>/file, which counts the download). The DGA frontend does the same at runtime via
    /dga-aggregated."""

    PATHS = {"resource": "/resources/%s", "file": "/resources/%s/file"}

    def __init__(self, target: str):
        self.path = self.PATHS[target]

    def on_get(self, request, response):
        info = apps.get_model("aed", "AggregatedAEDInfo").objects.select_related("resource__dataset").first()
        if not info or info.main_aed_resource is None or info.main_aed_dataset is None:
            raise falcon.HTTPNotFound
        response.status = falcon.HTTP_302
        response.location = settings.API_URL + self.path % info.resource_id
        response.cache_control = ["no-cache"]  # the target changes with every merge

    on_head = on_get
