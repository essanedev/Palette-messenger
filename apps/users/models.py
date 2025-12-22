from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel
from apps.chats.utils import compress_image

class User(AbstractUser):
    email = models.EmailField('Email', unique=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    bio = models.TextField('О себе', max_length=500, blank=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    is_online = models.BooleanField('Онлайн', default=False)
    last_seen = models.DateTimeField('Последний визит', null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']

    def save(self, *args, **kwargs):
        if self.avatar:
            if hasattr(self.avatar, 'file') and hasattr(self.avatar.file, 'read'):
                try:
                    if not self.pk or (self.pk and self._state.adding):
                        self.avatar = compress_image(self.avatar, max_size_mb=2, quality=90)
                        print(f"Аватарка пользователя {self.username} сжата")
                    else:
                        try:
                            old_user = User.objects.get(pk=self.pk)
                            if old_user.avatar != self.avatar:
                                self.avatar = compress_image(self.avatar, max_size_mb=2, quality=90)
                                print(f"Аватарка пользователя {self.username} обновелна")
                        except User.DoesNotExist:
                            pass
                except Exception as e:
                    print(f"Ошибка сжатия аватарки: {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def is_really_online(self):
        if not self.last_seen:
            return False
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() - self.last_seen < timedelta(minutes=5)


class UserContact(TimeStampedModel):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name='Владелец'
    )
    contact = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='added_by',
        verbose_name='Контакт'
    )
    nickname = models.CharField('Никнейм', max_length=100, blank=True)
    is_blocked = models.BooleanField('Заблокирован', default=False)

    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        unique_together = ('owner', 'contact')
        ordering = ['contact__username']

    def __str__(self):
        return f"{self.owner.username} -> {self.contact.username}"