from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class QuizTask(models.Model):
    """
    Tracks async quiz generation tasks from AI worker.
    
    Flow:
    1. Client requests quiz generation
    2. Django creates QuizTask (status='queued')
    3. Forward request to AI worker
    4. AI worker processes (takes 3-10 minutes)
    5. AI worker sends results back
    6. Django updates QuizTask (status='completed')
    7. Client polls for status or receives webhook
    """
    
    STATUS_CHOICES = [
        ('queued', 'Queued - Chờ xử lý'),
        ('processing', 'Processing - Đang xử lý'),
        ('completed', 'Completed - Hoàn tất'),
        ('failed', 'Failed - Lỗi'),
    ]

    # 🔑 Unique identifiers
    task_id = models.CharField(
        max_length=100, 
        unique=True, 
        db_index=True,
        help_text="Task ID from AI worker"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='quiz_tasks',
        help_text="User who requested the quiz"
    )
    
    # 📋 Request parameters
    quiz_size = models.IntegerField(
        default=10,
        help_text="Number of questions to generate"
    )
    declared_level = models.CharField(
        max_length=50,
        help_text="English proficiency level (Beginner, Advanced, etc.)"
    )
    profession = models.CharField(
        max_length=100, 
        blank=True,
        help_text="User's profession (engineer, teacher, student, etc.)"
    )
    goals = models.CharField(
        max_length=50,
        blank=True,
        help_text="Learning goal (job, exam, communication, etc.)"
    )
    preferred_topics = models.JSONField(
        default=list,
        help_text="List of topics user wants to practice"
    )
    weak_skills = models.JSONField(
        default=list,
        help_text="List of weak areas to focus on"
    )
    extra_instructions = models.TextField(
        blank=True,
        help_text="Additional instructions for AI to consider"
    )
    
    # 📊 Status tracking
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='queued',
        db_index=True,
        help_text="Current status of the task"
    )
    questions_created = models.IntegerField(
        default=0,
        help_text="Number of questions successfully created"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if task failed"
    )
    
    # ⏰ Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When task was created"
    )
    started_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When AI worker started processing"
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When task was completed"
    )
    
    # 🔧 Metadata
    worker_response = models.JSONField(
        default=dict,
        help_text="Full response from AI worker"
    )
    processing_time_sec = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time taken by AI worker (seconds)"
    )
    
    def __str__(self):
        return f"Task {self.task_id[:8]} - {self.user.username} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['task_id']),
        ]
        verbose_name = "Quiz Generation Task"
        verbose_name_plural = "Quiz Generation Tasks"
    
    @property
    def is_completed(self):
        """Check if task is completed successfully"""
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        """Check if task failed"""
        return self.status == 'failed'
    
    @property
    def is_pending(self):
        """Check if task is still pending"""
        return self.status in ['queued', 'processing']
    
    @property
    def duration_seconds(self):
        """Get task duration in seconds"""
        if self.completed_at:
            return int((self.completed_at - self.created_at).total_seconds())
        return None
    
    def mark_processing(self):
        """Mark task as processing"""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, questions_count=0, **kwargs):
        """Mark task as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.questions_created = questions_count
        if 'processing_time_sec' in kwargs:
            self.processing_time_sec = kwargs['processing_time_sec']
        self.save(update_fields=['status', 'completed_at', 'questions_created', 'processing_time_sec'])
    
    def mark_failed(self, error_msg=""):
        """Mark task as failed"""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_msg
        self.save(update_fields=['status', 'completed_at', 'error_message'])
