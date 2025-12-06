from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel

# Create your models here.
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

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


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