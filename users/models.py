from django.db import models

# Create your models here.
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
    completed_courses = models.ManyToManyField('courses.Course', blank=True)
    is_email_verified = models.BooleanField(default=False)
    def __str__(self):
        return self.username
    


class OTPStorage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.email}"