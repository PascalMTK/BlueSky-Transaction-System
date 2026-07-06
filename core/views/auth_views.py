import os, uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from core.models import User, Country
import bcrypt

_PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
_PHOTO_MAX  = 3 * 1024 * 1024  # 3 MB


def _save_photo(photo_file, user_id) -> str | None:
    """Save uploaded photo to MEDIA_ROOT/profiles/ and return relative path."""
    ext = os.path.splitext(photo_file.name)[1].lower()
    if ext not in _PHOTO_EXTS or photo_file.size > _PHOTO_MAX:
        return None
    rel = f"profiles/{user_id}{ext}"
    abs_path = os.path.join(settings.MEDIA_ROOT, rel)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, 'wb+') as f:
        for chunk in photo_file.chunks():
            f.write(chunk)
    return rel


def welcome(request):
    if request.session.get('user_id'):
        user = User.objects.get(pk=request.session['user_id'])
        return redirect('admin_dashboard' if user.is_admin() else 'agent_dashboard')
    return render(request, 'welcome.html')


def _notify_agent_pending(user):
    """Send confirmation email to agent after registration."""
    subject = '[BLUESKY] Votre candidature a été reçue — En attente de validation'
    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Inter,sans-serif;background:#f0f4f8;padding:30px 20px;margin:0;">
  <div style="max-width:520px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,.12);">
    <div style="background:linear-gradient(135deg,#0099e6,#0052b2);padding:28px 32px;text-align:center;">
      <div style="font-size:40px;margin-bottom:8px;">📋</div>
      <div style="color:white;font-size:20px;font-weight:900;letter-spacing:.5px;">BLUESKY TRANSACTIONS</div>
      <div style="color:rgba(255,255,255,.8);font-size:13px;margin-top:4px;">Confirmation de candidature</div>
    </div>
    <div style="padding:32px;">
      <p style="color:#334155;font-size:15px;margin:0 0 16px;">Bonjour <strong>{user.name}</strong>,</p>
      <p style="color:#64748b;font-size:14px;margin:0 0 20px;line-height:1.7;">
        Nous avons bien reçu votre demande d'inscription sur la plateforme <strong>BLUESKY Transactions</strong>.<br>
        Votre compte est actuellement <strong>en attente de validation</strong> par un administrateur.
      </p>
      <div style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:8px;padding:16px 20px;margin-bottom:24px;">
        <div style="font-size:13px;color:#92400e;font-weight:700;margin-bottom:6px;">⏳ Statut : En attente</div>
        <div style="font-size:13px;color:#78350f;line-height:1.6;">
          Un administrateur examinera votre dossier et vous recevrez un email dès que votre compte sera activé.
        </div>
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:24px;">
        <tr style="background:#f8fafc;"><td style="padding:10px 14px;color:#64748b;font-weight:600;">Nom</td><td style="padding:10px 14px;color:#1e293b;">{user.name}</td></tr>
        <tr><td style="padding:10px 14px;color:#64748b;font-weight:600;">Email</td><td style="padding:10px 14px;color:#1e293b;">{user.email}</td></tr>
        <tr style="background:#f8fafc;"><td style="padding:10px 14px;color:#64748b;font-weight:600;">Code agent</td><td style="padding:10px 14px;color:#1e293b;font-family:monospace;font-weight:700;">{user.agent_code or '—'}</td></tr>
      </table>
      <p style="color:#94a3b8;font-size:12px;text-align:center;margin:0;">
        Si vous n'avez pas créé ce compte, ignorez cet email.
      </p>
    </div>
    <div style="background:#f8fafc;border-top:1px solid #e8edf2;padding:16px;text-align:center;">
      <p style="margin:0;font-size:11px;color:#94a3b8;">© 2026 BLUESKY Transactions — Tous droits réservés</p>
    </div>
  </div>
</body>
</html>"""
    plain = f"Bonjour {user.name},\n\nVotre candidature BLUESKY a bien été reçue.\nVotre compte est en attente de validation par un administrateur.\n\nCode agent : {user.agent_code or '—'}\n\n— L'équipe BLUESKY Transactions"
    try:
        send_mail(
            subject=subject,
            message=plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_body,
            fail_silently=True,
        )
    except Exception as e:
        print(f'[BLUESKY] Pending notify error: {e}')


def _notify_admin_new_registration(user):
    """Send email to all admins when a new agent registers and needs validation."""
    admin_emails = list(User.objects.filter(role='admin', status='active').values_list('email', flat=True))
    if not admin_emails:
        return
    subject = f'[BLUESKY] Nouvelle inscription en attente — {user.name}'
    body = f"""Un nouvel utilisateur vient de s'inscrire et attend une validation.

Nom    : {user.name}
Email  : {user.email}
Tél.   : {user.phone or '—'}
Code   : {user.agent_code or '—'}

