import random
from minigames.models import Vocabulary

def pick_distractors(vocab, k=3):
    qs = Vocabulary.objects.exclude(id=vocab.id)

    if vocab.part_of_speech:
        qs = qs.filter(part_of_speech=vocab.part_of_speech)

    tag_ids = vocab.tags.values_list("id", flat=True)
    if tag_ids:
        qs = qs.filter(tags__in=tag_ids).distinct()

    defs = (
        qs.exclude(definition__isnull=True)
          .exclude(definition__exact="")
          .values_list("definition", flat=True)
    )

    defs = [
        d for d in defs
        if d.strip().lower() != vocab.definition.strip().lower()
    ]

    random.shuffle(defs)
    return defs[:k]