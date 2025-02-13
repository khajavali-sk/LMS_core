from django.urls import path
from . import views 
from .views import *


app_name = 'courses'
urlpatterns = [
    path('', views.home, name='home'),
    
    # path('learner_dashboard/', views.learner_dashboard, name='learner_dashboard'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/analytics/', views.course_analytics, name='course_analytics'),
    path('lesson/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
    path('create/', CourseCreateView.as_view(), name='course_create'),
    path('<int:pk>/edit/', CourseUpdateView.as_view(), name='course_edit'),
    path('<int:pk>/manage/', views.manage_course, name='manage_course'),
    path('', views.course_list, name='course_list'),
    path('category/<slug:slug>/', views.category_view, name='category'),
]