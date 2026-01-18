import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from leaderboard.models import UserElo

class Command(BaseCommand):
    help = "Seed random ELO for all users"

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all()

        self.stdout.write("🌱 Seeding ELO for users...")

        for user in users:
            elo_obj, _ = UserElo.objects.get_or_create(user=user)

            elo_obj.elo = random.randint(800, 2000)
            elo_obj.save()

            self.stdout.write(
                f"✅ {user.username} → ELO {elo_obj.elo}"
            )

        self.stdout.write(self.style.SUCCESS("🎉 ELO seeding completed"))