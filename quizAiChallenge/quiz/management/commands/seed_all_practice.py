from django.core.management.base import BaseCommand
from quiz.models import Quiz, QuestionForQuiz, Choice

class Command(BaseCommand):
    help = "Seed sample questions for all PRACTICE quizzes"

    def handle(self, *args, **kwargs):
        practice_quizzes = Quiz.objects.filter(quiz_type="PRACTICE")

        if not practice_quizzes.exists():
            self.stdout.write(self.style.WARNING("No PRACTICE quizzes found"))
            return

        for quiz in practice_quizzes:
            if quiz.questions_for_quiz.exists():
                self.stdout.write(self.style.NOTICE(
                    f"Quiz {quiz.id} already has {quiz.questions_for_quiz.count()} questions, skipping..."
                ))
                continue

            # Tạo một câu hỏi mẫu
            q = QuestionForQuiz.objects.create(
                quiz=quiz,
                content=f"Sample question for {quiz.title}",
                passage="This is a sample passage for practice quiz."
            )

            # Thêm 4 lựa chọn
            Choice.objects.create(question=q, content="Option A", is_correct=True)
            Choice.objects.create(question=q, content="Option B", is_correct=False)
            Choice.objects.create(question=q, content="Option C", is_correct=False)
            Choice.objects.create(question=q, content="Option D", is_correct=False)

            self.stdout.write(self.style.SUCCESS(
                f"Seeded 1 question with 4 choices for PRACTICE quiz {quiz.id} ({quiz.title})"
            ))