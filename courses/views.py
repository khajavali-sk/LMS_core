from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from .models import Course
from django.http import HttpResponseForbidden, HttpResponse
from courses.models import Course, UserProgress
from quizzes.models import Quiz
from django.utils.timezone import now 
from datetime import timedelta, timezone
from django.db.models import Case, When, Value, IntegerField, Avg, Count, OuterRef, ExpressionWrapper, Subquery


@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user.role != 'STUDENT':
        return HttpResponseForbidden()
    # Add payment integration here (Stripe/Razorpay)
    request.user.enrolled_courses.add(course)
    return redirect('course_detail', course_id=course.id)




from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Course

@login_required
def home(request):
    # Get the category from the query string (if any)
    selected_category = request.GET.get('category', '')

    # Filter courses if a category is selected; otherwise, return all published courses
    if selected_category:
        courses = Course.objects.filter(category=selected_category, is_published=True)
    else:
        courses = Course.objects.filter(is_published=True)
    
    # Get distinct categories from all courses
    categories = Course.objects.values_list('category', flat=True).distinct()

    context = {
        'courses': courses,
        'categories': categories,
        'selected_category': selected_category,
    }
    return render(request, 'courses/home.html', context)



# courses/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Course, Lesson

# @login_required
# def course_detail(request, course_id):
#     course = get_object_or_404(Course, id=course_id)
#     lessons = course.lesson_set.all().order_by('order')
#     return render(request, 'courses/course_detail.html', {
#         'course': course,
#         'lessons': lessons
#     })


from django.contrib import messages
from .models import Course, Enrollment

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

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        if course.price > 0 and not request.user.is_premium:
            messages.warning(request, "Premium course requires subscription")
            return redirect('payment_page')
            
        Enrollment.objects.get_or_create(user=request.user, course=course)
        messages.success(request, "Successfully enrolled in course!")
        return redirect('course_detail', course_id=course.id)
    
    return redirect('course_list')

@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'courses/lesson_detail.html', {'lesson': lesson})



# @login_required
# def home(request):
#     courses = Course.objects.all()
#     return render(request, 'courses/home.html', {'courses': courses})


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


@login_required
def course_analytics(request, course_id):
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    # Progress distribution
    progress_data = UserProgress.objects.filter(
        lesson__module__course=course
    ).values('user').annotate(
        progress=ExpressionWrapper(
            Count('lesson') * 100 / Subquery(
                Lesson.objects.filter(module__course=course).values('module__course').annotate(
                    total=Count('id')).values('total')
            ),
            output_field=IntegerField()
        )
    )
    
    context = {
        'course': course,
        'enrollments': course.enrollment_set.count(),
        'completion_rate': course.userprogress_set.filter(
            lesson__module__course=course
        ).values('user').distinct().count(),
        'progress_distribution': progress_data
    }
    return render(request, 'courses/course_analytics.html', context)
