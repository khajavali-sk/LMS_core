from django.urls import path
from . import views


app_name = 'courses'
urlpatterns = [
    path('', views.home, name='home'),
    
    # path('learner_dashboard/', views.learner_dashboard, name='learner_dashboard'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/analytics/', views.course_analytics, name='course_analytics'),
    path('lesson/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
]