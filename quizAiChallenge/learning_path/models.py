from django.db import models
from django.conf import settings
from entrance_test.models import EntranceTestResult
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from common.constants import SkillLevel, LearningPathItemStatus
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
    
    def get_total_items(self):
        return self.items.count()
    
    def get_completed_items(self):
        return self.items.filter(
            status = LearningPathItemStatus.COMPLETED
        ).count()
    
    def get_progress_percent(self):
        total = self.get_total_items()
        if(total == 0):
            return 0
        completed_items = self.get_completed_items()
        return int((completed_items / total) * 100)
    
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

    title = models.CharField(max_length=255)

    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    skill_code = models.CharField(max_length=50)

    level = models.CharField(
        max_length=20,
        choices=SkillLevel.choices
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    object_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )

    order = models.PositiveIntegerField()
    
    status = models.CharField(
        max_length=10,
        choices= LearningPathItemStatus.choices,
        default='LOCKED'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ['order']