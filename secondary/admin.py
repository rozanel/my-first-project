from django.contrib import admin
from .models import UserProfile, Inventory, CoinTransaction, MatchResult

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'coins', 'streak')

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'freeze', 'saver', 'eliminator', 'hint')

@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'reason', 'created_at')
    list_filter = ('user',)

@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'pair_count', 'time_seconds', 'mistakes', 'stars', 'coins_earned', 'created_at')
    list_filter = ('user', 'subject')
