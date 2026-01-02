from django.db import models
import random
import string

class Question(models.Model):
    text = models.CharField(max_length=300)
    a = models.CharField(max_length=200)
    b = models.CharField(max_length=200)
    c = models.CharField(max_length=200)
    d = models.CharField(max_length=200)
    correct = models.CharField(max_length=1)  # 'A', 'B', 'C', 'D'

    def as_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "a": self.a,
            "b": self.b,
            "c": self.c,
            "d": self.d,
        }


class Room(models.Model):
    code = models.CharField(max_length=6, unique=True)
    player_count = models.IntegerField(default=0)
    started = models.BooleanField(default=False)

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.ascii_uppercase, k=6))

class Quiz(models.Model):
    SKILL_CHOICES = [
    ('LISTENING_PICTURE', 'Listening – Picture'),
    ('LISTENING_QA', 'Listening – Question & Answer'),
    ('LISTENING_CONVERSATION', 'Listening – Conversation'),
    ('LISTENING_INFORMATION', 'Listening – Information'),
    ('READING_SENTENCE', 'Reading – Sentence Completion'),
    ('READING_TEXT', 'Reading – Text Completion'),
    ('READING_PASSAGE', 'Reading – Reading Comprehension'),
    ]

    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    QUIZ_TYPE_CHOICES = [
        ('PRACTICE', 'Practice'),
        ('QUIZ', 'Quiz'),
        ('MOCK', 'Mock Test'),
    ]

    title = models.CharField(max_length=255)

    skill_code = models.CharField(
        max_length=50,
        choices=SKILL_CHOICES
    )

    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES
    )

    quiz_type = models.CharField(
        max_length=20,
        choices=QUIZ_TYPE_CHOICES
    )

    time_limit = models.PositiveIntegerField(
        help_text="Seconds",
        null=True,
        blank=True
    )

    total_questions = models.PositiveIntegerField()

    pass_score = models.PositiveIntegerField(default=70)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
