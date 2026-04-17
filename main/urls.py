from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/',    views.login_view,    name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/',   views.logout_view,   name='logout'),

    # Library
    path('',                              views.library,        name='library'),
    path('subject/<int:subject_id>/',     views.subject_detail, name='subject_detail'),
    path('subject/create/',               views.create_subject, name='create_subject'),

    # Study game
    path('study/<int:chapter_id>/',       views.study,          name='study'),
    path('study/answer/',                 views.submit_answer,  name='submit_answer'),
    path('study/powerup/',                views.use_powerup,    name='use_powerup'),
    path('study/save/',                   views.save_session,   name='save_session'),
]
