from django.conf import settings
from django.db import models
# Create your models here.
class EntranceTest(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    PART_CHOICES = [
        (1, 'Part 1 - Picture'),
        (2, 'Part 2 - Question & Response'),
        (3, 'Part 3 - Conversation'),
        (4, 'Part 4 - Short Talk'),
        (5, 'Part 5 - Incomplete Sentences'),
        (6, 'Part 6 - Text Completion'),
        (7, 'Part 7 - Reading'),
    ]

    test = models.ForeignKey(
        EntranceTest,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    part = models.IntegerField(choices=PART_CHOICES)
    content = models.TextField()

    def __str__(self):
        return f'Part {self.part}: {self.content[:50]}'

class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    content = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['question'],
                condition=models.Q(is_correct=True),
                name='only_one_correct_choice'
            )
        ]
    
class EntranceTestResult(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    test = models.ForeignKey(EntranceTest, on_delete=models.CASCADE)
    score = models.IntegerField()
    correct_answers = models.IntegerField()
    total_questions = models.IntegerField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'test')

class UserAnswer(models.Model):
    result = models.ForeignKey(
        EntranceTestResult,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE
    )

    def is_correct(self):
        return self.selected_choice.is_correct