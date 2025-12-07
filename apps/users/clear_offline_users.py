from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User


class Command(BaseCommand):
    help = 'Помечает неактивных пользователей как оффлайн'

    def handle(self, *args, **kwargs):
        threshold = timezone.now() - timedelta(minutes=5)
        updated = User.objects.filter(
            is_online=True,
            last_seen__lt=threshold
        ).update(is_online=False)

        self.stdout.write(
            self.style.SUCCESS(f'Помечено как оффлайн: {updated} пользователей')
        )