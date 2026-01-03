from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from entrance_test.models import EntranceTest, EntranceTestResult
from learning_profile.models import UserSkillProfile
from learning_path.services.path_generator import generate_learning_path
from lesson.models import Lesson
from quiz.models import Quiz

from common.constants import SkillLevel

User = get_user_model()

class Command(BaseCommand):
    help = "Seed data for Learning Path testing"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding learning path data...")

        # ===== USER =====
        user, _ = User.objects.get_or_create(
            username="testuser",
        )

        # ===== ENTRANCE TEST =====
        test = EntranceTest.objects.filter(
            title="TOEIC Entrance Test"
        ).first()

        if not test:
            test = EntranceTest.objects.create(
                title="TOEIC Entrance Test",
                is_active=True
            )
        self.stdout.write(f"✅ EntranceTest ID = {test.id}")

        # ===== RESULT =====
        result = EntranceTestResult.objects.create(
            user=user,
            test=test,
            score=350,
            level="BEGINNER",
            correct_answers=18,
            total_questions=30,
        )

        # ===== SKILL PROFILE =====
        skills = [
            ("LISTENING_PICTURE", SkillLevel.BEGINNER),
            ("READING_PASSAGE", SkillLevel.BEGINNER),
        ]

        for skill_code, level in skills:
            UserSkillProfile.objects.get_or_create(
                user=user,
                result=result,
                skill=skill_code,
                accuracy = 0.4,
                defaults={"level": level}
            )

        # ===== LESSON =====
        Lesson.objects.get_or_create(
            skill_code="LISTENING_PICTURE",
            level=SkillLevel.BEGINNER,
            order=1,
            estimated_time = 15,
            defaults={
                "title": "Listening Picture - Lesson 1",
                "is_active": True,
            }
        )

        Lesson.objects.get_or_create(
            skill_code="READING_PASSAGE",
            level=SkillLevel.BEGINNER,
            order=1,
            estimated_time = 15,
            defaults={
                "title": "Reading Passage - Lesson 1",
                "is_active": True,
            }
        )

        # ===== PRACTICE =====
        Quiz.objects.get_or_create(
            skill_code="LISTENING_PICTURE",
            level=SkillLevel.BEGINNER,
            quiz_type="PRACTICE",
            total_questions = 10,
            defaults={
                "title": "Listening Picture Practice",
                "is_active": True,
            }
        )

        Quiz.objects.get_or_create(
            skill_code="READING_PASSAGE",
            level=SkillLevel.BEGINNER,
            quiz_type="PRACTICE",
            total_questions = 10,
            defaults={
                "title": "Reading Passage Practice",
                "is_active": True,
            }
        )

        # ===== QUIZ =====
        Quiz.objects.get_or_create(
            title="Listening Picture Quiz 1",
            skill_code="LISTENING_PICTURE",
            level="BEGINNER",
            quiz_type="QUIZ",
            total_questions = 10,
            is_active=True
        )

        # ===== GENERATE PATH =====
        path = generate_learning_path(result)

        self.stdout.write(self.style.SUCCESS("✅ Seed data created successfully"))
