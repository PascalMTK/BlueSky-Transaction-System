from core.models import Country, ForumMessage, User
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

    forum_unread_count = 0
    if user:
        qs = ForumMessage.objects.exclude(author=user)
        if user.forum_last_read_at:
            qs = qs.filter(created_at__gt=user.forum_last_read_at)
        forum_unread_count = qs.count()

    return {
        'active_countries':    active_countries,
        'auth_user':           user,
        'locale':              locale,
        't':                   get_translations(locale),
        'forum_unread_count':  forum_unread_count,
    }
