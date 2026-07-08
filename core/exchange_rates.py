import json
import urllib.request

from core.models import Country

RATES_URL = 'https://open.er-api.com/v6/latest/USD'


def fetch_and_update_rates(timeout=10):
    """Fetch USD exchange rates from a free, keyless API and update each
    Country's usd_exchange_rate to match (rates are already expressed as
    "units of local currency per 1 USD", the same convention used here).
    Returns (updated_count, skipped_codes, error) — error is None on success."""
    try:
        with urllib.request.urlopen(RATES_URL, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return 0, [], f'Impossible de contacter le service de taux de change : {e}'

    rates = data.get('rates') or {}
    if not rates:
        return 0, [], 'Réponse invalide du service de taux de change.'

    updated = 0
    skipped = []
    for country in Country.objects.all():
        rate = rates.get(country.currency_code.upper())
        if rate is None:
            skipped.append(country.currency_code)
            continue
        country.usd_exchange_rate = rate
        country.save(update_fields=['usd_exchange_rate'])
        updated += 1

    return updated, skipped, None
