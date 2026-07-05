import os
import base64
import urllib.request
import urllib.parse
import urllib.error
from django.conf import settings
from django.template.loader import render_to_string


def generate_receipt_pdf(tx):
    """Render the transaction as a PDF receipt under MEDIA_ROOT/receipts/.
    Returns the relative media path (e.g. 'receipts/BSK-....pdf'), or None
    on failure."""
    from xhtml2pdf import pisa

    html = render_to_string('agent/transactions/receipt_pdf.html', {'transaction': tx})
    relative_path = f"receipts/{tx.transaction_number}.pdf"
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

    with open(absolute_path, 'wb') as f:
        result = pisa.CreatePDF(html, dest=f)
    if result.err:
        return None
    return relative_path


def _twilio_send_whatsapp(to_phone: str, media_url: str, body: str) -> bool:
    sid   = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_WHATSAPP_FROM
    if not from_number.startswith('whatsapp:'):
        from_number = f'whatsapp:{from_number}'

    url = f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'
    data = urllib.parse.urlencode({
        'To':       f'whatsapp:{to_phone}',
        'From':     from_number,
        'Body':     body,
        'MediaUrl': media_url,
    }).encode()
    credentials = base64.b64encode(f'{sid}:{token}'.encode()).decode()
    req = urllib.request.Request(
        url, data=data,
        headers={
            'Authorization': f'Basic {credentials}',
            'Content-Type':  'application/x-www-form-urlencoded',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        return True
    except urllib.error.HTTPError as e:
        print(f'[BLUESKY WHATSAPP] Twilio HTTP {e.code}: {e.read().decode(errors="replace")}')
        return False
    except Exception as e:
        print(f'[BLUESKY WHATSAPP] error: {e}')
        return False


def send_whatsapp_receipt(tx, phone: str, locale: str = 'fr') -> bool:
    """Generate the PDF receipt and send it to the client via WhatsApp
    (Twilio). Silent on failure — never blocks the transaction."""
    if not settings.WHATSAPP_ENABLED:
        return False
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_WHATSAPP_FROM):
        return False
    if not settings.SITE_BASE_URL:
        print('[BLUESKY WHATSAPP] SITE_BASE_URL not set — cannot build a public PDF URL for Twilio.')
        return False
    if not phone:
        return False

    phone = phone.strip()
    if not phone.startswith('+'):
        phone = '+' + phone.lstrip('0')

    relative_path = generate_receipt_pdf(tx)
    if not relative_path:
        return False

    media_url = f"{settings.SITE_BASE_URL.rstrip('/')}{settings.MEDIA_URL}{relative_path}"
    body = (
        f"Votre reçu de transaction {tx.transaction_number} est en pièce jointe."
        if locale != 'en' else
        f"Your receipt for transaction {tx.transaction_number} is attached."
    )
    return _twilio_send_whatsapp(phone, media_url, body)
