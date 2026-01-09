from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# Create your models here.
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Vocabulary(models.Model):
    term = models.CharField(max_length=255)
    language = models.CharField(max_length=20, default='en')
    part_of_speech = models.CharField(max_length=50, blank=True)
    definition = models.TextField(blank=True)
    example = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='vocabularies')

    def __str__(self):
        return f"{self.term} ({self.language})"

class Minigame(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Question(models.Model):
    minigame = models.ForeignKey(Minigame, on_delete=models.CASCADE)
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    prompt = models.CharField(max_length=255)
    difficulty = models.IntegerField(default=1)
    type = models.CharField(max_length=50)
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.prompt

class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    source = models.CharField(max_length=50)

    def __str__(self):
        return f"{'✓' if self.is_correct else ' '} {self.text}"

class GameSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    minigame = models.ForeignKey(Minigame, on_delete=models.CASCADE)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user} - {self.minigame}"

class Attempt(models.Model):
    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(
        Choice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    is_correct = models.BooleanField(default=False)
    responded_at = models.DateTimeField(auto_now_add=True)
    time_ms = models.IntegerField(default=0)