from django.core.management.base import BaseCommand
from minigames.models import Minigame

class Command(BaseCommand):
    help = "Seed minigames"

    def handle(self, *args, **kwargs):
        mg, _ = Minigame.objects.get_or_create(code='choose_meaning', defaults={'name': 'Chọn nghĩa'})
        self.stdout.write(self.style.SUCCESS(f"Seeded minigame: {mg.code}"))