Connectez-vous au panneau d'administration pour valider ou rejeter ce compte.
"""
    html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Inter,sans-serif;background:#f0f4f8;padding:30px 20px;margin:0;">
  <div style="max-width:520px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,.12);">
    <div style="background:linear-gradient(135deg,#f59e0b,#d97706);padding:28px 32px;text-align:center;">
      <div style="font-size:36px;margin-bottom:8px;">⏳</div>
      <div style="color:white;font-size:20px;font-weight:900;letter-spacing:.5px;">BLUESKY TRANSACTIONS</div>
      <div style="color:rgba(255,255,255,.8);font-size:13px;margin-top:4px;">Nouvelle inscription — validation requise</div>
    </div>
    <div style="padding:32px;">
      <p style="color:#334155;font-size:15px;margin:0 0 16px;">Bonjour Administrateur,</p>
      <p style="color:#64748b;font-size:14px;margin:0 0 24px;line-height:1.6;">
        L'utilisateur suivant vient de s'inscrire et son compte est <strong>en attente de validation</strong>.
      </p>
      <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:24px;">
        <tr style="background:#f8fafc;"><td style="padding:10px 14px;color:#64748b;font-weight:600;border-radius:4px;">Nom</td><td style="padding:10px 14px;color:#1e293b;">{user.name}</td></tr>
        <tr><td style="padding:10px 14px;color:#64748b;font-weight:600;">Email</td><td style="padding:10px 14px;color:#1e293b;">{user.email}</td></tr>
        <tr style="background:#f8fafc;"><td style="padding:10px 14px;color:#64748b;font-weight:600;">Téléphone</td><td style="padding:10px 14px;color:#1e293b;">{user.phone or '—'}</td></tr>
        <tr><td style="padding:10px 14px;color:#64748b;font-weight:600;">Code agent</td><td style="padding:10px 14px;color:#1e293b;">{user.agent_code or '—'}</td></tr>
      </table>
      <div style="background:#fef9c3;border-radius:8px;padding:14px 16px;margin-bottom:24px;">
        <p style="margin:0;font-size:13px;color:#92400e;">⚠️ Veuillez valider ou rejeter ce compte depuis le panneau d'administration.</p>
      </div>
    </div>
    <div style="background:#f8fafc;border-top:1px solid #e8edf2;padding:16px;text-align:center;">
      <p style="margin:0;font-size:11px;color:#94a3b8;">© 2026 BLUESKY Transactions — Tous droits réservés</p>
    </div>
  </div>
</body>
</html>
"""
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            html_message=html_body,
            fail_silently=True,
        )
    except Exception as e:
        print(f'[BLUESKY] Admin notify error: {e}')


def login_view(request):
    if request.session.get('user_id'):
        return redirect('welcome')
    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                if user.status == 'pending':
                    messages.error(request, 'Votre compte est en attente de validation.')
                elif user.status == 'inactive':
                    messages.error(request, 'Votre compte a été désactivé.')
                else:
                    request.session['user_id']   = user.id
                    request.session['user_role']  = user.role
                    request.session['user_name']  = user.name
                    return redirect('admin_dashboard' if user.is_admin() else 'agent_dashboard')
            else:
                messages.error(request, 'Email ou mot de passe incorrect.')
        except User.DoesNotExist:
            messages.error(request, 'Email ou mot de passe incorrect.')
    return render(request, 'auth/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')


def register_view(request):
    if request.session.get('user_id'):
        return redirect('welcome')
    countries = Country.objects.filter(is_active=True)
    if request.method == 'POST':
        name       = request.POST.get('name', '').strip()
        email      = request.POST.get('email', '').strip()
        phone      = request.POST.get('phone', '').strip()
        password   = request.POST.get('password', '')
        password2  = request.POST.get('password_confirmation', '')
        country_id = request.POST.get('country_id')

        errors = []
        if not name:     errors.append('Le nom est requis.')
        if not email:    errors.append("L'email est requis.")
        if len(password) < 8: errors.append('Le mot de passe doit contenir au moins 8 caractères.')
        if password != password2: errors.append('Les mots de passe ne correspondent pas.')
        if User.objects.filter(email=email).exists(): errors.append('Cet email est déjà utilisé.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            # Generate agent code: BSK-COUNTRYCODE-XXXX or AGT-RANDOM
            try:
                from core.models import Country as C
                country_obj = C.objects.get(pk=country_id) if country_id else None
                country_prefix = country_obj.code if country_obj else 'XX'
            except Exception:
                country_prefix = 'XX'
            code = f"BSK-{country_prefix}-{uuid.uuid4().hex[:6].upper()}"

            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10)).decode()
            user = User(
                name=name, email=email, phone=phone,
                password=hashed, role='agent', status='pending',
                agent_code=code,
                country_id=country_id if country_id else None,
            )
            user.save()

            # Handle optional photo upload
            photo_file = request.FILES.get('profile_photo')
            if photo_file:
                rel = _save_photo(photo_file, user.id)
                if rel:
                    user.profile_photo = rel
                    user.save()

            _notify_agent_pending(user)
            _notify_admin_new_registration(user)
            messages.success(request, 'Compte créé avec succès. En attente de validation par l\'administrateur.')
            return redirect('login')
    return render(request, 'auth/register.html', {'countries': countries})


def lang_switch(request, locale):
    if locale in ('fr', 'en'):
        request.session['locale'] = locale
    return redirect(request.META.get('HTTP_REFERER', '/'))


# ── Forgot password removed — admin resets passwords directly ─────────────


