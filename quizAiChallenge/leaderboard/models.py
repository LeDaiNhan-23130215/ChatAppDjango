from django.db import models
from django.conf import settings
# Create your models here.

class UserElo(models.Model):
    user = models.OneToOneField(
         settings.AUTH_USER_MODEL,
         on_delete=models.CASCADE,
         related_name='elo_profile'
    )
    elo = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - ELO {self.elo}"
    
class EloHistory(models.Model):
    user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    )
    elo_before = models.IntegerField()
    elo_after = models.IntegerField()
    change = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.elo_before} → {self.elo_after}"