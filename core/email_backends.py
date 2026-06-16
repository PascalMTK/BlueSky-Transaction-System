import json
import urllib.request
from email.utils import parseaddr
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class BrevoEmailBackend(BaseEmailBackend):
    """Send emails via Brevo HTTP API (works on PythonAnywhere free tier)."""

    API_URL = 'https://api.brevo.com/v3/smtp/email'

    def send_messages(self, email_messages):
        api_key = getattr(settings, 'BREVO_API_KEY', '')
        if not api_key:
            if not self.fail_silently:
                raise ValueError('BREVO_API_KEY is not set in settings.')
            return 0

        sent = 0
        for message in email_messages:
            try:
                self._send(message, api_key)
                sent += 1
            except Exception as e:
                print(f'[BLUESKY] Brevo send error: {e}')
                if not self.fail_silently:
                    raise
        return sent

    def _send(self, message, api_key):
        name, addr = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)

        payload = {
            'sender':      {'name': name or 'BLUESKY', 'email': addr},
            'to':          [{'email': r} for r in message.to],
            'subject':     message.subject,
            'textContent': message.body,
        }

        if message.cc:
            payload['cc'] = [{'email': r} for r in message.cc]
        if message.bcc:
            payload['bcc'] = [{'email': r} for r in message.bcc]

        for content, mimetype in getattr(message, 'alternatives', []):
            if mimetype == 'text/html':
                payload['htmlContent'] = content
                break

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.API_URL,
            data=data,
            headers={
                'api-key':      api_key,
                'Content-Type': 'application/json',
                'Accept':       'application/json',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status not in (200, 201):
                body = resp.read().decode()
                raise Exception(f'Brevo API {resp.status}: {body}')
