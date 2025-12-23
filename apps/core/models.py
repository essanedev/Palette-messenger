from django.db import models
from django.utils import timezone

# Create your models here.

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField('Дата создания', default=timezone.now)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        abstract = True