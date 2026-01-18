from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserElo

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_elo(sender, instance, created, **kwargs):
    if created:
        UserElo.objects.create(user = instance)