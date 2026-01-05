from django.db import models
from django.conf import settings
import random
import string
from common.constants import SkillCode, SkillLevel
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
    QUIZ_TYPE_CHOICES = [
        ('PRACTICE', 'Practice'),
        ('QUIZ', 'Quiz'),
        ('MOCK', 'Mock Test'),
    ]

    title = models.CharField(max_length=255)

    skill_code = models.CharField(
        max_length=50,
        choices=SkillCode.choices
    )

    level = models.CharField(
        max_length=20,
        choices=SkillLevel.choices
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

    @property
    def total_questions(self):
        return self.questions_for_quiz.count()

class QuestionForQuiz(models.Model):
    quiz = models.ForeignKey(Quiz, related_name="questions_for_quiz", on_delete=models.CASCADE)
    content = models.TextField()
    passage = models.TextField(blank=True, null=True)  # nếu có đoạn văn đi kèm
    image = models.ImageField(upload_to="quiz_images/", blank=True, null=True)

    def __str__(self):
        return f"Question {self.id} for {self.quiz.title}"


class Choice(models.Model):
    question = models.ForeignKey(QuestionForQuiz, related_name="choices", on_delete=models.CASCADE)
    content = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Choice {self.id} for Question {self.question.id}"

class QuizResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    percent = models.FloatField()
    passed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.quiz.title} ({'Passed' if self.passed else 'Failed'})"
