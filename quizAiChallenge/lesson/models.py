from django.db import models
from common.constants import SkillCode, SkillLevel
class Lesson(models.Model):
    title = models.CharField(max_length=255)

    skill_code = models.CharField(
        max_length=50,
        choices=SkillCode.choices
    )

    level = models.CharField(
        max_length=20,
        choices=SkillLevel.choices
    )

    description = models.TextField(blank=True)

    content = models.TextField()

    estimated_time = models.PositiveIntegerField(
        help_text="Minutes"
    )

    order = models.PositiveIntegerField(default=1)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

