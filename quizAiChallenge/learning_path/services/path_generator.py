from learning_path.rules import SKILL_LEARNING_RULES
from learning_path.models import LearningPath, LearningPathItem
from learning_profile.models import UserSkillProfile
from lesson.models import Lesson
from quiz.models import Quiz
from django.contrib.contenttypes.models import ContentType
from common.constants import SkillLevel

def get_lesson(skill_code, level):
    return Lesson.objects.filter(
        skill_code=skill_code,
        level=level,
        is_active=True
    ).order_by('order').first()

def get_quiz(skill_code, level, quiz_type):
    return Quiz.objects.filter(
        skill_code=skill_code,
        level=level,
        quiz_type=quiz_type,
        is_active=True
    ).first()

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
        
        level_enum = SkillLevel(skill.level)
        steps = rules.get(level_enum, [])

        for step in steps:
            content_object = None

            if step == 'LESSON':
                content_object = get_lesson(
                skill.skill,
                level_enum.value
                )

            elif step in ['PRACTICE', 'QUIZ', 'MOCK']:
                content_object = get_quiz(
                    skill.skill,
                    level_enum.value,
                    step
                )

            if not content_object:
                continue

            LearningPathItem.objects.create(
                path=path,
                skill_code=skill.skill,
                level=skill.level,
                item_type=step,
                title=content_object.title,
                content_object=content_object,
                order=order
            )
            order += 1

    items = LearningPathItem.objects.filter(path = path).order_by('order')
    if items.exists():
        firstItem = items.first()
        firstItem.status = 'UNLOCKED'
        firstItem.save()

    print("=== GENERATE LEARNING PATH ===")
    print("User:", user)

    skills = UserSkillProfile.objects.filter(
        user=user,
        result=result
    )

    print("Skill count:", skills.count())

    for skill in skills:
        print("Skill:", skill.skill, "Level:", skill.level)

        rules = SKILL_LEARNING_RULES.get(skill.skill)
        print("Rules:", rules)

        if not rules:
            print("❌ NO RULE FOR", skill.skill)
            continue

        level_enum = SkillLevel(skill.level)
        steps = rules.get(level_enum, [])
        print("Steps:", steps)


        for step in steps:
            print("  -> Create item:", step)
    return path
