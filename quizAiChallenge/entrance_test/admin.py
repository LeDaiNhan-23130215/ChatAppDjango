from django.contrib import admin
from .models import (
    EntranceTest,
    Question,
    Choice,
    EntranceTestResult,
    UserAnswer,
    QuestionImage
)
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'test', 'part', 'short_content')
    list_filter = ('part', 'test')
    search_fields = ('content', 'passage')
    
    inlines = [ChoiceInline]

    fieldsets = (
        ('Thông tin chung', {
            'fields': ('test', 'part')
        }),
        ('Nội dung câu hỏi', {
            'fields': ('content',)
        }),
        ('Passage / Conversation / Reading', {
            'fields': ('passage',),
        }),
        ('Hình ảnh (Part 1)', {
            'fields': ('image',),
        }),
    )

    def short_content(self, obj):
        return obj.content[:50]
    
    short_content.short_description = 'Question'

@admin.register(QuestionImage)
class QuestionImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'description')

@admin.register(EntranceTest)
class EntranceTestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_active')

@admin.register(EntranceTestResult)
class EntranceTestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score', 'level', 'taken_at')
    readonly_fields = ('user', 'test', 'score', 'level', 'taken_at')

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('result', 'question', 'selected_choice')
    readonly_fields = ('result', 'question', 'selected_choice')