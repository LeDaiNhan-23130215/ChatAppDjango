from django.contrib import admin
from learning_path.models import LearningPath, LearningPathItem
# Register your models here.
admin.site.register(LearningPath)
admin.site.register(LearningPathItem)