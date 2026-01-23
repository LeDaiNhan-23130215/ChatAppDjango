from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import QuizTask


@admin.register(QuizTask)
class QuizTaskAdmin(admin.ModelAdmin):
    """Admin interface for QuizTask"""
    
    list_display = [
        'task_id_short',
        'user',
        'quiz_size',
        'status_badge',
        'questions_created',
        'duration_display',
        'created_at_short',
    ]
    
    list_filter = [
        'status',
        'created_at',
        'declared_level',
    ]
    
    search_fields = [
        'task_id',
        'user__username',
        'user__email',
    ]
    
    readonly_fields = [
        'task_id',
        'created_at',
        'started_at',
        'completed_at',
        'worker_response_display',
        'duration_seconds',
    ]
    
    fieldsets = (
        ('Task Info', {
            'fields': ('task_id', 'user', 'status')
        }),
        ('Request Parameters', {
            'fields': (
                'quiz_size',
                'declared_level',
                'goals',
                'profession',
                'preferred_topics',
                'weak_skills',
                'extra_instructions',
            )
        }),
        ('Status & Results', {
            'fields': (
                'questions_created',
                'error_message',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at', 'duration_seconds'),
            'classes': ('collapse',)
        }),
        ('Worker Response', {
            'fields': ('worker_response_display', 'processing_time_sec'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    def task_id_short(self, obj):
        """Display shortened task ID"""
        return f"{obj.task_id[:12]}..."
    task_id_short.short_description = "Task ID"
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'queued': '#FFA500',      # Orange
            'processing': '#4169E1',  # Blue
            'completed': '#00AA00',   # Green
            'failed': '#FF0000',      # Red
        }
        color = colors.get(obj.status, '#808080')  # Gray default
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = "Status"
    
    def duration_display(self, obj):
        """Display duration in human-readable format"""
        if obj.duration_seconds is None:
            return "—"
        minutes = obj.duration_seconds / 60
        if minutes < 1:
            return f"{obj.duration_seconds}s"
        return f"{minutes:.1f}m"
    duration_display.short_description = "Duration"
    
    def created_at_short(self, obj):
        """Display created_at in short format"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_short.short_description = "Created"
    
    def worker_response_display(self, obj):
        """Display worker response as formatted JSON"""
        import json
        if not obj.worker_response:
            return "—"
        try:
            return format_html(
                '<pre style="background: #f5f5f5; padding: 10px; '
                'border-radius: 3px; overflow-x: auto;">{}</pre>',
                json.dumps(obj.worker_response, indent=2, ensure_ascii=False)
            )
        except:
            return str(obj.worker_response)
    worker_response_display.short_description = "Worker Response"
    
    def has_delete_permission(self, request):
        """Prevent deletion to maintain audit trail"""
        return request.user.is_superuser
