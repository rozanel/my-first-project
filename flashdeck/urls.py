from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),        # Team A: library, study, flashcards
    path('', include('secondary.urls')),   # Team B: shop, match, stats, powerups
]
