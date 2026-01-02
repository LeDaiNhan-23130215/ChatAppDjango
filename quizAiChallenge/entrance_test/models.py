from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
# Create your models here.
class EntranceTest(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class QuestionImage(models.Model):
    image = models.ImageField(upload_to='toeic_image/')
    description = models.TextField(blank=True)

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

    passage = models.TextField(
        blank=True,
        null=True,
        help_text= "Conversation / Short talk / Reading passage"
    )

    image = models.ForeignKey(
        QuestionImage,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    content = models.TextField()

    def __str__(self):
        return f'Part {self.part}: {self.content[:50]}'
    
    def clean(self):
        if self.part == 1 and not self.image:
            raise ValidationError("Part 1 requires an image")

        if self.part in [3, 4, 6, 7] and not self.passage:
            raise ValidationError("This part requires a passage")
        
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
                fields=['question', 'is_correct'],
                condition=models.Q(is_correct=True),
                name='only_one_correct_choice_per_question'
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
        ordering = ['-taken_at']

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
    
    class Meta:
        unique_together = ('result', 'question')