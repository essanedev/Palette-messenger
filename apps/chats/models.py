from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel

# Create your models here.

class Chat(TimeStampedModel):
    CHAT_TYPES = (
        ('private', 'Личный'),
        ('group', 'Группа'),
    )

    name = models.CharField('Название', max_length=255, blank=True)
    chat_type = models.CharField('Тип чата', max_length=10, choices=CHAT_TYPES)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ChatMembership',
        related_name='chats',
        verbose_name='Участники'
    )
    avatar = models.ImageField('Аватар группы', upload_to='chat_avatars/', blank=True, null=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'
        ordering = ['-updated_at']

    def __str__(self):
        if self.chat_type == 'private':
            members = list(self.members.all()[:2])
            return f"Чат: {' - '.join([m.username for m in members])}"
        return self.name or f"Группа #{self.id}"

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def get_unread_count(self, user):
        try:
            membership = self.chatmembership_set.get(user=user)
            if membership.last_read_at:
                return self.messages.filter(
                    created_at__gt=membership.last_read_at,
                    is_deleted=False
                ).exclude(sender=user).count()
            else:
                return self.messages.filter(is_deleted=False).exclude(sender=user).count()
        except ChatMembership.DoesNotExist:
            return 0

class ChatMembership(TimeStampedModel):
    ROLES = (
        ('admin', 'Администратор'),
        ('member', 'Участник'),
    )

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, verbose_name='Чат')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    role = models.CharField('Роль', max_length=10, choices=ROLES, default='member')
    is_muted = models.BooleanField('Звук выключен', default=False)
    last_read_at = models.DateTimeField('Последнее прочтение', null=True, blank=True)

    class Meta:
        verbose_name = 'Участник чата'
        verbose_name_plural = 'Участники чатов'
        unique_together = ('chat', 'user')

    def __str__(self):
        return f"{self.user.username} в {self.chat}"


class Message(TimeStampedModel):
    MESSAGE_TYPES = (
        ('text', 'Текст'),
        ('image', 'Изображение'),
        ('file', 'Файл'),
        ('voice', 'Голосовое'),
    )

    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Чат'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Отправитель'
    )
    message_type = models.CharField(
        'Тип сообщения',
        max_length=10,
        choices=MESSAGE_TYPES,
        default='text'
    )
    content = models.TextField('Содержание', blank=True)
    file = models.FileField('Файл', upload_to='messages/', blank=True, null=True)
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='Ответ на'
    )
    is_edited = models.BooleanField('Отредактировано', default=False)
    is_deleted = models.BooleanField('Удалено', default=False)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class MessageReadStatus(TimeStampedModel):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_statuses',
        verbose_name='Сообщение'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    read_at = models.DateTimeField('Прочитано', auto_now_add=True)

    class Meta:
        verbose_name = 'Статус прочтения'
        verbose_name_plural = 'Статусы прочтения'
        unique_together = ('message', 'user')

    def __str__(self):
        return f"{self.user.username} прочитал(а) сообщение #{self.message.id}"