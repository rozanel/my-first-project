from django.db import models
from django.contrib.auth.models import User


class Subject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default='📚')
    color = models.CharField(max_length=20, default='#ede9fe')

    def __str__(self):
        return self.name

    def mastery_percent(self):
        """Returns average mastery across all chapters."""
        chapters = self.chapter_set.all()
        if not chapters:
            return 0
        total = sum(c.mastery_percent() for c in chapters)
        return round(total / len(chapters))


class Chapter(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.subject.name} — {self.name}'

    def card_count(self):
        return self.flashcard_set.count()

    def mastery_percent(self):
        """
        Mastery = percentage of cards that have been answered correctly
        at least once in a StudySession for this chapter.
        """
        sessions = StudySession.objects.filter(chapter=self)
        if not sessions:
            return 0
        latest = sessions.order_by('-created_at').first()
        total = self.card_count()
        if total == 0:
            return 0
        return min(round((latest.score / total) * 100), 100)


class Flashcard(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()

    def __str__(self):
        return self.question[:50]


class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)          # number of correct answers
    streak_reached = models.IntegerField(default=0)
    coins_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} — {self.chapter.name} — {self.created_at.date()}'
