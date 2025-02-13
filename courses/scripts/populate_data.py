# courses/populate_data.py
from django.core.files import File
from django.contrib.auth import get_user_model
from courses.models import Category, Course, Module, Lesson, Enrollment, Review, UserProgress
from faker import Faker
import random
from datetime import timedelta

User = get_user_model()
fake = Faker()

def run():
    # Create Admin User
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@lms.com',
        password='adminpass',
        role='ADMIN'
    )
    
    # Create Categories
    categories = [
        ('Programming', 'Learn coding and software development'),
        ('Design', 'Master visual and UX design'),
        ('Business', 'Develop business skills'),
        ('Data Science', 'Work with data and analytics')
    ]
    
    created_categories = []
    for name, desc in categories:
        cat = Category.objects.create(
            name=name,
            slug=name.lower().replace(' ', '-')
        )
        created_categories.append(cat)
    
    # Create Instructors
    instructors = []
    for i in range(3):
        user = User.objects.create_user(
            username=f'instructor{i}',
            email=f'instructor{i}@lms.com',
            password='instructorpass',
            role='INSTRUCTOR',
            profile_pic=f'profiles/instructor{i}.jpg',
            bio=fake.text()
        )
        instructors.append(user)
    
    # Create Courses
    courses = []
    for i in range(5):
        course = Course.objects.create(
            title=fake.catch_phrase(),
            description=fake.paragraph(),
            category=random.choice(created_categories),
            instructor=random.choice(instructors),
            price=random.choice([0, 49.99, 99.99]),
            thumbnail=f'course_thumbnails/course{i}.jpg',
            is_published=True
        )
        courses.append(course)
    
    # Create Modules and Lessons
    for course in courses:
        for mod_num in range(1, 4):
            module = Module.objects.create(
                course=course,
                title=f'Module {mod_num}: {fake.word().title()}',
                order=mod_num
            )
            
            for les_num in range(1, 5):
                Lesson.objects.create(
                    module=module,
                    title=f'Lesson {les_num}: {fake.sentence()}',
                    content=fake.text(),
                    video_url=f'https://youtube.com/embed/{fake.uuid4()}',
                    duration=timedelta(minutes=random.randint(15, 60)),
                    order=les_num
                )
    
    # Create Students
    students = []
    for i in range(20):
        user = User.objects.create_user(
            username=f'student{i}',
            email=f'student{i}@lms.com',
            password='studentpass',
            role='STUDENT',
            profile_pic=f'profiles/student{i}.jpg',
            bio=fake.text()
        )
        students.append(user)
    
    # Create Enrollments
    for student in students:
        for course in random.sample(courses, k=random.randint(1, 3)):
            Enrollment.objects.create(
                user=student,
                course=course,
                is_paid=random.choice([True, False])
            )
    
    # Create Reviews
    for course in courses:
        for student in random.sample(students, k=random.randint(3, 8)):
            Review.objects.create(
                course=course,
                user=student,
                rating=random.randint(1, 5),
                comment=fake.paragraph()
            )
    
    # Create User Progress
    for enrollment in Enrollment.objects.all():
        lessons = Lesson.objects.filter(module__course=enrollment.course)
        for lesson in random.sample(list(lessons), k=random.randint(1, lessons.count())):
            UserProgress.objects.create(
                user=enrollment.user,
                lesson=lesson,
                score=random.randint(50, 100)
            )

    print("Database populated successfully!")

