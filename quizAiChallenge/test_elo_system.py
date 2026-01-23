#!/usr/bin/env python
"""Test ELO rating system"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quizAiChallenge.settings')
django.setup()

from accounts.models import User
from quiz_ai_battle.models import Match, Question, Round
from leaderboard.models import UserElo, EloHistory
from datetime import datetime

def test_elo_system():
    """Test the complete ELO system"""
    print("=" * 60)
    print("TESTING ELO RATING SYSTEM")
    print("=" * 60)
    
    # Get or create a test user
    test_user, created = User.objects.get_or_create(
        username='test_elo_user',
        defaults={
            'email': 'test_elo@test.com',
            'first_name': 'ELO',
            'last_name': 'Test',
            'elo_rating': 1000
        }
    )
    
    print(f"\n1. User: {test_user.username}")
    print(f"   Initial ELO: {test_user.elo_rating}")
    
    # Create a test match - WIN scenario
    print("\n2. Testing WIN scenario (+30 ELO)...")
    match_win = Match.objects.create(
        user=test_user,
        ai_mode='battle',
        ai_difficulty='medium',
        user_score=3,
        ai_score=0
    )
    
    print(f"   Match created: User {match_win.user_score} vs AI {match_win.ai_score}")
    print(f"   Match result: {match_win.result}")
    
    # Simulate ELO calculation
    from quiz_ai_battle.views import _calculate_elo_change, _update_user_elo
    
    elo_change = _calculate_elo_change(match_win)
    print(f"   ELO change calculated: {elo_change}")
    
    # Update ELO
    _update_user_elo(test_user, match_win, elo_change)
    test_user.refresh_from_db()
    match_win.refresh_from_db()
    
    print(f"   New ELO: {test_user.elo_rating}")
    print(f"   Match elo_before: {match_win.elo_before}")
    print(f"   Match elo_after: {match_win.elo_after}")
    print(f"   Match elo_change: {match_win.elo_change}")
    
    # Create a test match - LOSS scenario
    print("\n3. Testing LOSS scenario (-20 ELO)...")
    match_loss = Match.objects.create(
        user=test_user,
        ai_mode='battle',
        ai_difficulty='hard',
        user_score=0,
        ai_score=3
    )
    
    print(f"   Match created: User {match_loss.user_score} vs AI {match_loss.ai_score}")
    print(f"   Match result: {match_loss.result}")
    
    elo_change = _calculate_elo_change(match_loss)
    print(f"   ELO change calculated: {elo_change}")
    
    _update_user_elo(test_user, match_loss, elo_change)
    test_user.refresh_from_db()
    match_loss.refresh_from_db()
    
    print(f"   New ELO: {test_user.elo_rating}")
    print(f"   Match elo_before: {match_loss.elo_before}")
    print(f"   Match elo_after: {match_loss.elo_after}")
    print(f"   Match elo_change: {match_loss.elo_change}")
    
    # Create a test match - DRAW scenario
    print("\n4. Testing DRAW scenario (0 ELO)...")
    match_draw = Match.objects.create(
        user=test_user,
        ai_mode='battle',
        ai_difficulty='medium',
        user_score=2,
        ai_score=2
    )
    
    print(f"   Match created: User {match_draw.user_score} vs AI {match_draw.ai_score}")
    print(f"   Match result: {match_draw.result}")
    
    elo_change = _calculate_elo_change(match_draw)
    print(f"   ELO change calculated: {elo_change}")
    
    _update_user_elo(test_user, match_draw, elo_change)
    test_user.refresh_from_db()
    match_draw.refresh_from_db()
    
    print(f"   New ELO: {test_user.elo_rating}")
    print(f"   Match elo_before: {match_draw.elo_before}")
    print(f"   Match elo_after: {match_draw.elo_after}")
    print(f"   Match elo_change: {match_draw.elo_change}")
    
    # Check ELO history
    print("\n5. ELO History:")
    history = EloHistory.objects.filter(user=test_user).order_by('created_at')
    for i, entry in enumerate(history, 1):
        print(f"   {i}. {entry.created_at}: {entry.elo_before} → {entry.elo_after} (change: {entry.change:+d})")
    
    # Check UserElo model
    print("\n6. UserElo Model:")
    user_elo = UserElo.objects.get(user=test_user)
    print(f"   ELO from UserElo: {user_elo.elo}")
    print(f"   ELO from User: {test_user.elo_rating}")
    print(f"   Match: {user_elo.elo == test_user.elo_rating}")
    
    # Expected: 1000 + 30 - 20 + 0 = 1010
    expected_elo = 1000 + 30 - 20 + 0
    print(f"\n7. Final Verification:")
    print(f"   Expected ELO: {expected_elo}")
    print(f"   Actual ELO: {test_user.elo_rating}")
    print(f"   Test PASSED!" if test_user.elo_rating == expected_elo else f"   Test FAILED!")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_elo_system()
