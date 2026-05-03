import time
from django.core.management.base import BaseCommand
from django.utils import timezone

from investments.models import Investment


class Command(BaseCommand):
    help = "Crédite automatiquement les investissements arrivés à terme (wallet + ledger) et clôture."

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true", help="Boucle infinie (toutes les 30s).")
        parser.add_argument("--interval", type=int, default=30, help="Intervalle en secondes (avec --loop).")

    def handle(self, *args, **options):
        loop = options["loop"]
        interval = options["interval"]

        def run_once():
            now = timezone.now()
            qs = Investment.objects.filter(status=Investment.STATUS_ACTIVE)
            count_checked = 0
            count_credited = 0

            for inv in qs.iterator():
                count_checked += 1
                try:
                    if inv.try_auto_credit():
                        count_credited += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"[ERROR] inv#{inv.id}: {e}"))

            self.stdout.write(self.style.SUCCESS(
                f"[{now}] Checked={count_checked} Credited={count_credited}"
            ))

        if loop:
            self.stdout.write(self.style.WARNING("Mode LOOP activé. CTRL+C pour arrêter."))
            while True:
                run_once()
                time.sleep(max(5, interval))
        else:
            run_once()