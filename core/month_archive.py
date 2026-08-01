from datetime import date
from django.db.models import Count, Sum, Max
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
    months = []
    for row in rows:
        d = row['month']
        months.append({
            'year':       d.year,
            'month':      d.month,
            'key':        f'{d.year:04d}-{d.month:02d}',
            'label':      month_label(d.year, d.month, locale),
            'count':      row['count'],
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


def build_month_totals(qs):
    """Closing-summary totals for a Transaction queryset already filtered to
    one month: USD-equivalent grand totals, a per-currency raw breakdown,
    and a status breakdown. Amounts are converted to USD via each origin
    country's admin-set exchange rate before summing across countries —
    summing raw amounts directly would mix CDF/ZMW/KES/etc into one
    meaningless number (see build_month_archive)."""
    total_count = qs.count()

    country_rows = qs.values('origin_country_id').annotate(
        amount=Sum('amount'), fee=Sum('fee_amount'), total=Sum('total_amount'),
        rate=Max('origin_country__usd_exchange_rate'),
    )
    total_amount_usd = total_fee_usd = total_sum_usd = 0.0
    for r in country_rows:
        rate = float(r['rate'] or 1) or 1
        total_amount_usd += float(r['amount'] or 0) / rate
        total_fee_usd    += float(r['fee'] or 0) / rate
        total_sum_usd    += float(r['total'] or 0) / rate

    currency_breakdown = list(
        qs.exclude(currency__isnull=True).exclude(currency='')
        .values('currency')
        .annotate(count=Count('id'), amount=Sum('amount'), fee=Sum('fee_amount'), total=Sum('total_amount'))
        .order_by('-total')
    )

    status_counts = {r['status']: r['count'] for r in qs.values('status').annotate(count=Count('id'))}
    status_breakdown = [
        {
            'code':  code,
            'count': status_counts.get(code, 0),
            'pct':   round(status_counts.get(code, 0) / total_count * 100, 1) if total_count else 0,
        }
        for code in ('completed', 'pending', 'cancelled')
    ]

    return {
        'total_count':      total_count,
        'total_amount_usd': total_amount_usd,
        'total_fee_usd':    total_fee_usd,
        'total_sum_usd':    total_sum_usd,
        'currency_breakdown': currency_breakdown,
        'status_breakdown':   status_breakdown,
    }
