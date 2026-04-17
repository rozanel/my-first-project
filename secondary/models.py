from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extends Django's built-in User with coins and streak.
    Every user gets one of these (created on registration).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coins = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} — {self.coins} coins'


class Inventory(models.Model):
    """
    Tracks how many of each powerup a user owns.
    Every user gets one of these (created on registration).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    freeze = models.IntegerField(default=0)
    saver = models.IntegerField(default=0)
    eliminator = models.IntegerField(default=0)
    hint = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} inventory'


class CoinTransaction(models.Model):
    """
    A log of every coin change — both earning and spending.
    Positive amount = earned. Negative = spent.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f'{self.user.username}: {sign}{self.amount} — {self.reason}'


class MatchResult(models.Model):
    """
    Stores the result of each matching game a user plays.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    pair_count = models.IntegerField()
    time_seconds = models.IntegerField()
    mistakes = models.IntegerField()
    stars = models.IntegerField()        # 1, 2, or 3
    coins_earned = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} — {self.subject} — {self.stars}⭐'
