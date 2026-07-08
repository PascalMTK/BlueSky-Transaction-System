from django.core.management.base import BaseCommand

from core.exchange_rates import fetch_and_update_rates


class Command(BaseCommand):
    help = "Refresh each country's USD exchange rate from a free exchange-rate API."

    def handle(self, *args, **options):
        updated, skipped, error = fetch_and_update_rates()
        if error:
            self.stderr.write(self.style.ERROR(error))
            return
        self.stdout.write(self.style.SUCCESS(f'{updated} pays mis à jour.'))
        if skipped:
            self.stdout.write(self.style.WARNING(
                f"Devises non trouvées dans l'API (taux inchangé) : {', '.join(skipped)}"
            ))
