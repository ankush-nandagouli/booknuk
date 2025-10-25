from django.db import models
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from accounts.models import CustomUser
from cloudinary.models import CloudinaryField


# ---------------------
# Utility Validators
# ---------------------
def validate_image_size(file):
    limit = 1 * 1024 * 1024  # 1 MB
    if file.size > limit:
        raise ValidationError('Image file too large. Max size is 1MB.')

def validate_pdf_size(file):
    limit = 5 * 1024 * 1024  # 5 MB
    if file.size > limit:
        raise ValidationError('PDF file too large. Max size is 5MB.')

# ---------------------
# Book Model
# ---------------------
class Book(models.Model):
    CATEGORY_CHOICES = [
        ('Programming', 'Programming'),
        ('CSE', 'CSE'),
        ('ME', 'ME'),
        ('MI', 'MI'),
        ('CE', 'CE'),
        ('Math', 'Math'),
        ('Other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    isbn = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        unique=True,  # ensures uniqueness in DB
        help_text="Enter a unique ISBN (leave blank if not available)"
    )

    cover_image = CloudinaryField(
        'image',
        folder='scep-lms/book_covers/',
        blank=True,
        null=True,
        help_text="Upload JPG or PNG image",
        # Cloudinary handles size limits differently
    )

    pdf_file = CloudinaryField(
        'raw',  # Use 'raw' for PDF files
        folder='scep-lms/book_pdfs/',
        blank=True,
        null=True,
        help_text="Upload a PDF file",
        resource_type='raw'  # Important for non-image files
    )

    available = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:  # only set slug if it's not already set
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            # ensure uniqueness
            while Book.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("books:book_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return f"{self.title} by {self.author}"


    def issue_book(self):
        """Decrease available copies when issued"""
        if self.available_copies > 0:
            self.available_copies -= 1
            self.save()
            return True
        return False

    def return_book(self):
        """Increase available copies when returned"""
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            self.save()


    def clean(self):
        """
        Extra validation to prevent duplicate ISBNs.
        This works at the Django level before saving.
        """
        if self.isbn:  # only check when ISBN is provided
            qs = Book.objects.exclude(pk=self.pk).filter(isbn=self.isbn)
            if qs.exists():
                raise ValidationError({'isbn': 'This ISBN already exists.'})


def cover_upload_to(instance, filename):
    # media/books/covers/<isbn>.<ext>
    ext = filename.split(".")[-1].lower()
    safe_isbn = (instance.isbn or "noisbn").replace(" ", "").replace("/", "_")
    return f"books/covers/{safe_isbn}.{ext}"

class Meta:
    ordering = ["-created_at"]
    def clean(self):
        if self.available_copies > self.total_copies:
            raise ValidationError({"available_copies": "Available copies cannot exceed total copies."})


    def save(self, *args, **kwargs):
        self.full_clean()
        # auto-toggle available by stock
        self.available = self.available_copies > 0
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("books:book_detail", args=[self.pk])

    @property
    def cover_url(self):
        """
        Use uploaded cover if present; otherwise fall back to your static default.
        """
        if self.cover_image:
            try:
                return self.cover_image.url
            except Exception:
                pass
        return "/static/images/default_cover.jpg"


class IssuedBook(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    return_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Set due date = issue_date + 14 days if not already set
        if not self.due_date:
            self.due_date = self.issue_date + timedelta(days=14)
        super().save(*args, **kwargs)

    @property
    def fine(self):
        """Calculate fine: ₹10 per overdue day"""
        today = date.today()

        # Normalize due_date to date (in case it's a datetime)
        due = self.due_date.date() if hasattr(self.due_date, "date") else self.due_date

        if self.return_date:
            returned = self.return_date.date() if hasattr(self.return_date, "date") else self.return_date
            if returned > due:
                return (returned - due).days * 10
            return 0
        else:
            if today > due:
                return (today - due).days * 10
        return 0
    def __str__(self):
        return f"{self.book.title} issued to {self.student.username}"
