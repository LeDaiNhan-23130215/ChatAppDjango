from django.db import models
from django.conf import settings
import random
import string
from common.constants import SkillCode, SkillLevel
class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('grammar', 'Grammar'),
        ('vocabulary', 'Vocabulary'),
        ('sentence_completion', 'Sentence Completion'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    text = models.TextField()
    directive = models.TextField(blank=True, null=True, help_text="e.g., 'Choose the best word/phrase to complete the sentence:'")
    a = models.TextField()
    b = models.TextField()
    c = models.TextField()
    d = models.TextField()
    correct = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
        ]
    )
    explanation = models.TextField(blank=True, null=True, help_text="Detailed explanation why the answer is correct")
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        blank=True,
        null=True
    )
    category = models.CharField(max_length=100, blank=True, null=True)
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        blank=True,
        null=True
    )
    score = models.IntegerField(default=0, help_text="Points for correct answer (0-10)")
    context = models.CharField(max_length=255, blank=True, null=True, help_text="e.g., 'coding', 'debugging', 'agile meetings'")

    def __str__(self):
        return self.text[:50]

    def as_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "directive": self.directive,
            "a": self.a,
            "b": self.b,
            "c": self.c,
            "d": self.d,
            "correct": self.correct,
            "explanation": self.explanation,
            "question_type": self.question_type,
            "difficulty": self.difficulty,
            "score": self.score,
            "context": self.context,
        }


class Room(models.Model):
    code = models.CharField(max_length=10, unique=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_rooms',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    player_count = models.IntegerField(default=0)
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Room {self.code} ({self.player_count}/2)"

    @property
    def is_full(self):
        return self.player_count >= 2

    @property
    def is_available(self):
        return not self.started and not self.is_full

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


class GameHistory(models.Model):
    """
    Lưu lịch sử các trận đấu
    """
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='histories')
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player1'
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player2'
    )
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='won_games',
        null=True,
        blank=True
    )
    # ELO tracking for player1
    player1_elo_before = models.IntegerField(null=True, blank=True, help_text="Player1 ELO before match")
    player1_elo_after = models.IntegerField(null=True, blank=True, help_text="Player1 ELO after match")
    player1_elo_change = models.IntegerField(default=0, help_text="Player1 ELO change")
    
    # ELO tracking for player2
    player2_elo_before = models.IntegerField(null=True, blank=True, help_text="Player2 ELO before match")
    player2_elo_after = models.IntegerField(null=True, blank=True, help_text="Player2 ELO after match")
    player2_elo_change = models.IntegerField(default=0, help_text="Player2 ELO change")
    
    # Elo updated flag
    elo_updated = models.BooleanField(default=False, help_text="Whether ELO has been calculated and applied")
    
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-played_at']
        verbose_name_plural = 'Game Histories'

    def __str__(self):
        return f"{self.player1.username} vs {self.player2.username} - {self.played_at}"
    
    @property
    def player1_result(self):
        """Return result for player1: 'win', 'loss', or 'draw'"""
        if self.player1_score > self.player2_score:
            return 'win'
        elif self.player1_score < self.player2_score:
            return 'loss'
        else:
            return 'draw'
    
    @property
    def player2_result(self):
        """Return result for player2: 'win', 'loss', or 'draw'"""
        if self.player2_score > self.player1_score:
            return 'win'
        elif self.player2_score < self.player1_score:
            return 'loss'
        else:
            return 'draw'
