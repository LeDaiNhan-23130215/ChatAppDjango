from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from lesson.models import Lesson
from quiz.models import Quiz
from common.constants import SkillCode, SkillLevel
from learning_path.rules import SKILL_LEARNING_RULES

User = get_user_model()

class Command(BaseCommand):
    help = "Seed data for Learning Path testing"

    def handle(self, *args, **options):
        self.stdout.write("🌱 Seeding learning path data...")

        order_counter = 1

        for skill_code, levels in SKILL_LEARNING_RULES.items():
            for level, activities in levels.items():
                for activity in activities:
                    if activity == "LESSON":
                        Lesson.objects.get_or_create(
                            skill_code=skill_code,
                            level=level,
                            order=order_counter,
                            estimated_time=15,
                            defaults={
                                "title": f"{skill_code} - {level} Lesson {order_counter}",
                                "is_active": True,
                            }
                        )
                        order_counter += 1

                    elif activity == "PRACTICE":
                        Quiz.objects.get_or_create(
                            skill_code=skill_code,
                            level=level,
                            quiz_type="PRACTICE",
                            total_questions=10,
                            defaults={
                                "title": f"{skill_code} - {level} Practice",
                                "is_active": True,
                            }
                        )

                    elif activity == "QUIZ":
                        Quiz.objects.get_or_create(
                            skill_code=skill_code,
                            level=level,
                            quiz_type="QUIZ",
                            total_questions=10,
                            defaults={
                                "title": f"{skill_code} - {level} Quiz",
                                "is_active": True,
                            }
                        )

                    elif activity == "MOCK":
                        Quiz.objects.get_or_create(
                            skill_code=skill_code,
                            level=level,
                            quiz_type="MOCK",
                            total_questions=20,
                            defaults={
                                "title": f"{skill_code} - {level} Mock Test",
                                "is_active": True,
                            }
                        )

        self.stdout.write(self.style.SUCCESS("✅ Seed data created successfully"))

