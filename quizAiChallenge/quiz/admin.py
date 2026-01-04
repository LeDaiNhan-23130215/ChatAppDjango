from django.contrib import admin
from .models import Question, Room, Quiz, QuestionForQuiz, Choice, QuizResult

admin.site.register(Question)
admin.site.register(Room)
admin.site.register(Quiz)
admin.site.register(QuestionForQuiz)
admin.site.register(Choice)
admin.site.register(QuizResult)
