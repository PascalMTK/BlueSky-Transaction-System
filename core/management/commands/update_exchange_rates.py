import time

from django.core.management.base import BaseCommand

from core.exchange_rates import fetch_and_update_rates


class Command(BaseCommand):
    help = (
        "Refresh each country's USD exchange rate from a free exchange-rate API. "
        "Runs once by default (for a daily Scheduled Task); pass --interval to loop "
        "forever instead (for an Always-on Task, e.g. --interval 3600 for hourly)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval', type=int, default=0,
            help='If set, keep running and refresh every N seconds instead of exiting after one run.',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        if not interval:
            self._run_once()
            return

        self.stdout.write(f'Actualisation toutes les {interval}s (Ctrl+C pour arrêter)...')
        while True:
            self._run_once()
            time.sleep(interval)

    def _run_once(self):
        updated, skipped, error = fetch_and_update_rates()
        if error:
            self.stderr.write(self.style.ERROR(error))
            return
        self.stdout.write(self.style.SUCCESS(f'{updated} pays mis à jour.'))
        if skipped:
            self.stdout.write(self.style.WARNING(
                f"Devises non trouvées dans l'API (taux inchangé) : {', '.join(skipped)}"
            ))
