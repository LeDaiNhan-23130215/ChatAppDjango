from django.db import models
from django.conf import settings
from entrance_test.models import EntranceTestResult
# Create your models here.
class LearningPath(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    created_from_result = models.ForeignKey(
        EntranceTestResult,
        on_delete=models.SET_NULL,
        null=True
    )

    target_score = models.IntegerField(default=600)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Learning Path - {self.user}'
    
class LearningPathItem(models.Model):
    TYPE_CHOICES = [
        ('LESSON', 'Lesson'),
        ('PRACTICE', 'Practice'),
        ('QUIZ', 'Quiz'),
        ('MOCK', 'Mock Test'),
    ]

    path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name='items'
    )

    skill_code = models.CharField(max_length=50)
    # VD: LISTENING_PICTURE

    level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ]
    )

    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()

    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']