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


@register.simple_tag
def sparkline(values, color='#0284C7', width=72, height=26):
    """Tiny inline SVG trend line for stat/balance cards — no JS chart lib.
    `values` is a list of numbers (oldest → newest)."""
    values = [float(v or 0) for v in values]
    if len(values) < 2:
        return ''
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    step = width / (len(values) - 1)
    pad = 2
    usable_h = height - pad * 2

    points = []
    for i, v in enumerate(values):
        x = round(i * step, 1)
        y = round(pad + usable_h - ((v - lo) / span) * usable_h, 1)
        points.append((x, y))

    line = ' '.join(f'{x},{y}' for x, y in points)
    area = f'0,{height} ' + line + f' {width},{height}'
    uid = f'spark{abs(hash(tuple(values))) % 100000}'

    return mark_safe(
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" style="display:block;overflow:visible;">'
        f'<defs><linearGradient id="{uid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.35"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<polygon points="{area}" fill="url(#{uid})"/>'
        f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="1.75" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )
