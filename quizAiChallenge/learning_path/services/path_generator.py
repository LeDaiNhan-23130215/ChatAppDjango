from learning_path.rules import SKILL_LEARNING_RULES
from learning_path.models import LearningPath, LearningPathItem
from learning_profile.models import UserSkillProfile
def generate_learning_path(result):
    user = result.user
    LearningPath.objects.filter(
        user = user,
        is_active = True,
    ).update(is_active = False)

    path = LearningPath.objects.create(
        user = user,
        created_from_result = result
    )

    order = 1

    skills = UserSkillProfile.objects.filter(
        user = user,
        result = result
    )

    for skill in skills:
        rules = SKILL_LEARNING_RULES.get(skill.skill)
        if not rules:
            continue

        steps = rules.get(skill.level, [])

        for step in steps:
            LearningPathItem.objects.create(
                path = path,
                skill_code = skill.skill,
                level = skill.level,
                item_type = step,
                title=f'{skill.skill} - {step}',
                order=order
            )
            order += 1
    return path
