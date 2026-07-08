from django.shortcuts import redirect
from django.urls import reverse


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
        if not exempt and not request.session.get('user_id'):
            return redirect('login')
        return self.get_response(request)


class LocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        locale = request.session.get('locale', 'fr')
        request.locale = locale
        response = self.get_response(request)
        return response
