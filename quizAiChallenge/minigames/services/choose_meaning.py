import random
from .utils import pick_distractors
from minigames.models import Vocabulary, Minigame, Question, Choice

def build_question(vocab: Vocabulary, minigame: Minigame):
    prompt = f"Chọn nghĩa đúng của từ: {vocab.term}"

    q = Question.objects.create(
        minigame=minigame,
        vocabulary=vocab,
        prompt=prompt,
        type='choose_meaning'
    )

    correct = Choice.objects.create(
        question=q,
        text=vocab.definition,
        is_correct=True,
        source='gold'
    )

    distractors = [
        Choice.objects.create(
            question=q,
            text=text,
            is_correct=False,
            source='distractor'
        )
        for text in pick_distractors(vocab)
    ]

    choices = [correct] + distractors
    random.shuffle(choices)

    return q, choices