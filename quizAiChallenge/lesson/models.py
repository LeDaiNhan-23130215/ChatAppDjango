from django.db import models

class Lesson(models.Model):
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

    title = models.CharField(max_length=255)

    skill_code = models.CharField(
        max_length=50,
        choices=SKILL_CHOICES
    )

    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES
    )

    description = models.TextField(blank=True)

    content = models.TextField()

    estimated_time = models.PositiveIntegerField(
        help_text="Minutes"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

