from typing import Optional

from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import models

from mcod.datasets.models import Dataset
from mcod.resources.models import Resource


class AggregatedAEDInfo(models.Model):
    """Pointer to the current national AED list resource (one row), as AggregatedDGAInfo for the DGA list."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resource = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True)
    # Public report of the last merge: which lists were accepted or rejected and why (aed_standard.wykaz).
    report = JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Krajowy wykaz AED"
        verbose_name_plural = "Krajowy wykaz AED"

    def save(self, *args, **kwargs):
        if not self.id and AggregatedAEDInfo.objects.exists():
            raise ValidationError("There can be only one AggregatedAEDInfo instance")
        return super().save(*args, **kwargs)

    @property
    def main_aed_resource(self) -> Optional[Resource]:
        if self.resource and self.resource.is_published and not self.resource.is_removed:
            return self.resource
        return None

    @property
    def main_aed_dataset(self) -> Optional[Dataset]:
        if self.resource and self.resource.dataset.is_published and not self.resource.dataset.is_removed:
            return self.resource.dataset
        return None
