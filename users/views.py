from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.utils import timezone
from datetime import timedelta
from .models import User, OTPStorage
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import SignUpForm   #, ProfileUpdateForm
import random
from django.http import HttpResponseForbidden
from django.db.models import Case, When, Value, IntegerField, Avg, Count, OuterRef


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_email_verified = False
            user.save()
            
            # Generate and save OTP
            otp = str(random.randint(100000, 999999))
            OTPStorage.objects.create(user=user, otp=otp)  # This line was missing!
            
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
                
                # Check expiration (10 minutes)
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



def dashboard(request):
    pass


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from courses.models import Course, UserProgress, Enrollment
from quizzes.models import Quiz

@login_required
def learner_dashboard(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related('course')
    progress_data = []
    
    for enrollment in enrollments:
        progress = UserProgress.get_course_progress(request.user, enrollment.course)
        progress_data.append({
            'course': enrollment.course,
            'progress': progress,
            'last_accessed': enrollment.course.userprogress_set.latest('completed_at')
        })

    context = {
        'enrollments': progress_data,
        'completed_courses': request.user.completed_courses.count()
    }
    return render(request, 'users/learner_dashboard.html', context)


@login_required
def instructor_dashboard(request):
    if not request.user.role == 'INSTRUCTOR':
        return HttpResponseForbidden()
    
    courses = Course.objects.filter(instructor=request.user).annotate(
        total_enrollments=Count('enrollment'),
        avg_progress=Avg(
            Case(
                When(enrollment__user__userprogress__lesson__module__course=OuterRef('pk'), 
                     then=Value(1)),
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

# from courses.models import Course, Module, Lesson
# from users.models import User
# from django.utils.timezone import timedelta, now

# # Ensure there is at least one instructor
# instructor = User.objects.filter(role='INSTRUCTOR').first()
# if not instructor:
#     print("No instructor found. Please create an instructor first.")
# else:
#     # Define sample courses
#     courses_data = [
#         {
#             "title": "Python for Beginners",
#             "description": "Learn Python from scratch, covering basics to advanced topics.",
#             "category": "Programming",
#             "price": 49.99,
#         },
#         {
#             "title": "Machine Learning Basics",
#             "description": "An introduction to Machine Learning and AI concepts.",
#             "category": "AI & Data Science",
#             "price": 79.99,
#         },
#         {
#             "title": "Web Development with Django",
#             "description": "Learn to build full-stack web applications using Django.",
#             "category": "Web Development",
#             "price": 59.99,
#         },
#     ]

#     # Insert courses
#     for course_data in courses_data:
#         course = Course.objects.create(
#             title=course_data["title"],
#             description=course_data["description"],
#             category=course_data["category"],
#             instructor=instructor,
#             price=course_data["price"],
#             is_published=True,
#         )

#         # Create Modules for each course
#         for i in range(1, 4):  # 3 modules per course
#             module = Module.objects.create(
#                 course=course,
#                 title=f"Module {i} - {course.title}",
#                 order=i,
#             )

#             # Create Lessons for each module
#             for j in range(1, 4):  # 3 lessons per module
#                 Lesson.objects.create(
#                     module=module,
#                     title=f"Lesson {j} - {module.title}",
#                     content=f"Content for Lesson {j} of {module.title}.",
#                     video_url=f"https://example.com/video_{i}_{j}",
#                     duration=timedelta(minutes=10 * j),  # 10, 20, 30 min lessons
#                     is_free=(j == 1),  # First lesson is free
#                     order=j,
#                 )

#     print("✅ Courses, Modules, and Lessons added successfully!")
