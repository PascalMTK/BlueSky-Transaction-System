import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from core.decorators import login_required, get_auth_user
from core.translations import localized
import bcrypt
from PIL import Image, ImageOps

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_PHOTO_SIZE     = 5 * 1024 * 1024  # 5 MB
MAX_PHOTO_DIMENSION = 640  # px, longest side — plenty for any avatar display size


def _normalize_photo(absolute_path, ext):
    """Fix phone-camera EXIF rotation and downscale oversized uploads so
    avatars are sharp and consistently sized everywhere. Animated GIFs are
    left untouched since resaving would flatten them to a single frame."""
    if ext == '.gif':
        return
    with Image.open(absolute_path) as img:
        img = ImageOps.exif_transpose(img)
        img.thumbnail((MAX_PHOTO_DIMENSION, MAX_PHOTO_DIMENSION), Image.LANCZOS)
        if ext in ('.jpg', '.jpeg') and img.mode != 'RGB':
            img = img.convert('RGB')
        save_kwargs = {'optimize': True}
        if ext in ('.jpg', '.jpeg'):
            save_kwargs['quality'] = 85
        img.save(absolute_path, **save_kwargs)


@login_required
def profile_show(request):
    user = get_auth_user(request)
    return render(request, 'profile/show.html', {'auth_user': user})


@login_required
def profile_update(request):
    if request.method == 'POST':
        user         = get_auth_user(request)
        user.name    = request.POST.get('name', user.name).strip() or user.name
        user.phone   = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.save()
        request.session['user_name'] = user.name
        messages.success(request, localized(request, 'Profil mis à jour avec succès.', 'Profile updated successfully.'))
    return redirect('profile_show')


def save_profile_photo(user, photo):
    """Validate, save, and normalize an uploaded profile photo for the given
    user. Returns an error message string on failure, or None on success —
    shared by the agent's own profile page and the admin's agent-edit page."""
    if not photo:
        return 'Aucun fichier sélectionné.'

    ext = os.path.splitext(photo.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f'Format non supporté ({ext}). Utilisez JPEG, PNG ou WebP.'

    if photo.size > MAX_PHOTO_SIZE:
        return f'Photo trop volumineuse ({photo.size // 1024} Ko). Maximum 5 Mo.'

    relative_path = f"profiles/{user.id}{ext}"
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
    os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

    # Delete old photo if different extension (avoid orphan files)
    if user.profile_photo and user.profile_photo != relative_path:
        old_path = os.path.join(settings.MEDIA_ROOT, user.profile_photo)
        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass

    try:
        with open(absolute_path, 'wb+') as dest:
            for chunk in photo.chunks():
                dest.write(chunk)
        _normalize_photo(absolute_path, ext)
    except OSError as e:
        return f'Erreur lors de la sauvegarde : {e}'

    user.profile_photo = relative_path
    user.save()
    return None


@login_required
def profile_photo(request):
    if request.method != 'POST':
        return redirect('profile_show')

    user  = get_auth_user(request)
    error = save_profile_photo(user, request.FILES.get('photo'))
    if error:
        messages.error(request, error)
    else:
        messages.success(request, localized(request, 'Photo de profil mise à jour.', 'Profile photo updated.'))
    return redirect('profile_show')


@login_required
def profile_password(request):
    if request.method == 'POST':
        user    = get_auth_user(request)
        current = request.POST.get('current_password', '')
        new_pw  = request.POST.get('password', '')
        confirm = request.POST.get('password_confirmation', '')

        if not user.check_password(current):
            messages.error(request, localized(request, 'Mot de passe actuel incorrect.', 'Current password is incorrect.'))
        elif len(new_pw) < 8:
            messages.error(request, localized(request, 'Le nouveau mot de passe doit contenir au moins 8 caractères.', 'The new password must be at least 8 characters long.'))
        elif new_pw != confirm:
            messages.error(request, localized(request, 'Les mots de passe ne correspondent pas.', 'Passwords do not match.'))
        else:
            hashed = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt(10)).decode()
            user.password = hashed
            user.save()
            messages.success(request, localized(request, 'Mot de passe modifié avec succès.', 'Password changed successfully.'))

    return redirect('profile_show')
