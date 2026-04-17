import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import Subject, Chapter, Flashcard, StudySession
from secondary.models import UserProfile, Inventory, CoinTransaction



#  AUTH VIEWS


def login_view(request):
    """Show login form and handle login submission."""
    if request.user.is_authenticated:
        return redirect('library')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('library')
        else:
            error = 'Invalid username or password.'

    return render(request, 'main/login.html', {'error': error})


def register_view(request):
    """Show registration form and handle new user creation."""
    if request.user.is_authenticated:
        return redirect('library')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            error = 'Passwords do not match.'
        elif User.objects.filter(username=username).exists():
            error = 'Username already taken.'
        else:
            user = User.objects.create_user(username=username, password=password)
            # Create profile and inventory automatically for the new user
            UserProfile.objects.create(user=user, coins=100, streak=0)
            Inventory.objects.create(user=user)
            login(request, user)
            return redirect('library')

    return render(request, 'main/register.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')



#  LIBRARY


@login_required
def library(request):
    """Main library page — shows all subjects for the logged-in user."""
    subjects = Subject.objects.filter(user=request.user)
    profile = UserProfile.objects.get(user=request.user)
    return render(request, 'main/library.html', {
        'subjects': subjects,
        'profile': profile,
    })


@login_required
def subject_detail(request, subject_id):
    """Detail page for one subject — shows all chapters."""
    subject = get_object_or_404(Subject, id=subject_id, user=request.user)
    chapters = Chapter.objects.filter(subject=subject).order_by('order')
    profile = UserProfile.objects.get(user=request.user)
    return render(request, 'main/subject_detail.html', {
        'subject': subject,
        'chapters': chapters,
        'profile': profile,
    })


@login_required
def create_subject(request):
    """Handle creating a new subject."""
    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.POST.get('icon', '📚')
        color = request.POST.get('color', '#ede9fe')
        first_chapter = request.POST.get('first_chapter', 'Chapter 1')

        subject = Subject.objects.create(
            user=request.user,
            name=name,
            icon=icon,
            color=color,
        )
        Chapter.objects.create(subject=subject, name=first_chapter, order=1)
        return redirect('subject_detail', subject_id=subject.id)

    return redirect('library')



#  STUDY / FLASHCARD GAME


@login_required
def study(request, chapter_id):
    """
    Study screen for a chapter.
    Loads flashcards and passes them to the template as JSON
    so the JavaScript can run the quiz without page reloads.
    """
    chapter = get_object_or_404(Chapter, id=chapter_id)
    cards = list(Flashcard.objects.filter(chapter=chapter))

    if not cards:
        return render(request, 'main/study_empty.html', {'chapter': chapter})

    random.shuffle(cards)

    # Build wrong-answer pool for multiple choice
    all_answers = list(Flashcard.objects.filter(
        chapter__subject=chapter.subject
    ).values_list('answer', flat=True))

    cards_data = []
    for card in cards:
        wrong_pool = [a for a in all_answers if a != card.answer]
        wrongs = random.sample(wrong_pool, min(3, len(wrong_pool)))
        choices = wrongs + [card.answer]
        random.shuffle(choices)
        cards_data.append({
            'id': card.id,
            'question': card.question,
            'answer': card.answer,
            'choices': choices,
        })

    inventory = Inventory.objects.get(user=request.user)
    profile = UserProfile.objects.get(user=request.user)

    return render(request, 'main/study.html', {
        'chapter': chapter,
        'cards_json': json.dumps(cards_data),
        'inventory': inventory,
        'profile': profile,
    })


@login_required
@require_POST
def submit_answer(request):
    """
    Called via fetch() from the study page JS every time the user answers.
    Awards coins, updates streak, returns updated state as JSON.
    """
    data = json.loads(request.body)
    correct = data.get('correct', False)
    timer_val = data.get('timer_val', 0)   # seconds left on timer when answered

    profile = UserProfile.objects.get(user=request.user)
    coins_earned = 0
    reason = ''

    if correct:
        coins_earned += 10
        reason = 'Correct answer'
        profile.streak += 1

        # Fast answer bonus
        if timer_val >= 40:
            coins_earned += 5
            reason += ' + speed bonus'

        # Streak milestone bonus
        if profile.streak % 3 == 0:
            coins_earned += 5
            reason += f' + {profile.streak}-streak bonus'

        profile.coins += coins_earned
        profile.save()

        CoinTransaction.objects.create(
            user=request.user,
            amount=coins_earned,
            reason=reason,
        )
    else:
        profile.streak = 0
        profile.save()

    return JsonResponse({
        'coins': profile.coins,
        'streak': profile.streak,
        'coins_earned': coins_earned,
    })


@login_required
@require_POST
def use_powerup(request):
    """
    Called when the user clicks a powerup button.
    Deducts 1 from their inventory and returns updated counts.
    """
    data = json.loads(request.body)
    powerup = data.get('powerup')  # 'freeze', 'saver', 'eliminator', 'hint'

    inventory = Inventory.objects.get(user=request.user)
    field_map = {
        'freeze': 'freeze',
        'saver': 'saver',
        'eliminator': 'eliminator',
        'hint': 'hint',
    }

    if powerup not in field_map:
        return JsonResponse({'success': False, 'error': 'Unknown powerup'})

    field = field_map[powerup]
    current = getattr(inventory, field)

    if current < 1:
        return JsonResponse({'success': False, 'error': 'None left'})

    setattr(inventory, field, current - 1)
    inventory.save()

    return JsonResponse({
        'success': True,
        'inventory': {
            'freeze': inventory.freeze,
            'saver': inventory.saver,
            'eliminator': inventory.eliminator,
            'hint': inventory.hint,
        }
    })


@login_required
@require_POST
def save_session(request):
    """
    Called at the end of a study session.
    Saves a StudySession record so Stats can display history.
    """
    data = json.loads(request.body)
    chapter_id = data.get('chapter_id')
    score = data.get('score', 0)
    streak_reached = data.get('streak_reached', 0)
    coins_earned = data.get('coins_earned', 0)

    chapter = get_object_or_404(Chapter, id=chapter_id)
    StudySession.objects.create(
        user=request.user,
        chapter=chapter,
        score=score,
        streak_reached=streak_reached,
        coins_earned=coins_earned,
    )
    return JsonResponse({'success': True})
