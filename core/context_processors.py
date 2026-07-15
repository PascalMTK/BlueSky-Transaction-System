from core.models import Country, User
from core.translations import get_translations


def global_context(request):
    active_countries = Country.objects.filter(is_active=True)
    user   = getattr(request, 'auth_user', None)
    locale = getattr(request, 'locale', 'fr')
    if user is None and request.session.get('user_id'):
        try:
            user = User.objects.select_related('country').get(pk=request.session['user_id'])
            request.auth_user = user
        except User.DoesNotExist:
            pass
    return {
        'active_countries': active_countries,
        'auth_user':        user,
        'locale':           locale,
        't':                get_translations(locale),
    }
