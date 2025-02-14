from django.urls import path
from . import views
from django.contrib.auth import views as auth_views




app_name = 'users'
urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('learner_dashboard/', views.learner_dashboard, name='learner_dashboard'),
     path('learner/dashboard/', views.learner_dashboard, name='learner_dashboard'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    ]