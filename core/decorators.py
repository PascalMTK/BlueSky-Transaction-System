from functools import wraps
from django.shortcuts import redirect
from core.models import User


def login_required(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return f(request, *args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        uid = request.session.get('user_id')
        if not uid:
            return redirect('login')
        try:
            user = User.objects.get(pk=uid)
            if not user.is_admin():
                return redirect('agent_dashboard')
            # Admins must be active — deleted/inactive admins are locked out
            if user.status not in ('active',):
                request.session.flush()
                return redirect('login')
        except User.DoesNotExist:
            request.session.flush()
            return redirect('login')
        return f(request, *args, **kwargs)
    return wrapper


def agent_required(f):
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        uid = request.session.get('user_id')
        if not uid:
            return redirect('login')
        try:
            user = User.objects.get(pk=uid)
            # Only active users can access agent pages
            if user.status != 'active':
                request.session.flush()
                return redirect('login')
        except User.DoesNotExist:
            request.session.flush()
            return redirect('login')
        return f(request, *args, **kwargs)
    return wrapper


def get_auth_user(request):
    uid = request.session.get('user_id')
    if uid:
        try:
            return User.objects.select_related('country').get(pk=uid)
        except User.DoesNotExist:
            pass
    return None
