from django.db import models
from django.conf import settings
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
    AI_MODES = [
        ("random", "Random AI"),
        ("gpt", "GPT AI"),
    ]

    AI_DIFFICULTY = [
        ("easy", "Dễ"),
        ("medium", "Trung bình"),
        ("hard", "Khó"),
        ("expert", "Chuyên gia"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    ai_mode = models.CharField(
        max_length=10,
        choices=AI_MODES,
        default="random"
    )

    ai_difficulty = models.CharField(
        max_length=10,
        choices=AI_DIFFICULTY,
        default="medium"
    )

    user_score = models.IntegerField(default=0)
    ai_score = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    
    # ✨ NEW: ELO tracking
    elo_change = models.IntegerField(default=0, help_text="ELO points gained/lost in this match")
    elo_before = models.IntegerField(null=True, blank=True, help_text="User ELO before match")
    elo_after = models.IntegerField(null=True, blank=True, help_text="User ELO after match")

    def __str__(self):
        return f"Match #{self.id} - {self.user.username} ({self.ai_mode}, {self.ai_difficulty})"
    
    @property
    def result(self):
        """Return match result: 'win', 'loss', or 'draw'"""
        if self.user_score > self.ai_score:
            return 'win'
        elif self.user_score < self.ai_score:
            return 'loss'
        else:
            return 'draw'

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