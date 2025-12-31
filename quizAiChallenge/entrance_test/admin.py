from django.contrib import admin
from .models import (
    EntranceTest,
    Question,
    Choice,
    EntranceTestResult,
    UserAnswer,
)

admin.site.register(EntranceTest)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(EntranceTestResult)
admin.site.register(UserAnswer)