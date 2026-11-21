import falcon
from django.apps import apps

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
    report = fields.Raw(data_key="report")


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
            if not data or data.resource is None or data.resource.is_removed or not data.resource.is_published:
                raise falcon.HTTPNotFound
            return data

        def serialize(self, *args, **kwargs):
            self.prepare_context(*args, **kwargs)
            return self.serializer.dump(self.response.context.data)
