from django.contrib import admin
from .models import Question, Room, Quiz

admin.site.register(Question)
admin.site.register(Room)
admin.site.register(Quiz)
