from datetime import datetime, timedelta
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

# How often to write last_seen to the DB — updating on every single request
# would be a lot of writes for no real benefit, since "online" is judged in
# multi-minute buckets anyway (see User.is_online / ONLINE_THRESHOLD).
LAST_SEEN_WRITE_INTERVAL = timedelta(minutes=2)


class AuthMiddleware:
    EXEMPT = [
        '/login/', '/register/', '/logout/', '/', '/contact/',
        '/lang/', '/static/', '/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        exempt = any(path.startswith(e) or path == e for e in self.EXEMPT)
        uid = request.session.get('user_id')
        if not exempt and not uid:
            return redirect('login')
        if uid:
            self._touch_last_seen(uid, request.session)
        return self.get_response(request)

    def _touch_last_seen(self, uid, session):
        from core.models import User
        last_write = session.get('_last_seen_write')
        now = timezone.now()
        if last_write:
            try:
                if now - datetime.fromisoformat(last_write) < LAST_SEEN_WRITE_INTERVAL:
                    return
            except (ValueError, TypeError):
                pass
        User.objects.filter(pk=uid).update(last_seen=now)
        session['_last_seen_write'] = now.isoformat()


class LocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        locale = request.session.get('locale', 'fr')
        request.locale = locale
        response = self.get_response(request)
        return response
