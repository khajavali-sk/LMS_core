from django.db import models

# Create your models here.
from django.db import models
from users.models import User

from django.db import models
from users.models import User

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    # Added category field for filtering purposes
    category = models.CharField(max_length=100, blank=True)
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