from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Max, F
from django.contrib import messages as django_messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Chat, Message, ChatMembership
from .utils import compress_image, validate_file_size, get_file_type, get_readable_size
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)


@login_required
def chats_list(request):
    user_chats = Chat.objects.filter(members=request.user).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')

    for chat in user_chats:
        chat.unread_count = chat.get_unread_count(request.user)

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
    chat = get_object_or_404(Chat, id=chat_id, chat_type='group')

    if chat.members.filter(id=request.user.id).exists():
        django_messages.info(request, 'Вы уже участник этой группы')
        return redirect('chats:detail', chat_id=chat.id)

    ChatMembership.objects.create(chat=chat, user=request.user)
    django_messages.success(request, f'Вы присоединились к группе "{chat.name}"')
    return redirect('chats:detail', chat_id=chat.id)


@login_required
def add_member_to_group(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, chat_type='group')

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


@login_required
@require_POST
def upload_file(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if not chat.members.filter(id=request.user.id).exists():
        return JsonResponse({'error': 'Нет доступа к этому чату'}, status=403)

    if 'file' not in request.FILES:
        return JsonResponse({'error': 'Файл не найден'}, status=400)

    file = request.FILES['file']
    original_size = file.size
    file_type = get_file_type(file.name)

    logger.info(f"Загрузка файла: {file.name} ({get_readable_size(original_size)}) от {request.user.username}")

    if file_type == 'image':
        valid, error_msg = validate_file_size(file, 15)  # 15MB для фото
        if not valid:
            logger.warning(f"Файл отклонен (размер): {error_msg}")
            return JsonResponse({'error': error_msg}, status=400)

        try:
            file = compress_image(file, max_size_mb=15, quality=85)
            logger.info(f"✓ Изображение сжато: {get_readable_size(file.size)}")
        except Exception as e:
            logger.error(f"Ошибка сжатия изображения: {e}")
            return JsonResponse({'error': 'Ошибка обработки изображения'}, status=500)

        message_type = 'image'

    elif file_type == 'video':
        valid, error_msg = validate_file_size(file, 100)  # 100MB для видео
        if not valid:
            logger.warning(f"Видео отклонено (размер): {error_msg}")
            return JsonResponse({'error': error_msg}, status=400)
        message_type = 'file'
        logger.info(f"Видео принято: {get_readable_size(file.size)}")

    elif file_type == 'voice':
        valid, error_msg = validate_file_size(file, 10)  # 10MB для аудио
        if not valid:
            logger.warning(f"Аудио отклонено (размер): {error_msg}")
            return JsonResponse({'error': error_msg}, status=400)
        message_type = 'voice'

    else:
        valid, error_msg = validate_file_size(file, 50)  # 50MB для других файлов
        if not valid:
            logger.warning(f"Файл отклонен (размер): {error_msg}")
            return JsonResponse({'error': error_msg}, status=400)
        message_type = 'file'

    try:
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            message_type=message_type,
            file=file,
            content=f"Отправил(а) {file.name}"
        )
        logger.info(f"Файл сохранен в БД: message_id={message.id}")
    except Exception as e:
        logger.error(f"Ошибка сохранения сообщения: {e}")
        return JsonResponse({'error': 'Ошибка сохранения файла'}, status=500)

    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{chat_id}',
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'sender': message.sender.username,
                    'content': message.content,
                    'file_url': message.file.url if message.file else None,
                    'message_type': message.message_type,
                    'created_at': message.created_at.isoformat(),
                }
            }
        )
    except Exception as e:
        logger.error(f"Ошибка отправки через WebSocket: {e}")

    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'sender': message.sender.username,
            'content': message.content,
            'file_url': message.file.url if message.file else None,
            'message_type': message.message_type,
            'created_at': message.created_at.isoformat(),
        }
    })


@login_required
@require_POST
def upload_voice(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if not chat.members.filter(id=request.user.id).exists():
        return JsonResponse({'error': 'Нет доступа к этому чату'}, status=403)

    if 'audio' not in request.FILES:
        return JsonResponse({'error': 'Аудио файл не найден'}, status=400)

    audio_file = request.FILES['audio']
    is_video = request.POST.get('is_video', 'false') == 'true'

    original_size = audio_file.size
    logger.info(
        f"Загрузка {'видео' if is_video else 'аудио'}сообщения: {get_readable_size(original_size)} от {request.user.username}")

    max_size = 50 if is_video else 10  # 50MB для видео, 10MB для аудио
    valid, error_msg = validate_file_size(audio_file, max_size)
    if not valid:
        logger.warning(f"Голосовое сообщение отклонено: {error_msg}")
        return JsonResponse({'error': error_msg}, status=400)

    try:
        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            message_type='voice',
            file=audio_file,
            content=f"{'Видео' if is_video else 'Голосовое'} сообщение"
        )
        logger.info(f"Голосовое сообщение сохранено: message_id={message.id}")
    except Exception as e:
        logger.error(f"Ошибка сохранения голосового сообщения: {e}")
        return JsonResponse({'error': 'Ошибка сохранения аудио'}, status=500)

    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{chat_id}',
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'sender': message.sender.username,
                    'content': message.content,
                    'file_url': message.file.url,
                    'message_type': message.message_type,
                    'created_at': message.created_at.isoformat(),
                }
            }
        )
    except Exception as e:
        logger.error(f"Ошибка отправки через WebSocket: {e}")

    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'sender': message.sender.username,
            'content': message.content,
            'file_url': message.file.url,
            'message_type': message.message_type,
            'created_at': message.created_at.isoformat(),
        }
    })
