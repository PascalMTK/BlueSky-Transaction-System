import uuid
import os
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from decimal import Decimal, InvalidOperation
from django.db.models import Sum, Count, Q
from django.conf import settings
from core.models import User, Country, Transaction, AgentReport, DirectMessage
from core.decorators import agent_required, get_auth_user


# ── SMS helper ─────────────────────────────────────────────────────────────

def _build_sms_message(tx, locale='fr'):
    """Return bilingual SMS text for the client after a transaction."""
    amount_str = f"{tx.total_amount:,.0f} {tx.currency}"
    date_str   = tx.sent_at.strftime('%d/%m/%Y %H:%M') if tx.sent_at else ''

    if locale == 'en':
        if tx.transaction_type == 'send':
            name = tx.sender_name or 'Client'
            return (
                f"Hello {name},\n"
                f"Your transfer of {amount_str} (ref: {tx.transaction_number}) "
                f"has been successfully recorded on {date_str}.\n"
                f"Thank you for trusting BLUESKY Transactions!"
            )
        else:
            name = tx.receiver_name or 'Client'
            return (
                f"Hello {name},\n"
                f"Your withdrawal of {amount_str} (ref: {tx.transaction_number}) "
                f"has been successfully recorded on {date_str}.\n"
                f"Thank you for trusting BLUESKY Transactions!"
            )
    else:
        if tx.transaction_type == 'send':
            name = tx.sender_name or 'Client'
            return (
                f"Bonjour {name},\n"
                f"Votre transfert de {amount_str} (réf: {tx.transaction_number}) "
                f"a été enregistré avec succès le {date_str}.\n"
                f"Merci de faire confiance à BLUESKY Transactions !"
            )
        else:
            name = tx.receiver_name or 'Client'
            return (
                f"Bonjour {name},\n"
                f"Votre retrait de {amount_str} (réf: {tx.transaction_number}) "
                f"a été enregistré avec succès le {date_str}.\n"
                f"Merci de faire confiance à BLUESKY Transactions !"
            )

def _send_transaction_sms(tx, locale='fr'):
    """Send SMS to the client. Silent on failure — never blocks the transaction."""
    if not settings.AT_SMS_ENABLED:
        return False
    if not settings.AT_API_KEY:
        return False

    # Pick the right phone number
    phone = None
    if tx.transaction_type == 'send' and tx.sender_phone:
        phone = tx.sender_phone.strip()
    elif tx.transaction_type in ('withdrawal', 'receive') and tx.receiver_phone:
        phone = tx.receiver_phone.strip()

    if not phone:
        return False

    # Normalize phone: ensure it starts with +
    if not phone.startswith('+'):
        phone = '+' + phone.lstrip('0')

    try:
        import africastalking
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        sms     = africastalking.SMS
        message = _build_sms_message(tx, locale)
        sender  = settings.AT_SENDER_ID or None
        response = sms.send(message, [phone], sender_id=sender)
        print(f'[BLUESKY SMS] sent to {phone}: {response}')
        return True
    except Exception as e:
        print(f'[BLUESKY SMS] error: {e}')
        return False


def _parse_decimal(value, default=0):
    if value is None:
        return float(default or 0)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return float(default or 0)
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, TypeError, ValueError):
        return float(default or 0)


def _resolve_fee_amount(amount, post, fallback_fee):
    """Fee can come from either the 'fee_amount' field or the 'total_amount'
    (montant remis au client) field — whichever the agent last edited. Total
    takes priority since it's the figure actually handed to the client."""
    total_value = post.get('total_amount', '')
    if total_value is not None and str(total_value).strip() != '':
        total_amt = _parse_decimal(total_value, amount)
        return round(amount - total_amt, 2)
    fee_value = post.get('fee_amount', '')
    if fee_value is None or str(fee_value).strip() == '':
        return fallback_fee
    return _parse_decimal(fee_value, fallback_fee)


