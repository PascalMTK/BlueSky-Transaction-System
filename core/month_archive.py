from datetime import date
from django.db.models import Count
from django.db.models.functions import TruncMonth

MONTH_NAMES_FR = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
]
MONTH_NAMES_EN = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]


def month_label(year, month, locale='fr'):
    names = MONTH_NAMES_EN if locale == 'en' else MONTH_NAMES_FR
    return f"{names[month - 1]} {year}"


def build_month_archive(qs, locale='fr'):
    """Group a Transaction queryset by calendar month, newest first — each
    entry is a clickable 'page' showing only that month's transactions.
    No aggregate amount here: transactions mix currencies (per-country, and
    historically per-transaction), so a summed total would be meaningless."""
    rows = (
        qs.annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('-month')
    )
    today = date.today()
    max_count = max((row['count'] for row in rows), default=0)
    months = []
    for row in rows:
        d = row['month']
        months.append({
            'year':       d.year,
            'month':      d.month,
            'key':        f'{d.year:04d}-{d.month:02d}',
            'label':      month_label(d.year, d.month, locale),
            'count':      row['count'],
            'pct':        round(row['count'] / max_count * 100) if max_count else 0,
            'is_current': d.year == today.year and d.month == today.month,
        })
    return months


def parse_month_key(value):
    """Parse a 'YYYY-MM' key into (year, month), or None if invalid."""
    try:
        year_str, month_str = value.split('-')
        year, month = int(year_str), int(month_str)
        if not (1 <= month <= 12):
            return None
        return year, month
    except (ValueError, AttributeError):
        return None
