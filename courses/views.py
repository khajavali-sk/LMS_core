from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.db.models import Count, Avg, Case, When, Value, IntegerField, ExpressionWrapper, Subquery

from .models import Course, Lesson, Enrollment, UserProgress
from quizzes.models import Quiz

# Home view: Lists courses with optional category filtering
@login_required
def home(request):
    selected_category = request.GET.get('category', '')
    if selected_category:
        courses = Course.objects.filter(category=selected_category, is_published=True)
    else:
        courses = Course.objects.filter(is_published=True)
    categories = Course.objects.values_list('category', flat=True).distinct()
    context = {
        'courses': courses,
        'categories': categories,
        'selected_category': selected_category,
    }
    return render(request, 'courses/home.html', context)

# Course detail: Shows course information, enrollment status, and progress bar
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    progress = UserProgress.get_course_progress(request.user, course)
    context = {
        'course': course,
        'is_enrolled': is_enrolled,
        'progress': progress,
        'enrollment_count': course.enrollment_set.count()
    }
    return render(request, 'courses/course_detail.html', context)

# Enroll in a course (includes dummy premium check)
@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        # Dummy check: if course costs > 0 and user is not premium, redirect to payment
        if course.price > 0 and not getattr(request.user, 'is_premium', False):
            messages.warning(request, "This course requires a premium subscription. Please make a payment first.")
            # Redirect with course_id as a query parameter
            return redirect(f"{reverse('courses:payment_page')}?course_id={course.id}")
        
        Enrollment.objects.get_or_create(user=request.user, course=course)
        messages.success(request, "Successfully enrolled in the course!")
        return redirect('courses:course_detail', course_id=course.id)
    
    return redirect('courses:home')

# Lesson view: Marks lesson as completed; shows next lesson and quiz if available
@login_required
def lesson_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        return HttpResponseForbidden("You're not enrolled in this course")
    
    # Mark lesson as completed
    UserProgress.objects.update_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'completed_at': timezone.now()}
    )
    
    next_lesson = Lesson.objects.filter(
        module__course=course,
        order__gt=lesson.order
    ).order_by('order').first()

    context = {
        'lesson': lesson,
        'course': course,
        'next_lesson': next_lesson,
        'quiz': Quiz.objects.filter(lesson=lesson).first()
    }
    return render(request, 'courses/lesson_view.html', context)

# Course analytics: For instructors to view enrollments and average progress
@login_required
def course_analytics(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    total_enrollments = course.enrollment_set.count()

    # Calculate average progress across enrolled students
    all_progress = [
        UserProgress.get_course_progress(enrollment.user, course)
        for enrollment in course.enrollment_set.all()
    ]
    avg_progress = sum(all_progress) / len(all_progress) if all_progress else 0

    context = {
        'course': course,
        'enrollments': total_enrollments,
        'avg_progress': avg_progress,
    }
    return render(request, 'courses/course_analytics.html', context)

# Dummy Payment Page: Simulate payment success and enroll the user
@login_required
def payment_page(request):
    # Retrieve course_id from query parameters (e.g., ?course_id=1)
    course_id = request.GET.get('course_id')
    if not course_id:
        messages.error(request, "No course specified for payment.")
        return redirect('courses:home')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        # Simulate payment success: mark user as premium and enroll them
        request.user.is_premium = True
        request.user.save()
        Enrollment.objects.get_or_create(user=request.user, course=course)
        messages.success(request, "Payment successful! You are now enrolled in the course.")
        return redirect('courses:course_detail', course_id=course.id)
    
    return render(request, 'courses/payment_page.html', {'course': course})



# Existing imports and views ...

# New: Course Lessons View - Lists lessons for an enrolled course
@login_required
def course_lessons(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Ensure the user is enrolled in the course
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        return HttpResponseForbidden("You're not enrolled in this course")
    
    # Get lessons through modules
    lessons = Lesson.objects.filter(module__course=course).order_by('order')
    
    context = {
        'course': course,
        'lessons': lessons,
    }
    return render(request, 'courses/course_lessons.html', context)

