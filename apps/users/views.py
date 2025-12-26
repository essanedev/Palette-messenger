# user/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count

from . import models
from .forms import RegisterForm, LoginForm, ProfileEditForm
from .models import User, UserContact, Tag
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from ..chats.models import Chat


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
            from django.utils import timezone
            user.last_seen = timezone.now()
            user.save()
            return redirect('core:dashboard')
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    request.user.is_online = False
    from django.utils import timezone
    request.user.last_seen = timezone.now()
    request.user.save()
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('users:login')


@login_required
def discover(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'users')

    context = {
        'query': query,
        'search_type': search_type,
        'users_results': [],
        'groups_results': [],
        'tags_results': [],
    }

    if query:
        if search_type == 'users':
            context['users_results'] = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            ).exclude(id=request.user.id)[:20]

        elif search_type == 'groups':
            context['groups_results'] = Chat.objects.filter(
                chat_type='group',
                name__icontains=query
            ).annotate(
                member_count=Count('members')
            )[:20]

        elif search_type == 'tags':
            tag_name = query.lower().strip().replace('#', '')

            try:
                tag = Tag.objects.get(name__iexact=tag_name)
            except Tag.DoesNotExist:
                tag = None

            if tag:
                groups_with_tag = Chat.objects.filter(
                    chat_type='group',
                    tags=tag
                ).annotate(
                    member_count=Count('members')
                )

                users_with_tag = User.objects.filter(
                    tags=tag
                ).exclude(id=request.user.id)

                context['groups_results'] = groups_with_tag
                context['users_results'] = users_with_tag
                context['tag'] = tag
            else:
                similar_tags = Tag.objects.filter(
                    name__icontains=tag_name
                )[:5]
                context['similar_tags'] = similar_tags

    return render(request, 'users/discover.html', context)


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
            user = form.save()

            tags_str = request.POST.get('tags_input', '')

            tag_names = [t.strip().lstrip('#') for t in tags_str.split() if t.strip()]

            tag_objs = []
            for name in tag_names:
                tag, created = Tag.objects.get_or_create(name=name)
                tag_objs.append(tag)

            user.tags.set(tag_objs)

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
def manage_tags(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            tag_name = request.POST.get('tag_name', '').strip().lower().replace('#', '')
            if tag_name:
                if len(tag_name) > 50:
                    messages.error(request, 'Тег слишком длинный (максимум 50 символов)')
                else:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    request.user.tags.add(tag)
                    messages.success(request, f'Тег #{tag_name} добавлен')
            else:
                messages.error(request, 'Введите название тега')

        elif action == 'remove':
            tag_id = request.POST.get('tag_id')
            try:
                tag = Tag.objects.get(id=tag_id)
                request.user.tags.remove(tag)
                messages.success(request, f'Тег #{tag.name} удален')
            except Tag.DoesNotExist:
                messages.error(request, 'Тег не найден')

        return redirect('users:manage_tags')

    user_tags = request.user.tags.all()
    popular_tags = Tag.objects.annotate(
        usage_count=models.Count('users') + models.Count('chats')
    ).order_by('-usage_count')[:10]

    return render(request, 'users/manage_tags.html', {
        'user_tags': user_tags,
        'popular_tags': popular_tags,
    })


@login_required
def add_contact(request, username):
    contact_user = get_object_or_404(User, username=username)

    if contact_user == request.user:
        messages.error(request, 'Нельзя добавить самого себя в контакты')
        return redirect('users:profile', username=username)

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


@require_GET
@login_required
def autocomplete_users(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        qs = User.objects.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        ).exclude(id=request.user.id)[:10]
        for u in qs:
            results.append({
                'username': u.username,
                'full_name': (u.get_full_name() or ''),
                'avatar': (u.avatar.url if getattr(u, 'avatar', None) else '')
            })
    return JsonResponse({'results': results})
