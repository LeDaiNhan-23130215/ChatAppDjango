from django.core.management.base import BaseCommand
from minigames.models import Minigame, Vocabulary, Tag, Question

class Command(BaseCommand):
    help = "Seed minigames with vocabulary questions"

    def handle(self, *args, **kwargs):
        # Tạo 2 minigame: MCQ và Flashcard
        mcq, _ = Minigame.objects.get_or_create(
            code='choose_meaning',
            defaults={'name': 'Chọn nghĩa (MCQ)'}
        )
        flashcard, _ = Minigame.objects.get_or_create(
            code='flashcard',
            defaults={'name': 'Học từ vựng (Flashcard)'}
        )
        self.stdout.write(self.style.SUCCESS("Seeded minigames"))

        vocab_data = [
            ("apple", "quả táo", "I eat an apple every morning.", ["fruit", "basic"]),
            ("banana", "quả chuối", "Bananas are yellow.", ["fruit", "basic"]),
            ("orange", "quả cam", "Orange juice is tasty.", ["fruit", "basic"]),
            ("grape", "quả nho", "Grapes can be made into wine.", ["fruit", "basic"]),
            ("pear", "quả lê", "She ate a sweet pear.", ["fruit", "basic"]),
            ("pineapple", "quả dứa", "Pineapple is juicy and sweet.", ["fruit", "basic"]),
            ("watermelon", "quả dưa hấu", "Watermelon is refreshing in summer.", ["fruit", "basic"]),
            ("strawberry", "quả dâu tây", "Strawberries are red and sweet.", ["fruit", "basic"]),
            ("mango", "quả xoài", "Mangoes are tropical fruits.", ["fruit", "basic"]),
            ("lemon", "quả chanh", "Lemon juice is sour.", ["fruit", "basic"]),
        ]

        for term, definition, example, tag_names in vocab_data:
            vocab, _ = Vocabulary.objects.get_or_create(
                term=term,
                defaults={
                    "language": "en",
                    "part_of_speech": "noun",
                    "definition": definition,
                    "example": example,
                }
            )
            tag_objs = [Tag.objects.get_or_create(name=name)[0] for name in tag_names]
            vocab.tags.set(tag_objs)

            # Tạo câu hỏi cho MCQ
            Question.objects.get_or_create(
                minigame=mcq,
                vocabulary=vocab,
                prompt=f"What is the meaning of '{term}'?",
                defaults={"difficulty": 1, "type": "mcq"}
            )

            # Tạo câu hỏi cho Flashcard
            Question.objects.get_or_create(
                minigame=flashcard,
                vocabulary=vocab,
                prompt=f"Flashcard for '{term}'",
                defaults={"difficulty": 1, "type": "flashcard"}
            )

        self.stdout.write(self.style.SUCCESS("Seeded 10 vocabulary questions for both MCQ and Flashcard"))
