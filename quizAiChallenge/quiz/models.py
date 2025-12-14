from django.db import models
import random
import string

class Question(models.Model):
    text = models.CharField(max_length=300)
    a = models.CharField(max_length=200)
    b = models.CharField(max_length=200)
    c = models.CharField(max_length=200)
    d = models.CharField(max_length=200)
    correct = models.CharField(max_length=1)  # 'A', 'B', 'C', 'D'

    def as_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "a": self.a,
            "b": self.b,
            "c": self.c,
            "d": self.d,
        }


class Room(models.Model):
    code = models.CharField(max_length=6, unique=True)
    player_count = models.IntegerField(default=0)
    started = models.BooleanField(default=False)

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.ascii_uppercase, k=6))