def _build_currencies():
    """Build currency dict from DB countries."""
    currencies = {}
    for c in Country.objects.values('currency_code', 'currency_name').distinct():
        if c['currency_code']:
            currencies[c['currency_code']] = c['currency_name'] or c['currency_code']
    # Add common international currencies not in DB
    extra = {
        'USD': 'Dollar américain', 'EUR': 'Euro', 'GBP': 'Livre sterling',
        'CHF': 'Franc suisse', 'CAD': 'Dollar canadien', 'AED': 'Dirham EAU',
    }
    for k, v in extra.items():
        if k not in currencies:
            currencies[k] = v
    return dict(sorted(currencies.items()))


@agent_required
def dashboard(request):
    user  = get_auth_user(request)
    today = date.today()
    my_tx = Transaction.objects.filter(agent=user)
    stats = {
        'total_transactions': my_tx.count(),
        'transactions_today': my_tx.filter(created_at__date=today).count(),
        'transactions_month': my_tx.filter(created_at__month=today.month, created_at__year=today.year).count(),
        'total_amount':       float(my_tx.filter(status='completed').aggregate(s=Sum('amount'))['s'] or 0),
        'total_fees':         float(my_tx.filter(status='completed').aggregate(s=Sum('fee_amount'))['s'] or 0),
        'amount_month':       float(my_tx.filter(created_at__month=today.month, created_at__year=today.year, status='completed').aggregate(s=Sum('amount'))['s'] or 0),
    }
    recent_tx = my_tx.select_related('origin_country', 'destination_country').order_by('-created_at')[:10]
    return render(request, 'agent/dashboard.html', {'stats': stats, 'recent_tx': recent_tx, 'auth_user': user})


@agent_required
def tx_index(request):
    user = get_auth_user(request)
    qs   = Transaction.objects.filter(agent=user).select_related('origin_country', 'destination_country').order_by('-created_at')
    q           = request.GET.get('q', '')
    status_f    = request.GET.get('status', '')
    type_f      = request.GET.get('transaction_type', '')
    country_f   = request.GET.get('country_id', '')
    date_from   = request.GET.get('date_from', '')
    date_to     = request.GET.get('date_to', '')
    if q:         qs = qs.filter(Q(transaction_number__icontains=q) | Q(sender_name__icontains=q) | Q(receiver_name__icontains=q) | Q(sender_phone__icontains=q))
    if status_f:  qs = qs.filter(status=status_f)
    if type_f:    qs = qs.filter(transaction_type=type_f)
    if country_f: qs = qs.filter(Q(origin_country_id=country_f) | Q(destination_country_id=country_f))
    if date_from:
        try: qs = qs.filter(created_at__date__gte=date_from)
        except Exception: pass
    if date_to:
        try: qs = qs.filter(created_at__date__lte=date_to)
        except Exception: pass
    countries = Country.objects.filter(is_active=True)
    return render(request, 'agent/transactions/index.html', {
        'transactions':      qs,
        'countries':         countries,
        'q':                 q,
        'status_filter':     status_f,
        'type_filter':       type_f,
        'country_filter':    country_f,
        'date_from':         date_from,
        'date_to':           date_to,
        'auth_user':         user,
    })


