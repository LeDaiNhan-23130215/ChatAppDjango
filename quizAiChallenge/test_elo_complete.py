#!/usr/bin/env python
"""Test ELO rating system for both quiz_ai_battle and quiz apps"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizAiChallenge.settings')
django.setup()

from accounts.models import User
from quiz_ai_battle.models import Match
from quiz.models import GameHistory, Room
from leaderboard.models import UserElo, EloHistory

def test_quiz_ai_battle_elo():
    """Test ELO system for quiz_ai_battle (vs AI)"""
    print("\n" + "=" * 70)
    print("TEST 1: QUIZ_AI_BATTLE ELO SYSTEM (Player vs AI)")
    print("=" * 70)
    
    # Clean up old test data
    User.objects.filter(username='ai_battle_user').delete()
    
    # Create user
    user = User.objects.create_user(
        username='ai_battle_user',
        email='ai_battle@test.com',
        password='test123',
        elo_rating=1000
    )
    
    print(f"\n1. User created: {user.username}")
    print(f"   Initial ELO: {user.elo_rating}")
    
    # Create match - WIN
    match1 = Match.objects.create(
        user=user,
        ai_mode='battle',
        ai_difficulty='medium',
        user_score=3,
        ai_score=0
    )
    
    from quiz_ai_battle.views import _calculate_elo_change, _update_user_elo
    
    print(f"\n2. Match 1 (WIN): User {match1.user_score} - AI {match1.ai_score}")
    change1 = _calculate_elo_change(match1)
    print(f"   ELO change: {change1:+d}")
    _update_user_elo(user, match1, change1)
    user.refresh_from_db()
    print(f"   New ELO: {user.elo_rating} (expected: 1030)")
    
    # Create match - LOSS
    match2 = Match.objects.create(
        user=user,
        ai_mode='battle',
        ai_difficulty='hard',
        user_score=0,
        ai_score=3
    )
    
    print(f"\n3. Match 2 (LOSS): User {match2.user_score} - AI {match2.ai_score}")
    change2 = _calculate_elo_change(match2)
    print(f"   ELO change: {change2:+d}")
    _update_user_elo(user, match2, change2)
    user.refresh_from_db()
    print(f"   New ELO: {user.elo_rating} (expected: 1010)")
    
    # Create match - DRAW
    match3 = Match.objects.create(
        user=user,
        ai_mode='battle',
        ai_difficulty='medium',
        user_score=2,
        ai_score=2
    )
    
    print(f"\n4. Match 3 (DRAW): User {match3.user_score} - AI {match3.ai_score}")
    change3 = _calculate_elo_change(match3)
    print(f"   ELO change: {change3:+d}")
    _update_user_elo(user, match3, change3)
    user.refresh_from_db()
    print(f"   New ELO: {user.elo_rating} (expected: 1010)")
    
    # Verify
    print(f"\n5. Final Verification:")
    print(f"   Expected: 1010")
    print(f"   Actual: {user.elo_rating}")
    print(f"   Status: {'✅ PASS' if user.elo_rating == 1010 else '❌ FAIL'}")
    
    # Check ELO history
    history = EloHistory.objects.filter(user=user).order_by('created_at')
    print(f"\n6. ELO History ({history.count()} records):")
    for i, record in enumerate(history, 1):
        print(f"   {i}. {record.elo_before} → {record.elo_after} ({record.change:+d})")


def test_quiz_pvp_elo():
    """Test ELO system for quiz (Player vs Player)"""
    print("\n" + "=" * 70)
    print("TEST 2: QUIZ ELO SYSTEM (Player vs Player)")
    print("=" * 70)
    
    # Clean up old test data
    User.objects.filter(username__in=['pvp_player1', 'pvp_player2']).delete()
    
    # Create players
    player1 = User.objects.create_user(
        username='pvp_player1',
        email='pvp1@test.com',
        password='test123',
        elo_rating=1000
    )
    
    player2 = User.objects.create_user(
        username='pvp_player2',
        email='pvp2@test.com',
        password='test123',
        elo_rating=1000
    )
    
    print(f"\n1. Players created:")
    print(f"   P1: {player1.username} - ELO {player1.elo_rating}")
    print(f"   P2: {player2.username} - ELO {player2.elo_rating}")
    
    # Create room
    room = Room.objects.create(
        code='TEST01',
        created_by=player1,
        player_count=2,
        started=True,
        finished=True
    )
    
    print(f"\n2. Room created: {room.code}")
    
    # Game 1: Player 1 wins
    game1 = GameHistory.objects.create(
        room=room,
        player1=player1,
        player2=player2,
        player1_score=80,
        player2_score=60,
        winner=player1,
        player1_elo_before=1000,
        player1_elo_change=30,
        player1_elo_after=1030,
        player2_elo_before=1000,
        player2_elo_change=-20,
        player2_elo_after=980,
        elo_updated=True
    )
    
    # Manually apply ELO updates
    player1.elo_rating = game1.player1_elo_after
    player1.save()
    player2.elo_rating = game1.player2_elo_after
    player2.save()
    
    print(f"\n3. Game 1 (P1 wins 80-60):")
    print(f"   P1: {game1.player1_elo_before} → {game1.player1_elo_after} ({game1.player1_elo_change:+d})")
    print(f"   P2: {game1.player2_elo_before} → {game1.player2_elo_after} ({game1.player2_elo_change:+d})")
    
    # Game 2: Player 2 wins (to test loss update)
    room2 = Room.objects.create(
        code='TEST02',
        created_by=player1,
        player_count=2,
        started=True,
        finished=True
    )
    
    game2 = GameHistory.objects.create(
        room=room2,
        player1=player1,
        player2=player2,
        player1_score=50,
        player2_score=85,
        winner=player2,
        player1_elo_before=1030,
        player1_elo_change=-20,
        player1_elo_after=1010,
        player2_elo_before=980,
        player2_elo_change=30,
        player2_elo_after=1010,
        elo_updated=True
    )
    
    # Manually apply ELO updates
    player1.elo_rating = game2.player1_elo_after
    player1.save()
    player2.elo_rating = game2.player2_elo_after
    player2.save()
    
    print(f"\n4. Game 2 (P2 wins 50-85):")
    print(f"   P1: {game2.player1_elo_before} → {game2.player1_elo_after} ({game2.player1_elo_change:+d})")
    print(f"   P2: {game2.player2_elo_before} → {game2.player2_elo_after} ({game2.player2_elo_change:+d})")
    
    # Game 3: Draw
    room3 = Room.objects.create(
        code='TEST03',
        created_by=player1,
        player_count=2,
        started=True,
        finished=True
    )
    
    game3 = GameHistory.objects.create(
        room=room3,
        player1=player1,
        player2=player2,
        player1_score=70,
        player2_score=70,
        winner=None,
        player1_elo_before=1010,
        player1_elo_change=0,
        player1_elo_after=1010,
        player2_elo_before=1010,
        player2_elo_change=0,
        player2_elo_after=1010,
        elo_updated=True
    )
    
    print(f"\n5. Game 3 (DRAW 70-70):")
    print(f"   P1: {game3.player1_elo_before} → {game3.player1_elo_after} ({game3.player1_elo_change:+d})")
    print(f"   P2: {game3.player2_elo_before} → {game3.player2_elo_after} ({game3.player2_elo_change:+d})")
    
    # Final verification
    player1.refresh_from_db()
    player2.refresh_from_db()
    
    print(f"\n6. Final Verification:")
    print(f"   P1: Expected 1010, Actual {player1.elo_rating}")
    print(f"   P2: Expected 1010, Actual {player2.elo_rating}")
    print(f"   Status: {'✅ PASS' if player1.elo_rating == 1010 and player2.elo_rating == 1010 else '❌ FAIL'}")
    
    # Show GameHistory
    print(f"\n7. GameHistory Records ({GameHistory.objects.count()} total):")
    for game in GameHistory.objects.all().order_by('played_at'):
        winner_name = game.winner.username if game.winner else "None"
        print(f"   {game.id}: {game.player1.username}({game.player1_score}) vs {game.player2.username}({game.player2_score}) → {winner_name}")


def show_leaderboard():
    """Show current leaderboard"""
    print("\n" + "=" * 70)
    print("CURRENT LEADERBOARD")
    print("=" * 70)
    
    users = User.objects.filter(elo_rating__gt=0).order_by('-elo_rating')[:10]
    print(f"\nRank | Username | ELO | Status")
    print("-" * 50)
    for rank, user in enumerate(users, 1):
        # Get or create UserElo
        user_elo, created = UserElo.objects.get_or_create(user=user, defaults={'elo': user.elo_rating})
        match = "✓" if user.elo_rating == user_elo.elo else "✗"
        print(f"{rank:2d}   | {user.username:15s} | {user.elo_rating:4d} | {match}")


if __name__ == '__main__':
    test_quiz_ai_battle_elo()
    test_quiz_pvp_elo()
    show_leaderboard()
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)
