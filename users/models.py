from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLES = (
        ('STUDENT', 'Student'),
        ('INSTRUCTOR', 'Instructor'),
        ('ADMIN', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLES, default='STUDENT')
    profile_pic = models.ImageField(upload_to='profiles/', blank=True)
    bio = models.TextField(blank=True)
    is_email_verified = models.BooleanField(default=False)
    # Use a through model for completed courses and track progress
    completed_courses = models.ManyToManyField('courses.Course', through='UserCourseProgress', blank=True)

    def __str__(self):
        return self.username
    

class OTPStorage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.email}"
    

class UserCourseProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    progress = models.FloatField(default=0.0)  # Percentage (0-100)
    completed_at = models.DateTimeField(null=True, blank=True)
    grade = models.CharField(max_length=5, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.progress}%)"
