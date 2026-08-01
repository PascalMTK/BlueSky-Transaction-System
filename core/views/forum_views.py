from django.shortcuts import render, redirect
from django.utils import timezone
from core.decorators import agent_required, get_auth_user
from core.models import ForumMessage

MAX_BODY_LEN = 2000


@agent_required
def forum_index(request):
    """Company-wide message wall — any active user (admin or agent) can
    post; everyone sees the same feed. agent_required only checks that the
    session user is active, not their role, so admins land here too."""
    user = get_auth_user(request)

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()[:MAX_BODY_LEN]
        if body:
            ForumMessage.objects.create(author=user, body=body)
        return redirect('forum_index')

    forum_messages = ForumMessage.objects.select_related('author').order_by('-created_at')[:200]
    # Visiting the page is what clears the sidebar's unread badge (see
    # core.context_processors.global_context) — every other page keeps
    # comparing against this timestamp.
    user.forum_last_read_at = timezone.now()
    user.save(update_fields=['forum_last_read_at'])
    return render(request, 'forum/index.html', {
        'auth_user':      user,
        'forum_messages': forum_messages,
    })
