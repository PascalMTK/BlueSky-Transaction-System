from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Country names are stored in French (the canonical/editable value in Admin →
# Pays). This maps them to English for display on agent/client-facing pages
# when the interface locale is 'en' — the stored name itself is untouched.
COUNTRY_NAME_EN = {
    'Congo (RDC)':         'DR Congo',
    'Zambie':              'Zambia',
    'Tanzanie':            'Tanzania',
    'Malawi':              'Malawi',
    'Kenya':               'Kenya',
    'Zimbabwe':            'Zimbabwe',
    'Afrique du Sud':      'South Africa',
    'Namibie':             'Namibia',
    'Congo (Brazzaville)': 'Congo (Brazzaville)',
    'Angola':              'Angola',
    'Rwanda':              'Rwanda',
    'Burundi':             'Burundi',
    'Uganda':              'Uganda',
    'Ouganda':             'Uganda',
    'Cameroun':            'Cameroon',
    'Gabon':               'Gabon',
    'Sénégal':             'Senegal',
    "Côte d'Ivoire":       'Ivory Coast',
    'France':              'France',
    'Belgique':            'Belgium',
    'USA':                 'United States',
    'Canada':              'Canada',
    'Chine':               'China',
}


@register.filter
def country_name(name, locale):
    if locale == 'en':
        return COUNTRY_NAME_EN.get(name, name)
    return name

@register.filter
def number_format(value, decimals=0):
    try:
        val = float(value)
        if decimals:
            return f"{val:,.{decimals}f}".replace(',', ' ')
        return f"{int(val):,}".replace(',', ' ')
    except (TypeError, ValueError):
        return value

@register.filter
def currency(value):
    try:
        return f"{float(value):,.0f}".replace(',', ' ')
    except Exception:
        return value

@register.simple_tag
def flag_img(code, size='sm'):
    sizes = {'xs': '16px', 'sm': '22px', 'md': '32px'}
    w = sizes.get(size, '22px')
    url = f"https://flagcdn.com/w40/{code.lower()}.png"
    return mark_safe(f'<img src="{url}" style="width:{w};border-radius:2px;" alt="{code}">')

@register.filter
def initials(name):
    return (name or '')[:2].upper()

@register.filter
def limit(value, num):
    return str(value)[:int(num)]
