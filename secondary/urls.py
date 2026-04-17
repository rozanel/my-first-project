from django.urls import path
from . import views

urlpatterns = [
    # Shop
    path('shop/',          views.shop,              name='shop'),
    path('shop/buy/',      views.buy_item,          name='buy_item'),

    # Matching game
    path('match/',         views.match_setup,       name='match_setup'),
    path('match/cards/',   views.match_cards,       name='match_cards'),
    path('match/result/',  views.save_match_result, name='save_match_result'),

    # Stats
    path('stats/',         views.stats,             name='stats'),
]
