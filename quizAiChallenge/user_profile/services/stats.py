from django.db.models import Avg
from learning_profile.models import UserSkillProfile

def get_user_skill_stats(user):
    skills = UserSkillProfile.objects.filter(user=user)

    skills_accuracy = (
        skills.values('skill').annotate(avg_accuracy = Avg('accuracy')).order_by('skill')
    )

    section_accuracy = (
        skills.values('skill').annotate(avg_accuracy = Avg('accuracy'))
    )

    return {"skill_accuracy": skills_accuracy, "section_accuracy": section_accuracy,}