@agent_required
def tx_create(request):
    user      = get_auth_user(request)
    countries = Country.objects.filter(is_active=True)
    currencies = _build_currencies()
    if request.method == 'POST':
        tx_type   = request.POST.get('transaction_type') or request.GET.get('type', 'send')
        origin_id = request.POST.get('origin_country_id')
        dest_id   = request.POST.get('destination_country_id')
        try:
            origin  = Country.objects.get(pk=origin_id)
            dest    = Country.objects.get(pk=dest_id)
            amount = _parse_decimal(request.POST.get('amount', 0), 0)
            default_pct = float(origin.default_fee_percentage or 0)
            default_fee = round(amount * default_pct / 100, 2)
            fee_amt = _resolve_fee_amount(amount, request.POST, default_fee)
            if fee_amt > amount or fee_amt < 0:
                messages.error(request, "Le montant des frais et le montant remis ne peuvent pas dépasser le montant envoyé.")
                raise ValueError('fee_amount_too_high')
            amount, fee_amt, fee_pct, total = Transaction.calculate_totals(amount, fee_amt, fee_is_percentage=False)
            tx_num  = 'BSK-' + datetime.now().strftime('%Y%m%d') + '-' + str(uuid.uuid4())[:6].upper()
            currency = (request.POST.get('currency') or origin.currency_code or '').upper()
            sent_at_str = request.POST.get('sent_at', '')
            sent_at = None
            if sent_at_str:
                try:
                    sent_at = datetime.fromisoformat(sent_at_str)
                except ValueError:
                    sent_at = None
            if not sent_at:
                sent_at = datetime.now()

            # Validate required fields by type
            sender_name  = request.POST.get('sender_name', '').strip()
            sender_phone = request.POST.get('sender_phone', '').strip()
            recv_name    = request.POST.get('receiver_name', '').strip()
            recv_phone   = request.POST.get('receiver_phone', '').strip()

            if tx_type not in ('send', 'receive', 'exchange', 'withdrawal'):
                tx_type = 'send'
            if tx_type == 'send' and not sender_name:
                messages.error(request, "Le nom de l'expéditeur est obligatoire pour un envoi.")
                raise ValueError('sender_name required')
            if tx_type in ('send', 'exchange', 'withdrawal') and not recv_name:
                messages.error(request, "Le nom du bénéficiaire est obligatoire pour ce type de transaction.")
                raise ValueError('receiver_name required')
            if tx_type == 'exchange' and not sender_name:
                messages.error(request, "Le nom de l'expéditeur est obligatoire pour un échange.")
                raise ValueError('sender_name required')

            tx = Transaction(
                transaction_number   = tx_num,
                transaction_type     = tx_type,
                sender_name          = sender_name,
                sender_phone         = sender_phone,
                receiver_name        = recv_name,
                receiver_phone       = recv_phone,
                amount               = amount,
                fee_percentage       = fee_pct,
                fee_amount           = fee_amt,
                total_amount         = total,
                currency             = currency,
                origin_country       = origin,
                destination_country  = dest,
                agent                = user,
                status               = request.POST.get('status', 'completed'),
                notes                = request.POST.get('notes', ''),
                payment_method       = request.POST.get('payment_method', 'cash'),
                sent_at              = sent_at,
            )
            tx.save()
            locale = request.session.get('locale', 'fr')
            _send_transaction_sms(tx, locale)
            messages.success(request, f'Transaction {tx_num} créée avec succès.')
            return redirect('tx_show', tx_id=tx.id)
        except ValueError:
            pass
        except Exception as e:
            messages.error(request, f'Erreur : {e}')
    if request.method == 'POST':
        default_tx_type = request.POST.get('transaction_type', 'send')
        type_preselected = True
    else:
        default_tx_type = request.GET.get('type', '')
        type_preselected = bool(default_tx_type)
        if not default_tx_type:
            default_tx_type = 'send'
    sent_at_value = datetime.now().strftime('%Y-%m-%dT%H:%M')
    return render(request, 'agent/transactions/create.html', {
        'countries': countries, 'currencies': currencies, 'auth_user': user,
        'default_tx_type': default_tx_type,
        'type_preselected': type_preselected,
        'sent_at_value': sent_at_value,
    })


@agent_required
def tx_show(request, tx_id):
    user = get_auth_user(request)
    tx   = get_object_or_404(Transaction, pk=tx_id)
    if not user.is_admin() and tx.agent_id != user.id:
        return redirect('tx_index')
    return render(request, 'agent/transactions/show.html', {'transaction': tx, 'auth_user': user})


