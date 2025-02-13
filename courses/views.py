from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from .models import Course
from django.http import HttpResponseForbidden, HttpResponse

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



# @login_required
# def home(request):
#     courses = Course.objects.all()
#     return render(request, 'courses/home.html', {'courses': courses})





