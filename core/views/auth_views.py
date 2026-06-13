import os, uuid, random, string
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.cache import cache
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

            messages.success(request, 'Compte créé avec succès. En attente de validation par l\'administrateur.')
            return redirect('login')
    return render(request, 'auth/register.html', {'countries': countries})


def lang_switch(request, locale):
    if locale in ('fr', 'en'):
        request.session['locale'] = locale
    return redirect(request.META.get('HTTP_REFERER', '/'))


# ── Forgot password ────────────────────────────────────────────────────────

def _generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))


def _send_otp_email(email: str, otp: str, user_name: str) -> bool:
    subject = f'🔐 Votre code de vérification BLUESKY — {otp}'
    body = f"""Bonjour {user_name},

Vous avez demandé la réinitialisation de votre mot de passe BLUESKY.

Votre code OTP : {otp}

Ce code est valable 10 minutes. Ne le partagez avec personne.

Si vous n'avez pas fait cette demande, ignorez cet email.

— L'équipe BLUESKY Transactions
"""
    html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Inter,sans-serif;background:#f0f4f8;padding:30px 20px;margin:0;">
  <div style="max-width:480px;margin:0 auto;background:white;border-radius:16px;overflow:hidden;box-shadow:0 8px 40px rgba(0,0,0,.12);">
    <div style="background:linear-gradient(135deg,#0099e6,#0052b2);padding:28px 32px;text-align:center;">
      <div style="font-size:36px;margin-bottom:8px;">🔐</div>
      <div style="color:white;font-size:20px;font-weight:900;letter-spacing:.5px;">BLUESKY TRANSACTIONS</div>
      <div style="color:rgba(255,255,255,.7);font-size:13px;margin-top:4px;">Réinitialisation du mot de passe</div>
    </div>
    <div style="padding:32px;">
      <p style="color:#334155;font-size:15px;margin:0 0 20px;">Bonjour <strong>{user_name}</strong>,</p>
      <p style="color:#64748b;font-size:14px;margin:0 0 24px;line-height:1.6;">
        Vous avez demandé la réinitialisation de votre mot de passe.<br>
        Utilisez le code ci-dessous pour continuer.
      </p>

      <div style="background:#f0f9ff;border:2px dashed #0284c7;border-radius:12px;padding:24px;text-align:center;margin-bottom:24px;">
        <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">Votre code OTP</div>
        <div style="font-size:42px;font-weight:900;color:#0284c7;letter-spacing:10px;font-family:monospace;">{otp}</div>
        <div style="font-size:12px;color:#94a3b8;margin-top:10px;">⏱ Valable 10 minutes</div>
      </div>

      <div style="background:#fef9c3;border-radius:8px;padding:12px 16px;margin-bottom:20px;">
        <p style="margin:0;font-size:12.5px;color:#92400e;">⚠️ Ne partagez jamais ce code. L'équipe BLUESKY ne vous le demandera jamais.</p>
      </div>

      <p style="color:#94a3b8;font-size:12px;text-align:center;margin:0;">
        Si vous n'avez pas fait cette demande, ignorez cet email.
      </p>
    </div>
    <div style="background:#f8fafc;border-top:1px solid #e8edf2;padding:16px;text-align:center;">
      <p style="margin:0;font-size:11px;color:#94a3b8;">© 2025 BLUESKY Transactions — Tous droits réservés</p>
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
            recipient_list=[email],
            html_message=html_body,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'[BLUESKY] Email error: {e}')
        return False


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists — same message either way
            messages.success(request, 'Si cet email existe, un code vous a été envoyé.')
            return redirect('forgot_password')

        otp = _generate_otp()
        cache.set(f'otp:{email}', otp, timeout=settings.OTP_EXPIRY_SECONDS)
        cache.delete(f'otp_verified:{email}')   # reset any old verified state

        sent = _send_otp_email(email, otp, user.name)
        if sent:
            request.session['otp_email'] = email
            messages.success(request, f'Code envoyé à {email}. Vérifiez votre boîte mail.')
            return redirect('verify_otp')
        else:
            messages.error(request, 'Erreur d\'envoi email. Vérifiez la configuration SMTP.')

    return render(request, 'auth/forgot_password.html')


def verify_otp(request):
    email = request.session.get('otp_email')
    if not email:
        return redirect('forgot_password')

    if request.method == 'POST':
        entered = ''.join(request.POST.get('otp', '').strip().split())
        stored  = cache.get(f'otp:{email}')

        if not stored:
            messages.error(request, 'Code expiré. Veuillez recommencer.')
            return redirect('forgot_password')

        if entered != stored:
            messages.error(request, 'Code incorrect. Réessayez.')
            return render(request, 'auth/verify_otp.html', {'email': email})

        # OTP correct — mark as verified, delete OTP
        cache.delete(f'otp:{email}')
        cache.set(f'otp_verified:{email}', True, timeout=300)  # 5 min to reset pw
        return redirect('reset_password')

    return render(request, 'auth/verify_otp.html', {'email': email})


def resend_otp(request):
    email = request.session.get('otp_email')
    if not email:
        return redirect('forgot_password')
    try:
        user = User.objects.get(email=email)
        otp  = _generate_otp()
        cache.set(f'otp:{email}', otp, timeout=settings.OTP_EXPIRY_SECONDS)
        _send_otp_email(email, otp, user.name)
        messages.success(request, 'Nouveau code envoyé.')
    except User.DoesNotExist:
        pass
    return redirect('verify_otp')


def reset_password(request):
    email = request.session.get('otp_email')
    if not email or not cache.get(f'otp_verified:{email}'):
        messages.error(request, 'Session expirée. Recommencez.')
        return redirect('forgot_password')

    if request.method == 'POST':
        pw1 = request.POST.get('password', '')
        pw2 = request.POST.get('password_confirmation', '')

        if len(pw1) < 8:
            messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères.')
        elif pw1 != pw2:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
        else:
            try:
                user = User.objects.get(email=email)
                user.password = bcrypt.hashpw(pw1.encode(), bcrypt.gensalt(10)).decode()
                user.save()
                cache.delete(f'otp_verified:{email}')
                del request.session['otp_email']
                messages.success(request, 'Mot de passe modifié avec succès. Connectez-vous.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'Utilisateur introuvable.')
                return redirect('forgot_password')

    return render(request, 'auth/reset_password.html', {'email': email})
