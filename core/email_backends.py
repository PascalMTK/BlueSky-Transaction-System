import json
import base64
import urllib.request
import urllib.error
from email.utils import parseaddr
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class SendGridEmailBackend(BaseEmailBackend):
    """Send emails via SendGrid HTTP API — free 100 emails/day."""

    API_URL = 'https://api.sendgrid.com/v3/mail/send'

    def send_messages(self, email_messages):
        api_key = getattr(settings, 'SENDGRID_API_KEY', '')
        if not api_key:
            if not self.fail_silently:
                raise ValueError('SENDGRID_API_KEY not set.')
            return 0

        sent = 0
        for message in email_messages:
            try:
                self._send(message, api_key)
                sent += 1
            except Exception as e:
                print(f'[BLUESKY] SendGrid error: {e}')
                if not self.fail_silently:
                    raise
        return sent

    def _send(self, message, api_key):
        name, addr = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)

        html_body = None
        for content, mimetype in getattr(message, 'alternatives', []):
            if mimetype == 'text/html':
                html_body = content
                break

        content = []
        if message.body:
            content.append({'type': 'text/plain', 'value': message.body})
        if html_body:
            content.append({'type': 'text/html', 'value': html_body})
        if not content:
            content.append({'type': 'text/plain', 'value': ' '})

        payload = {
            'personalizations': [{'to': [{'email': r} for r in message.to]}],
            'from': {'email': addr, 'name': name or 'BLUESKY'},
            'subject': message.subject,
            'content': content,
        }

        if message.cc:
            payload['personalizations'][0]['cc'] = [{'email': r} for r in message.cc]
        if message.bcc:
            payload['personalizations'][0]['bcc'] = [{'email': r} for r in message.bcc]

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.API_URL,
            data=data,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type':  'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp.read()
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='replace')
            raise Exception(f'SendGrid HTTP {e.code}: {body}') from e


class MailjetEmailBackend(BaseEmailBackend):
    """Send emails via Mailjet HTTP API — free 200 emails/day."""

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
            'From':     {'Email': addr, 'Name': name or 'BLUESKY'},
            'To':       [{'Email': r} for r in message.to],
            'Subject':  message.subject,
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
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp.read()
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='replace')
            raise Exception(f'Mailjet HTTP {e.code}: {body}') from e
