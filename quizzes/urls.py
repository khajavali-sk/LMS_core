from django.urls import path
from . import views


app_name = 'quizzes'
urlpatterns = [
    path('quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
]