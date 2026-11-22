import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("resources", "0076_resource_contains_aed_list"),
    ]

    operations = [
        migrations.CreateModel(
            name="AggregatedAEDInfo",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("report", django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                (
                    "resource",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="resources.Resource"),
                ),
            ],
            options={
                "verbose_name": "Krajowy wykaz AED",
                "verbose_name_plural": "Krajowy wykaz AED",
            },
        ),
    ]
