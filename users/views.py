from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta
import random

from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseForbidden

from .models import User, OTPStorage
from .forms import SignUpForm  # Ensure this form exists in your project
from courses.models import Course, UserProgress, Enrollment
from quizzes.models import Quiz

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_email_verified = False
            user.save()
            
            # Generate and save OTP
            otp = str(random.randint(100000, 999999))
            OTPStorage.objects.create(user=user, otp=otp)
            
            # Send OTP via email
            send_mail(
                'Verify Your Email',
                f'Your OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            request.session['otp_user_id'] = user.id
            return redirect('users:verify_otp')
    else:
        form = SignUpForm()
    return render(request, 'users/signup.html', {'form': form})

def verify_otp(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        user_id = request.session.get('otp_user_id')
        
        if not user_id:
            messages.error(request, "Session expired. Please register again.")
            return redirect('users:signup')
            
        try:
            user = User.objects.get(id=user_id)
            try:
                stored_otp = OTPStorage.objects.filter(user=user).latest('created_at')
                
                # Check OTP expiration (10 minutes)
                if stored_otp.created_at < timezone.now() - timedelta(minutes=10):
                    messages.error(request, "OTP expired. Please request a new one.")
                    return redirect('users:signup')
                    
                if stored_otp.otp == otp_entered:
                    user.is_email_verified = True
                    user.save()
                    login(request, user)
                    del request.session['otp_user_id']  # Clear session
                    return redirect('courses:home')
                else:
                    messages.error(request, "Invalid OTP")
            except OTPStorage.DoesNotExist:
                messages.error(request, "No OTP found. Please register again.")
                return redirect('users:signup')
        except User.DoesNotExist:
            messages.error(request, "User not found. Please register again.")
            return redirect('users:signup')
    
    return render(request, 'users/verify_otp.html')

@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN':
        return HttpResponseForbidden()
    users = User.objects.all()
    return render(request, 'users/admin_dashboard.html', {'users': users})

@login_required
def learner_dashboard(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    progress_data = []
    
    for enrollment in enrollments:
        progress = UserProgress.get_course_progress(request.user, enrollment.course)
        # Using latest progress update as last accessed (if available)
        try:
            last_progress = enrollment.course.userprogress_set.latest('completed_at')
        except Exception:
            last_progress = None
        
        progress_data.append({
            'course': enrollment.course,
            'progress': progress,
            'last_accessed': last_progress
        })

    context = {
        'enrollments': progress_data,
        'completed_courses': request.user.completed_courses.count()
    }
    return render(request, 'users/learner_dashboard.html', context)

@login_required
def instructor_dashboard(request):
    if request.user.role != 'INSTRUCTOR':
        return HttpResponseForbidden()
    
    courses = Course.objects.filter(instructor=request.user).annotate(
        total_enrollments=Count('enrollment'),
        avg_progress=Avg(
            Case(
                When(enrollment__user__userprogress__lesson__module__course=OuterRef('pk'), then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        )
    )
    
    context = {
        'courses': courses,
        'total_students': User.objects.filter(role='STUDENT').count()
    }
    return render(request, 'users/instructor_dashboard.html', context)

def dashboard(request):
    # General dashboard view (extend as needed)
    pass