@agent_required
def tx_edit(request, tx_id):
    user = get_auth_user(request)
    tx   = get_object_or_404(Transaction, pk=tx_id)
    if not user.is_admin() and tx.agent_id != user.id:
        return redirect('tx_index')
    countries  = Country.objects.filter(is_active=True)
    currencies = _build_currencies()
    if request.method == 'POST':
        tx_type  = request.POST.get('transaction_type', tx.transaction_type)
        amount = _parse_decimal(request.POST.get('amount', tx.amount), tx.amount)
        fee_amt = _resolve_fee_amount(amount, request.POST, tx.fee_amount)
        if fee_amt > amount or fee_amt < 0:
            messages.error(request, "Le montant des frais et le montant remis ne peuvent pas dépasser le montant envoyé.")
            return render(request, 'agent/transactions/edit.html', {
                'transaction': tx, 'countries': countries, 'currencies': currencies, 'auth_user': user,
            })
        amount, fee_amt, fee_pct, total = Transaction.calculate_totals(amount, fee_amt, fee_is_percentage=False)
        currency = (request.POST.get('currency') or tx.currency or '').upper()
        sent_at_str = request.POST.get('sent_at', '')
        if sent_at_str:
            try:
                tx.sent_at = datetime.fromisoformat(sent_at_str)
            except ValueError:
                pass

        tx.transaction_type  = tx_type
        tx.sender_name       = request.POST.get('sender_name', tx.sender_name)
        tx.sender_phone      = request.POST.get('sender_phone', tx.sender_phone)
        tx.receiver_name     = request.POST.get('receiver_name', tx.receiver_name)
        tx.receiver_phone    = request.POST.get('receiver_phone', tx.receiver_phone)
        tx.amount            = amount
        tx.fee_percentage    = fee_pct
        tx.fee_amount        = fee_amt
        tx.total_amount      = total
        tx.currency          = currency
        tx.status            = request.POST.get('status', tx.status)
        tx.payment_method    = request.POST.get('payment_method', tx.payment_method)
        tx.notes             = request.POST.get('notes', tx.notes)
        origin_id  = request.POST.get('origin_country_id')
        dest_id    = request.POST.get('destination_country_id')
        if origin_id:  tx.origin_country_id = origin_id
        if dest_id:    tx.destination_country_id = dest_id
        tx.save()
        locale = request.session.get('locale', 'fr')
        _send_transaction_sms(tx, locale)
        messages.success(request, 'Transaction mise à jour.')
        return redirect('tx_show', tx_id=tx.id)
    return render(request, 'agent/transactions/edit.html', {
        'transaction': tx, 'countries': countries, 'currencies': currencies, 'auth_user': user,
    })


@agent_required
def tx_print(request, tx_id):
    user = get_auth_user(request)
    tx   = get_object_or_404(Transaction, pk=tx_id)
    if not user.is_admin() and tx.agent_id != user.id:
        return redirect('tx_index')
    return render(request, 'agent/transactions/print.html', {'transaction': tx, 'auth_user': user})


@agent_required
def tx_destroy(request, tx_id):
    if request.method == 'POST':
        user = get_auth_user(request)
        tx   = get_object_or_404(Transaction, pk=tx_id)
        if user.is_admin() or tx.agent_id == user.id:
            tx.delete()
            messages.success(request, 'Transaction supprimée.')
    return redirect('tx_index')


@agent_required
def report_store(request):
    if request.method == 'POST':
        user = get_auth_user(request)
        AgentReport.objects.create(
            agent   = user,
            subject = request.POST.get('subject', ''),
            message = request.POST.get('message', ''),
        )
        messages.success(request, 'Rapport envoyé à l\'administrateur.')
    return redirect('agent_dashboard')


@agent_required
def agent_reports_portal(request):
    user = get_auth_user(request)
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        if subject and message:
            report = AgentReport.objects.create(
                agent   = user,
                subject = subject,
                message = message,
            )
            return redirect(f'/agent/reports/portal/?r={report.id}')
        return redirect('agent_reports_portal')

    reports     = AgentReport.objects.filter(agent=user).order_by('-created_at')
    selected_id = request.GET.get('r')
    selected    = None
    if selected_id:
        try:
            selected = reports.get(id=int(selected_id))
        except (AgentReport.DoesNotExist, ValueError):
            pass

    replied_count = reports.filter(admin_reply__isnull=False).exclude(admin_reply='').count()

    return render(request, 'agent/reports.html', {
        'reports':       reports,
        'selected':      selected,
        'replied_count': replied_count,
        'auth_user':     user,
    })


@agent_required
def report_delete(request, report_id):
    if request.method == 'POST':
        user = get_auth_user(request)
        try:
            report = AgentReport.objects.get(pk=report_id, agent=user)
            report.delete()
        except AgentReport.DoesNotExist:
            pass
    return redirect('agent_reports_portal')


@agent_required
def message_delete(request, msg_id):
    if request.method == 'POST':
        user = get_auth_user(request)
        try:
            msg = DirectMessage.objects.get(pk=msg_id, sender=user)
            partner_id = msg.recipient_id
            msg.delete()
            return redirect(f'/messages/{partner_id}/')
        except DirectMessage.DoesNotExist:
            pass
    return redirect('messages_list')


