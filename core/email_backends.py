import json
import base64
import urllib.request
from email.utils import parseaddr
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class MailjetEmailBackend(BaseEmailBackend):
    """Send emails via Mailjet HTTP API — free 200 emails/day, no credit card."""

    API_URL = 'https://api.mailjet.com/v3.1/send'

    def send_messages(self, email_messages):
        api_key    = getattr(settings, 'MAILJET_API_KEY', '')
        api_secret = getattr(settings, 'MAILJET_API_SECRET', '')
        if not api_key or not api_secret:
            if not self.fail_silently:
                raise ValueError('MAILJET_API_KEY or MAILJET_API_SECRET not set.')
            return 0

        credentials = base64.b64encode(f'{api_key}:{api_secret}'.encode()).decode()
        sent = 0
        for message in email_messages:
            try:
                self._send(message, credentials)
                sent += 1
            except Exception as e:
                print(f'[BLUESKY] Mailjet error: {e}')
                if not self.fail_silently:
                    raise
        return sent

    def _send(self, message, credentials):
        name, addr = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)

        msg = {
            'From':    {'Email': addr, 'Name': name or 'BLUESKY'},
            'To':      [{'Email': r} for r in message.to],
            'Subject': message.subject,
            'TextPart': message.body,
        }

        for content, mimetype in getattr(message, 'alternatives', []):
            if mimetype == 'text/html':
                msg['HTMLPart'] = content
                break

        if message.cc:
            msg['Cc'] = [{'Email': r} for r in message.cc]
        if message.bcc:
            msg['Bcc'] = [{'Email': r} for r in message.bcc]

        payload = json.dumps({'Messages': [msg]}).encode('utf-8')
        req = urllib.request.Request(
            self.API_URL,
            data=payload,
            headers={
                'Authorization': f'Basic {credentials}',
                'Content-Type':  'application/json',
                'Accept':        'application/json',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status not in (200, 201):
                body = resp.read().decode()
                raise Exception(f'Mailjet {resp.status}: {body}')
