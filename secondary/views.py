import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import UserProfile, Inventory, CoinTransaction, MatchResult
from main.models import Subject, StudySession

# ─────────────────────────────────────────
#  SHOP CATALOGUE
#  Defined here so views and templates share the same list.
# ─────────────────────────────────────────

SHOP_ITEMS = [
    {
        'id': 'freeze',
        'icon': '❄️',
        'name': 'Time Freeze',
        'desc': 'Pause the timer for 10 seconds so you can think without pressure.',
        'price': 80,
    },
    {
        'id': 'saver',
        'icon': '🛡️',
        'name': 'Streak Saver',
        'desc': 'Protect your streak on one wrong answer. The fire keeps burning!',
        'price': 120,
    },
    {
        'id': 'eliminator',
        'icon': '🔥',
        'name': 'Eliminator',
        'desc': 'Burn away 2 wrong answer choices — narrow it down to the right one.',
        'price': 100,
    },
    {
        'id': 'hint',
        'icon': '💡',
        'name': 'Card Hint',
        'desc': 'Flip the card briefly to peek at the answer before choosing.',
        'price': 60,
    },
]


# ─────────────────────────────────────────
#  SHOP
# ─────────────────────────────────────────

@login_required
def shop(request):
    """Shop page — shows all powerups with prices and owned counts."""
    profile = UserProfile.objects.get(user=request.user)
    inventory = Inventory.objects.get(user=request.user)

    # Attach owned count to each item so the template can display it
    items = []
    for item in SHOP_ITEMS:
        items.append({
            **item,
            'owned': getattr(inventory, item['id']),
            'can_afford': profile.coins >= item['price'],
        })

    return render(request, 'secondary/shop.html', {
        'profile': profile,
        'items': items,
    })


@login_required
@require_POST
def buy_item(request):
    """
    Called via fetch() when user clicks Buy.
    Checks funds, deducts coins, adds to inventory, logs transaction.
    Returns JSON so the page can update without reload.
    """
    data = json.loads(request.body)
    item_id = data.get('item_id')

    # Find the item in the catalogue
    item = next((i for i in SHOP_ITEMS if i['id'] == item_id), None)
    if not item:
        return JsonResponse({'success': False, 'error': 'Item not found'})

    profile = UserProfile.objects.get(user=request.user)
    if profile.coins < item['price']:
        return JsonResponse({'success': False, 'error': 'Not enough coins'})

    # Deduct coins
    profile.coins -= item['price']
    profile.save()

    # Add to inventory
    inventory = Inventory.objects.get(user=request.user)
    setattr(inventory, item_id, getattr(inventory, item_id) + 1)
    inventory.save()

    # Log it
    CoinTransaction.objects.create(
        user=request.user,
        amount=-item['price'],
        reason=f"Bought {item['name']}",
    )

    return JsonResponse({
        'success': True,
        'coins': profile.coins,
        'owned': getattr(inventory, item_id),
    })


# ─────────────────────────────────────────
#  MATCHING GAME
# ─────────────────────────────────────────

@login_required
def match_setup(request):
    """Match game setup page — user picks subject and pair count."""
    subjects = Subject.objects.filter(user=request.user)
    profile = UserProfile.objects.get(user=request.user)
    return render(request, 'secondary/match_setup.html', {
        'subjects': subjects,
        'profile': profile,
    })


@login_required
def match_cards(request):
    """
    Returns JSON list of term/definition pairs for the selected subject.
    Called by the match game JS to build the board.
    Example: GET /match/cards/?subject_id=1&pairs=4
    """
    subject_id = request.GET.get('subject_id')
    pair_count = int(request.GET.get('pairs', 4))
    pair_count = max(3, min(5, pair_count))  # clamp between 3 and 5

    subject = Subject.objects.get(id=subject_id, user=request.user)

    # Gather all flashcards across all chapters of this subject
    from main.models import Flashcard
    cards = list(Flashcard.objects.filter(chapter__subject=subject))

    if len(cards) < pair_count:
        return JsonResponse({'error': 'Not enough cards'}, status=400)

    import random
    selected = random.sample(cards, pair_count)
    pairs = [{'id': c.id, 'term': c.question, 'definition': c.answer} for c in selected]

    return JsonResponse({'pairs': pairs})


@login_required
@require_POST
def save_match_result(request):
    """
    Called at the end of a match game.
    Saves result, awards coins, logs transaction.
    """
    data = json.loads(request.body)
    subject_name = data.get('subject', '')
    pair_count = data.get('pair_count', 4)
    time_seconds = data.get('time_seconds', 0)
    mistakes = data.get('mistakes', 0)
    coins_to_award = data.get('coins_earned', 0)
    perfect = data.get('perfect', False)

    # Star rating
    if mistakes == 0:
        stars = 3
    elif mistakes <= 2:
        stars = 2
    else:
        stars = 1

    # Perfect round bonus
    if perfect:
        coins_to_award += 30

    MatchResult.objects.create(
        user=request.user,
        subject=subject_name,
        pair_count=pair_count,
        time_seconds=time_seconds,
        mistakes=mistakes,
        stars=stars,
        coins_earned=coins_to_award,
    )

    profile = UserProfile.objects.get(user=request.user)
    profile.coins += coins_to_award
    profile.save()

    if coins_to_award > 0:
        CoinTransaction.objects.create(
            user=request.user,
            amount=coins_to_award,
            reason=f'Match game — {subject_name} ({stars}⭐)',
        )

    return JsonResponse({
        'success': True,
        'coins': profile.coins,
        'stars': stars,
    })


# ─────────────────────────────────────────
#  STATS
# ─────────────────────────────────────────

@login_required
def stats(request):
    """
    Stats page — pulls study sessions and match results
    and computes accuracy per subject and daily activity.
    """
    profile = UserProfile.objects.get(user=request.user)

    # Last 10 study sessions
    sessions = StudySession.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]

    # Last 10 match results
    match_results = MatchResult.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]

    # Accuracy per subject
    subjects = Subject.objects.filter(user=request.user)
    subject_accuracy = []
    for subject in subjects:
        subject_sessions = StudySession.objects.filter(
            user=request.user,
            chapter__subject=subject,
        )
        if subject_sessions.exists():
            total_score = sum(s.score for s in subject_sessions)
            total_cards = sum(s.chapter.card_count() for s in subject_sessions)
            pct = round((total_score / total_cards) * 100) if total_cards > 0 else 0
        else:
            pct = 0
        subject_accuracy.append({'subject': subject, 'pct': pct})

    # Total stats
    total_studied = StudySession.objects.filter(user=request.user).count()
    best_streak = profile.streak
    total_coins = CoinTransaction.objects.filter(
        user=request.user, amount__gt=0
    ).values_list('amount', flat=True)
    total_earned = sum(total_coins)

    return render(request, 'secondary/stats.html', {
        'profile': profile,
        'sessions': sessions,
        'match_results': match_results,
        'subject_accuracy': subject_accuracy,
        'total_studied': total_studied,
        'best_streak': best_streak,
        'total_earned': total_earned,
    })
