from .models import UserElo, EloHistory

def update_elo(user, delta):
    elo_profile = user.elo_profile

    before = elo_profile.elo
    after = before + delta

    elo_profile.elo = after
    elo_profile.save()

    EloHistory.objects.create(
        user=user,
        elo_before=before,
        elo_after=after,
        change=delta
    )

def get_top_users(limit=3):
    return (
        UserElo.objects
        .select_related("user")
        .order_by("-elo")[:limit]
    )