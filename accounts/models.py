from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.text import slugify
import uuid
from django.conf import settings

def generate_library_id():
    """Generate a unique library card ID"""
    return f"LMS-{uuid.uuid4().hex[:8].upper()}"


class CustomUser(AbstractUser):
    # Role field with choices for better clarity and extensibility
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('librarian', 'Librarian'),
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='student',  # Default role for new users
    )

    is_approved = models.BooleanField(default=False, help_text="Admin approval required before login")
    slug = models.SlugField(unique=True, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)


    # Auto-generated unique library card ID
    library_card = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default=generate_library_id,
        unique=True,
        help_text="Auto-generated unique library card ID"
    )

    # Profile picture for students
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text="Student's profile image"
    )

    # Additional Student Profile Info
    branch = models.CharField(max_length=100, blank=True, null=True)
    roll_number = models.CharField(max_length=20, blank=True, null=True)
    academic_session = models.CharField(max_length=20, blank=True, null=True)
    mobile_number = models.CharField(max_length=10, blank=True, null=True)

    # Avoid conflicts with auth.User reverse relationships
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    @property
    def profile_completed(self):
        if self.is_librarian() or self.is_teacher():
            return True
        return all([
            self.branch,
            self.roll_number,
            self.mobile_number,
            self.academic_session,
            self.profile_picture
        ])

    def __str__(self):
        return self.username

    def is_student(self):
        return self.role == 'student'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_librarian(self):
        return self.role == 'librarian'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.username)  # or any unique field
        super().save(*args, **kwargs)

        # Generate Library Card ID for students and teachers only
        if self.role in ['student', 'teacher'] and not self.library_card:
            new_id = generate_library_id()
            while CustomUser.objects.filter(library_card_id=new_id).exists():
                new_id = generate_library_id()
            self.library_card_id = new_id

        super().save(*args, **kwargs)

class StudentRegistration(models.Model):
    COURSE_CHOICES = [
        ('BTECH', 'B.Tech'),
        ('POLY', 'Polytechnic'),
    ]


    YEAR_CHOICES = [
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=10)
    course = models.CharField(max_length=100, choices=COURSE_CHOICES)
    year_of_study = models.IntegerField(choices=YEAR_CHOICES)
    address = models.TextField()

    def __str__(self):
        return f"Student Registration: {self.full_name}"


class TeacherRegistration(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    address = models.TextField()

    def __str__(self):
        return f"Teacher Registration: {self.full_name}"