@agent_required
def conversation_delete(request, user_id):
    if request.method == 'POST':
        user = get_auth_user(request)
        try:
            partner = User.objects.get(pk=user_id)
            DirectMessage.objects.filter(
                Q(sender=user, recipient=partner) | Q(sender=partner, recipient=user)
            ).delete()
        except User.DoesNotExist:
            pass
    return redirect('messages_list')


@agent_required
def export_csv(request):
    user = get_auth_user(request)
    qs   = Transaction.objects.filter(agent=user).select_related('origin_country', 'destination_country').order_by('-created_at')
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    if date_from:
        try: qs = qs.filter(created_at__date__gte=date_from)
        except Exception: pass
    if date_to:
        try: qs = qs.filter(created_at__date__lte=date_to)
        except Exception: pass

    headers = [
        'N° Transaction', 'Date', 'Type', 'Expéditeur', 'Tél. Expéditeur',
        'Bénéficiaire', 'Tél. Bénéficiaire', 'Montant', 'Frais %',
        'Frais', 'Total', 'Devise', 'Pays Origine', 'Pays Destination', 'Statut',
    ]
    col_widths = [20, 18, 12, 22, 16, 22, 16, 14, 10, 14, 14, 10, 18, 18, 12]
    money_cols = {8, 10, 11}
    text_cols  = {4, 6}

    # Shared styles helper (inline to avoid cross-file dependency)
    thin   = Side(border_style='thin', color='CBD5E1')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal='center', vertical='center')
    left_a = Alignment(horizontal='left',   vertical='center')
    hdr_fill  = PatternFill('solid', fgColor='0284C7')
    even_fill = PatternFill('solid', fgColor='EFF6FF')
    odd_fill  = PatternFill('solid', fgColor='FFFFFF')
    money_fill= PatternFill('solid', fgColor='DBEAFE')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Mes Transactions — {user.name[:18]}'

    # Header
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.fill = hdr_fill
        cell.font = Font(bold=True, color='FFFFFF', size=11)
        cell.border = border
        cell.alignment = center
        ws.column_dimensions[get_column_letter(col_idx)].width = col_widths[col_idx - 1]
    ws.freeze_panes = 'A2'
    ws.row_dimensions[1].height = 28

    TYPE_MAP = {'send': 'Envoi', 'receive': 'Réception', 'exchange': 'Échange', 'withdrawal': 'Retrait'}
    STA_MAP  = {'completed': 'Complété', 'pending': 'En attente', 'cancelled': 'Annulé'}

    # Status cell colors
    sta_colors = {'completed': ('DCFCE7', '15803D'), 'pending': ('FEF9C3', 'CA8A04'), 'cancelled': ('FEE2E2', 'DC2626')}

    for row_idx, t in enumerate(qs, 2):
        row = [
            t.transaction_number,
            t.created_at.strftime('%d/%m/%Y %H:%M'),
            TYPE_MAP.get(t.transaction_type, t.transaction_type),
            t.sender_name,
            t.sender_phone or '',
            t.receiver_name or '',
            t.receiver_phone or '',
            float(t.amount),
            float(t.fee_percentage),
            float(t.fee_amount),
            float(t.total_amount),
            t.currency or '',
            t.origin_country.name,
            t.destination_country.name,
            STA_MAP.get(t.status, t.status),
        ]
        fill = even_fill if row_idx % 2 == 0 else odd_fill
        for col_idx, val in enumerate(row, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = border
            if col_idx in money_cols:
                cell.fill = money_fill
                cell.number_format = '#,##0.00'
                cell.alignment = center
            elif col_idx == len(headers):   # Statut
                bg, fg = sta_colors.get(t.status, ('FFFFFF', '1E293B'))
                cell.fill = PatternFill('solid', fgColor=bg)
                cell.font = Font(bold=True, color=fg, size=10)
                cell.alignment = center
            elif col_idx in text_cols:
                cell.fill = fill
                cell.alignment = left_a
            else:
                cell.fill = fill
                cell.alignment = center
        ws.row_dimensions[row_idx].height = 20

    ws.auto_filter.ref = ws.dimensions

    filename = f"MesTransactions_{user.agent_code or 'agent'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


# ── Network transactions (all countries, read-only) ──────────────────────────

@agent_required
def tx_network(request):
    user     = get_auth_user(request)
    qs       = Transaction.objects.select_related('agent', 'origin_country', 'destination_country').order_by('-created_at')
    q        = request.GET.get('q', '')
    status_f = request.GET.get('status', '')
    country_f= request.GET.get('country_id', '')
    agent_f  = request.GET.get('agent_id', '')
    date_from= request.GET.get('date_from', '')
    date_to  = request.GET.get('date_to', '')
    if q:         qs = qs.filter(Q(transaction_number__icontains=q) | Q(sender_name__icontains=q) | Q(receiver_name__icontains=q))
    if status_f:  qs = qs.filter(status=status_f)
    if country_f: qs = qs.filter(Q(origin_country_id=country_f) | Q(destination_country_id=country_f))
    if agent_f:   qs = qs.filter(agent_id=agent_f)
    if date_from:
        try: qs = qs.filter(created_at__date__gte=date_from)
        except Exception: pass
    if date_to:
        try: qs = qs.filter(created_at__date__lte=date_to)
        except Exception: pass
    countries = Country.objects.filter(is_active=True)
    agents    = User.objects.filter(role='agent', status='active').select_related('country').order_by('name')
    return render(request, 'agent/transactions/network.html', {
        'transactions':  qs[:500],
        'countries':     countries,
        'agents':        agents,
        'q':             q,
        'status_filter': status_f,
        'country_filter':country_f,
        'agent_filter':  agent_f,
        'date_from':     date_from,
        'date_to':       date_to,
        'auth_user':     user,
    })


# ── Direct messaging ─────────────────────────────────────────────────────────

@agent_required
def messages_list(request):
    user = get_auth_user(request)

    sent_to   = DirectMessage.objects.filter(sender=user).values_list('recipient_id', flat=True).distinct()
    recv_from = DirectMessage.objects.filter(recipient=user).values_list('sender_id', flat=True).distinct()
    partner_ids = set(list(sent_to) + list(recv_from))

    if not partner_ids:
        conversations = []
    else:
        # Batch-load all partners in one query
        partners = {u.pk: u for u in User.objects.select_related('country').filter(pk__in=partner_ids)}

        # Unread counts per sender in one query
        unread_map = {
            r['sender_id']: r['cnt']
            for r in DirectMessage.objects
            .filter(recipient=user, sender_id__in=partner_ids, is_read=False)
            .values('sender_id')
            .annotate(cnt=Count('id'))
        }

        # Last message per conversation — walk once through ordered messages
        last_msgs: dict = {}
        for msg in DirectMessage.objects.filter(
            Q(sender=user, recipient_id__in=partner_ids) |
            Q(sender_id__in=partner_ids, recipient=user)
        ).order_by('-created_at'):
            pid = msg.recipient_id if msg.sender_id == user.pk else msg.sender_id
            if pid not in last_msgs:
                last_msgs[pid] = msg

        conversations = []
        for pid in partner_ids:
            partner = partners.get(pid)
            if not partner:
                continue
            conversations.append({
                'partner':  partner,
                'last_msg': last_msgs.get(pid),
                'unread':   unread_map.get(pid, 0),
            })

    conversations.sort(key=lambda c: c['last_msg'].created_at if c['last_msg'] else datetime.min, reverse=True)

    # All users available to message (exclude self)
    all_users = User.objects.select_related('country').exclude(pk=user.pk).filter(
        status='active'
    ).order_by('role', 'name')

    return render(request, 'agent/messages.html', {
        'conversations': conversations,
        'all_users':     all_users,
        'selected':      None,
        'thread':        [],
        'auth_user':     user,
    })


@agent_required
def messages_thread(request, user_id):
    user    = get_auth_user(request)
    try:
        partner = User.objects.select_related('country').get(pk=user_id)
    except User.DoesNotExist:
        return redirect('messages_list')

    if request.method == 'POST':
        msg_text = request.POST.get('message', '').strip()
        new_msg = None
        if msg_text:
            new_msg = DirectMessage.objects.create(sender=user, recipient=partner, message=msg_text)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if new_msg:
                initials = ''.join(w[0].upper() for w in (user.name or '?').split()[:2])
                return JsonResponse({
                    'ok': True, 'id': new_msg.id, 'is_mine': True,
                    'message': new_msg.message, 'is_read': False,
                    'time': new_msg.created_at.strftime('%H:%M'),
                    'date': new_msg.created_at.strftime('%Y%m%d'),
                    'date_label': new_msg.created_at.strftime('%d/%m/%Y'),
                    'initials': initials,
                })
            return JsonResponse({'ok': False})
        return redirect(f'/messages/{user_id}/')

    # Mark received messages as read
    DirectMessage.objects.filter(sender=partner, recipient=user, is_read=False).update(is_read=True)

    raw_thread = list(
        DirectMessage.objects.filter(
            Q(sender=user, recipient=partner) | Q(sender=partner, recipient=user)
        ).select_related('sender').order_by('created_at')
    )

    # Pre-compute display flags so the template needs no expressions
    prev_date = None
    prev_sid  = None
    thread = []
    for msg in raw_thread:
        d = msg.created_at.strftime('%Y%m%d')
        show_sep  = (d != prev_date)
        new_group = (msg.sender_id != prev_sid) or show_sep
        thread.append({
            'msg':        msg,
            'is_mine':    msg.sender_id == user.id,
            'show_sep':   show_sep,
            'sep_label':  msg.created_at.strftime('%d/%m/%Y'),
            'new_group':  new_group,
        })
        prev_date = d
        prev_sid  = msg.sender_id

    from django.db.models import Max
    sent_to   = DirectMessage.objects.filter(sender=user).values_list('recipient_id', flat=True).distinct()
    recv_from = DirectMessage.objects.filter(recipient=user).values_list('sender_id', flat=True).distinct()
    partner_ids = set(list(sent_to) + list(recv_from))
    if user_id not in partner_ids:
        partner_ids.add(user_id)

    conversations = []
    for pid in partner_ids:
        try:
            p = User.objects.select_related('country').get(pk=pid)
        except User.DoesNotExist:
            continue
        last_msg = DirectMessage.objects.filter(
            Q(sender=user, recipient_id=pid) | Q(sender_id=pid, recipient=user)
        ).order_by('-created_at').first()
        unread = DirectMessage.objects.filter(sender_id=pid, recipient=user, is_read=False).count()
        conversations.append({'partner': p, 'last_msg': last_msg, 'unread': unread})

    conversations.sort(key=lambda c: c['last_msg'].created_at if c['last_msg'] else datetime.min, reverse=True)

    all_users = User.objects.select_related('country').exclude(pk=user.pk).filter(
        status='active'
    ).order_by('role', 'name')

    return render(request, 'agent/messages.html', {
        'conversations': conversations,
        'all_users':     all_users,
        'selected':      partner,
        'thread':        thread,
        'auth_user':     user,
    })


@agent_required
def messages_since(request, user_id, since_id):
    """AJAX: returns JSON of messages newer than since_id between current user and user_id."""
    user = get_auth_user(request)
    qs = DirectMessage.objects.filter(
        id__gt=since_id,
    ).filter(
        Q(sender=user, recipient_id=user_id) |
        Q(sender_id=user_id, recipient=user)
    ).order_by('created_at').select_related('sender')

    # Mark received messages as read
    qs.filter(sender_id=user_id, recipient=user, is_read=False).update(is_read=True)

    data = []
    for msg in qs:
        initials = ''.join(w[0].upper() for w in (msg.sender.name or '?').split()[:2])
        data.append({
            'id': msg.id,
            'is_mine': msg.sender_id == user.id,
            'message': msg.message,
            'is_read': msg.is_read,
            'time': msg.created_at.strftime('%H:%M'),
            'date': msg.created_at.strftime('%Y%m%d'),
            'date_label': msg.created_at.strftime('%d/%m/%Y'),
            'initials': initials,
        })

    return JsonResponse({'messages': data})


@agent_required
def fee_for_country(request, country_id):
    try:
        c = Country.objects.get(pk=country_id)
        return JsonResponse({'fee': float(c.default_fee_percentage), 'currency': c.currency_code})
    except Country.DoesNotExist:
        return JsonResponse({'fee': 3.0, 'currency': ''})
