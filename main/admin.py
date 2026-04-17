from django.contrib import admin
from .models import Subject, Chapter, Flashcard, StudySession

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'icon')
    list_filter = ('user',)

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'order', 'card_count')
    list_filter = ('subject',)

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ('question', 'chapter')
    list_filter = ('chapter__subject',)
    search_fields = ('question', 'answer')

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'chapter', 'score', 'streak_reached', 'coins_earned', 'created_at')
    list_filter = ('user',)
