from entrance_test.models import UserAnswer
from learning_profile.models import UserSkillProfile
TOEIC_PART_MAP = {
    1: {
        "code": "LISTENING_PICTURE",
        "name": "Listening – Picture",
        "section": "LISTENING",
    },
    2: {
        "code": "LISTENING_QA",
        "name": "Listening – Q&A",
        "section": "LISTENING",
    },
    3: {
        "code": "LISTENING_CONVERSATION",
        "name": "Listening – Short Conversation",
        "section": "LISTENING",
    },
    4: {
        "code": "LISTENING_INFORMATION",
        "name": "Listening – Short Information",
        "section": "LISTENING",
    },
    5: {
        "code": "READING_SENTENCE",
        "name": "Reading – Incomplete Sentences",
        "section": "READING",
    },
    6: {
        "code": "READING_TEXT",
        "name": "Reading – Text Completion",
        "section": "READING",
    },
    7: {
        "code": "READING_PASSAGE",
        "name": "Reading – Passage",
        "section": "READING",
    },
}

def count_questions(result, part):
    return UserAnswer.objects.filter(
        result = result,
        question__part = part
    ).count()

def count_correct(result, part):
    return UserAnswer.objects.filter(
        result=result,
        question__part=part,
        selected_choice__is_correct=True
    ).count()

def classify_level(accuracy):
    if accuracy < 0.3:
        return 'BEGINNER'
    elif accuracy < 0.6:
        return 'ELEMENTARY'
    elif accuracy < 0.85:
        return 'INTERMEDIATE'
    return 'ADVANCED'

def save_or_update_user_skill(
    user,
    result,
    skill,
    section,
    accuracy,
    level
):
    UserSkillProfile.objects.update_or_create(
        user=user,
        result=result,
        skill=skill,
        defaults={
            'section': section,
            'accuracy': round(accuracy, 2),
            'level': level,
        }
    )

def analyze_entrance_test(result):
    for part, meta in TOEIC_PART_MAP.items():
        total = count_questions(result, part)
        correct = count_correct(result, part)

        if total == 0:
            continue

        accuracy = correct / total

        level = classify_level(accuracy)

        save_or_update_user_skill(
            user=result.user,
            result=result,
            skill=meta["code"],
            section=meta["section"],
            accuracy=accuracy,
            level=level
        )