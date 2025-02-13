from datetime import timezone
from django.db import models

# Create your models here.
from django.db import models
from users.models import User

from django.db import models
from users.models import User
from django.conf import settings

from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    # Added category field for filtering purposes
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    instructor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'INSTRUCTOR'}
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbnail = models.ImageField(upload_to='course_thumbnails/')
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
    def student_progress(self, user):
        total_lessons = self.lesson_set.count()
        completed = self.userprogress_set.filter(user=user).count()
        return {
            'completed': completed,
            'total': total_lessons,
            'percentage': round((completed / total_lessons) * 100) if total_lessons else 0
        }

# (Other models like Module, Lesson, UserProgress remain unchanged)


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()  # Can be HTML/JSON for rich content
    video_url = models.URLField(blank=True)
    duration = models.DurationField()  # e.g., "00:45:00"
    is_free = models.BooleanField(default=False)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']



class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')  # Prevent duplicate entries

    @staticmethod
    def get_course_progress(user, course):
        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_lessons = UserProgress.objects.filter(user=user, lesson__module__course=course).count()

        if total_lessons == 0:
            return 0  # Avoid division by zero

        return int((completed_lessons / total_lessons) * 100)  # Convert to percentage

    @classmethod
    def complete_lesson(cls, user, lesson):
        obj, created = cls.objects.get_or_create(
            user=user,
            lesson=lesson,
            defaults={'completed_at': timezone.now()}
        )
        return obj

class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'course')
    
    def __str__(self):
        return f"{self.user} in {self.course}"
    

# courses/models.py
class Review(models.Model):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('course', 'user')

    def __str__(self):
        return f"{self.user}'s review for {self.course}"
    



