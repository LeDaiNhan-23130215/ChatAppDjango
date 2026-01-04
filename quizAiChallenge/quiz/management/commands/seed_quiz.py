from django.core.management.base import BaseCommand
from quiz.models import Quiz, QuestionForQuiz, Choice

class Command(BaseCommand):
    help = "Seed questions and choices for existing quizzes"

    def handle(self, *args, **kwargs):
        # Seed cho PRACTICE quiz (id=19)
        try:
            practice = Quiz.objects.get(id=19, quiz_type="PRACTICE")
            q1 = QuestionForQuiz.objects.create(
                quiz=practice,
                content="What is the man talking about?",
                passage="A man is speaking about his daily routine."
            )
            Choice.objects.create(question=q1, content="His job", is_correct=True)
            Choice.objects.create(question=q1, content="His hobby", is_correct=False)
            Choice.objects.create(question=q1, content="His family", is_correct=False)
            Choice.objects.create(question=q1, content="His travel", is_correct=False)
            self.stdout.write(self.style.SUCCESS("Seeded Practice quiz (id=19)"))
        except Quiz.DoesNotExist:
            self.stdout.write(self.style.WARNING("Practice quiz id=19 not found"))

        # Seed cho QUIZ (id=20)
        try:
            quiz = Quiz.objects.get(id=20, quiz_type="QUIZ")
            q2 = QuestionForQuiz.objects.create(
                quiz=quiz,
                content="What is the main idea of the passage?",
                passage="Tom likes to play football after school."
            )
            Choice.objects.create(question=q2, content="Tom enjoys sports", is_correct=True)
            Choice.objects.create(question=q2, content="Tom hates school", is_correct=False)
            Choice.objects.create(question=q2, content="Tom studies math", is_correct=False)
            Choice.objects.create(question=q2, content="Tom is a teacher", is_correct=False)
            self.stdout.write(self.style.SUCCESS("Seeded Quiz (id=20)"))
        except Quiz.DoesNotExist:
            self.stdout.write(self.style.WARNING("Quiz id=20 not found"))

        # Seed cho MOCK exam (id=45)
        try:
            mock = Quiz.objects.get(id=45, quiz_type="MOCK")
            q3 = QuestionForQuiz.objects.create(
                quiz=mock,
                content="What is the speaker's main concern?",
                passage="The speaker is discussing project deadlines."
            )
            Choice.objects.create(question=q3, content="Project delays", is_correct=True)
            Choice.objects.create(question=q3, content="Budget increase", is_correct=False)
            Choice.objects.create(question=q3, content="Team expansion", is_correct=False)
            Choice.objects.create(question=q3, content="Office relocation", is_correct=False)
            self.stdout.write(self.style.SUCCESS("Seeded Mock exam (id=45)"))
        except Quiz.DoesNotExist:
            self.stdout.write(self.style.WARNING("Mock exam id=45 not found"))