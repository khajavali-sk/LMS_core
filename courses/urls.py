from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.home, name='home'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('course/<int:course_id>/analytics/', views.course_analytics, name='course_analytics'),
    path('lesson/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
    path('course/<int:course_id>/lessons/', views.course_lessons, name='course_lessons'),  # New URL
    path('payment/', views.payment_page, name='payment_page'),

    
    path('instructor/create/', views.create_course, name='create_course'),
    path('instructor/manage/', views.manage_courses, name='manage_courses'),
]
