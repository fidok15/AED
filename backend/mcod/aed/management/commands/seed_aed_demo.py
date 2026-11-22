"""Local demo only: institutions, datasets and three AED list resources from real files (docs/wykaz-aed-w-portalu.md)."""
import datetime
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from mcod.aed import constants as C
from mcod.datasets.models import Dataset
from mcod.organizations.models import Organization
from mcod.resources.models import Resource, ResourceFile

LISTS = [
    # (institution pk, institution, type, dataset, file under --data-dir)
    (C.OWNER_ORGANIZATION_PK, "Ministerstwo Cyfryzacji", "state", "Rejestr zgłoszeń AED", "out/aed_dane_gov_pl.csv"),
    (90001, "Gmina Miejska Legionowo", "local", "Defibrylatory AED w Legionowie",
     "raw/dane_gov_pl/legionowo/resource_2625221.csv"),
    (90002, "Gmina Krosno", "local", "Defibrylatory AED w Krośnie", "raw/dane_gov_pl/krosno/resource_54632.csv"),
]


class Command(BaseCommand):
    help = "Demo lokalne: instytucje, zbiory i trzy wykazy AED z prawdziwych plików (idempotentne)."

    def add_arguments(self, parser):
        parser.add_argument("--data-dir", default="/usr/src/mcod_backend/aed_datasets")

    def handle(self, *args, **options):
        for org_pk, org_title, org_type, ds_title, rel_path in LISTS:
            org, _ = Organization.objects.get_or_create(
                pk=org_pk,
                defaults=dict(
                    title=org_title, slug="aed-demo-%s" % org_pk, institution_type=org_type, status="published",
                    postal_code="00-001", city="Warszawa", street="Królewska", street_number="27",
                    email="kontakt@example.gov.pl", tel="221234567", regon="123456785", website="https://example.gov.pl",
                ),
            )
            dataset, _ = Dataset.objects.get_or_create(
                title=ds_title, organization=org,
                defaults=dict(
                    notes="Wykaz defibrylatorów AED (demo lokalne).", status="published", update_frequency="daily",
                    has_dynamic_data=False, has_high_value_data=False, has_high_value_data_from_ec_list=False,
                    has_research_data=False, update_notification_recipient_email="admin@mcod.local",
                ),
            )
            if dataset.resources.filter(contains_aed_list=True).exists():
                continue
            with open(os.path.join(options["data_dir"], rel_path), "rb") as f:
                upload = SimpleUploadedFile(os.path.basename(rel_path), f.read(), content_type="text/csv")
            resource = Resource.objects.create(
                title="Wykaz AED – %s" % org_title, description="Wykaz AED w strukturze standardu AED (demo).",
                dataset=dataset, format="csv", status="published", data_date=datetime.date.today(),
                has_dynamic_data=False, has_high_value_data=False, has_high_value_data_from_ec_list=False,
                has_research_data=False, contains_protected_data=False, contains_aed_list=True,
            )
            ResourceFile.objects.create(resource=resource, is_main=True, file=upload)
            self.stdout.write("%s: zbiór %s, zasób %s (%s)" % (org_title, dataset.pk, resource.pk, rel_path))
