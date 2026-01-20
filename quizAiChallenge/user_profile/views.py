import json
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from learning_profile.models import UserSkillProfile

@login_required
def profile_view(request):
    user = request.user

    skill_qs = (
        UserSkillProfile.objects
        .filter(user=user)
        .values('skill')
        .annotate(avg_accuracy=Avg('accuracy'))
    )

    section_qs = (
        UserSkillProfile.objects
        .filter(user=user)
        .values('section')
        .annotate(avg_accuracy=Avg('accuracy'))
    )

    context = {
        "skill_accuracy": json.dumps(list(skill_qs)),
        "section_accuracy": json.dumps(list(section_qs)),
    }

    return render(request, "user_profile/profile.html", context)
