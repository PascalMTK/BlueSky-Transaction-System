from django import template
from django.utils.safestring import mark_safe

register = template.Library()

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
