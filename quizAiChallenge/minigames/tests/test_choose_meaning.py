from django.test import TestCase
from minigames.models import Vocabulary, Minigame
from minigames.services.choose_meaning import build_question

# Create your tests here.
class ChooseMeaningTest(TestCase):
    def setUp(self):
        self.mg = Minigame.objects.create(code='choose_meaning', name='Chọn nghĩa')
        Vocabulary.objects.create(term='apple', language='en', definition='quả táo', part_of_speech='noun', tags=['fruit'])
        Vocabulary.objects.create(term='banana', language='en', definition='quả chuối', part_of_speech='noun', tags=['fruit'])
        Vocabulary.objects.create(term='orange', language='en', definition='quả cam', part_of_speech='noun', tags=['fruit'])

    def test_build_question(self):
        vocab = Vocabulary.objects.get(term='apple')
        q, choices = build_question(vocab, self.mg)
        self.assertEqual(q.type, 'choose_meaning')
        self.assertTrue(any(c.is_correct for c in choices))
        self.assertGreaterEqual(len(choices), 3)
        # Không có nghĩa trùng lặp
        defs = [c.text for c in choices]
        self.assertEqual(len(defs), len(set(defs)))
