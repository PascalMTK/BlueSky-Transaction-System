import json
import time
import urllib.request
import urllib.parse

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
# Nominatim's usage policy requires an identifying User-Agent and caps
# requests at ~1/sec — this module is only ever called for a single address
# at a time (create/edit/retry), never in a bulk import loop.
USER_AGENT = 'BLUESKY-Logistics/1.0 (internal dispatch tool)'


def geocode_address(address_line, city='', country_name='', timeout=8):
    """Resolve a free-text address to (lat, lon) via OpenStreetMap's free
    Nominatim search API. Returns (lat, lon, None) on success or
    (None, None, error_message) on failure. Best-effort only — free-text
    geocoding is not always accurate; a manual latitude/longitude override
    is always available as a fallback."""
    query = ', '.join(part for part in [address_line, city, country_name] if part)
    if not query.strip():
        return None, None, 'Adresse vide.'

    params = urllib.parse.urlencode({'q': query, 'format': 'json', 'limit': 1})
    url = f'{NOMINATIM_URL}?{params}'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})

    time.sleep(1)  # unconditional throttle — respects Nominatim's rate limit

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return None, None, f'Impossible de contacter le service de géocodage : {e}'

    if not data:
        return None, None, "Aucune correspondance trouvée pour cette adresse."

    try:
        lat = float(data[0]['lat'])
        lon = float(data[0]['lon'])
    except (KeyError, ValueError, TypeError):
        return None, None, 'Réponse invalide du service de géocodage.'

    return lat, lon, None
