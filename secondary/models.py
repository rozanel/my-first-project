from django.db import models
from django.contrib.auth.models import User

class Inventory(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    freeze = models.IntegerField(default=0)
    saver = models.IntegerField(default=0)
    eliminator = models.IntegerField(default=0)
    hint = models.IntegerField(default=0)

class CoinTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    coins = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)

class MatchResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    pair_count = models.IntegerField()
    time_seconds = models.IntegerField()
    mistakes = models.IntegerField()
    stars = models.IntegerField()
    coins_earned = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)