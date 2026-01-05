from django.db import models
from django.conf import settings
from entrance_test.models import EntranceTestResult
from common.constants import SkillCode, SkillLevel
# Create your models here.
class UserSkillProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skill_profiles'
    )

    result = models.ForeignKey(
        EntranceTestResult,
        on_delete=models.CASCADE,
        related_name='skill_profiles'
    )

    skill = models.CharField(
        max_length=50,
        choices=SkillCode.choices,
        help_text="TOEIC skill or part, e.g. PART_1_LISTENING"
    )

    section = models.CharField(
        max_length=20,
        choices=[
            ('LISTENING', 'Listening'),
            ('READING', 'Reading'),
        ]
    )

    accuracy = models.FloatField(
        help_text="Correct rate from 0.0 to 1.0"
    )

    level = models.CharField(
        max_length=20,
        choices=SkillLevel.choices
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'result', 'skill')
    