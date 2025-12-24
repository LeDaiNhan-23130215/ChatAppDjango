from django.db import models
from django.contrib.auth.models import AbstractUser

LEVEL_CHOICES = (
    ('Beginner', 'Beginner'),
    ('Elementary', 'Elementary'),
    ('Pre-intermediate', 'Pre-intermediate'),
    ('Intermediate', 'Intermediate'),
    ('Upper-intermediate', 'Upper-intermediate'),
    ('University', 'University'),
    ('Advanced', 'Advanced'),
)

class User(AbstractUser):
    is_admin = models.BooleanField(default=False)

    birth_day = models.DateField(null=True, blank=True)
    declared_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True, blank=True)
    goals = models.TextField(null=True, blank=True)
    education = models.CharField(max_length=100, null=True, blank=True)
    profession = models.CharField(max_length=100, blank=True)
    referred_frequency = models.CharField(max_length=100, null=True, blank=True)
    motivation_level = models.PositiveSmallIntegerField(null=True, blank=True)

    def is_profile_completed(self):
        required_fields = [
            self.declared_level,
            self.goals,
            self.motivation_level
        ]
        return all(required_fields)

