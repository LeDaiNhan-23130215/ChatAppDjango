from django.core.management.base import BaseCommand
from quiz.models import Quiz, QuestionForQuiz, Choice

class Command(BaseCommand):
    help = "Seed sample questions for all QUIZ and MOCK quizzes"

    def handle(self, *args, **kwargs):
        # Seed cho tất cả QUIZ
        quiz_quizzes = Quiz.objects.filter(quiz_type="QUIZ")
        for quiz in quiz_quizzes:
            if quiz.questions_for_quiz.exists():
                self.stdout.write(self.style.NOTICE(
                    f"Quiz {quiz.id} already has {quiz.questions_for_quiz.count()} questions, skipping..."
                ))
                continue

            q = QuestionForQuiz.objects.create(
                quiz=quiz,
                content=f"Sample question for {quiz.title}",
                passage="This is a sample passage for quiz."
            )
            Choice.objects.create(question=q, content="Option A", is_correct=True)
            Choice.objects.create(question=q, content="Option B", is_correct=False)
            Choice.objects.create(question=q, content="Option C", is_correct=False)
            Choice.objects.create(question=q, content="Option D", is_correct=False)

            self.stdout.write(self.style.SUCCESS(
                f"Seeded 1 question with 4 choices for QUIZ {quiz.id} ({quiz.title})"
            ))

        # Seed cho tất cả MOCK
        mock_quizzes = Quiz.objects.filter(quiz_type="MOCK")
        for mock in mock_quizzes:
            if mock.questions_for_quiz.exists():
                self.stdout.write(self.style.NOTICE(
                    f"Mock {mock.id} already has {mock.questions_for_quiz.count()} questions, skipping..."
                ))
                continue

            q = QuestionForQuiz.objects.create(
                quiz=mock,
                content=f"Sample question for {mock.title}",
                passage="This is a sample passage for mock exam."
            )
            Choice.objects.create(question=q, content="Option A", is_correct=True)
            Choice.objects.create(question=q, content="Option B", is_correct=False)
            Choice.objects.create(question=q, content="Option C", is_correct=False)
            Choice.objects.create(question=q, content="Option D", is_correct=False)

            self.stdout.write(self.style.SUCCESS(
                f"Seeded 1 question with 4 choices for MOCK {mock.id} ({mock.title})"
            ))