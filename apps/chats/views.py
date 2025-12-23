from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Max, F
from django.contrib import messages as django_messages
from .models import Chat, Message, ChatMembership
from apps.users.models import User


@login_required
def chats_list(request):
    user_chats = Chat.objects.filter(members=request.user).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')

    for chat in user_chats:
        chat.unread_count = chat.get_unread_count(request.user)  # ИСПРАВЛЕНО!

    context = {
        'chats': user_chats,
    }
    return render(request, 'chats/chats_list.html', context)

@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if not chat.members.filter(id=request.user.id).exists():
        django_messages.error(request, 'У вас нет доступа к этому чату')
        return redirect('chats:list')

    chat_messages = chat.messages.filter(is_deleted=False).select_related(
        'sender', 'reply_to'
    ).order_by('created_at')

    membership = ChatMembership.objects.get(chat=chat, user=request.user)
    from django.utils import timezone
    membership.last_read_at = timezone.now()
    membership.save()

    is_admin = membership.role == 'admin'

    context = {
        'chat': chat,
        'messages': chat_messages,
        'members': chat.members.all(),
        'is_admin': is_admin,
    }
    return render(request, 'chats/chat_detail.html', context)


@login_required
def create_private_chat(request, username):
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        django_messages.error(request, 'Нельзя создать чат с самим собой')
        return redirect('users:profile', username=username)

    existing_chat = Chat.objects.filter(
        chat_type='private',
        members=request.user
    ).filter(members=other_user).first()

    if existing_chat:
        return redirect('chats:detail', chat_id=existing_chat.id)

    chat = Chat.objects.create(chat_type='private')
    ChatMembership.objects.create(chat=chat, user=request.user)
    ChatMembership.objects.create(chat=chat, user=other_user)

    django_messages.success(request, f'Чат с {other_user.username} создан')
    return redirect('chats:detail', chat_id=chat.id)


@login_required
def create_group_chat(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        member_ids = request.POST.getlist('members')

        if not name:
            django_messages.error(request, 'Укажите название группы')
            return redirect('chats:list')

        chat = Chat.objects.create(
            name=name,
            description=description,
            chat_type='group'
        )

        ChatMembership.objects.create(
            chat=chat,
            user=request.user,
            role='admin'
        )

        for user_id in member_ids:
            try:
                user = User.objects.get(id=user_id)
                if user != request.user:
                    ChatMembership.objects.create(chat=chat, user=user)
            except User.DoesNotExist:
                pass

        django_messages.success(request, 'Группа создана!')
        return redirect('chats:detail', chat_id=chat.id)

    contacts = request.user.contacts.all()
    return render(request, 'chats/create_group.html', {'contacts': contacts})


@login_required
def search_groups(request):
    """Поиск групповых чатов"""
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        results = Chat.objects.filter(
            chat_type='group',
            name__icontains=query
        )[:20]

    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'chats/search_groups.html', context)


@login_required
def join_group(request, chat_id):
    """Присоединиться к группе"""
    chat = get_object_or_404(Chat, id=chat_id, chat_type='group')

    # Проверяем, не является ли уже участником
    if chat.members.filter(id=request.user.id).exists():
        django_messages.info(request, 'Вы уже участник этой группы')
        return redirect('chats:detail', chat_id=chat.id)

    # Добавляем пользователя
    ChatMembership.objects.create(chat=chat, user=request.user)
    django_messages.success(request, f'Вы присоединились к группе "{chat.name}"')
    return redirect('chats:detail', chat_id=chat.id)


@login_required
def add_member_to_group(request, chat_id):
    """Добавить участника в группу (только для админов)"""
    chat = get_object_or_404(Chat, id=chat_id, chat_type='group')

    # Проверка что пользователь - админ
    membership = ChatMembership.objects.filter(chat=chat, user=request.user).first()
    if not membership or membership.role != 'admin':
        django_messages.error(request, 'Только администраторы могут добавлять участников')
        return redirect('chats:detail', chat_id=chat.id)

    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user_to_add = User.objects.get(username=username)

            if chat.members.filter(id=user_to_add.id).exists():
                django_messages.info(request, f'{username} уже в группе')
            else:
                ChatMembership.objects.create(chat=chat, user=user_to_add)
                django_messages.success(request, f'{username} добавлен в группу')
        except User.DoesNotExist:
            django_messages.error(request, 'Пользователь не найден')

    return redirect('chats:detail', chat_id=chat.id)