from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Question(models.Model):
    content = models.TextField()

    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    correct_answer = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
        ]
    )

    def __str__(self):
        return self.content[:50]
    
class Match(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    user_score = models.IntegerField(default=0)
    ai_score = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Match #{self.id} - {self.user.username}"

class Round(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    user_answer = models.CharField(
        max_length=1,
        null=True,
        blank=True
    )

    ai_answer = models.CharField(
        max_length=1,
        null=True,
        blank=True
    )

    user_correct = models.BooleanField(null=True)
    ai_correct = models.BooleanField(null=True)

    def __str__(self):
        return f"Round #{self.id} - Match #{self.match.id}"

