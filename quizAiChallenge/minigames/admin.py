from django.contrib import admin
from .models import Vocabulary, Minigame, Question, Choice, GameSession, Attempt

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'type', 'difficulty', 'minigame', 'vocabulary')
    inlines = [ChoiceInline]

@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ('term', 'language', 'part_of_speech')
    search_fields = ('term', 'definition', 'tags')

@admin.register(Minigame)
class MinigameAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'minigame', 'score', 'total_questions', 'started_at', 'finished_at')

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('session', 'question', 'is_correct', 'time_ms', 'responded_at')