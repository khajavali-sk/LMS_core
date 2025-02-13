from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from .models import Course
from django.http import HttpResponseForbidden, HttpResponse
from courses.models import Course, UserProgress
from quizzes.models import Quiz
from django.utils.timezone import now 
from datetime import timedelta, timezone
from django.db.models import Case, When, Value, IntegerField, Avg, Count, OuterRef, ExpressionWrapper, Subquery, Q
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Course
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import ReviewForm
from django.contrib import messages
from .models import Course, Enrollment

from django.core.paginator import Paginator
from .models import Course, Category

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user.role != 'STUDENT':
        return HttpResponseForbidden()
    # Add payment integration here (Stripe/Razorpay)
    request.user.enrolled_courses.add(course)
    return redirect('course_detail', course_id=course.id)






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





# @login_required
# def course_detail(request, course_id):
#     course = get_object_or_404(Course, id=course_id)
#     lessons = course.lesson_set.all().order_by('order')
#     return render(request, 'courses/course_detail.html', {
#         'course': course,
#         'lessons': lessons
#     })




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




class CourseCreateView(CreateView):
    model = Course
    fields = ['title', 'description', 'category', 'price', 'thumbnail']
    template_name = 'courses/course_form.html'
    
    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('courses:manage_course', kwargs={'pk': self.object.pk})

class CourseUpdateView(UpdateView):
    model = Course
    fields = ['title', 'description', 'category', 'price', 'thumbnail', 'is_published']
    template_name = 'courses/course_form.html'
    
    def get_success_url(self):
        return reverse_lazy('courses:manage_course', kwargs={'pk': self.object.pk})

def manage_course(request, pk):
    course = get_object_or_404(Course, pk=pk, instructor=request.user)
    modules = course.module_set.annotate(
        lesson_count=Count('lesson')
    ).order_by('order')
    
    if request.method == 'POST':
        # Handle module/lesson ordering
        pass
    
    return render(request, 'courses/manage_course.html', {
        'course': course,
        'modules': modules
    })


@login_required
def track_progress(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    progress = course.student_progress(request.user)
    modules = course.module_set.annotate(
        completed_lessons=Count(
            'lesson__userprogress',
            filter=Q(lesson__userprogress__user=request.user)
    ))
    
    context = {
        'course': course,
        'progress': progress,
        'modules': modules
    }
    return render(request, 'courses/progress_tracking.html', context)



# courses/views.py
@login_required
def submit_review(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not course.enrollment_set.filter(user=request.user).exists():
        return HttpResponseForbidden("You must enroll first")
    
    review, created = Review.objects.get_or_create(
        course=course,
        user=request.user,
        defaults={'rating': 5}
    )
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review submitted successfully!")
            return redirect('course_detail', course_id=course.id)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'courses/review_form.html', {'form': form, 'course': course})



# courses/views.py
def landing_page(request):
    featured_courses = Course.objects.filter(is_published=True).order_by('-created_at')[:6]
    testimonials = Review.objects.select_related('user').order_by('-created_at')[:5]
    
    return render(request, 'landing.html', {
        'featured_courses': featured_courses,
        'testimonials': testimonials
    })





from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Course, Category

def course_list(request):
    # Get all published courses
    course_list = Course.objects.filter(is_published=True).annotate(
        enrollment_count=Count('enrollment')
    )  # Added missing parenthesis here

    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        course_list = course_list.filter(category=category)

    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        course_list = course_list.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(course_list, 9)  # 9 courses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all categories for filter sidebar
    categories = Category.objects.annotate(course_count=Count('course'))

    # Get trending courses (most enrolled)
    trending_courses = Course.objects.filter(is_published=True).annotate(
        enrollment_count=Count('enrollment')
    ).order_by('-enrollment_count')[:4]

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'trending_courses': trending_courses,
        'selected_category': category_slug,
        'search_query': search_query or ''
    }
    return render(request, 'courses/course_list.html', context)


from django.shortcuts import get_object_or_404
from .models import Category, Course

def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    courses = Course.objects.filter(category=category, is_published=True)
    
    return render(request, 'courses/category.html', {
        'category': category,
        'courses': courses
    })