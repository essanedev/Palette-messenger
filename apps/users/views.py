from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import RegisterForm, LoginForm, ProfileEditForm
from .models import User, UserContact


def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('core:dashboard')
    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            user.is_online = True
            user.save()
            return redirect('core:dashboard')
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    request.user.is_online = False
    request.user.save()
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('users:login')


@login_required
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    is_contact = UserContact.objects.filter(
        owner=request.user,
        contact=user
    ).exists() if request.user != user else False

    context = {
        'profile_user': user,
        'is_contact': is_contact,
    }
    return render(request, 'users/profile.html', context)


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен!')
            return redirect('users:profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def contacts_list(request):
    contacts = UserContact.objects.filter(owner=request.user).select_related('contact')
    return render(request, 'users/contacts.html', {'contacts': contacts})


@login_required
def search_users(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).exclude(id=request.user.id)[:20]  # Максимум 20 результатов

    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'users/search.html', context)


@login_required
def add_contact(request, username):
    contact_user = get_object_or_404(User, username=username)

    if contact_user == request.user:
        messages.error(request, 'Нельзя добавить самого себя в контакты')
        return redirect('users:profile', username=username)

    # Проверяем, не добавлен ли уже
    contact, created = UserContact.objects.get_or_create(
        owner=request.user,
        contact=contact_user
    )

    if created:
        messages.success(request, f'{contact_user.username} добавлен в контакты')
    else:
        messages.info(request, f'{contact_user.username} уже в ваших контактах')

    return redirect('users:profile', username=username)


@login_required
def remove_contact(request, username):
    contact_user = get_object_or_404(User, username=username)

    deleted_count = UserContact.objects.filter(
        owner=request.user,
        contact=contact_user
    ).delete()[0]

    if deleted_count:
        messages.success(request, f'{contact_user.username} удален из контактов')
    else:
        messages.error(request, 'Контакт не найден')

    return redirect('users:contacts')


@login_required
def block_contact(request, username):
    contact_user = get_object_or_404(User, username=username)

    try:
        contact = UserContact.objects.get(owner=request.user, contact=contact_user)
        contact.is_blocked = not contact.is_blocked
        contact.save()

        if contact.is_blocked:
            messages.success(request, f'{contact_user.username} заблокирован')
        else:
            messages.success(request, f'{contact_user.username} разблокирован')
    except UserContact.DoesNotExist:
        messages.error(request, 'Контакт не найден')

    return redirect('users:contacts')