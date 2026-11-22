import json

from django.core.management.base import BaseCommand

from mcod.aed.aed_utils import build_main_aed_list, get_all_aed_list_resources
from mcod.aed.tasks import create_main_aed_resource_task


class Command(BaseCommand):
    help = "Scala wszystkie wykazy AED w Krajowy wykaz AED (to samo zadanie, które Celery uruchamia codziennie)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Tylko odczyt: pokaż raport i początek pliku, nic nie zapisuj."
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            content, report = build_main_aed_list(get_all_aed_list_resources())
            self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
            self.stdout.write("\n".join(content.splitlines()[:5]))
            return
        result = create_main_aed_resource_task.delay()
        self.stdout.write("Zlecono zadanie %s (kolejka resources). Wynik: GET /aed-aggregated" % result.id)
